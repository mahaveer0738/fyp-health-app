import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.rag.vectorstore import add_documents
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_pdfs(data_dir: str = "../../data/"):
    """
    Reads all PDFs in the data directory, chunks them, and stores them in ChromaDB.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_data_dir = os.path.abspath(os.path.join(current_dir, data_dir))
    
    pdf_files = glob.glob(os.path.join(full_data_dir, "*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {full_data_dir}")
        return
        
    logger.info(f"Found {len(pdf_files)} PDF(s). Starting ingestion...")
    
    all_docs = []
    for pdf_path in pdf_files:
        logger.info(f"Loading {os.path.basename(pdf_path)}...")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        all_docs.extend(docs)
        
    logger.info(f"Loaded {len(all_docs)} pages. Splitting text...")
    
    # Split text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(all_docs)
    
    logger.info(f"Created {len(splits)} chunks. Storing in ChromaDB...")
    
    # Prepare data for ChromaDB
    documents = [split.page_content for split in splits]
    metadatas = [split.metadata for split in splits]
    ids = [f"doc_{i}" for i in range(len(splits))]
    
    add_documents(documents=documents, ids=ids, metadatas=metadatas)
    
    logger.info("✅ Ingestion complete! The Vector DB is ready.")

if __name__ == "__main__":
    ingest_pdfs()
