<div align="center">
  
# 🏥 ER Triage Intelligence & Agentic Assistant
  
**An AI-Powered Clinical Decision Support System built for Emergency Rooms.**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

*A Final Year Project predicting triage priority levels (L0-L3) using vital signs, enriched with an autonomous LLM Agent (LangGraph) for contextual medical guidance and patient history tracking.*

</div>

---

## 🌟 Key Features

### 🧠 1. Machine Learning Triage Prediction
- Predicts emergency severity levels (**L0 Non-Urgent** to **L3 Emergent**).
- Analyzes 9 core patient features (Age, Heart Rate, SpO2, Pain Level, etc.).
- Powered by a robust **Random Forest Classifier** trained via Scikit-Learn pipelines.

### 🤖 2. Agentic LLM Workflow (LangGraph)
- Instead of a simple chatbot, the system operates as an **Autonomous Agent**.
- Evaluates the ML prediction, extracts text from uploaded prescriptions (Vision OCR), and queries a Vector Database for clinical guidelines (RAG).
- **Tool Calling**: Automatically decides when to use external tools like `hospital_locator` or `pharmacy_locator`.

### 🔐 3. Patient Authentication & Memory
- Secure, custom-built authentication system using **JWT** and **bcrypt** password hashing.
- **Persistent SQLite Database**: Stores user accounts, patient profiles (age, gender, chronic conditions).
- **Long-term Agent Memory**: The agent remembers past visit history and automatically references it in new conversations.

### 🚨 4. Automated Visit Summary Emails
- After every consultation, the system automatically drafts and sends a **Visit Summary Email** to the patient.
- Uses the **Resend API** to dynamically deliver the predicted triage level, clinical advice, and nearby hospital details without prompting the user.

---

## 🏗️ System Architecture

The backbone of this project is built on **LangGraph**. The workflow acts as a state machine that seamlessly transitions between data preparation, retrieval, and LLM reasoning.

```mermaid
graph TD
    %% Entry
    Input[/Authenticated User Input/] --> START(((START)))
    START --> AuthCheck

    AuthCheck[Fetch Patient Profile & Past History] --> N1

    %% Sequential Data Prep Pipeline
    subgraph "Data Preparation"
        N1[prepare_vitals_node<br>Runs ML Random Forest] --> N2
        N2[ocr_node<br>Vision Extraction] --> N3
        N3[retrieval_node<br>Queries ChromaDB]
    end

    N3 --> N4

    %% The ReAct Agent Loop
    subgraph "The Agentic Loop"
        N4{chatbot_node<br>Groq LLM Reasoning}
        N4 -- "Requires Tool" --> N5[ToolNode<br>Executes Function]
        N5 -- "Returns Result" --> N4
    end

    %% Exit
    N4 -- "Final Answer" --> SaveVisit
    SaveVisit[Save Visit to SQLite History] --> END(((END)))
    
    %% Post-Graph Processes
    END --> Email[Send Visit Summary Email via Resend]
    END --> Output[/Response sent to User/]

    %% Tool Definitions
    subgraph "External APIs"
        T1[[hospital_locator]]
        T2[[pharmacy_locator]]
    end
    
    N5 -.-> T1
    N5 -.-> T2
```
---

## 🚀 User Guide: How to Run the App

### Prerequisites
- Python 3.9+
- API Keys for **Groq** (LLM) and optionally Google/OpenAI (if used for Vision/Places). Set these in a `.env` file at the root.

### 1. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/mahaveer0738/fyp-health-app.git
cd "fyp health-app/fyp app"
pip install -r requirements.txt
```

### 2. Start the Backend Server
Run the FastAPI application via Uvicorn. *(The SQLite database will automatically be generated on the first run).*
```bash
uvicorn backend.main:app --reload
```
The API will be available at: `http://localhost:8000`

### 3. Using the Web Interface
1. Open `frontend/templates/register.html` in your web browser.
2. **Create an Account**: Enter your details and any chronic conditions.
3. **Login**: Authenticate at `login.html`. Your JWT token will be saved securely in your browser.
4. **Dashboard**: Navigate the interface to input your vitals for ML prediction or chat with the autonomous clinical agent!

---

## 📂 Deep Dives & Documentation
Want to know how the internals work? We have detailed documentation in the `backend/` folder:
- 📖 [**Architecture Guide**](backend/ARCHITECTURE.md): An in-depth look at LangGraph, Nodes, Edges, and the ReAct Agent flow.
- 🔐 [**Auth & Security Deep Dive**](backend/AUTH_DEEPDIVE.md): Detailed explanation of JWT, bcrypt hashing, SQLite schema design, and how to protect against XSS/MITM attacks.

---

## 🔮 Future Implementations & Roadmap

While this project is fully functional, there are several exciting features planned for future iterations:

1. **Gmail / Google OAuth2 Single Sign-On (SSO)**
   - *Plan:* Allow users to bypass traditional email/password registration by clicking "Sign in with Google" (Gmail Login).
   - *Why:* Simplifies user onboarding and relies on enterprise-grade Google security for authentication.
   
2. **HTTPS & Secure Cookies**
   - *Plan:* Transition away from storing JWTs in `localStorage` and move to `HttpOnly` secure cookies to prevent XSS attacks in a production environment.
   
3. **Advanced RAG Integration**
   - *Plan:* Connect the ChromaDB to live, constantly updating medical journal APIs rather than static PDF uploads.
   
4. **Frontend Framework Migration**
   - *Plan:* Port the Vanilla HTML/JS frontend to **React** or **Next.js** for smoother state management, faster routing, and dynamic UI animations.

---
<div align="center">
  <i>Developed for a Final Year Project. Always consult a real medical professional for health emergencies.</i>
</div>
