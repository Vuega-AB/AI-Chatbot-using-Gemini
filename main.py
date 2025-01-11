import streamlit as st
from PyPDF2 import PdfReader
import pdfplumber
import os
import json
from io import BytesIO
from PIL import Image
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import io

load_dotenv()

fetched_api_key = os.getenv("API_Key")
genai.configure(api_key=fetched_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(
    page_title="AI Chatbot Assistant",
    page_icon="🤖"
)

def save_config(config):
    """Save configuration as a JSON file."""
    json_bytes = json.dumps(config).encode('utf-8')
    return BytesIO(json_bytes)

def load_config(uploaded_file):
    """Load configuration from a JSON file."""
    try:
        return json.load(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        return None

def process_pdfs(uploaded_files):
    """Extract text from multiple PDFs."""
    all_texts = []
    for uploaded_file in uploaded_files:
        text = ""
        try:
            file_bytes = io.BytesIO(uploaded_file.getvalue())
            with pdfplumber.open(file_bytes) as pdf:
                text = ''.join([page.extract_text() or " " for page in pdf.pages])
        except Exception as e:
            st.error(f"An error occurred with pdfplumber on file {uploaded_file.name}: {e}")

        if not text:
            try:
                file_bytes.seek(0)
                reader = PdfReader(file_bytes)
                text = ''.join([page.extract_text() or " " for page in reader.pages])
            except Exception as e:
                st.error(f"An error occurred with PyPDF2 on file {uploaded_file.name}: {e}")

        if text:
            all_texts.append(text)

    return "\n".join(all_texts)

def process_images(uploaded_images):
    """Process multiple images and convert them to a suitable format."""
    image_parts = []
    for uploaded_image in uploaded_images:
        try:
            image = Image.open(uploaded_image)
            if image.mode != "RGB":
                image = image.convert("RGB")
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            image_parts.append({
                "mime_type": "image/jpeg",
                "data": buffered.getvalue()
            })
        except Exception as e:
            st.error(f"An error occurred while processing the image {uploaded_image.name}: {e}")
    return image_parts

def send_message_to_genai(prompt, config, pdf_text=None, image_parts=None):
    """Send message to VertexAI and get the response."""
    system_prompt = config.get("system_prompt", "")
    prompt_parts = [system_prompt, pdf_text, prompt] if pdf_text else [system_prompt, prompt]

    try:
        input_parts = prompt_parts
        if image_parts:
            input_parts = image_parts + input_parts

        generation_config = genai.GenerationConfig(
            max_output_tokens=2048,
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 1.0),
            top_k=32
        )

        response = model.generate_content(
            input_parts, generation_config=generation_config
        )
        return response.text
    except Exception as e:
        st.error(f"An error occurred while sending to VertexAI: {e}")
        return None

def main():
    """Main function to run the Streamlit app."""
    st.title("AI Chatbot with PDF and Image Processing")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'config' not in st.session_state:
        st.session_state.config = {"system_prompt": "", "temperature": 0.7, "top_p": 1.0}

    uploaded_pdfs = st.file_uploader("Upload PDFs", type=['pdf'], accept_multiple_files=True)
    uploaded_images = st.file_uploader("Upload Images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

    with st.sidebar:
        st.write("**Configure Parameters**")
        config_file = st.file_uploader("Upload Configuration", type=['json'])
        if config_file:
            st.session_state.config = load_config(config_file)

        st.session_state.config["system_prompt"] = st.text_area(
            "System Prompt",
            value=st.session_state.config.get("system_prompt", "")
        )
        st.session_state.config["temperature"] = st.slider(
            "Temperature", 0.0, 1.0, st.session_state.config.get("temperature", 0.7)
        )
        st.session_state.config["top_p"] = st.slider(
            "Top-p Sampling", 0.0, 1.0, st.session_state.config.get("top_p", 1.0)
        )

        if st.button("Generate and Download Configuration"):
            config_bytes = save_config(st.session_state.config)
            st.download_button(
                "Download Config",
                data=config_bytes,
                file_name="config.json",
                mime="application/json"
            )

    pdf_text = process_pdfs(uploaded_pdfs) if uploaded_pdfs else None
    image_parts = process_images(uploaded_images) if uploaded_images else None

    user_prompt = st.chat_input("Ask a question:")

    if user_prompt:
        st.session_state.chat_history.append({"sender": "user", "text": user_prompt})
        response_text = send_message_to_genai(
            user_prompt,
            st.session_state.config,
            pdf_text,
            image_parts
        )
        st.session_state.chat_history.append({"sender": "assistant", "text": response_text})

    for message in st.session_state.chat_history:
        if message["sender"] == "user":
            st.chat_message("user").write(message['text'])
        else:
            st.chat_message("assistant").write(message['text'])

if __name__ == "__main__":
    main()
