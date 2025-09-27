from configurations.config import config
from pymongo import MongoClient


try:
    mongodb_client = MongoClient(config.MONGODB_URI)
    chat_db = mongodb_client["chat_database"]
    chat_collection = chat_db["chat_history"]
    deleted_chat_collection = chat_db["deleted_chat_history"]
    checkpointing_db = mongodb_client["checkpointing_db"]
    checkpoint_writes_collection = checkpointing_db["checkpoint_writes"]
    checkpoints_collection = checkpointing_db["checkpoints"]
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise Exception(f"Error connecting to MongoDB: {e}")