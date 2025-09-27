"""
Utility functions for formatting conversation messages from agent states.
"""

from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage


def format_conversation_messages(state: Dict[str, Any]) -> str:
    """
    Extract and format human and AI messages from agent state into a readable string.
    
    Args:
        state: Agent state containing messages list
        
    Returns:
        str: Formatted conversation string with human and AI messages only
    """
    messages = state.get("messages", [])
    formatted_messages = []
    
    for message in messages:
        if isinstance(message, HumanMessage):
            formatted_messages.append(f"Human: {message.content}")
        elif isinstance(message, AIMessage):
            # Skip AI messages that only contain tool calls (empty content)
            if message.content and message.content.strip():
                formatted_messages.append(f"AI: {message.content}")
    
    return "\n\n".join(formatted_messages)


def extract_conversation_summary(state: Dict[str, Any]) -> str:
    """
    Extract a concise summary of the conversation for case submission.
    
    Args:
        state: Agent state containing messages list
        
    Returns:
        str: Concise conversation summary
    """
    messages = state.get("messages", [])
    conversation_parts = []
    
    for message in messages:
        if isinstance(message, HumanMessage):
            # Clean up human messages (remove formatting markers)
            content = message.content.strip()
            if content:
                conversation_parts.append(f"User: {content}")
        elif isinstance(message, AIMessage):
            # Only include AI messages with actual content (not tool calls)
            if message.content and message.content.strip():
                conversation_parts.append(f"Assistant: {message.content}")
    
    return " | ".join(conversation_parts)


def get_last_human_message(state: Dict[str, Any]) -> str:
    """
    Get the content of the last human message from the state.
    
    Args:
        state: Agent state containing messages list
        
    Returns:
        str: Content of the last human message, or empty string if none found
    """
    messages = state.get("messages", [])
    
    # Iterate in reverse to find the last human message
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content.strip()
    
    return ""


def get_conversation_count(state: Dict[str, Any]) -> int:
    """
    Get the count of human messages in the conversation.
    
    Args:
        state: Agent state containing messages list
        
    Returns:
        int: Number of human messages
    """
    messages = state.get("messages", [])
    return sum(1 for message in messages if isinstance(message, HumanMessage))
