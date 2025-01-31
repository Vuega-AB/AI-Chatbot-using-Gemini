import os
import json
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma  # Updated import
from together import Together
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Together API Key
api_key = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""  # Ensure no NoneType issues
    return text.strip()

def split_text_into_chunks(text):
    """Split text into manageable chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_text(text)

def create_embedding(text):
    """Generate embeddings using DeepSeek API."""
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": f"Create an embedding vector for: {text}"}],
        max_tokens=150
    )

    # Extract response content
    content = response.choices[0].message.content
    print("Raw Response:", content)  # Debugging: Print raw response

    if not content:
        raise ValueError("Received empty response from DeepSeek.")

    try:
        # Expecting JSON format for embeddings
        embedding = json.loads(content)
        if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
            raise ValueError("Invalid embedding format received.")
        return embedding
    except json.JSONDecodeError:
        raise ValueError(f"Response from DeepSeek could not be parsed as JSON: {content}")

def store_embeddings(vectorstore, chunks):
    """Store text embeddings in ChromaDB."""
    for chunk in chunks:
        try:
            vector = create_embedding(chunk)
            vectorstore.add_texts([chunk], vectors=[vector])
        except ValueError as e:
            print(f"Skipping chunk due to error: {e}")

def query_vector_database(vectorstore, query_text):
    """Retrieve relevant chunks from the vector database."""
    query_vector = create_embedding(query_text)
    results = vectorstore.similarity_search_by_vector(query_vector, k=3)
    return " ".join([doc.page_content for doc in results])

def generate_answer_with_deepseek(context, question):
    """Generate an answer using Together DeepSeek."""
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "system", "content": "Use the provided context to answer the user's question."},
            {"role": "user", "content": f"Context: {context}. Question: {question}"}
        ],
        max_tokens=200,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

# Main workflow
pdf_path = "WEF_Future_of_Jobs_2023-82-143.pdf"
user_query = "What does the document say about future job trends?"

# Extract text and split into chunks
pdf_text = extract_text_from_pdf(pdf_path)
if not pdf_text:
    raise ValueError("No text extracted from the PDF. Check the file.")

chunks = split_text_into_chunks(pdf_text)

# Initialize vector store
vectorstore = Chroma()

# Store embeddings
store_embeddings(vectorstore, chunks)

# Query the database
retrieved_context = query_vector_database(vectorstore, user_query)

# Generate the answer
answer = generate_answer_with_deepseek(retrieved_context, user_query)

print("\nAI's Response:")
print(answer)
