import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # Default model names
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

settings = Settings()
