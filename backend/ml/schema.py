from pydantic import BaseModel, Field

class PatientVitals(BaseModel):
    age: float = Field(..., description="Age of the patient in years")
    heart_rate: float = Field(..., description="Heart rate in beats per minute (bpm)")
    systolic_blood_pressure: float = Field(..., description="Systolic blood pressure in mmHg")
    oxygen_saturation: float = Field(..., description="Oxygen saturation (SpO2) percentage")
    body_temperature: float = Field(..., description="Body temperature in Celsius")
    pain_level: int = Field(..., ge=0, le=10, description="Self-reported pain level from 0 to 10")
    chronic_disease_count: int = Field(..., ge=0, description="Number of known chronic diseases")
    previous_er_visits: int = Field(..., ge=0, description="Number of previous ER visits")
    arrival_mode: str = Field(..., description="Mode of arrival (e.g., Ambulance, Walk-in, Private Vehicle)")

class PredictionResponse(BaseModel):
    triage_level: int
    triage_label: str
    probability: float
