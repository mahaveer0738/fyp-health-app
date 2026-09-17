import os
import resend
from langchain_core.tools import tool
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# We expect RESEND_API_KEY to be in the .env file.
resend.api_key = os.getenv("RESEND_API_KEY", "")

def send_visit_summary_email(user_email: str, ai_summary: str, triage_label: str) -> bool:
    """
    Sends an automated visit summary email to the patient after every consultation.
    """
    if not resend.api_key:
        print("Warning: RESEND_API_KEY is missing. Cannot send summary email.")
        return False
        
    try:
        html_content = f"""
        <div style='font-family: sans-serif; color: #1a2340;'>
            <h2>🏥 ER Triage - Visit Summary</h2>
            <p>Thank you for using our AI triage system. Below is a summary of your consultation:</p>
            <div style='background: #f0f4fb; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <p><strong>Predicted Triage Level:</strong> {triage_label}</p>
                <p><strong>Clinical Advice:</strong><br/>
                {ai_summary.replace(chr(10), '<br>')}</p>
            </div>
            <p style='font-size: 0.8rem; color: #7a8aab;'>Please remember to consult a real medical professional for emergencies.</p>
        </div>
        """
        
        params = {
            "from": "onboarding@resend.dev",
            "to": [user_email],
            "subject": "Your ER Triage Visit Summary",
            "html": html_content
        }
        
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Failed to send summary email: {e}")
        return False

