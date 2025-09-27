from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    message: str

class DeleteChatRequest(BaseModel):
    user_id: str