import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools.email_alert import send_visit_summary_email
from dotenv import load_dotenv

# load .env from parent dir (fyp app/.env)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

print(f"Testing with Sender: {os.getenv('SENDER_EMAIL')}")
print("Sending test email...")

# Send a test email to yourself (using .invoke since it's a Langchain tool)
success = send_visit_summary_email.invoke({
    "user_email": os.getenv("SENDER_EMAIL"), 
    "ai_summary": "This is a test summary. Your API setup is working perfectly!", 
    "triage_label": "TEST - Safe"
})

if success:
    print("✅ Email sent successfully! Check your inbox.")
else:
    print("❌ Failed to send email.")
