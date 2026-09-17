import operator
from typing import TypedDict, Annotated, Optional, List
from langchain_core.messages import BaseMessage
from backend.ml.schema import PatientVitals, PredictionResponse

def add_messages(left: list, right: list):
    """Reducer function to append new messages to the existing list."""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right

class AgentState(TypedDict):
    # Core Agent conversational memory
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Inputs
    vitals: Optional[PatientVitals]
    symptoms_text: str
    image_bytes: Optional[bytes]
    user_location: str  # Added for tools to use
    
    # Intermediates
    ocr_text: Optional[str]
    ml_prediction: Optional[PredictionResponse]
    retrieved_context: List[str]
