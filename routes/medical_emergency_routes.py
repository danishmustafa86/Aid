from fastapi import BackgroundTasks, APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import tempfile
import os
import asyncio
from models.chat_model import ChatRequest, VoiceChatRequest, DeleteChatRequest
from configurations.db import chat_collection, checkpoint_writes_collection, checkpoints_collection, deleted_chat_collection
from utils.medical_emergency_utils import respond, save_history
from utils.voice_utils import speech_to_text, text_to_speech

medical_emergency_router = APIRouter()

async def cleanup_audio_file(audio_path: str, delay_seconds: int = 300):
    """
    Clean up audio file after specified delay (default 5 minutes).
    This prevents disk space issues from accumulated audio files.
    """
    await asyncio.sleep(delay_seconds)
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up audio file: {audio_path}")
    except Exception as e:
        print(f"Error cleaning up audio file {audio_path}: {str(e)}")

@medical_emergency_router.post("/api/medical-emergency/chat")
async def medical_emergency_chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(""),
    input_type: str = Form("text"),
    audio: UploadFile = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
        user_message = message
        
        # Step 1: Handle input based on input_type
        if input_type == "voice" and audio is not None:
            temp_audio_path = f"temp_{user_id}.wav"
            with open(temp_audio_path, "wb") as f:
                f.write(await audio.read())
            user_message = speech_to_text(temp_audio_path)
            os.remove(temp_audio_path)
            print(f"Voice converted to text: {user_message}")
        elif input_type == "text" and message:
            user_message = message
        
        # Ensure we have a message to process
        if not user_message:
            return JSONResponse(status_code=400, content={"error": "No message provided"})
        
        bot_response = await respond(user_id, user_message)
        background_tasks.add_task(save_history, user_id, user_message, bot_response)
        
        # Generate audio response if input was voice
        audio_response_path = None
        if input_type == "voice":
            try:
                audio_response_path = f"audio_files/response_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                text_to_speech(bot_response, save_path=audio_response_path)
                print(f"Audio response generated: {audio_response_path}")
                # Schedule cleanup of audio file after 5 minutes
                background_tasks.add_task(cleanup_audio_file, audio_response_path, 300)
            except Exception as audio_error:
                print(f"Error generating audio response: {str(audio_error)}")
                # Continue without audio if generation fails
        
        response_data = {"response": bot_response}
        if audio_response_path:
            response_data["audio_response_path"] = f"/audio/{os.path.basename(audio_response_path)}"
            
        return JSONResponse(status_code=200, content=response_data)
    except Exception as e:
        print("Error while working on medical emergency chat request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})

@medical_emergency_router.get("/api/medical-emergency/chatHistory/{user_id}")
async def get_medical_emergency_chat_history(user_id: str):
    try:
        record = chat_collection.find_one({"user_id": f"medical_emergency_{user_id}"})
        if not record or "history" not in record:
            return JSONResponse(status_code=200, content={"history": []})
        history=[
            {"role": msg["role"], "content": msg["content"]} for msg in record["history"]
        ]
        history.reverse()
        return JSONResponse(status_code=200, content={"history": history})
    except Exception as e:
        print("Error while working on medical emergency chatHistory request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})

@medical_emergency_router.delete("/api/medical-emergency/chat")
async def delete_and_archive_medical_emergency_chat(delete_request: DeleteChatRequest):
    try:
        user_id = delete_request.user_id
        prefixed_user_id = f"medical_emergency_{user_id}"
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
        print("Error while working on medical emergency chat delete request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})
