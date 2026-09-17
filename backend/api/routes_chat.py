from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional
from sqlalchemy.orm import Session
import json
from pydantic import ValidationError
import uuid

from backend.ml.schema import PatientVitals
from backend.agent.graph import clinical_agent
from backend.api.routes_auth import get_current_user
from backend.db.database import get_db
from backend.db.models import User, VisitHistory, PatientProfile
from backend.agent.tools.email_alert import send_visit_summary_email

router = APIRouter(prefix="/chat", tags=["clinical_agent"])

@router.post("/")
async def chat_with_agent(
    symptoms: str = Form(...),
    location: str = Form("Unknown Location"),
    thread_id: Optional[str] = Form(None, description="Provide a thread ID to continue a conversation"),
    vitals_json: Optional[str] = Form(None, description="JSON string of PatientVitals"),
    file: Optional[UploadFile] = File(None, description="Optional prescription or lab report image"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        
    # Fetch patient profile and history
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    
    profile_dict = {}
    history_dicts = []
    
    if profile:
        profile_dict = {
            "name": profile.name,
            "age": profile.age,
            "gender": profile.gender,
            "chronic_conditions": profile.chronic_conditions
        }
        
        history = db.query(VisitHistory).filter(VisitHistory.patient_id == profile.id).order_by(VisitHistory.timestamp.asc()).all()
        for h in history:
            history_dicts.append({
                "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M"),
                "symptoms": h.symptoms,
                "triage_label": h.triage_label,
            })
            
    initial_state = {
        "symptoms_text": symptoms,
        "user_location": location,
        "vitals": vitals_obj,
        "image_bytes": image_bytes,
        "patient_profile": profile_dict,
        "visit_history": history_dicts,
        "user_email": current_user.email,
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
        
        # Save this visit to history
        if profile:
            ml_pred = result.get("ml_prediction")
            triage_label = ml_pred.triage_label if ml_pred else "Unknown"
            
            new_visit = VisitHistory(
                patient_id=profile.id,
                symptoms=symptoms,
                triage_label=triage_label,
                ai_summary=final_message
            )
            db.add(new_visit)
            db.commit()
            
            # Send summary email for EVERY visit
            send_visit_summary_email(current_user.email, final_message, triage_label)
            
        return {
            "thread_id": current_thread_id,
            "ml_prediction": result.get("ml_prediction"),
            "ocr_extracted": bool(result.get("ocr_text")),
            "agent_response": final_message
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")
