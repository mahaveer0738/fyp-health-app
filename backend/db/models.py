from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    profile = relationship("PatientProfile", back_populates="user", uselist=False)

class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    chronic_conditions = Column(Text, nullable=True) # E.g., "Diabetes, Hypertension"

    # Relationships
    user = relationship("User", back_populates="profile")
    visit_history = relationship("VisitHistory", back_populates="patient")

class VisitHistory(Base):
    __tablename__ = "visit_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Information captured during the triage process
    symptoms = Column(Text)
    triage_label = Column(String, nullable=True)
    triage_confidence = Column(Float, nullable=True)  # ML prediction confidence %
    ai_summary = Column(Text, nullable=True)

    # Vitals snapshot (stored per-visit so history shows exact readings)
    heart_rate = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    body_temperature = Column(Float, nullable=True)
    pain_level = Column(Integer, nullable=True)

    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_string = Column(String, nullable=True)  # Reverse-geocoded city/area name

    # Session metadata
    arrival_mode = Column(String, nullable=True)  # Ambulance, Walk-in, Private Vehicle
    input_mode = Column(String, default="manual")  # "manual" or "hardware"
    ocr_extracted = Column(Boolean, default=False)  # Whether an image was processed by OCR

    # Relationships
    patient = relationship("PatientProfile", back_populates="visit_history")

