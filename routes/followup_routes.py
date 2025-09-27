from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from agents.followup_agent import followup_graph
from utils.database_utils import get_emergency_report_by_id
import logging

logger = logging.getLogger(__name__)

followup_router = APIRouter(prefix="/followup", tags=["Follow-up"])

# Pydantic models for API requests/responses
class FollowupChatRequest(BaseModel):
    message: str
    emergency_id: str
    emergency_type: str
    user_id: str
    thread_id: Optional[str] = None

class FollowupChatResponse(BaseModel):
    response: str
    thread_id: str
    emergency_id: str
    emergency_type: str

class EmergencyCaseInfo(BaseModel):
    emergency_id: str
    emergency_type: str
    user_id: str
    status: str
    case_data: dict

@followup_router.post("/chat", response_model=FollowupChatResponse)
async def chat_with_followup_agent(request: FollowupChatRequest, background_tasks: BackgroundTasks):
    """
    Chat with the follow-up agent for emergency case resolution
    
    Args:
        request: Chat request with message, emergency details, and user info
        
    Returns:
        FollowupChatResponse: Agent response with thread and case information
    """
    try:
        # Verify the emergency case exists
        case = get_emergency_report_by_id(request.emergency_id, request.emergency_type)
        if not case:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        # Verify the user owns this case
        if case.user_id != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this emergency case")
        
        # Use thread_id if provided, otherwise generate one
        thread_id = request.thread_id or f"followup_{request.emergency_id}_{request.user_id}"
        
        # Create the initial message with context
        from langchain_core.messages import HumanMessage
        
        # Add context about the emergency case
        context_message = f"""
        Emergency Case Context:
        - Case ID: {request.emergency_id}
        - Emergency Type: {request.emergency_type}
        - Case Status: {case.status.value}
        - User ID: {request.user_id}
        
        User Message: {request.message}
        """
        
        # Create the conversation state
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get the current state
        current_state = followup_graph.get_state(config)
        
        # Add the new message
        messages = current_state.values.get("messages", [])
        messages.append(HumanMessage(content=context_message))
        
        # Update the state
        followup_graph.update_state(config, {"messages": messages})
        
        # Invoke the agent
        result = followup_graph.invoke(None, config)
        
        # Get the last AI message
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        return FollowupChatResponse(
            response=response_text,
            thread_id=thread_id,
            emergency_id=request.emergency_id,
            emergency_type=request.emergency_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in follow-up chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@followup_router.get("/case/{emergency_id}/{emergency_type}/{user_id}", response_model=EmergencyCaseInfo)
async def get_emergency_case_info(emergency_id: str, emergency_type: str, user_id: str):
    """
    Get emergency case information for follow-up
    
    Args:
        emergency_id: ID of the emergency case
        emergency_type: Type of emergency (medical, police, electricity, fire)
        user_id: User ID
        
    Returns:
        EmergencyCaseInfo: Case information for follow-up
    """
    try:
        # Get the emergency case
        case = get_emergency_report_by_id(emergency_id, emergency_type)
        if not case:
            raise HTTPException(status_code=404, detail="Emergency case not found")
        
        # Verify the user owns this case
        if case.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied: You don't own this emergency case")
        
        # Extract case data based on emergency type
        case_data = {}
        if emergency_type.lower() == "medical":
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
        elif emergency_type.lower() == "police":
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
        elif emergency_type.lower() == "electricity":
            case_data = {
                "reporter_name": case.reporter_name,
                "reporter_phone": case.reporter_phone,
                "location": case.location,
                "issue_type": case.issue_type,
                "severity": case.severity,
                "time_started": case.time_started,
                "description": case.description
            }
        
        return EmergencyCaseInfo(
            emergency_id=case.id,
            emergency_type=emergency_type,
            user_id=case.user_id,
            status=case.status.value,
            case_data=case_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting emergency case info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@followup_router.get("/conversation/{thread_id}")
async def get_conversation_history(thread_id: str):
    """
    Get conversation history for a follow-up thread
    
    Args:
        thread_id: Thread ID for the conversation
        
    Returns:
        dict: Conversation history
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = followup_graph.get_state(config)
        
        messages = state.values.get("messages", [])
        
        # Convert messages to a readable format
        conversation = []
        for message in messages:
            conversation.append({
                "type": message.__class__.__name__,
                "content": message.content if hasattr(message, 'content') else str(message),
                "timestamp": getattr(message, 'timestamp', None)
            })
        
        return {
            "thread_id": thread_id,
            "conversation": conversation,
            "message_count": len(conversation)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@followup_router.delete("/conversation/{thread_id}")
async def clear_conversation_history(thread_id: str):
    """
    Clear conversation history for a follow-up thread
    
    Args:
        thread_id: Thread ID for the conversation
        
    Returns:
        dict: Success message
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # Clear the conversation by updating with empty messages
        followup_graph.update_state(config, {"messages": []})
        
        return {
            "success": True,
            "message": f"Conversation history cleared for thread {thread_id}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
