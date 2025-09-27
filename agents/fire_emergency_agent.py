import logging
from langchain_community.document_loaders import TextLoader
from dotenv import load_dotenv
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from typing import Annotated
from configurations.config import config
from configurations.db import mongodb_client
from utils.message_formatter import format_conversation_messages
from utils.database_utils import save_fire_emergency
from agents.schemas.agent_schemas import FireEmergencySchema

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("fire_emergency.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize embeddings, vector store, and retriever
try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = InMemoryVectorStore(embeddings)

    loader = TextLoader(f"data/{config.SOURCE_FILENAME_FIRE}", encoding="utf-8")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    all_splits = text_splitter.split_documents(docs)

    _ = vector_store.add_documents(documents=all_splits)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
except Exception as e:
    logger.error(f"Error during initialization: {e}")
    raise

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

fire_emergency_info_retriever = create_retriever_tool(
    retriever,
    "fire_emergency_info_retriever",
    "Searches information about fire emergencies, fire safety procedures, emergency protocols, and fire guidance. Takes in a query and finds relevant fire emergency context to answer emergency situations.",
)

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

def submit_fire_case(state: MessagesState):
    """
    Submit fire emergency case to database
    
    Args:
        state: Current agent state with conversation history
        
    Returns:
        dict: Submission result
    """
    # Extract information from conversation history
    messages = state.get("messages", [])
    
    # Format conversation for processing
    formatted_conversation = format_conversation_messages(state)
    print("-------------")
    print("formatted_conversation", formatted_conversation)
    print("-------------")
    
    try:
        # Use LLM with structured output to extract data from conversation
        structured_llm = llm.with_structured_output(FireEmergencySchema)
        
        # Create prompt for data extraction
        extraction_prompt = f"""
        Extract fire emergency information from the following conversation and structure it according to the FireEmergencySchema.
        
        Conversation:
        {formatted_conversation}
        
        Please extract the following information:
        - Reporter name, phone number
        - Location address
        - Fire type (building fire, vehicle fire, etc.)
        - Severity level (critical, major, minor)
        - Time fire started
        - People at risk
        - Building/structure details
        - Hazards present
        
        If any information is not available in the conversation, leave it as null.
        """
        
        # Extract structured data using LLM
        fire_data = structured_llm.invoke(extraction_prompt)
        
        # Save to database
        user_id = "default_user"  # In real implementation, this would come from authentication
        case_id = save_fire_emergency(user_id, fire_data)
        
        print(f"Fire emergency case saved to database with ID: {case_id}")
        
        return {
            "status": "submitted",
            "case_id": case_id,
            "message": "Fire emergency case has been submitted successfully. Emergency services have been notified."
        }
        
    except Exception as e:
        logger.error(f"Error submitting fire emergency case: {e}")
        return {
            "status": "error",
            "case_id": None,
            "message": f"Failed to submit fire emergency case: {str(e)}"
        }

@tool
def submit_case():
    """
    Submit the fire emergency case with all collected information.
    
    This tool should be called ONLY when all required information has been collected:
    - Reporter details (name, phone)
    - Location information (address, coordinates)
    - Fire type and severity level
    - Time fire started
    - People at risk
    - Building/structure details
    - Hazards present
    
    Once all information is gathered, call this tool to submit the case
    for fire department authorities to receive comprehensive fire emergency
    details upfront, reducing response delays.
    """
    # This tool will be handled by the custom tool node
    return {"status": "Submitted"}

# Define tools
tools = [fire_emergency_info_retriever, submit_case]
tools_by_name = {t.name: t for t in tools}

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

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
        
        if tool_name == "submit_case":
            # Handle submit_case with access to full state
            result = submit_fire_case(state)
            results.append(ToolMessage(
                content=f"Case submitted successfully. Case ID: {result['case_id']}. {result['message']}", 
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
    fire_emergency_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise