import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from configurations.db import mongodb_client
from utils.database_utils import update_emergency_status, get_emergency_report_by_id
from models.database_models import EmergencyStatus

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("followup_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

def resolve_emergency_case(emergency_id: str, emergency_type: str):
    """
    Resolve an emergency case by updating its status to RESOLVED
    
    Args:
        emergency_id: ID of the emergency case
        emergency_type: Type of emergency (medical, police, electricity)
        
    Returns:
        dict: Resolution result
    """
    try:
        # Update status to resolved
        success = update_emergency_status(emergency_id, emergency_type, EmergencyStatus.RESOLVED)
        
        if success:
            return {
                "status": "resolved",
                "message": f"Your {emergency_type} emergency case has been successfully resolved and closed."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to resolve the {emergency_type} emergency case. Please try again."
            }
            
    except Exception as e:
        logger.error(f"Error resolving emergency case: {e}")
        return {
            "status": "error",
            "message": f"An error occurred while resolving the case: {str(e)}"
        }

@tool
def mark_case_resolved(emergency_id: str, emergency_type: str):
    """
    Mark an emergency case as resolved when the user confirms satisfaction.
    
    This tool should be called ONLY when the user explicitly confirms they are satisfied
    with the resolution of their emergency case.
    
    Args:
        emergency_id: ID of the emergency case to resolve
        emergency_type: Type of emergency (medical, police, electricity)
        
    Returns:
        dict: Resolution confirmation
    """
    return resolve_emergency_case(emergency_id, emergency_type)

# Define tools
tools = [mark_case_resolved]
tools_by_name = {t.name: t for t in tools}

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

sys_msg = """
You are a Follow-up Emergency Resolution Assistant specialized in helping users confirm that their emergency cases have been properly resolved. Your role is to engage with users to ensure they are satisfied with the resolution of their emergency situation.

#Tone:
- Warm and supportive
- Professional and empathetic
- Patient and understanding
- Encouraging and positive

#Important Guidelines:
- If the user greets you, respond warmly and introduce yourself as a Follow-up Resolution Assistant.
- Answer Spanish queries in Spanish and English queries in English.
- Always provide context about the specific emergency case being discussed.
- If the user's question is not related to emergency case resolution, respond politely:
'I am specialized in helping with emergency case follow-up and resolution. How can I help you with your emergency case resolution?'
- If the user's question is unclear, ask for clarification about their satisfaction with the case resolution.
- Always prioritize user satisfaction and safety when discussing case resolution.
- Your responses should end with asking if they need any additional assistance with their case.

#Case Resolution Process:
You MUST guide users through the following process:

1. **Case Verification**: Confirm the user is discussing the correct emergency case
2. **Resolution Check**: Ask about their satisfaction with how the case was handled
3. **Service Quality**: Inquire about the quality of service received from authorities
4. **Outcome Confirmation**: Verify that the emergency situation has been properly resolved
5. **Final Satisfaction**: Confirm overall satisfaction with the resolution process

#Required Information Collection:
You MUST collect the following information to properly resolve the case:

**Case Details:**
- Emergency case ID (provided in context)
- Emergency type (medical, police, electricity)

**User Satisfaction:**
- Overall satisfaction with the resolution
- Quality of service received
- Whether the emergency situation is resolved
- Any remaining concerns or issues

**Resolution Confirmation:**
- User's explicit confirmation of satisfaction
- Agreement to mark the case as resolved

#Must Do:
- Must answer in the same language as the user's query. Respond in English if the query is in English, and in Spanish if it is in Spanish.
- ALWAYS verify the user is satisfied before calling the resolution tool.
- Use the `mark_case_resolved` tool ONLY when the user explicitly confirms they are satisfied.
- Do NOT call the resolution tool until you have confirmed user satisfaction.
- After calling the resolution tool, confirm to the user that their case has been resolved.

#Tool Usage:
- Use the `mark_case_resolved` tool ONLY when the user explicitly confirms satisfaction with the case resolution.
- This tool requires the arguments `emergency_id` and `emergency_type`.
- Make sure to pass the correct emergency ID and type to the tool.
- The tool will update the case status to "resolved" in the database.
- After calling this tool, inform the user that their case has been successfully resolved.

#Response Language:
Respond in the same language as the user's query - English for English queries, Spanish for Spanish queries.
"""

def generate(state: MessagesState):
    """
    Generates a response based on the user's message history.

    Parameters:
        state (MessagesState): The state of the conversation, containing past messages.

    Returns:
        dict: A dictionary containing the generated message.
    """
    try:
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"][-6:])]}
    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        raise

def custom_tool_node(state: MessagesState):
    """
    Custom tool node that can access the agent's state and handle tools accordingly.
    """
    results: list[ToolMessage] = []
    
    # Get the last AI message which may contain tool calls
    ai_msg = state["messages"][-1]
    
    if not hasattr(ai_msg, "tool_calls"):
        return {"messages": results}
    
    for call in ai_msg.tool_calls:
        tool_name = call["name"]
        args = call["args"]
        tool_call_id = call["id"]
        
        if tool_name == "mark_case_resolved":
            # Handle mark_case_resolved tool
            emergency_id = args.get("emergency_id")
            emergency_type = args.get("emergency_type")
            
            if not emergency_id or not emergency_type:
                results.append(ToolMessage(
                    content="Error: Missing emergency_id or emergency_type parameters",
                    tool_call_id=tool_call_id
                ))
                continue
            
            result = resolve_emergency_case(emergency_id, emergency_type)
            results.append(ToolMessage(
                content=f"Case resolution result: {result['message']}",
                tool_call_id=tool_call_id
            ))
        else:
            # Handle other tools normally
            tool_fn = tools_by_name.get(tool_name)
            if tool_fn is not None:
                observation = tool_fn.invoke(args)
                results.append(ToolMessage(content=str(observation), tool_call_id=tool_call_id))
    
    return {"messages": results}

# Build graph
try:
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("generate", generate)
    graph_builder.add_node("tools", custom_tool_node)
    graph_builder.add_edge(START, "generate")
    graph_builder.add_conditional_edges("generate", tools_condition)
    graph_builder.add_edge("tools", "generate")

    memory = MongoDBSaver(mongodb_client)
    followup_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise
