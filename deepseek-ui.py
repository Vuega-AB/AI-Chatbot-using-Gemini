import os
import streamlit as st
import openai
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from together import Together
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

# Initialize Together API client
client = Together(api_key=TOGETHER_API_KEY)

# Initialize OpenAI embeddings
embedding_function = OpenAIEmbeddings(model="text-embedding-ada-002")

# ChromaDB Setup (Fixes tenant error)
DB_PATH = "chroma_db"
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

vectorstore = None  # Initialize empty vectorstore

# Load stored vectorstore if exists
if os.path.exists(DB_PATH):
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)

# Streamlit UI Configuration
st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 AI Chatbot with DeepSeek-V3")
st.markdown("💡 **Ask me anything based on your uploaded PDFs!**")

# Extract Text from PDFs
def extract_text_from_pdfs(pdf_files):
    text = ""
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        text += "".join(page.extract_text() or "" for page in reader.pages)
    return text.strip()

# Split Text into Chunks
def split_text_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_text(text)

# Store Embeddings in ChromaDB
def store_embeddings(chunks):
    global vectorstore  # Ensure we store the vector DB globally
    vectorstore = Chroma.from_texts(chunks, embedding=embedding_function, persist_directory=DB_PATH)
    return vectorstore

# Retrieve Relevant Chunks
def query_vector_database(query_text):
    if vectorstore is None:
        return "⚠️ No database found. Please upload PDFs first!"
    
    results = vectorstore.similarity_search(query_text, k=3)
    return " ".join([doc.page_content for doc in results])

# Generate Answers with DeepSeek-V3
def generate_answer_with_deepseek(context, question):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "system", "content": "Use the provided context to answer the user's question."},
            {"role": "user", "content": f"Context: {context}. Question: {question}"}
        ],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Streamlit Sidebar
with st.sidebar:
    st.header("📂 Upload PDFs")
    uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.success("✅ PDFs uploaded successfully!")

    with st.spinner("📖 Extracting text..."):
        pdf_text = extract_text_from_pdfs(uploaded_files)

    with st.spinner("✂️ Splitting text into chunks..."):
        chunks = split_text_into_chunks(pdf_text)

    with st.spinner("📥 Storing embeddings in ChromaDB..."):
        store_embeddings(chunks)

    st.success("✅ PDF processing complete! Now ask a question.")

# Chat Interface
st.subheader("💬 Chat with AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
user_query = st.chat_input("Type your question here...", key="unique_chat_input")
if user_query:
    # Save user message before displaying
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Retrieve relevant context
    with st.spinner("🔍 Searching relevant information..."):
        retrieved_context = query_vector_database(user_query)

    # Generate AI response
    with st.spinner("🤖 Generating response..."):
        answer = generate_answer_with_deepseek(retrieved_context, user_query)

    # Save AI response
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display AI response
    with st.chat_message("assistant"):
        st.markdown(answer)
