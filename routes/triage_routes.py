from fastapi import BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from models.chat_model import ChatRequest, DeleteChatRequest
from configurations.db import chat_collection, checkpoint_writes_collection, checkpoints_collection, deleted_chat_collection
from utils.triage_utils import respond, save_history

triage_router = APIRouter()

@triage_router.post("/api/triage/chat")
async def triage_chat_endpoint(chat_request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        user_id = chat_request.user_id
        user_message = chat_request.message
        bot_response = await respond(user_id, user_message)
        background_tasks.add_task(save_history, user_id, user_message, bot_response)
        return JSONResponse(status_code=200, content=bot_response)
    except Exception as e:
        print("Error while working on triage chat request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})

@triage_router.get("/api/triage/chatHistory/{user_id}")
async def get_triage_chat_history(user_id: str):
    try:
        record = chat_collection.find_one({"user_id": f"triage_{user_id}"})
        if not record or "history" not in record:
            return JSONResponse(status_code=200, content={"history": []})
        history=[
            {"role": msg["role"], "content": msg["content"]} for msg in record["history"]
        ]
        history.reverse()
        return JSONResponse(status_code=200, content={"history": history})
    except Exception as e:
        print("Error while working on triage chatHistory request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})

@triage_router.delete("/api/triage/chat")
async def delete_and_archive_triage_chat(delete_request: DeleteChatRequest):
    try:
        user_id = delete_request.user_id
        prefixed_user_id = f"triage_{user_id}"
        record = chat_collection.find_one({"user_id": prefixed_user_id})

        if not record or "history" not in record:
            return JSONResponse(status_code=404, content={"message": "User chat history not found"})

        if not record["history"]:
            return JSONResponse(status_code=200, content={"message": "Chat history is already reset"})

        try:
            checkpoint_writes_collection.delete_many({ "thread_id": prefixed_user_id })
            checkpoints_collection.delete_many({ "thread_id": prefixed_user_id })
        except Exception as e:
            print("error while deleting=",e)
        record["deleted_at"] = datetime.now(timezone.utc)
        record.pop("_id", None)
        deleted_chat_collection.insert_one(record)
        chat_collection.update_one({"user_id": prefixed_user_id}, {"$set": {"history": []}})

        return JSONResponse(status_code=200, content={"message": "Chat history reset successfully."})
    except Exception as e:
        print("Error while working on triage chat delete request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})
