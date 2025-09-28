from configurations.db import chat_collection
from datetime import datetime, timezone
from langchain.schema import AIMessage


def load_history(user_id: str):
    """Load user history from MongoDB."""
    try:
        prefixed_user_id = f"fire_emergency_{user_id}"
        record = chat_collection.find_one({"user_id": prefixed_user_id})
        if record and "history" in record:
            return record["history"]
        return []
    except Exception as e:
        raise Exception(f"Error loading fire emergency chat history: {e}")

def save_history(user_id: str, user_message: str, bot_messages: str):
    """Save user history to MongoDB."""
    try:
        prefixed_user_id = f"fire_emergency_{user_id}"
        messages = load_history(user_id)
        created_at_time = datetime.now(timezone.utc)
        messages.append({"role": "user", "content": user_message, "created_at": created_at_time})
        messages.append({"role": "bot", "content": bot_messages, "created_at": created_at_time})
        chat_collection.update_one({"user_id": prefixed_user_id}, {"$set": {"history": messages}}, upsert=True)
    except Exception as e:
        raise Exception(f"Error saving fire emergency chat history: {e}")

async def respond(user_id: str, user_message: str):
    try:
        print(f"Fire emergency respond called - user_id: {user_id}, message: {user_message}")
        
        # Import the fire emergency graph
        from agents.fire_emergency_agent import fire_emergency_graph
        
        config = {"configurable": {"thread_id": f"fire_emergency_{user_id}"}}
        combined_response = ""
        
        print(f"Starting fire emergency graph stream for user: {user_id}")
        for step in fire_emergency_graph.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="values",
            config=config,
            ):
            print(f"Fire emergency step: {step}")
    
            if "messages" in step and step["messages"]:
                last_message = step["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, "content"):
                    combined_response += last_message.content + "\n"
        
        result = combined_response.strip()
        print(f"Fire emergency response result: {result}")
        return result
    except Exception as e:
        print(f"Error in fire emergency respond: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Error generating fire emergency response: {e}")