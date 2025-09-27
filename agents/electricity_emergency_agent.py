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
from utils.database_utils import save_electricity_emergency
from agents.schemas.agent_schemas import ElectricityEmergencySchema

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("electricity_emergency.log"),
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

    loader = TextLoader(f"data/{config.SOURCE_FILENAME_ELECTRICITY}", encoding="utf-8")
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

electricity_emergency_info_retriever = create_retriever_tool(
    retriever,
    "electricity_emergency_info_retriever",
    "Searches information about electrical emergencies, power outages, electrical safety protocols, and emergency electrical procedures. Takes in a query and finds relevant electrical emergency context to answer emergency situations.",
)

def submit_electricity_case(state: MessagesState):
    """
    Submit electricity emergency case to database
    
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
        structured_llm = llm.with_structured_output(ElectricityEmergencySchema)
        
        # Create prompt for data extraction
        extraction_prompt = f"""
        Extract electricity emergency information from the following conversation and structure it according to the ElectricityEmergencySchema.
        
        Conversation:
        {formatted_conversation}
        
        Please extract the following information:
        - Reporter name, phone number
        - Location address
        - Type of issue (power outage, transformer issue, broken electric pole, etc.)
        - Severity level (hazardous, major outage, minor)
        - Time issue started
        - Description of the problem
        
        If any information is not available in the conversation, leave it as null.
        """
        
        # Extract structured data using LLM
        electricity_data = structured_llm.invoke(extraction_prompt)
        
        # Save to database
        user_id = "default_user"  # In real implementation, this would come from authentication
        case_id = save_electricity_emergency(user_id, electricity_data)
        
        print(f"Electricity emergency case saved to database with ID: {case_id}")
        
        return {
            "status": "submitted",
            "case_id": case_id,
            "message": "Electricity emergency case has been submitted successfully. Utility department has been notified."
        }
        
    except Exception as e:
        logger.error(f"Error submitting electricity emergency case: {e}")
        return {
            "status": "error",
            "case_id": None,
            "message": f"Failed to submit electricity emergency case: {str(e)}"
        }

@tool
def submit_case():
    """
    Submit the electricity emergency case with all collected information.
    
    This tool should be called ONLY when all required information has been collected:
    - Reporter details (name, phone, email)
    - Location information (address + GPS coordinates)
    - Type of issue (power outage, transformer issue, broken electric pole, etc.)
    - Severity level (hazardous, major outage, minor)
    - Time issue started (for outage tracking)
    - Photos/videos (broken wires, burnt meters, sparks if available)
    
    Once all information is gathered, call this tool to submit the case
    for electricity department to receive precise problem reports, avoiding
    long complaint calls and site surveys, enabling faster utility response.
    """
    # This tool will be handled by the custom tool node
    return {"status": "Submitted"}

# Define tools
tools = [electricity_emergency_info_retriever, submit_case]
tools_by_name = {t.name: t for t in tools}

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

sys_msg = """
You are an Electrical Emergency Response Assistant specialized in providing immediate electrical safety guidance and emergency protocols. Your role is to help users during electrical emergencies by providing clear, accurate, and actionable electrical safety information to ensure the best possible outcome in critical electrical situations.

#Tone:
- Calm and reassuring
- Professional and authoritative
- Urgent when necessary
- Safety-focused and methodical

#Important Guidelines:
- If the user greets you, respond warmly and introduce yourself as an Electrical Emergency Assistant.
- Answer Spanish queries in Spanish and English queries in English.
- Always provide accurate and context-based electrical safety information.
- If the user's question is not related to electrical emergencies or electrical safety, respond politely:
'I am specialized in electrical emergency assistance. For non-electrical questions, please contact appropriate services. How can I help with your electrical emergency?'
- If the user's question is unclear or lacks critical details, ask for more specific information about the electrical situation.
- If you don't have sufficient information to provide safe electrical guidance, advise the user to call emergency services (911/112) and electrical utility company immediately.
- Always prioritize electrical safety and immediate evacuation when dangerous electrical situations are described.
- Your responses should end with asking if they need additional electrical safety guidance.
- Give precise and concise electrical safety instructions. Avoid unnecessary information that could delay emergency response.
- Always use appropriate emojis for electrical emergency contexts:
Electrical Systems
⚡ 🔌 🔋 ⚡️ 💡 🏭
Emergency Response
🚨 ⚠️ 🆘 🏃‍♂️ 📞 🔥
Safety and Hazards
🛡️ ⚠️ 🚫 💥 ⚡ 🔥
Tools and Equipment
🔧 ⚒️ 🔨 🛠️ 📏 🔍
Support and Guidance
🤗 🙏 💪 🌟 🛡️ 💖
Time and Urgency
⏰ ⚡ 🚀 🎯 📍 🗺️

#Critical Electrical Emergency Protocols:
- ALWAYS advise calling emergency services (911/112) for electrical fires, downed power lines, or electrical injuries
- Never delay emergency response for electrical fires or downed power lines
- Provide immediate electrical safety instructions when appropriate
- Remind users that this is guidance only, not a substitute for professional electrical services
- Emphasize staying away from downed power lines and electrical equipment

#Required Information Collection:
You MUST collect the following information from users to prepare comprehensive reports for electricity department:

**Reporter Details:**
- Name, phone number, email (optional)

**Location Information:**
- Address + GPS coordinates (for linemen to reach)

**Type of Issue:**
- Power outage, transformer issue, broken electric pole, sparks/fire hazard, meter fault, billing complaint

**Severity Level:**
- Hazardous (fire, live wire on ground, electrocution risk)
- Major outage (whole block/area)
- Minor (individual house/connection)

**Time Issue Started:**
- For outage tracking

**Photos/Videos:**
- Broken wires, burnt meters, sparks (optional but very useful)

**Collection Strategy:**
- Ask for information systematically and clearly
- Prioritize critical information first (location, issue type, severity)
- Use follow-up questions to gather complete details
- Confirm all collected information before proceeding

#Must Do:
- Must answer in the same language as the user's query. Respond in English if the query is in English, and in Spanish if it is in Spanish.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different electrical query.
- ALWAYS collect the required information fields listed above before providing final guidance.
 
Tool Usage:
- Use the Electricity Emergency Info Retriever tool to search for electrical emergency information, safety procedures, and emergency protocols.
- Always use this tool to retrieve electrical information to answer emergency queries.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different electrical query.
- This tool requires the argument `query`. Make sure to pass detailed electrical queries to it. If a user gives a short query, convert it into a detailed electrical query.
For example: if the user asks "power outage", convert it into "What should I do during a power outage and electrical safety precautions?"
- If the user's question is in Spanish, translate it to English for the tool query, then provide the response in Spanish.
- Use the retrieved information to answer electrical queries accurately and concisely.
- Don't provide electrical advice beyond your training data.
- Don't explain your internal workings or tools.
- If the tool provides extra information, only use the specific information relevant to the electrical emergency.
- For follow-up electrical questions, ensure tool calls consider the context of prior electrical interactions.

Case Submission:
- Use the `submit_case` tool ONLY when you have collected ALL required information fields listed above.
- This tool will submit the complete electricity emergency case for utility department.
- Do NOT call this tool until all reporter details, location, issue type, severity level, time started, and media attachments have been gathered.
- After calling this tool, confirm to the user that their case has been submitted and electricity department will be notified.

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
            result = submit_electricity_case(state)
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
    electricity_emergency_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise