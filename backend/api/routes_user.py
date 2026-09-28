from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.api.routes_auth import get_current_user
from backend.db.database import get_db
from backend.db.models import User, PatientProfile, VisitHistory

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/history")
def get_user_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    
    if not profile:
        return {"profile": None, "history": []}
        
    history = db.query(VisitHistory).filter(VisitHistory.patient_id == profile.id).order_by(VisitHistory.timestamp.desc()).all()
    
    # Map to expected frontend format
    history_result = []
    for h in history:
        history_result.append({
            "id": h.id,
            "created_at": h.timestamp.isoformat(),
            "symptoms": h.symptoms,
            "triage_level": int([c for c in h.triage_label if c.isdigit()][0]) if h.triage_label and any(c.isdigit() for c in h.triage_label) else 0,
            "triage_label": h.triage_label,
            "heart_rate": h.heart_rate,
            "systolic_blood_pressure": h.systolic_bp,
            "oxygen_saturation": h.oxygen_saturation
        })
        
    profile_result = {
        "name": profile.name,
        "age": profile.age,
        "gender": profile.gender,
        "chronic_conditions": profile.chronic_conditions,
        "email": current_user.email
    }
        
    return {"profile": profile_result, "history": history_result}

from backend.agent.tools.hospital_locator import search_places

@router.get("/locator")
async def locate_places(location: str, place_type: str = "hospital", query: str = ""):
    """Standalone API endpoint for the frontend locator tool."""
    if not query:
        query = "emergency hospital" if place_type == "hospital" else "pharmacy"
    results = await search_places(query=query, location=location, place_type=place_type)
    return results
