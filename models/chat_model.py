from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile

class ChatRequest(BaseModel):
    user_id: str
    message: str
    input_type: str = "text"  # "text" or "voice"
    voice_file_path: Optional[str] = None

class VoiceChatRequest(BaseModel):
    user_id: str
    message: str
    input_type: str = "text"  # "text" or "voice"

class DeleteChatRequest(BaseModel):
    user_id: str