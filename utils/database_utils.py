from sqlalchemy.orm import Session
from models.database_models import (
    MedicalEmergencyReport, 
    PoliceEmergencyReport, 
    ElectricityEmergencyReport, 
    FireEmergencyReport,
    TriageReport,
    Notification,
    EmergencyStatus
)
from agents.schemas.agent_schemas import (
    MedicalEmergencySchema,
    PoliceEmergencySchema,
    ElectricityEmergencySchema,
    FireEmergencySchema,
    TriageSchema
)
from configurations.postgres_db import SessionLocal
import logging

logger = logging.getLogger(__name__)

def get_db_session():
    """Get database session"""
    return SessionLocal()

def save_medical_emergency(user_id: str, data: MedicalEmergencySchema) -> str:
    """
    Save medical emergency data to database
    
    Args:
        user_id: User ID
        data: MedicalEmergencySchema object with emergency data
        
    Returns:
        str: ID of the saved record
    """
    db = get_db_session()
    try:
        medical_report = MedicalEmergencyReport(
            user_id=user_id,
            patient_name=data.patient_name,
            patient_age=data.patient_age,
            patient_phone=data.patient_phone,
            location_address=data.location_address,
            emergency_type=data.emergency_type,
            symptoms=data.symptoms,
            urgency_level=data.urgency_level,
            allergies=data.allergies,
            medications=data.medications,
            contact_person=data.contact_person
        )
        
        db.add(medical_report)
        db.commit()
        db.refresh(medical_report)
        
        logger.info(f"Medical emergency report saved with ID: {medical_report.id}")
        return medical_report.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving medical emergency report: {e}")
        raise
    finally:
        db.close()

def save_police_emergency(user_id: str, data: PoliceEmergencySchema) -> str:
    """
    Save police emergency data to database
    
    Args:
        user_id: User ID
        data: PoliceEmergencySchema object with incident data
        
    Returns:
        str: ID of the saved record
    """
    db = get_db_session()
    try:
        police_report = PoliceEmergencyReport(
            user_id=user_id,
            reporter_name=data.reporter_name,
            reporter_phone=data.reporter_phone,
            incident_location=data.incident_location,
            incident_type=data.incident_type,
            incident_time=data.incident_time,
            description=data.description,
            suspect_details=data.suspect_details,
            urgency=data.urgency
        )
        
        db.add(police_report)
        db.commit()
        db.refresh(police_report)
        
        logger.info(f"Police emergency report saved with ID: {police_report.id}")
        return police_report.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving police emergency report: {e}")
        raise
    finally:
        db.close()

def save_electricity_emergency(user_id: str, data: ElectricityEmergencySchema) -> str:
    """
    Save electricity emergency data to database
    
    Args:
        user_id: User ID
        data: ElectricityEmergencySchema object with issue data
        
    Returns:
        str: ID of the saved record
    """
    db = get_db_session()
    try:
        electricity_report = ElectricityEmergencyReport(
            user_id=user_id,
            reporter_name=data.reporter_name,
            reporter_phone=data.reporter_phone,
            location=data.location,
            issue_type=data.issue_type,
            severity=data.severity,
            time_started=data.time_started,
            description=data.description
        )
        
        db.add(electricity_report)
        db.commit()
        db.refresh(electricity_report)
        
        logger.info(f"Electricity emergency report saved with ID: {electricity_report.id}")
        return electricity_report.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving electricity emergency report: {e}")
        raise
    finally:
        db.close()

def save_fire_emergency(user_id: str, data: FireEmergencySchema) -> str:
    """
    Save fire emergency data to database
    
    Args:
        user_id: User ID
        data: FireEmergencySchema object with fire emergency data
        
    Returns:
        str: ID of the saved record
    """
    db = get_db_session()
    try:
        fire_report = FireEmergencyReport(
            user_id=user_id,
            reporter_name=data.reporter_name,
            reporter_phone=data.reporter_phone,
            location=data.location,
            fire_type=data.fire_type,
            severity_level=data.severity_level,
            time_started=data.time_started,
            people_at_risk=data.people_at_risk,
            building_details=data.building_details,
            hazards_present=data.hazards_present
        )
        
        db.add(fire_report)
        db.commit()
        db.refresh(fire_report)
        
        logger.info(f"Fire emergency report saved with ID: {fire_report.id}")
        return fire_report.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving fire emergency report: {e}")
        raise
    finally:
        db.close()

def save_triage_report(user_id: str, data: TriageSchema) -> str:
    """
    Save triage report to database
    
    Args:
        user_id: User ID
        data: TriageSchema object with triage data
        
    Returns:
        str: ID of the saved record
    """
    db = get_db_session()
    try:
        triage_report = TriageReport(
            user_id=user_id,
            emergency_type=data.emergency_type,
            user_query=data.user_query
        )
        
        db.add(triage_report)
        db.commit()
        db.refresh(triage_report)
        
        logger.info(f"Triage report saved with ID: {triage_report.id}")
        return triage_report.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving triage report: {e}")
        raise
    finally:
        db.close()

def get_medical_emergency_reports(user_id: str) -> list:
    """
    Get all medical emergency reports for a user
    
    Args:
        user_id: User ID
        
    Returns:
        list: List of medical emergency reports
    """
    db = get_db_session()
    try:
        reports = db.query(MedicalEmergencyReport).filter(
            MedicalEmergencyReport.user_id == user_id
        ).order_by(MedicalEmergencyReport.created_at.desc()).all()
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching medical emergency reports: {e}")
        raise
    finally:
        db.close()

def get_police_emergency_reports(user_id: str) -> list:
    """
    Get all police emergency reports for a user
    
    Args:
        user_id: User ID
        
    Returns:
        list: List of police emergency reports
    """
    db = get_db_session()
    try:
        reports = db.query(PoliceEmergencyReport).filter(
            PoliceEmergencyReport.user_id == user_id
        ).order_by(PoliceEmergencyReport.created_at.desc()).all()
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching police emergency reports: {e}")
        raise
    finally:
        db.close()

def get_electricity_emergency_reports(user_id: str) -> list:
    """
    Get all electricity emergency reports for a user
    
    Args:
        user_id: User ID
        
    Returns:
        list: List of electricity emergency reports
    """
    db = get_db_session()
    try:
        reports = db.query(ElectricityEmergencyReport).filter(
            ElectricityEmergencyReport.user_id == user_id
        ).order_by(ElectricityEmergencyReport.created_at.desc()).all()
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching electricity emergency reports: {e}")
        raise
    finally:
        db.close()

def get_triage_reports(user_id: str) -> list:
    """
    Get all triage reports for a user
    
    Args:
        user_id: User ID
        
    Returns:
        list: List of triage reports
    """
    db = get_db_session()
    try:
        reports = db.query(TriageReport).filter(
            TriageReport.user_id == user_id
        ).order_by(TriageReport.created_at.desc()).all()
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching triage reports: {e}")
        raise
    finally:
        db.close()

def get_emergency_report_by_id(report_id: str, emergency_type: str):
    """
    Get a specific emergency report by ID and type
    
    Args:
        report_id: Report ID
        emergency_type: Type of emergency (medical, police, electricity, fire)
        
    Returns:
        Emergency report object or None
    """
    db = get_db_session()
    try:
        if emergency_type.lower() == "medical":
            return db.query(MedicalEmergencyReport).filter(
                MedicalEmergencyReport.id == report_id
            ).first()
        elif emergency_type.lower() == "police":
            return db.query(PoliceEmergencyReport).filter(
                PoliceEmergencyReport.id == report_id
            ).first()
        elif emergency_type.lower() == "electricity":
            return db.query(ElectricityEmergencyReport).filter(
                ElectricityEmergencyReport.id == report_id
            ).first()
        elif emergency_type.lower() == "fire":
            return db.query(FireEmergencyReport).filter(
                FireEmergencyReport.id == report_id
            ).first()
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error fetching emergency report: {e}")
        raise
    finally:
        db.close()

# Status management functions
def update_emergency_status(emergency_id: str, emergency_type: str, new_status: EmergencyStatus) -> bool:
    """
    Update the status of an emergency case
    
    Args:
        emergency_id: ID of the emergency case
        emergency_type: Type of emergency (medical, police, electricity, fire)
        new_status: New status to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    db = get_db_session()
    try:
        if emergency_type.lower() == "medical":
            report = db.query(MedicalEmergencyReport).filter(MedicalEmergencyReport.id == emergency_id).first()
        elif emergency_type.lower() == "police":
            report = db.query(PoliceEmergencyReport).filter(PoliceEmergencyReport.id == emergency_id).first()
        elif emergency_type.lower() == "electricity":
            report = db.query(ElectricityEmergencyReport).filter(ElectricityEmergencyReport.id == emergency_id).first()
        elif emergency_type.lower() == "fire":
            report = db.query(FireEmergencyReport).filter(FireEmergencyReport.id == emergency_id).first()
        else:
            return False
        
        if report:
            report.status = new_status
            db.commit()
            logger.info(f"Updated {emergency_type} emergency {emergency_id} status to {new_status.value}")
            return True
        return False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating emergency status: {e}")
        return False
    finally:
        db.close()

def get_emergency_cases_by_status(emergency_type: str, status: EmergencyStatus = None) -> list:
    """
    Get emergency cases by status
    
    Args:
        emergency_type: Type of emergency (medical, police, electricity, fire)
        status: Optional status filter
        
    Returns:
        list: List of emergency cases
    """
    db = get_db_session()
    try:
        if emergency_type.lower() == "medical":
            query = db.query(MedicalEmergencyReport)
        elif emergency_type.lower() == "police":
            query = db.query(PoliceEmergencyReport)
        elif emergency_type.lower() == "electricity":
            query = db.query(ElectricityEmergencyReport)
        elif emergency_type.lower() == "fire":
            query = db.query(FireEmergencyReport)
        else:
            return []
        
        if status:
            query = query.filter(query.column_descriptions[0]['entity'].status == status)
        
        return query.order_by(query.column_descriptions[0]['entity'].created_at.desc()).all()
        
    except Exception as e:
        logger.error(f"Error fetching emergency cases by status: {e}")
        return []
    finally:
        db.close()

# Notification functions
def create_notification(user_id: str, title: str, message: str, notification_type: str, 
                       emergency_id: str = None, emergency_type: str = None) -> str:
    """
    Create a new notification
    
    Args:
        user_id: User ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        emergency_id: Optional emergency case ID
        emergency_type: Optional emergency type
        
    Returns:
        str: Notification ID
    """
    db = get_db_session()
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            emergency_id=emergency_id,
            emergency_type=emergency_type
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating notification: {e}")
        raise
    finally:
        db.close()

def get_user_notifications(user_id: str, is_read: str = None) -> list:
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        is_read: Optional filter by read status
        
    Returns:
        list: List of notifications
    """
    db = get_db_session()
    try:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        return query.order_by(Notification.created_at.desc()).all()
        
    except Exception as e:
        logger.error(f"Error fetching user notifications: {e}")
        return []
    finally:
        db.close()

def mark_notification_read(notification_id: str) -> bool:
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        
    Returns:
        bool: True if successful
    """
    db = get_db_session()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = "true"
            db.commit()
            logger.info(f"Marked notification {notification_id} as read")
            return True
        return False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking notification as read: {e}")
        return False
    finally:
        db.close()

def update_notification_approval(notification_id: str, is_approved: str) -> bool:
    """
    Update notification approval status
    
    Args:
        notification_id: Notification ID
        is_approved: Approval status (true/false)
        
    Returns:
        bool: True if successful
    """
    db = get_db_session()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_approved = is_approved
            db.commit()
            logger.info(f"Updated notification {notification_id} approval to {is_approved}")
            return True
        return False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating notification approval: {e}")
        return False
    finally:
        db.close()
