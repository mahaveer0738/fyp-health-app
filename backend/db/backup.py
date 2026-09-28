import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file (located in the fyp app folder)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# Ensure backend folder is in Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, PatientProfile, VisitHistory
from db.database import engine as sqlite_engine

def clone_model(instance, model_class):
    """Helper to convert a SQLAlchemy object to a dictionary for safe insertion."""
    return model_class(**{c.name: getattr(instance, c.name) for c in model_class.__table__.columns})

def backup_to_neon():
    """Reads all data from local SQLite and securely copies/updates it on Neon."""
    neon_url = os.getenv("DATABASE_URL")
    if not neon_url:
        print("Note: DATABASE_URL not set in environment. Cannot backup to Neon.")
        return
        
    try:
        print("Connecting to Neon database...")
        # Create Neon engine
        neon_engine = create_engine(neon_url, pool_pre_ping=True, pool_recycle=300)
        
        # Ensure tables exist in Neon
        Base.metadata.create_all(bind=neon_engine)
        
        # Sessions
        NeonSession = sessionmaker(bind=neon_engine)
        neon_session = NeonSession()
        
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        
        print("Copying data from local SQLite to Neon...")
        
        # Get all records from SQLite
        users = sqlite_session.query(User).all()
        profiles = sqlite_session.query(PatientProfile).all()
        visits = sqlite_session.query(VisitHistory).all()
        
        # Merge (Upsert) into Neon. This securely inserts or updates existing records.
        for u in users:
            neon_session.merge(clone_model(u, User))
            
        for p in profiles:
            neon_session.merge(clone_model(p, PatientProfile))
            
        for v in visits:
            neon_session.merge(clone_model(v, VisitHistory))
            
        # Commit to save on Neon
        neon_session.commit()
        print(f"✅ Successfully backed up {len(users)} users, {len(profiles)} profiles, and {len(visits)} visits to Neon!")
        
    except Exception as e:
        print("\n⚠️ NOTE: Neon database isn't working right now.")
        print(f"Error details: {e}")
        print("Don't worry, your data is safely stored in your local SQLite primary database.\n")
    finally:
        if 'neon_session' in locals(): neon_session.close()
        if 'sqlite_session' in locals(): sqlite_session.close()

if __name__ == "__main__":
    backup_to_neon()
