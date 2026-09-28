# Final Year Project (FYP) - Progression Tracker

This document tracks the progression of the AI-Powered ER Triage & Clinical Assistant project.

## 🟢 Phase 1: Machine Learning & Core AI (Completed)
- [x] Train Random Forest triage model (`triage_model.pkl` / `pipe.pkl`).
- [x] Define ML input schemas (Vitals).
- [x] Test Gemini API for OCR and text extraction from medical images.
- [x] Design initial LangChain agent prompts.

## 🟢 Phase 2: Backend API & Architecture (Completed)
- [x] **FastAPI Setup:** Created structured API routes (`routes_auth.py`, `routes_chat.py`, `routes_predict.py`).
- [x] **Database (SQLAlchemy):** 
  - Designed `users`, `patient_profiles`, and `visit_history` tables.
  - Configured dynamic fallback between local SQLite and cloud PostgreSQL (Neon).
- [x] **Security:** 
  - Implemented secure JWT token generation.
  - Replaced buggy `passlib` with modern `bcrypt` for password hashing.
- [x] **LangGraph AI Pipeline:**
  - Integrated Groq LLM as the reasoning engine.
  - Integrated Gemini API for optional image/prescription OCR.
  - Integrated ChromaDB for RAG (Retrieval-Augmented Generation) medical guidelines.
  - Bound hospital locator tools.
- [x] **Email Notifications:** Integrated Resend API to email patient summaries after every chat session.
- [x] **Testing & Deployment Ready:** Fixed dependency conflicts (`scikit-learn` versions, `psycopg2`, `Pillow`) and created `.env` template. Tested successfully via Swagger UI.

## 🟢 Phase 3: Frontend Development & Rebranding (Completed)
- [x] Initialize Frontend framework (Vanilla HTML/CSS/JS).
- [x] Build Authentication UI (Login and Registration forms).
- [x] Build Chat Interface & Dashboards.
- [x] Connect Frontend to FastAPI Backend (Handling JWT tokens in local storage).
- [x] **UI Polish & Rebranding:**
  - Rebranded the entire application to **NexaCare**.
  - Generated and implemented a custom medical AI logo with pixel-perfect transparent cropping.
  - Redesigned the automated email template (dynamic colors based on triage level + AI summarization).
  - Optimized the AI response engine for extreme conciseness to better fit the chat UI.

## 🔴 Phase 4: Final Deployment & Polish (Pending)
- [ ] Deploy PostgreSQL database (Neon) - *Configured but waiting for final use.*
- [ ] Deploy FastAPI Backend to a cloud provider (e.g., Render, Railway, AWS).
- [ ] Deploy Frontend Web App (e.g., Vercel, Netlify).
- [ ] Record final project demonstration video.
