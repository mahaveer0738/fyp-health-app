from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import json
from pydantic import ValidationError
import uuid

from backend.ml.schema import PatientVitals
from backend.agent.graph import clinical_agent

router = APIRouter(prefix="/chat", tags=["clinical_agent"])

@router.post("/")
async def chat_with_agent(
    symptoms: str = Form(...),
    location: str = Form("Unknown Location"),
    thread_id: Optional[str] = Form(None, description="Provide a thread ID to continue a conversation"),
    vitals_json: Optional[str] = Form(None, description="JSON string of PatientVitals"),
    file: Optional[UploadFile] = File(None, description="Optional prescription or lab report image")
):
    """
    Triggers the LangGraph clinical assistant workflow.
    Provides memory across requests if `thread_id` is supplied.
    """
    vitals_obj = None
    if vitals_json:
        try:
            vitals_dict = json.loads(vitals_json)
            vitals_obj = PatientVitals(**vitals_dict)
        except (json.JSONDecodeError, ValidationError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid vitals format: {e}")

    image_bytes = None
    if file:
        image_bytes = await file.read()
        
    initial_state = {
        "symptoms_text": symptoms,
        "user_location": location,
        "vitals": vitals_obj,
        "image_bytes": image_bytes,
        "messages": [] # The system will append to this automatically
    }
    
    # Use the provided thread_id or create a new one
    current_thread_id = thread_id if thread_id else str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": current_thread_id}}
    
    try:
        # Run the agent graph
        result = clinical_agent.invoke(initial_state, config=config)
        
        # The final message in the state is the agent's response
        final_message = result["messages"][-1].content if result.get("messages") else "No response generated."
        
        return {
            "thread_id": current_thread_id,
            "ml_prediction": result.get("ml_prediction"),
            "ocr_extracted": bool(result.get("ocr_text")),
            "agent_response": final_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")
