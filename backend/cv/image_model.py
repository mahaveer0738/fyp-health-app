import base64
from io import BytesIO
from PIL import Image
from google import genai
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize GenAI client
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Uses Gemini Multimodal to perform OCR and entity extraction on a prescription or lab report.
    """
    if not client:
        logger.warning("Gemini API Key not set. Cannot perform OCR.")
        return "OCR Unavailable: Gemini API key missing."
        
    try:
        # We can pass PIL Image to google-genai
        img = Image.open(BytesIO(image_bytes))
        
        prompt = (
            "You are a medical OCR assistant. Read this medical document (prescription or lab report). "
            "Extract all text, but structure it clearly. Highlight medications, dosages, and patient conditions. "
            "Do not invent any information. Only return what is written."
        )
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt, img]
        )
        
        return response.text
    except Exception as e:
        logger.error(f"Error during OCR extraction: {str(e)}")
        return f"Error extracting text: {str(e)}"
