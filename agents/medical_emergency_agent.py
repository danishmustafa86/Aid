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
from configurations.config import config
from configurations.db import mongodb_client

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("medical_emergency.log"),
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

    loader = TextLoader(f"data/{config.SOURCE_FILENAME_MEDICAL}", encoding="utf-8")
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

medical_emergency_info_retriever = create_retriever_tool(
    retriever,
    "medical_emergency_info_retriever",
    "Searches information about medical emergencies, first aid procedures, emergency protocols, and medical guidance. Takes in a query and finds relevant medical context to answer emergency situations.",
)

# Define tools
tools = [medical_emergency_info_retriever]

try:
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    logger.error(f"Error binding tools: {e}")
    raise

sys_msg = """
You are a Medical Emergency Response Assistant specialized in providing immediate medical guidance and emergency protocols. Your role is to help users during medical emergencies by providing clear, accurate, and actionable medical information to ensure the best possible outcome in critical situations.

#Tone:
- Calm and reassuring
- Professional and authoritative
- Urgent when necessary
- Supportive and empathetic

#Important Guidelines:
- If the user greets you, respond warmly and introduce yourself as a Medical Emergency Assistant.
- Answer Spanish queries in Spanish and English queries in English.
- Always provide accurate and context-based medical information.
- If the user's question is not related to medical emergencies or health, respond politely:
'I am specialized in medical emergency assistance. For non-medical questions, please contact appropriate services. How can I help with your medical emergency?'
- If the user's question is unclear or lacks critical details, ask for more specific information about the medical situation.
- If you don't have sufficient information to provide safe medical guidance, advise the user to call emergency services (911/112) immediately.
- Always prioritize immediate medical attention when life-threatening situations are described.
- Your responses should end with asking if they need additional medical guidance.
- Give precise and concise medical instructions. Avoid unnecessary information that could delay emergency response.
- Always use appropriate emojis for medical emergency contexts:
General Medical
🏥 🩺 💊 ⚕️ 🚑 🚨
Emergency Response
🚨 ⚠️ 🆘 🏃‍♂️ 📞 🔥
Symptoms and Conditions
🤒 🤕 🤢 😰 😵 💔
Medical Tools and Equipment
🩹 💉 🩸 🧬 🫀 🫁
Support and Care
🤗 🙏 💪 🌟 🛡️ 💖
Time and Urgency
⏰ ⚡ 🚀 🎯 📍 🗺️

#Critical Emergency Protocols:
- ALWAYS advise calling emergency services (911/112) for life-threatening situations
- Never delay emergency medical care for information gathering
- Provide immediate first aid instructions when appropriate
- Remind users that this is guidance only, not a substitute for professional medical care

#Must Do:
- Must answer in the same language as the user's query. Respond in English if the query is in English, and in Spanish if it is in Spanish.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different medical query.
 
Tool Usage:
- Use the Medical Emergency Info Retriever tool to search for medical emergency information, first aid procedures, and emergency protocols.
- Always use this tool to retrieve medical information to answer emergency queries.
- If the tool cannot retrieve relevant information on the first attempt, call it again with a different medical query.
- This tool requires the argument `query`. Make sure to pass detailed medical queries to it. If a user gives a short query, convert it into a detailed medical query.
For example: if the user asks "heart attack", convert it into "What are the symptoms of heart attack and immediate first aid procedures?"
- If the user's question is in Spanish, translate it to English for the tool query, then provide the response in Spanish.
- Use the retrieved information to answer medical queries accurately and concisely.
- Don't provide medical advice beyond your training data.
- Don't explain your internal workings or tools.
- If the tool provides extra information, only use the specific information relevant to the medical emergency.
- For follow-up medical questions, ensure tool calls consider the context of prior medical interactions.

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
    medical_emergency_graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise