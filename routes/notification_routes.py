from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from utils.database_utils import (
    get_user_notifications,
    mark_notification_read,
    update_notification_approval,
    update_emergency_status
)
from models.database_models import EmergencyStatus
import logging

logger = logging.getLogger(__name__)

notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Pydantic models for API requests/responses
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    emergency_id: Optional[str]
    emergency_type: Optional[str]
    is_read: str
    is_approved: Optional[str]
    created_at: str
    updated_at: str

class NotificationApprovalRequest(BaseModel):
    is_approved: str  # "true" or "false"

class NotificationApprovalResponse(BaseModel):
    success: bool
    message: str

@notification_router.get("/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications_endpoint(
    user_id: str,
    is_read: Optional[str] = Query(None, description="Filter by read status (true/false)"),
    limit: int = Query(50, description="Number of notifications to return")
):
    """Get notifications for a specific user"""
    try:
        notifications = get_user_notifications(user_id, is_read)
        
        # Limit results
        notifications = notifications[:limit]
        
        # Convert to response format
        response_notifications = []
        for notification in notifications:
            response_notifications.append(NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                emergency_id=notification.emergency_id,
                emergency_type=notification.emergency_type,
                is_read=notification.is_read,
                is_approved=notification.is_approved,
                created_at=notification.created_at.isoformat() if notification.created_at else "",
                updated_at=notification.updated_at.isoformat() if notification.updated_at else ""
            ))
        
        return response_notifications
        
    except Exception as e:
        logger.error(f"Error fetching user notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@notification_router.put("/{notification_id}/read")
async def mark_notification_as_read(notification_id: str):
    """Mark a notification as read"""
    try:
        success = mark_notification_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@notification_router.put("/{notification_id}/approval", response_model=NotificationApprovalResponse)
async def update_notification_approval_endpoint(
    notification_id: str, 
    request: NotificationApprovalRequest
):
    """Update notification approval status (for resolution requests)"""
    try:
        # Validate approval value
        if request.is_approved not in ["true", "false"]:
            raise HTTPException(status_code=400, detail="is_approved must be 'true' or 'false'")
        
        # Update notification approval
        success = update_notification_approval(notification_id, request.is_approved)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # If approved, update the emergency case status to resolved
        if request.is_approved == "true":
            # Get notification to find emergency details
            notifications = get_user_notifications("", None)  # Get all notifications
            notification = next((n for n in notifications if n.id == notification_id), None)
            
            if notification and notification.emergency_id and notification.emergency_type:
                # Update emergency status to resolved
                update_success = update_emergency_status(
                    notification.emergency_id,
                    notification.emergency_type,
                    EmergencyStatus.RESOLVED
                )
                
                if update_success:
                    return NotificationApprovalResponse(
                        success=True,
                        message="Notification approved and emergency case marked as resolved"
                    )
                else:
                    return NotificationApprovalResponse(
                        success=True,
                        message="Notification approved but failed to update emergency status"
                    )
        
        return NotificationApprovalResponse(
            success=True,
            message=f"Notification approval updated to {request.is_approved}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification approval: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@notification_router.get("/user/{user_id}/unread/count")
async def get_unread_notification_count(user_id: str):
    """Get count of unread notifications for a user"""
    try:
        unread_notifications = get_user_notifications(user_id, "false")
        
        return {
            "user_id": user_id,
            "unread_count": len(unread_notifications)
        }
        
    except Exception as e:
        logger.error(f"Error getting unread notification count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@notification_router.get("/user/{user_id}/pending-approvals")
async def get_pending_approval_notifications(user_id: str):
    """Get notifications pending user approval"""
    try:
        all_notifications = get_user_notifications(user_id, None)
        
        # Filter for resolution requests that are not yet approved/denied
        pending_notifications = [
            n for n in all_notifications 
            if n.notification_type == "resolution_request" and n.is_approved is None
        ]
        
        # Convert to response format
        response_notifications = []
        for notification in pending_notifications:
            response_notifications.append(NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                emergency_id=notification.emergency_id,
                emergency_type=notification.emergency_type,
                is_read=notification.is_read,
                is_approved=notification.is_approved,
                created_at=notification.created_at.isoformat() if notification.created_at else "",
                updated_at=notification.updated_at.isoformat() if notification.updated_at else ""
            ))
        
        return response_notifications
        
    except Exception as e:
        logger.error(f"Error fetching pending approval notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
