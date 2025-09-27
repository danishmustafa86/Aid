from configurations.db import chat_collection
from datetime import datetime, timezone
from langchain.schema import AIMessage
from agents.triage_agent import graph


def load_history(user_id: str):
    """Load user history from MongoDB."""
    try:
        prefixed_user_id = f"triage_{user_id}"
        record = chat_collection.find_one({"user_id": prefixed_user_id})
        if record and "history" in record:
            return record["history"]
        return []
    except Exception as e:
        raise Exception(f"Error loading triage chat history: {e}")

def save_history(user_id: str, user_message: str, bot_response: dict):
    """Save user history to MongoDB."""
    try:
        prefixed_user_id = f"triage_{user_id}"
        messages = load_history(user_id)
        created_at_time = datetime.now(timezone.utc)
        messages.append({"role": "user", "content": user_message, "created_at": created_at_time})
        # For triage, bot_response is a dict with response and section
        bot_content = bot_response.get("response", "")
        messages.append({"role": "bot", "content": bot_content, "created_at": created_at_time})
        chat_collection.update_one({"user_id": prefixed_user_id}, {"$set": {"history": messages}}, upsert=True)
    except Exception as e:
        raise Exception(f"Error saving triage chat history: {e}")

async def respond(user_id: str, user_message: str):
    try:
        config = {"configurable": {"thread_id": f"triage_{user_id}"}}
        combined_response = ""
        last_section = None
        for step in graph.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="values",
            config=config,
            ):
            # Capture the latest emergency_type if present in state
            if isinstance(step, dict) and "emergency_type" in step and step["emergency_type"]:
                last_section = step["emergency_type"]
            if "messages" in step and step["messages"]:
                last_message = step["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, "content"):
                    combined_response += last_message.content + "\n"
        return {"response": combined_response.strip(), "emergency_type": last_section}
    except Exception as e:
        raise Exception(f"Error generating triage response: {e}")
