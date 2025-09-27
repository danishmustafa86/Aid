
import logging
from langchain_community.document_loaders import TextLoader
from dotenv import load_dotenv
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.tools import tool
from configurations.config import config
from configurations.db import mongodb_client

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
    pass

# Define tools
tools = [police_emergency_info_retriever, submit_case]

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
- If you don't have sufficient information to provide safe law enforcement guidance, advise the user to call emergency services (911/112) and local police immediately.
- Always prioritize immediate law enforcement response when criminal activities or dangerous situations are described.
- Your responses should end with asking if they need additional law enforcement guidance.
- Give precise and concise law enforcement instructions. Avoid unnecessary information that could delay emergency response.
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
- ALWAYS advise calling emergency services (911/112) for crimes in progress, suspicious activities, or immediate threats
- Never delay emergency law enforcement response for information gathering
- Provide immediate safety instructions when appropriate
- Remind users that this is guidance only, not a substitute for professional law enforcement
- Emphasize personal safety and avoiding confrontation with criminals

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
- This tool will submit the complete police emergency case for law enforcement officers.
- Do NOT call this tool until all reporter details, incident location, incident type, time, description, suspect details, victim details, and urgency level have been gathered.
- After calling this tool, confirm to the user that their case has been submitted and police will be notified.

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

# Build graph
try:
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(generate)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_edge(START, "generate")
    graph_builder.add_conditional_edges("generate", tools_condition)
    graph_builder.add_edge("tools", "generate")

    memory = MongoDBSaver(mongodb_client)
    police_emergency_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise