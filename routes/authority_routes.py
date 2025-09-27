from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from utils.database_utils import (
    get_emergency_cases_by_status,
    update_emergency_status,
    get_emergency_report_by_id,
    create_notification
)
from models.database_models import EmergencyStatus
import logging

logger = logging.getLogger(__name__)

authority_router = APIRouter(prefix="/authority", tags=["Authority"])

# Pydantic models for API requests/responses
class StatusUpdateRequest(BaseModel):
    emergency_id: str
    emergency_type: str
    new_status: str
    message: Optional[str] = None

class StatusUpdateResponse(BaseModel):
    success: bool
    message: str

class EmergencyCaseResponse(BaseModel):
    id: str
    user_id: str
    status: str
    created_at: str
    updated_at: str
    # Dynamic fields based on emergency type
    data: dict

# Medical Emergency Authority Endpoints
@authority_router.get("/medical/emergencies", response_model=List[EmergencyCaseResponse])
async def get_medical_emergencies(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of cases to return")
):
    """Get medical emergency cases for medical authorities"""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = EmergencyStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        cases = get_emergency_cases_by_status("medical", status_enum)
        
        # Limit results
        cases = cases[:limit]
        
        # Convert to response format
        response_cases = []
        for case in cases:
            case_data = {
                "patient_name": case.patient_name,
                "patient_age": case.patient_age,
                "patient_phone": case.patient_phone,
                "location_address": case.location_address,
                "emergency_type": case.emergency_type,
                "symptoms": case.symptoms,
                "urgency_level": case.urgency_level,
                "allergies": case.allergies,
                "medications": case.medications,
                "contact_person": case.contact_person
            }
            
            response_cases.append(EmergencyCaseResponse(
                id=case.id,
                user_id=case.user_id,
                status=case.status.value,
                created_at=case.created_at.isoformat() if case.created_at else "",
                updated_at=case.updated_at.isoformat() if case.updated_at else "",
                data=case_data
            ))
        
        return response_cases
        
    except Exception as e:
        logger.error(f"Error fetching medical emergencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@authority_router.put("/medical/emergencies/{emergency_id}/status", response_model=StatusUpdateResponse)
async def update_medical_emergency_status(emergency_id: str, request: StatusUpdateRequest):
    """Update medical emergency case status"""
    try:
        # Validate status
        try:
            new_status = EmergencyStatus(request.new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.new_status}")
        
        # Update status
        success = update_emergency_status(emergency_id, "medical", new_status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        # Create notification for user based on status change
        case = get_emergency_report_by_id(emergency_id, "medical")
        if case:
            if new_status == EmergencyStatus.IN_PROGRESS:
                create_notification(
                    user_id=case.user_id,
                    title="Case Assigned",
                    message="Your medical emergency case has been assigned to medical authorities and is now in progress.",
                    notification_type="status_update",
                    emergency_id=emergency_id,
                    emergency_type="medical"
                )
            elif new_status == EmergencyStatus.REQUESTED_FOR_RESOLUTION:
                create_notification(
                    user_id=case.user_id,
                    title="Resolution Request",
                    message="Medical authorities have requested to mark your emergency case as resolved. Please review and approve.",
                    notification_type="resolution_request",
                    emergency_id=emergency_id,
                    emergency_type="medical"
                )
        
        return StatusUpdateResponse(
            success=True,
            message=f"Medical emergency status updated to {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating medical emergency status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Police Emergency Authority Endpoints
@authority_router.get("/police/emergencies", response_model=List[EmergencyCaseResponse])
async def get_police_emergencies(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of cases to return")
):
    """Get police emergency cases for law enforcement authorities"""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = EmergencyStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        cases = get_emergency_cases_by_status("police", status_enum)
        
        # Limit results
        cases = cases[:limit]
        
        # Convert to response format
        response_cases = []
        for case in cases:
            case_data = {
                "reporter_name": case.reporter_name,
                "reporter_phone": case.reporter_phone,
                "incident_location": case.incident_location,
                "incident_type": case.incident_type,
                "incident_time": case.incident_time,
                "description": case.description,
                "suspect_details": case.suspect_details,
                "urgency": case.urgency
            }
            
            response_cases.append(EmergencyCaseResponse(
                id=case.id,
                user_id=case.user_id,
                status=case.status.value,
                created_at=case.created_at.isoformat() if case.created_at else "",
                updated_at=case.updated_at.isoformat() if case.updated_at else "",
                data=case_data
            ))
        
        return response_cases
        
    except Exception as e:
        logger.error(f"Error fetching police emergencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@authority_router.put("/police/emergencies/{emergency_id}/status", response_model=StatusUpdateResponse)
async def update_police_emergency_status(emergency_id: str, request: StatusUpdateRequest):
    """Update police emergency case status"""
    try:
        # Validate status
        try:
            new_status = EmergencyStatus(request.new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.new_status}")
        
        # Update status
        success = update_emergency_status(emergency_id, "police", new_status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        # Create notification for user based on status change
        case = get_emergency_report_by_id(emergency_id, "police")
        if case:
            if new_status == EmergencyStatus.IN_PROGRESS:
                create_notification(
                    user_id=case.user_id,
                    title="Case Assigned",
                    message="Your police incident case has been assigned to law enforcement authorities and is now in progress.",
                    notification_type="status_update",
                    emergency_id=emergency_id,
                    emergency_type="police"
                )
            elif new_status == EmergencyStatus.REQUESTED_FOR_RESOLUTION:
                create_notification(
                    user_id=case.user_id,
                    title="Resolution Request",
                    message="Police authorities have requested to mark your incident case as resolved. Please review and approve.",
                    notification_type="resolution_request",
                    emergency_id=emergency_id,
                    emergency_type="police"
                )
        
        return StatusUpdateResponse(
            success=True,
            message=f"Police emergency status updated to {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating police emergency status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Electricity Emergency Authority Endpoints
@authority_router.get("/electricity/emergencies", response_model=List[EmergencyCaseResponse])
async def get_electricity_emergencies(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of cases to return")
):
    """Get electricity emergency cases for utility authorities"""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = EmergencyStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        cases = get_emergency_cases_by_status("electricity", status_enum)
        
        # Limit results
        cases = cases[:limit]
        
        # Convert to response format
        response_cases = []
        for case in cases:
            case_data = {
                "reporter_name": case.reporter_name,
                "reporter_phone": case.reporter_phone,
                "location": case.location,
                "issue_type": case.issue_type,
                "severity": case.severity,
                "time_started": case.time_started,
                "description": case.description
            }
            
            response_cases.append(EmergencyCaseResponse(
                id=case.id,
                user_id=case.user_id,
                status=case.status.value,
                created_at=case.created_at.isoformat() if case.created_at else "",
                updated_at=case.updated_at.isoformat() if case.updated_at else "",
                data=case_data
            ))
        
        return response_cases
        
    except Exception as e:
        logger.error(f"Error fetching electricity emergencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@authority_router.put("/electricity/emergencies/{emergency_id}/status", response_model=StatusUpdateResponse)
async def update_electricity_emergency_status(emergency_id: str, request: StatusUpdateRequest):
    """Update electricity emergency case status"""
    try:
        # Validate status
        try:
            new_status = EmergencyStatus(request.new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.new_status}")
        
        # Update status
        success = update_emergency_status(emergency_id, "electricity", new_status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        # Create notification for user based on status change
        case = get_emergency_report_by_id(emergency_id, "electricity")
        if case:
            if new_status == EmergencyStatus.IN_PROGRESS:
                create_notification(
                    user_id=case.user_id,
                    title="Case Assigned",
                    message="Your electricity issue has been assigned to utility authorities and is now in progress.",
                    notification_type="status_update",
                    emergency_id=emergency_id,
                    emergency_type="electricity"
                )
            elif new_status == EmergencyStatus.REQUESTED_FOR_RESOLUTION:
                create_notification(
                    user_id=case.user_id,
                    title="Resolution Request",
                    message="Electricity department has requested to mark your utility issue as resolved. Please review and approve.",
                    notification_type="resolution_request",
                    emergency_id=emergency_id,
                    emergency_type="electricity"
                )
        
        return StatusUpdateResponse(
            success=True,
            message=f"Electricity emergency status updated to {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating electricity emergency status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# General Authority Endpoints
@authority_router.get("/emergencies/{emergency_type}/{emergency_id}")
async def get_emergency_case(emergency_type: str, emergency_id: str):
    """Get a specific emergency case by ID and type"""
    try:
        case = get_emergency_report_by_id(emergency_id, emergency_type)
        
        if not case:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        return {
            "id": case.id,
            "user_id": case.user_id,
            "status": case.status.value,
            "created_at": case.created_at.isoformat() if case.created_at else "",
            "updated_at": case.updated_at.isoformat() if case.updated_at else "",
            "data": case.__dict__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching emergency case: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
