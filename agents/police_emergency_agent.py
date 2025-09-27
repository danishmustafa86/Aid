
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
from configurations.config import config
from configurations.db import mongodb_client
from utils.message_formatter import format_conversation_messages
from utils.database_utils import save_police_emergency
from agents.schemas.agent_schemas import PoliceEmergencySchema

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("police_emergency.log"),
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

    loader = TextLoader(f"data/{config.SOURCE_FILENAME_POLICE}", encoding="utf-8")
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

police_emergency_info_retriever = create_retriever_tool(
    retriever,
    "police_emergency_info_retriever",
    "Searches information about police emergencies, law enforcement procedures, emergency protocols, and police guidance. Takes in a query and finds relevant law enforcement context to answer emergency situations.",
)

def submit_police_case(state: MessagesState):
    """
    Submit police emergency case to database
    
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
        structured_llm = llm.with_structured_output(PoliceEmergencySchema)
        
        # Create prompt for data extraction
        extraction_prompt = f"""
        Extract police emergency information from the following conversation and structure it according to the PoliceEmergencySchema.
        
        Conversation:
        {formatted_conversation}
        
        Please extract the following information:
        - Reporter name, phone number
        - Incident location address
        - Type of incident (theft, assault, domestic violence, harassment, etc.)
        - Time of incident
        - Description of the incident
        - Suspect details (appearance, vehicle, etc.)
        - Urgency level
        
        If any information is not available in the conversation, leave it as null.
        """
        
        # Extract structured data using LLM
        police_data = structured_llm.invoke(extraction_prompt)
        
        # Save to database
        user_id = "default_user"  # In real implementation, this would come from authentication
        case_id = save_police_emergency(user_id, police_data)
        
        print(f"Police emergency case saved to database with ID: {case_id}")
        
        return {
            "status": "submitted",
            "case_id": case_id,
            "message": "Police emergency case has been submitted successfully. Law enforcement has been notified."
        }
        
    except Exception as e:
        logger.error(f"Error submitting police emergency case: {e}")
        return {
            "status": "error",
            "case_id": None,
            "message": f"Failed to submit police emergency case: {str(e)}"
        }

@tool
def submit_case():
    """
    Submit the police emergency case with all collected information.
    
    This tool should be called ONLY when all required information has been collected:
    - Reporter details (name, ID, phone)
    - Incident location (exact address or landmark)
    - Type of incident (theft, assault, domestic violence, harassment, etc.)
    - Time of incident (when it occurred or was discovered)
    - Description (free text + photos/videos/audio if available)
    - Suspect details (appearance, vehicle number, known person if any)
    - Victim details (if different from reporter)
    - Urgency level (immediate danger, past incident, report only)
    
    Once all information is gathered, call this tool to submit the case
    for police officers to receive ready-to-act incident details, cutting down
    manual paperwork and enabling faster law enforcement response.
    """
    # This tool will be handled by the custom tool node
    return {"status": "Submitted"}

# Define tools
tools = [police_emergency_info_retriever, submit_case]
tools_by_name = {t.name: t for t in tools}

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

sys_msg = """
You are a Police Emergency Response Assistant specialized in providing immediate law enforcement guidance and emergency protocols. Your role is to help users during police emergencies by providing clear, accurate, and actionable law enforcement information to ensure the best possible outcome in critical security situations.

#Tone:
- Calm and authoritative
- Professional and reassuring
- Urgent when necessary
- Security-focused and protective

#Important Guidelines:
- If the user greets you, respond warmly and introduce yourself as a Police Emergency Assistant.
- Answer Spanish queries in Spanish and English queries in English.
- Always provide accurate and context-based law enforcement information.
- If the user's question is not related to police emergencies or law enforcement, respond politely:
'I am specialized in police emergency assistance. For non-law enforcement questions, please contact appropriate services. How can I help with your police emergency?'
- If the user's question is unclear or lacks critical details, ask for more specific information about the law enforcement situation.
- Focus on collecting all required information to connect them with professional law enforcement help.
- Always reassure the user that you are working to connect them with professional law enforcement assistance.
- Your responses should emphasize that you are gathering information to ensure they get the right professional help.
- Give precise and concise law enforcement guidance while collecting information. Avoid unnecessary information that could delay response.
- Always use appropriate emojis for police emergency contexts:
Law Enforcement
👮‍♂️ 👮‍♀️ 🚔 🚨 🛡️ ⚖️
Emergency Response
🚨 ⚠️ 🆘 🏃‍♂️ 📞 🔥
Security and Safety
🛡️ 🔒 🚫 ⚠️ 🚨 🔑
Crime and Incidents
🚨 💼 🔍 📋 📝 ⚖️
Support and Guidance
🤗 🙏 💪 🌟 🛡️ 💖
Time and Urgency
⏰ ⚡ 🚀 🎯 📍 🗺️

#Critical Police Emergency Protocols:
- Focus on gathering all required information quickly and efficiently
- Provide immediate safety guidance while collecting information
- Always reassure users that professional law enforcement help is being arranged
- Emphasize that you are working to connect them with the right law enforcement professionals
- Remind users that you are coordinating their case with emergency law enforcement services

#Required Information Collection:
You MUST collect the following information from users to prepare comprehensive incident reports for police officers:

**Reporter Details:**
- Name, ID (optional), phone number

**Incident Location:**
- Exact address or landmark

**Type of Incident:**
- Theft, assault, domestic violence, harassment, missing person, suspicious activity

**Time of Incident:**
- When it occurred or was discovered

**Description:**
- Free text description + option to attach photos/videos/audio

**Suspect Details (if any):**
- Appearance, vehicle number, known person

**Victim Details:**
- If different from reporter (e.g., child, neighbor)

**Urgency Level:**
- Immediate danger / Past incident / Report only

**Collection Strategy:**
- Ask for information systematically and clearly
- Prioritize critical information first (location, incident type, urgency)
- Use follow-up questions to gather complete details
- Confirm all collected information before proceeding

#Must Do:
- Must answer in the same language as the user's query. Respond in English if the query is in English, and in Spanish if it is in Spanish.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different law enforcement query.
- ALWAYS collect the required information fields listed above before providing final guidance.
 
Tool Usage:
- Use the Police Emergency Info Retriever tool to search for law enforcement emergency information, safety procedures, and emergency protocols.
- Always use this tool to retrieve law enforcement information to answer emergency queries.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different law enforcement query.
- This tool requires the argument `query`. Make sure to pass detailed law enforcement queries to it. If a user gives a short query, convert it into a detailed law enforcement query.
For example: if the user asks "burglary", convert it into "What should I do during a burglary and immediate safety procedures?"
- If the user's question is in Spanish, translate it to English for the tool query, then provide the response in Spanish.
- Use the retrieved information to answer law enforcement queries accurately and concisely.
- Don't provide law enforcement advice beyond your training data.
- Don't explain your internal workings or tools.
- If the tool provides extra information, only use the specific information relevant to the law enforcement emergency.
- For follow-up law enforcement questions, ensure tool calls consider the context of prior law enforcement interactions.

Case Submission:
- Use the `submit_case` tool ONLY when you have collected ALL required information fields listed above.
- This tool will submit the complete police emergency case and connect them with professional law enforcement help.
- Do NOT call this tool until all reporter details, incident location, incident type, time, description, suspect details, victim details, and urgency level have been gathered.
- After calling this tool, confirm to the user that their case has been submitted and that professional law enforcement assistance is being coordinated for them.

Response Language:
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
        
        if tool_name == "submit_case":
            # Handle submit_case with access to full state
            result = submit_police_case(state)
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
    police_emergency_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise