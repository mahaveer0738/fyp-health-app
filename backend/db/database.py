import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the path to the 'backend' directory to find the database file reliably
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BACKEND_DIR, "data", "fyp_health.db")

# Always use the local SQLite file as the primary database
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Only SQLite requires the 'check_same_thread' argument
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
