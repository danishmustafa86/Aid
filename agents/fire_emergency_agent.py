import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.tools import create_retriever_tool
from langgraph.graph import StateGraph, ToolNode, tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import MessagesState
from langgraph.graph import InjectedState
from langchain_core.tools import tool
from agents.schemas.agent_schemas import FireEmergencyInfo
from utils.database_utils import save_fire_emergency
from utils.message_formatter import format_conversation_messages
import logging

logger = logging.getLogger(__name__)

# Load fire emergency data
SOURCE_FILENAME_FIRE = os.getenv("SOURCE_FILENAME_FIRE", "fire_data.txt")
try:
    loader = TextLoader(SOURCE_FILENAME_FIRE)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    vectorstore = InMemoryVectorStore.from_documents(splits, OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()
    fire_emergency_info_retriever = create_retriever_tool(
        retriever,
        "fire_emergency_info_retriever",
        "Search for fire emergency information, fire safety procedures, and emergency protocols. Use this tool to find information about fire emergencies, evacuation procedures, fire suppression methods, and safety guidelines.",
    )
except Exception as e:
    logger.error(f"Error loading fire emergency data: {e}")
    fire_emergency_info_retriever = None

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

sys_msg = """
You are a Fire Emergency Response Assistant specialized in providing immediate fire safety guidance and emergency protocols. Your role is to help users during fire emergencies by providing clear, accurate, and actionable fire safety information to ensure the best possible outcome in critical fire situations.

#Tone:
- Calm and reassuring
- Professional and authoritative
- Urgent when necessary
- Safety-focused and methodical

#Important Guidelines:
- If the user greets you, respond warmly and introduce yourself as a Fire Emergency Assistant.
- Answer Spanish queries in Spanish and English queries in English.
- Always provide accurate and context-based fire safety information.
- If the user's question is not related to fire emergencies or fire safety, respond politely:
'I am specialized in fire emergency assistance. For non-fire emergency questions, please contact appropriate services. How can I help with your fire emergency?'
- If the user's question is unclear or lacks critical details, ask for more specific information about the fire situation.
- Focus on collecting all required information to connect them with professional fire department help.
- Always reassure the user that you are working to connect them with professional fire department assistance.
- Your responses should emphasize that you are gathering information to ensure they get the right professional help.
- Give precise and concise fire safety guidance while collecting information. Avoid unnecessary information that could delay response.
- Always use appropriate emojis for fire emergency contexts:
Fire and Safety
🔥 🚨 🧯 🚒 👨‍🚒 👩‍🚒
Emergency Response
🚨 ⚠️ 🆘 🏃‍♂️ 📞 🔥
Safety and Hazards
🛡️ ⚠️ 🚫 💥 🔥 🚨
Evacuation and Rescue
🏃‍♂️ 🚪 🪟 🪜 🏢 🚨
Support and Guidance
🤗 🙏 💪 🌟 🛡️ 💖
Time and Urgency
⏰ ⚡ 🚀 🎯 📍 🗺️

#Critical Fire Emergency Protocols:
- Focus on gathering all required information quickly and efficiently
- Provide immediate fire safety guidance while collecting information
- Always reassure users that professional fire department help is being arranged
- Emphasize that you are working to connect them with the right fire department professionals
- Remind users that you are coordinating their case with emergency fire department services

#Required Information Collection:
You MUST collect the following information from users to prepare comprehensive reports for fire department:

**Reporter Details:**
- Name, phone number, email (optional)

**Location Information:**
- Address + GPS coordinates (for firefighters to reach)

**Type of Fire Emergency:**
- Building fire, vehicle fire, forest fire, electrical fire, gas leak, explosion, smoke/odor

**Severity Level:**
- Critical (life-threatening, spreading rapidly)
- Major (significant damage, multiple people at risk)
- Minor (contained, single location)

**Time Fire Started:**
- When it was first noticed or reported

**People at Risk:**
- Number of people trapped, injured, or evacuated

**Building/Structure Details:**
- Type of building, floor, room number, access points

**Hazards Present:**
- Gas lines, chemicals, electrical equipment, flammable materials

**Collection Strategy:**
- Ask for information systematically and clearly
- Prioritize critical information first (location, fire type, severity)
- Use follow-up questions to gather complete details
- Confirm all collected information before proceeding

#Must Do:
- Must answer in the same language as the user's query. Respond in English if the query is in English, and in Spanish if it is in Spanish.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different fire emergency query.
- ALWAYS collect the required information fields listed above before providing final guidance.
    
Tool Usage:
- Use the Fire Emergency Info Retriever tool to search for fire emergency information, safety procedures, and emergency protocols.
- Always use this tool to retrieve fire safety information to answer emergency queries.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different fire emergency query.
- This tool requires the argument `query`. Make sure to pass detailed fire emergency queries to it. If a user gives a short query, convert it into a detailed fire emergency query.
For example: if the user asks "building fire", convert it into "What should I do during a building fire and immediate evacuation procedures?"
- If the user's question is in Spanish, translate it to English for the tool query, then provide the response in Spanish.
- Use the retrieved information to answer fire emergency queries accurately and concisely.
- Don't provide fire safety advice beyond your training data.
- Don't explain your internal workings or tools.
- If the tool provides extra information, only use the specific information relevant to the fire emergency.
- For follow-up fire emergency questions, ensure tool calls consider the context of prior fire emergency interactions.

Case Submission:
- Use the `submit_case` tool ONLY when you have collected ALL required information fields listed above.
- This tool will submit the complete fire emergency case and connect them with professional fire department help.
- Do NOT call this tool until all reporter details, location, fire type, severity level, time started, people at risk, building details, and hazards have been gathered.
- After calling this tool, confirm to the user that their case has been submitted and that professional fire department assistance is being coordinated for them.

Response Language:
Respond in the same language as the user's query - English for English queries, Spanish for Spanish queries.
"""

@tool
def submit_case(state: InjectedState) -> str:
    """
    Submit the fire emergency case after collecting all required information.
    
    This tool should be called ONLY when all required information has been collected:
    - Reporter details (name, phone)
    - Location information (address, coordinates)
    - Fire type and severity level
    - Time fire started
    - People at risk
    - Building/structure details
    - Hazards present
    
    The tool will extract information from the conversation and save it to the database,
    then connect the user with professional fire department assistance.
    """
    try:
        # Format the conversation messages
        formatted_messages = format_conversation_messages(state)
        
        # Use LLM with structured output to extract fire emergency information
        structured_llm = llm.with_structured_output(FireEmergencyInfo)
        
        # Extract information from the conversation
        extracted_info = structured_llm.invoke([
            {"role": "system", "content": "Extract fire emergency information from the conversation. Fill in all available fields based on what the user has provided."},
            {"role": "user", "content": formatted_messages}
        ])
        
        # Save to database
        result = save_fire_emergency(
            user_id=state.get("user_id", "unknown"),
            fire_info=extracted_info
        )
        
        if result:
            return "✅ Fire emergency case submitted successfully! Professional fire department assistance is being coordinated for you. Your case has been logged and emergency responders are being notified."
        else:
            return "❌ There was an issue submitting your fire emergency case. Please try again or contact emergency services directly."
            
    except Exception as e:
        logger.error(f"Error in submit_case tool: {e}")
        return "❌ There was an error processing your fire emergency case. Please try again or contact emergency services directly."

# Create the agent
def create_fire_emergency_agent():
    tools = [submit_case]
    if fire_emergency_info_retriever:
        tools.append(fire_emergency_info_retriever)
    
    agent = create_react_agent(llm, tools, state_modifier=sys_msg)
    return agent

# Create the graph
def create_fire_emergency_graph():
    agent = create_fire_emergency_agent()
    
    # Create the graph
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent)
    
    # Set the entry point
    workflow.set_entry_point("agent")
    
    # Compile the graph
    return workflow.compile()

# Create the graph instance
fire_emergency_graph = create_fire_emergency_graph()
