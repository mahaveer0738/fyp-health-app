from backend.agent.state import AgentState
from backend.rag.vectorstore import query_vectorstore

def retrieval_node(state: AgentState) -> dict:
    """
    Queries ChromaDB based on patient symptoms and extracted OCR text.
    """
    query_text = state.get("symptoms_text", "")
    
    ocr_text = state.get("ocr_text")
    if ocr_text:
        query_text += f"\n\nContext from scanned document:\n{ocr_text}"
        
    if not query_text.strip():
        return {"retrieved_context": []}
        
    docs = query_vectorstore(query_text, n_results=3)
    
    context_chunks = [doc.page_content for doc in docs]
    
    return {"retrieved_context": context_chunks}
