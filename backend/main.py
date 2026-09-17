import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes_predict import router as predict_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_auth import router as auth_router
from backend.db.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = FastAPI(
    title="FYP Health App - ER Triage API",
    description="Agentic Clinical Assistant Backend with FastAPI and LangGraph",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only, update for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the ER Triage API. Go to /docs for the interactive API documentation."}

if __name__ == "__main__":
    import uvicorn
    # Make sure to run this from the root directory so 'backend' is in PYTHONPATH
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
