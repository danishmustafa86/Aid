from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class MedicalEmergencyReport(Base):
    __tablename__ = "medical_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Essential fields
    patient_name = Column(String, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_phone = Column(String, nullable=True)
    location_address = Column(Text, nullable=True)
    emergency_type = Column(String, nullable=True)
    symptoms = Column(Text, nullable=True)
    urgency_level = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    contact_person = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PoliceEmergencyReport(Base):
    __tablename__ = "police_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Essential fields
    reporter_name = Column(String, nullable=True)
    reporter_phone = Column(String, nullable=True)
    incident_location = Column(Text, nullable=True)
    incident_type = Column(String, nullable=True)
    incident_time = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    suspect_details = Column(Text, nullable=True)
    urgency = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ElectricityEmergencyReport(Base):
    __tablename__ = "electricity_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Essential fields
    reporter_name = Column(String, nullable=True)
    reporter_phone = Column(String, nullable=True)
    location = Column(Text, nullable=True)
    issue_type = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    time_started = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Triage Report to track which agent was selected
class TriageReport(Base):
    __tablename__ = "triage_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Essential fields
    emergency_type = Column(String, nullable=True)  # Medical, Police, Electricity
    user_query = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
