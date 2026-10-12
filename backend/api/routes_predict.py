from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from backend.ml.schema import PatientVitals, PredictionResponse, MRIPredictionResponse
from backend.ml.model import triage_model
from backend.DL.tumor_model import tumor_detector
from backend.db.database import get_db
from backend.db.models import MRIPrediction, PatientProfile, User
from backend.api.routes_auth import get_current_user

router = APIRouter(prefix="/predict", tags=["ml_prediction"])

@router.post("/", response_model=PredictionResponse)
async def predict_triage(vitals: PatientVitals):
    """
    Takes patient vitals and returns the deterministic ML triage prediction.
    """
    try:
        result = triage_model.predict(vitals)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Service Unavailable: Model not loaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.post("/mri", response_model=MRIPredictionResponse)
async def predict_brain_mri(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an MRI scan image file (JPEG, PNG), performs ONNX inference,
    returns tumor classification, and saves the result to the logged-in user's profile.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG).")
    
    try:
        image_bytes = await file.read()
        prediction = tumor_detector.predict(image_bytes)
        
        # Find the patient profile
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
        if profile:
            # Save to database
            mri_record = MRIPrediction(
                patient_id=profile.id,
                diagnosis=prediction["diagnosis"],
                class_key=prediction["class_key"],
                confidence=prediction["confidence"],
                triage_level=prediction["triage_level"],
                triage_label=prediction["triage_label"],
                severity=prediction["severity"],
                recommendation=prediction["recommendation"]
            )
            db.add(mri_record)
            db.commit()
            
        return prediction
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
