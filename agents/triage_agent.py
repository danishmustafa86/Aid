import logging
from enum import Enum
from typing import Annotated, Optional
from dotenv import load_dotenv
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from configurations.db import mongodb_client
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("zaingpt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def keep_last(left, right):
    if left and right:
        return right
    if left:
        return left
    if right:
        return right
    return None


class TriageState(MessagesState):
    emergency_type: Annotated[Optional[str], keep_last]


class EmergencyType(Enum):
    Medical = "Medical"
    Police = "Police"
    Electricity = "Electricity"


llm = ChatOpenAI(model="gpt-4o-mini")

@tool
def classify_emergency_type(emergency_type: EmergencyType):
    """Classify the emergency type based on the user's query.

    Args:
        emergency_type: One of the enum values: Medical, Police, Electricity

    Returns:
        dict with the classified emergency type under key 'emergency_type'.
    """
    return {"emergency_type": emergency_type.value}


tools = [classify_emergency_type]
tools_by_name = {t.name: t for t in tools}

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

sys_msg = """You are an Emergency Triage Agent, designed to quickly assess and classify emergency situations to route users to the appropriate emergency service. Your primary goal is to analyze user queries and determine the type of emergency they are experiencing.

## Emergency Types
You can classify emergencies into three main categories:
- **Medical Emergency**: Health-related emergencies including injuries, illnesses, accidents, medical conditions, ambulance needs
- **Police Emergency**: Security-related emergencies including crimes, theft, violence, suspicious activities, law enforcement needs
- **Electricity Emergency**: Power-related emergencies including power outages, electrical hazards, electrical fires, utility issues

## Response Guidelines

### Emergency Assessment:
- Listen carefully to the user's description of their emergency
- Ask clarifying questions if needed to better understand the situation
- Classify the emergency type using the available tool
- Provide appropriate initial guidance based on the emergency type
- Always prioritize safety and immediate action when necessary

### Emergency Classification Tool:
- You have access to a tool named `classify_emergency_type(emergency_type)` where `emergency_type` is one of: Medical, Police, Electricity
- ALWAYS call this tool when a user describes an emergency situation
- After calling the tool, provide relevant guidance and next steps
- Include the emergency type in your response for transparency

### Response Structure:
- Acknowledge the emergency with empathy and urgency
- Classify the emergency type using the tool
- Provide immediate actionable guidance
- Suggest appropriate emergency contacts if relevant
- Offer reassurance while emphasizing the importance of professional help

### Emergency-Specific Guidance:
- **Medical**: Prioritize calling emergency services (911/ambulance), basic first aid if safe
- **Police**: Advise calling police emergency number, staying safe, preserving evidence if possible
- **Electricity**: Warn about electrical hazards, advise turning off power if safe, contact utility company

### Context Boundaries:
- If the query is not an emergency, politely redirect: "I'm an Emergency Triage Agent specialized in helping with emergency situations. Please describe your emergency so I can help you get the appropriate assistance."
- For non-emergency situations, suggest contacting appropriate non-emergency services

## Response Language:
- Use clear, concise, and urgent language
- Be empathetic and reassuring
- Provide actionable steps
- Always prioritize safety
"""


def assistant(state: TriageState):
    """Calls the LLM (with tools bound) using the last 6 messages."""
    try:
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"][-6:])]}
    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        raise


def tool_node(state: TriageState):
    results: list[ToolMessage] = []
    # The last AI message may include tool calls
    ai_msg = state["messages"][-1]
    if not hasattr(ai_msg, "tool_calls"):
        return {"messages": results}
    for call in ai_msg.tool_calls:
        tool_name = call["name"]
        args = call["args"]
        tool_fn = tools_by_name.get(tool_name)
        if tool_fn is None:
            continue
        observation = tool_fn.invoke(args)
        results.append(ToolMessage(content=observation, tool_call_id=call["id"]))
        if tool_name == "classify_emergency_type":
            # Prefer observation, else raw arg value (may be enum or string)
            emergency_value = observation.get("emergency_type") or args.get("emergency_type")
            return {"messages": results, "emergency_type": emergency_value}
    return {"messages": results}

# Build graph
try:
    graph_builder = StateGraph(TriageState)
    graph_builder.add_node("assistant", assistant)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "assistant")
    graph_builder.add_conditional_edges("assistant", tools_condition)
    graph_builder.add_edge("tools", "assistant")

    memory = MongoDBSaver(mongodb_client)
    graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise