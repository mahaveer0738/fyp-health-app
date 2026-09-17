from fastapi import APIRouter, HTTPException
from backend.ml.schema import PatientVitals, PredictionResponse
from backend.ml.model import triage_model

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
