"""
Profile API Schemas
"""
from pydantic import BaseModel
from typing import Optional


class ChatMessageRequest(BaseModel):
    """Request para enviar mensagem no chat"""
    user_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Response do chat"""
    conversation_id: str
    message: str
    state: str
    progress: int
