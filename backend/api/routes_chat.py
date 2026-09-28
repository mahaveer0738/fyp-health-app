from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional
from sqlalchemy.orm import Session
import json
from pydantic import ValidationError
import uuid
import httpx
import logging
from langchain_core.messages import HumanMessage

from backend.ml.schema import PatientVitals
from backend.agent.graph import clinical_agent
from backend.api.routes_auth import get_current_user
from backend.db.database import get_db
from backend.db.models import User, VisitHistory, PatientProfile
from backend.agent.tools.email_alert import send_visit_summary_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["clinical_agent"])


async def _reverse_geocode(lat: float, lon: float) -> str:
    """Reverse-geocode lat/lon to a human-readable location string using Nominatim."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
        headers = {"User-Agent": "FYP-Health-App/2.0 (student-project)"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            data = resp.json()
            # Build a readable string from the address components
            addr = data.get("address", {})
            parts = [
                addr.get("city") or addr.get("town") or addr.get("village", ""),
                addr.get("state", ""),
                addr.get("country", "")
            ]
            return ", ".join([p for p in parts if p]) or data.get("display_name", "Unknown")
    except Exception as e:
        logger.warning(f"Reverse geocode failed: {e}")
        return "Unknown"


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
    vitals_dict = {}
    if vitals_json:
        try:
            vitals_dict = json.loads(vitals_json)
            vitals_obj = PatientVitals(**vitals_dict)
        except (json.JSONDecodeError, ValidationError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid vitals format: {e}")

    image_bytes = None
    if file:
        image_bytes = await file.read()
        
    # Parse GPS coordinates from location JSON
    lat, lon = None, None
    location_string = "Unknown"
    try:
        loc_data = json.loads(location)
        lat = float(loc_data.get("lat", 0))
        lon = float(loc_data.get("lon", 0))
        if lat and lon:
            location_string = await _reverse_geocode(lat, lon)
    except (json.JSONDecodeError, TypeError, ValueError):
        location_string = location if location != "Unknown Location" else "Unknown"

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
                "location": h.location_string or "Unknown",
            })
            
    initial_state = {
        "symptoms_text": symptoms,
        "user_location": location_string if location_string != "Unknown" else location,
        "vitals": vitals_obj,
        "image_bytes": image_bytes,
        "patient_profile": profile_dict,
        "visit_history": history_dicts,
        "user_email": current_user.email,
        "messages": [HumanMessage(content=symptoms)]
    }
    
    # Use the provided thread_id or create a new one
    current_thread_id = thread_id if thread_id else str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": current_thread_id}}
    
    try:
        # Run the agent graph asynchronously to support async tools
        result = await clinical_agent.ainvoke(initial_state, config=config)
        
        # The final message in the state is the agent's response
        final_message = result["messages"][-1].content if result.get("messages") else "No response generated."
        
        # Extract ML prediction safely
        ml_pred = result.get("ml_prediction")
        if isinstance(ml_pred, dict):
            triage_label = ml_pred.get("triage_label", "Unknown")
            triage_confidence = ml_pred.get("probability")
        else:
            triage_label = getattr(ml_pred, "triage_label", "Unknown") if ml_pred else "Unknown"
            triage_confidence = getattr(ml_pred, "probability", None) if ml_pred else None

        # Only save this visit and send an email if it's the FIRST message of a new session (indicated by the presence of vitals)
        if vitals_json and profile:
            new_visit = VisitHistory(
                patient_id=profile.id,
                symptoms=symptoms,
                triage_label=triage_label,
                triage_confidence=triage_confidence,
                ai_summary=final_message,
                # Vitals snapshot
                heart_rate=vitals_dict.get("heart_rate"),
                systolic_bp=vitals_dict.get("systolic_blood_pressure"),
                oxygen_saturation=vitals_dict.get("oxygen_saturation"),
                body_temperature=vitals_dict.get("body_temperature"),
                pain_level=vitals_dict.get("pain_level"),
                # Location data
                latitude=lat,
                longitude=lon,
                location_string=location_string,
                # Session metadata
                arrival_mode=vitals_dict.get("arrival_mode"),
                input_mode="manual",
                ocr_extracted=bool(result.get("ocr_text")),
            )
            db.add(new_visit)
            db.commit()
            
            # Send summary email for EVERY NEW visit
            try:
                send_visit_summary_email.invoke({
                    "user_email": current_user.email,
                    "ai_summary": final_message,
                    "triage_label": triage_label
                })
            except Exception as e:
                logger.error(f"Failed to send email summary: {e}")
            
        return {
            "thread_id": current_thread_id,
            "ml_prediction": result.get("ml_prediction"),
            "ocr_extracted": bool(result.get("ocr_text")),
            "agent_response": final_message
        }
    except Exception as e:
        import traceback
        logger.error(f"Agent workflow failed:\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")

