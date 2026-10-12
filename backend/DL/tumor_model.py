import os
import io
import logging
import numpy as np
from PIL import Image
import onnxruntime as ort

logger = logging.getLogger(__name__)

CLASS_NAMES = ["glioma", "meningioma", "notumor", "pituitary"]

CLASS_DISPLAY_NAMES = {
    "glioma": "Glioma",
    "meningioma": "Meningioma",
    "notumor": "No Tumor (Healthy)",
    "pituitary": "Pituitary Tumor"
}

TRIAGE_INFO = {
    "notumor": {
        "level": 0,
        "label": "Level 0 - Routine / No Neoplasm Detected",
        "severity": "low",
        "recommendation": "No abnormal neoplastic mass detected in the scan. Standard non-urgent outpatient follow-up recommended."
    },
    "pituitary": {
        "level": 1,
        "label": "Level 1 - Urgent / Pituitary Mass Detected",
        "severity": "medium",
        "recommendation": "Abnormal mass detected in the pituitary region. Prompt endocrine profiling and specialist neurosurgical consultation recommended."
    },
    "meningioma": {
        "level": 2,
        "label": "Level 2 - High Urgency / Meningioma Detected",
        "severity": "high",
        "recommendation": "Extra-axial mass consistent with meningioma detected. High-priority neurosurgical evaluation and contrast imaging required."
    },
    "glioma": {
        "level": 3,
        "label": "Level 3 - Critical Emergent / Glioma Detected",
        "severity": "critical",
        "recommendation": "Invasive parenchymal lesion consistent with glioma detected. Immediate emergency neurosurgical admission and neuro-oncology staging required."
    }
}

class TumorDetector:
    def __init__(self, model_filename: str = "brain_tumor_model.onnx"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, model_filename)
        self.session = None
        self.input_name = None
        self.output_name = None

        self._load_model()

    def _load_model(self):
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"❌ ONNX model file not found at {self.model_path}")
                return

            self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            logger.info(f"✅ Brain Tumor ONNX model loaded successfully from {self.model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load ONNX model: {str(e)}")
            self.session = None

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Takes raw image bytes, converts to RGB, resizes to (150, 150),
        and normalizes pixel values to [0, 1].
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((150, 150))
        img_array = np.array(image, dtype=np.float32) / 255.0
        # Expand dims to batch: (1, 150, 150, 3)
        img_tensor = np.expand_dims(img_array, axis=0)
        return img_tensor

    def predict(self, image_bytes: bytes) -> dict:
        """
        Runs inference on uploaded MRI image bytes and returns structured diagnostic results.
        """
        if self.session is None:
            # Attempt lazy reload if not loaded on startup
            self._load_model()
            if self.session is None:
                raise RuntimeError("Brain Tumor ONNX model is not loaded.")

        input_tensor = self.preprocess_image(image_bytes)
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        probabilities = outputs[0][0]  # shape (4,)

        predicted_idx = int(np.argmax(probabilities))
        predicted_class = CLASS_NAMES[predicted_idx]
        confidence = float(probabilities[predicted_idx]) * 100.0

        all_probs = {
            CLASS_DISPLAY_NAMES[CLASS_NAMES[i]]: round(float(probabilities[i]) * 100.0, 2)
            for i in range(len(CLASS_NAMES))
        }

        triage_meta = TRIAGE_INFO.get(predicted_class, {
            "level": 2,
            "label": "Level 2 - Urgent / Unspecified Lesion",
            "severity": "high",
            "recommendation": "Clinical review required."
        })

        return {
            "diagnosis": CLASS_DISPLAY_NAMES[predicted_class],
            "class_key": predicted_class,
            "confidence": round(confidence, 2),
            "all_probabilities": all_probs,
            "triage_level": triage_meta["level"],
            "triage_label": triage_meta["label"],
            "severity": triage_meta["severity"],
            "recommendation": triage_meta["recommendation"]
        }

# Singleton instance
tumor_detector = TumorDetector()
