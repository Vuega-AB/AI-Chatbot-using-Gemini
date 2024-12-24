import streamlit as st
from PyPDF2 import PdfReader
import pdfplumber
import os
from io import BytesIO
from PIL import Image
import google.generativeai as genai
import io

# Initialize and configure the environment
from dotenv import load_dotenv
load_dotenv()  # This will load environment variables from a .env file

fetched_api_key = os.getenv("API_Key")
genai.configure(api_key=fetched_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


def process_pdf(uploaded_file):
    text = ""
    try:
        # Read the uploaded PDF file into a BytesIO stream
        file_bytes = io.BytesIO(uploaded_file.getvalue())

        # Use pdfplumber to extract text
        with pdfplumber.open(file_bytes) as pdf:
            text = ''.join([page.extract_text() or " " for page in pdf.pages])
    except Exception as e:
        st.error(f"An error occurred with pdfplumber: {e}")

    if not text:  # Fallback to PyPDF2 if pdfplumber fails or returns empty text
        try:
            file_bytes.seek(0)  # Reset file pointer for PyPDF2
            reader = PdfReader(file_bytes)
            text = ''.join([page.extract_text() or " " for page in reader.pages])
        except Exception as e:
            st.error(f"An error occurred with PyPDF2: {e}")

    if not text:
        st.error("Failed to extract text from the PDF.")
        return None

    return text

def process_image(uploaded_image):
    try:
        # Load the image
        image = Image.open(uploaded_image)
        
        # Convert the grayscale image to bytes
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return {
            "mime_type": "image/jpeg",
            "data": buffered.getvalue()
        }
    except Exception as e:
        st.error(f"An error occurred while processing the image: {e}")
        return None



def send_message_to_genai(prompt, pdf_text=None, image_part=None):
    prompt_parts = [prompt]
    
    if pdf_text:
        prompt_parts.insert(0, pdf_text)  # Include PDF text
    
    if image_part:
        prompt_parts.append(image_part)  # Include image data

    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while sending to GenAI: {e}")
        return None


def handle_chat_interaction(prompt, messages_container, pdf_text=None, image_part=None):
    if not prompt.strip():
        st.warning("Please enter some text to send.")
        return

    st.session_state.chat_history.append({"sender": "user", "text": prompt})

    try:
        with st.spinner("Thinking..."):
            response_text = send_message_to_genai(prompt, pdf_text, image_part)
    except Exception as e:
        response_text = f"An error occurred: {str(e)}"
        st.error(response_text)

    st.session_state.chat_history.append({"sender": "assistant", "text": response_text})
    for message in st.session_state.chat_history:
        if message["sender"] == "user":
            messages_container.chat_message("user").write(message['text'])
        else:
            messages_container.chat_message("assistant").write(message['text'])


def main():
    st.title("AI Chatbot with PDF and Image Processing")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    uploaded_file = st.file_uploader("Upload a PDF", type=['pdf'])
    uploaded_image = st.file_uploader("Upload an Image", type=['jpg', 'jpeg', 'png'])

    pdf_text = None
    image_part = None

    if uploaded_file:
        pdf_text = process_pdf(uploaded_file)
        st.session_state.pdf_text = pdf_text if pdf_text else ""

    if uploaded_image:
        image_part = process_image(uploaded_image)

    if pdf_text or image_part:
        user_prompt = None
        messages = st.container()

        if st.button("Get Summary"):
            user_prompt = "Provide a concise summary of the document and analyze the image."

        custom_prompt = st.chat_input("Or ask your question:")
        if custom_prompt:
            user_prompt = custom_prompt

        if user_prompt:
            handle_chat_interaction(user_prompt, messages, pdf_text, image_part)


if __name__ == "__main__":
    main()
