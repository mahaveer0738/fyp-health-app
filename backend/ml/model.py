import pickle
import pandas as pd
import os
import logging
from .schema import PatientVitals, PredictionResponse

logger = logging.getLogger(__name__)

class TriageModel:
    def __init__(self, model_path: str = "pipe.pkl"):
        # Resolve path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, model_path)
        
        self.model = None
        self.triage_levels = {
            0: "Level 0 - Non-Urgent",
            1: "Level 1 - Less Urgent",
            2: "Level 2 - Urgent",
            3: "Level 3 - Emergent / Life-threatening"
        }
        
        try:
            with open(full_path, 'rb') as file:
                self.model = pickle.load(file)
            logger.info("✅ ML Model loaded successfully!")
        except FileNotFoundError:
            logger.error(f"❌ Error: Model file '{model_path}' not found at {full_path}")

    def predict(self, vitals: PatientVitals) -> PredictionResponse:
        if self.model is None:
            raise RuntimeError("Model is not loaded.")
            
        # Convert Pydantic model to DataFrame
        data_dict = vitals.model_dump()
        input_df = pd.DataFrame([data_dict])
        
        try:
            # Predict
            prediction = self.model.predict(input_df)[0]
            probability = self.model.predict_proba(input_df).max() * 100
            
            result_label = self.triage_levels.get(prediction, "Unknown")
            
            return PredictionResponse(
                triage_level=int(prediction),
                triage_label=result_label,
                probability=round(probability, 2)
            )
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise e

# Create a singleton instance to be imported by routes
triage_model = TriageModel()
