import os
import chromadb
from langchain_core.documents import Document

# Simple local ChromaDB client
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection_name = "medical_guidelines"

def get_collection():
    return client.get_or_create_collection(name=collection_name)

def add_documents(documents: list[str], ids: list[str], metadatas: list[dict] = None):
    collection = get_collection()
    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

def query_vectorstore(query_text: str, n_results: int = 3):
    collection = get_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    # Format as LangChain documents for easy integration
    docs = []
    if results['documents'] and len(results['documents']) > 0:
        for i, doc_text in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            docs.append(Document(page_content=doc_text, metadata=metadata))
            
    return docs
