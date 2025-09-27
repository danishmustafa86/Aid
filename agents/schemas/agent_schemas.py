from pydantic import BaseModel, Field
from typing import Optional

# Medical Emergency Schema
class MedicalEmergencySchema(BaseModel):
    patient_name: Optional[str] = Field(None, description="Patient's name")
    patient_age: Optional[int] = Field(None, description="Patient's age")
    patient_phone: Optional[str] = Field(None, description="Patient's phone number")
    location_address: Optional[str] = Field(None, description="Current address")
    emergency_type: Optional[str] = Field(None, description="Type of emergency")
    symptoms: Optional[str] = Field(None, description="Symptoms description")
    urgency_level: Optional[str] = Field(None, description="Urgency: severe, moderate, minor")
    allergies: Optional[str] = Field(None, description="Known allergies")
    medications: Optional[str] = Field(None, description="Current medications")
    contact_person: Optional[str] = Field(None, description="Emergency contact")

# Police Emergency Schema
class PoliceEmergencySchema(BaseModel):
    reporter_name: Optional[str] = Field(None, description="Reporter's name")
    reporter_phone: Optional[str] = Field(None, description="Reporter's phone")
    incident_location: Optional[str] = Field(None, description="Incident address")
    incident_type: Optional[str] = Field(None, description="Type of incident")
    incident_time: Optional[str] = Field(None, description="When it occurred")
    description: Optional[str] = Field(None, description="Incident description")
    suspect_details: Optional[str] = Field(None, description="Suspect information")
    urgency: Optional[str] = Field(None, description="Urgency level")

# Electricity Emergency Schema
class ElectricityEmergencySchema(BaseModel):
    reporter_name: Optional[str] = Field(None, description="Reporter's name")
    reporter_phone: Optional[str] = Field(None, description="Reporter's phone")
    location: Optional[str] = Field(None, description="Issue location")
    issue_type: Optional[str] = Field(None, description="Type of issue")
    severity: Optional[str] = Field(None, description="Severity level")
    time_started: Optional[str] = Field(None, description="When issue started")
    description: Optional[str] = Field(None, description="Issue description")

# Triage Schema
class TriageSchema(BaseModel):
    emergency_type: Optional[str] = Field(None, description="Medical, Police, or Electricity")
    user_query: Optional[str] = Field(None, description="User's query")
