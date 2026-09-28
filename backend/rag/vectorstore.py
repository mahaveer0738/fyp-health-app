import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

# Path to save/load the local FAISS index
FAISS_INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faiss_index")

# Initialize HuggingFace embeddings
# We use all-MiniLM-L6-v2 as requested for local fast embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vectorstore():
    """Load the FAISS index if it exists, otherwise create a new empty one."""
    if os.path.exists(os.path.join(FAISS_INDEX_DIR, "index.faiss")):
        return FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    
    # Initialize a new empty FAISS store with a dummy document
    dummy_doc = Document(page_content="[System init]", metadata={"source": "init"})
    vs = FAISS.from_documents([dummy_doc], embeddings)
    vs.save_local(FAISS_INDEX_DIR)
    return vs

def add_documents(documents: list[str], ids: list[str], metadatas: list[dict] = None):
    vs = get_vectorstore()
    
    docs = []
    for i, doc_text in enumerate(documents):
        meta = metadatas[i] if metadatas else {}
        meta['id'] = ids[i]
        docs.append(Document(page_content=doc_text, metadata=meta))
        
    vs.add_documents(docs)
    vs.save_local(FAISS_INDEX_DIR)

def query_vectorstore(query_text: str, n_results: int = 3):
    vs = get_vectorstore()
    
    # Perform similarity search
    results = vs.similarity_search(query_text, k=n_results)
    
    # Filter out our dummy init document
    docs = [doc for doc in results if doc.page_content != "[System init]"]
    
    return docs
