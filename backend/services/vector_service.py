# backend/services/vector_service.py

import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
# <<< 1. IMPORT THE NEW HUGGING FACE EMBEDDING CLASS >>>
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from dotenv import load_dotenv

from core.config import LOCAL_VECTOR_STORE_DIR

# --- CONFIGURATION ---
load_dotenv() 

os.makedirs(LOCAL_VECTOR_STORE_DIR, exist_ok=True)

# <<< 2. INITIALIZE THE LOCAL HUGGING FACE EMBEDDINGS MODEL (LAZY LOAD) >>>
embeddings_model = None

def get_embeddings_model():
    """Lazy load embeddings model to avoid startup delays"""
    global embeddings_model
    if embeddings_model is None:
        try:
            # This model runs on your CPU, avoiding API calls and rate limits.
            model_name = "all-MiniLM-L6-v2"
            model_kwargs = {'device': 'cpu'}
            embeddings_model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs
            )
            print(f"INFO: Local embedding model '{model_name}' loaded successfully.")
        except Exception as e:
            print(f"CRITICAL: Failed to load local embedding model. Error: {e}")
            embeddings_model = None
    return embeddings_model

# --- PUBLIC FUNCTIONS ---

async def create_vector_store_for_book(book_id: str, book_text: str) -> bool:
    """
    Creates and saves a FAISS vector store for the text content of a single book.
    """
    embeddings = get_embeddings_model()
    if not embeddings:
        print(f"ERROR: Cannot create vector store for book_id {book_id}. Embeddings model not available.")
        return False
        
    print(f"INFO: Starting vector store creation for book_id: {book_id}")
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(book_text)
        
        if not chunks:
            print(f"WARNING: No text chunks were generated for book_id: {book_id}.")
            return False

        print(f"INFO: Split text into {len(chunks)} chunks for book_id: {book_id}")

        vector_store = FAISS.from_texts(texts=chunks, embedding=embeddings)
        
        file_path = os.path.join(LOCAL_VECTOR_STORE_DIR, f"{book_id}.faiss")
        vector_store.save_local(file_path)
        
        print(f"INFO: Successfully created and saved vector store for book_id: {book_id} at {file_path}")
        return True

    except Exception as e:
        print(f"ERROR: Failed during vector store creation for book_id {book_id}. Error: {e}")
        return False

def search_in_vector_store(book_id: str, query: str, k: int = 4) -> List[Document]:
    """
    Searches for relevant documents in a book's vector store.
    """
    embeddings = get_embeddings_model()
    if not embeddings:
        print("ERROR: Cannot search vector store. Embeddings model not available.")
        return []

    vector_store_path = os.path.join(LOCAL_VECTOR_STORE_DIR, f"{book_id}.faiss")
    
    if not os.path.exists(vector_store_path):
        print(f"WARNING: No vector store found for book_id: {book_id} at {vector_store_path}")
        return []

    try:
        # Load the local FAISS index
        vector_store = FAISS.load_local(
            vector_store_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # Perform similarity search to get the most relevant chunks
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        relevant_docs = retriever.invoke(query)
        
        print(f"INFO: Retrieved {len(relevant_docs)} documents for query in book_id: {book_id}")
        return relevant_docs

    except Exception as e:
        print(f"ERROR: Failed to search in vector store for book_id {book_id}. Error: {e}")
        return []