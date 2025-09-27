from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

Base = declarative_base()

# Enums for different emergency types and urgency levels
class MedicalEmergencyType(PyEnum):
    ACCIDENT = "accident"
    HEART_ATTACK = "heart_attack"
    UNCONSCIOUSNESS = "unconsciousness"
    BLEEDING = "bleeding"
    BREATHING_ISSUE = "breathing_issue"
    STROKE = "stroke"
    SEIZURE = "seizure"
    ALLERGIC_REACTION = "allergic_reaction"
    POISONING = "poisoning"
    OTHER = "other"

class MedicalUrgencyLevel(PyEnum):
    SEVERE = "severe"
    MODERATE = "moderate"
    MINOR = "minor"

class PoliceIncidentType(PyEnum):
    THEFT = "theft"
    ASSAULT = "assault"
    DOMESTIC_VIOLENCE = "domestic_violence"
    HARASSMENT = "harassment"
    MISSING_PERSON = "missing_person"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BURGLARY = "burglary"
    ROBBERY = "robbery"
    VANDALISM = "vandalism"
    FRAUD = "fraud"
    OTHER = "other"

class PoliceUrgencyLevel(PyEnum):
    IMMEDIATE_DANGER = "immediate_danger"
    PAST_INCIDENT = "past_incident"
    REPORT_ONLY = "report_only"

class ElectricityIssueType(PyEnum):
    POWER_OUTAGE = "power_outage"
    TRANSFORMER_ISSUE = "transformer_issue"
    BROKEN_ELECTRIC_POLE = "broken_electric_pole"
    SPARKS_FIRE_HAZARD = "sparks_fire_hazard"
    METER_FAULT = "meter_fault"
    BILLING_COMPLAINT = "billing_complaint"
    LIVE_WIRE_GROUND = "live_wire_ground"
    ELECTRICAL_FIRE = "electrical_fire"
    OTHER = "other"

class ElectricitySeverityLevel(PyEnum):
    HAZARDOUS = "hazardous"
    MAJOR_OUTAGE = "major_outage"
    MINOR = "minor"

class MedicalEmergencyReport(Base):
    __tablename__ = "medical_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Patient Details
    patient_name = Column(String, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String, nullable=True)
    patient_id = Column(String, nullable=True)
    patient_phone = Column(String, nullable=True)
    
    # Location Information
    location_address = Column(Text, nullable=True)
    location_gps_lat = Column(Float, nullable=True)
    location_gps_lng = Column(Float, nullable=True)
    
    # Emergency Details
    emergency_type = Column(Enum(MedicalEmergencyType), nullable=True)
    symptoms_description = Column(Text, nullable=True)
    urgency_level = Column(Enum(MedicalUrgencyLevel), nullable=True)
    
    # Medical Information
    allergies = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    existing_conditions = Column(Text, nullable=True)
    
    # Contact Information
    contact_person_name = Column(String, nullable=True)
    contact_person_phone = Column(String, nullable=True)
    
    # Additional Information
    additional_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PoliceEmergencyReport(Base):
    __tablename__ = "police_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Reporter Details
    reporter_name = Column(String, nullable=True)
    reporter_id = Column(String, nullable=True)
    reporter_phone = Column(String, nullable=True)
    
    # Incident Location
    incident_address = Column(Text, nullable=True)
    incident_landmark = Column(String, nullable=True)
    incident_gps_lat = Column(Float, nullable=True)
    incident_gps_lng = Column(Float, nullable=True)
    
    # Incident Details
    incident_type = Column(Enum(PoliceIncidentType), nullable=True)
    incident_time = Column(DateTime(timezone=True), nullable=True)
    incident_description = Column(Text, nullable=True)
    urgency_level = Column(Enum(PoliceUrgencyLevel), nullable=True)
    
    # Suspect Details
    suspect_appearance = Column(Text, nullable=True)
    suspect_vehicle_number = Column(String, nullable=True)
    suspect_known_person = Column(String, nullable=True)
    
    # Victim Details
    victim_name = Column(String, nullable=True)
    victim_phone = Column(String, nullable=True)
    victim_relationship = Column(String, nullable=True)
    
    # Media Attachments
    has_photos = Column(Boolean, default=False)
    has_videos = Column(Boolean, default=False)
    has_audio = Column(Boolean, default=False)
    media_files_path = Column(Text, nullable=True)
    
    # Additional Information
    additional_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ElectricityEmergencyReport(Base):
    __tablename__ = "electricity_emergency_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Reporter Details
    reporter_name = Column(String, nullable=True)
    reporter_phone = Column(String, nullable=True)
    reporter_email = Column(String, nullable=True)
    
    # Location Information
    location_address = Column(Text, nullable=True)
    location_gps_lat = Column(Float, nullable=True)
    location_gps_lng = Column(Float, nullable=True)
    
    # Issue Details
    issue_type = Column(Enum(ElectricityIssueType), nullable=True)
    severity_level = Column(Enum(ElectricitySeverityLevel), nullable=True)
    issue_started_time = Column(DateTime(timezone=True), nullable=True)
    issue_description = Column(Text, nullable=True)
    
    # Media Attachments
    has_photos = Column(Boolean, default=False)
    has_videos = Column(Boolean, default=False)
    media_files_path = Column(Text, nullable=True)
    
    # Additional Information
    additional_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Triage Report to track which agent was selected
class TriageReport(Base):
    __tablename__ = "triage_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Triage Details
    emergency_type = Column(String, nullable=False)  # Medical, Police, Electricity
    user_query = Column(Text, nullable=False)
    triage_reasoning = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
