"""
Profile API Routes - Chat para configuração de perfil
"""
from fastapi import APIRouter, HTTPException
import logging

from .schemas import ChatMessageRequest, ChatMessageResponse
from modules.profile.chat_agent import ProfileChatAgent
from modules.resume.llm_adapter import create_llm_for_resume
from database.mongodb import get_mongodb
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Global instances
chat_agent = None
db = None


def init_profile_system():
    """Initialize profile chat system"""
    global chat_agent, db
    
    llm_router = create_llm_for_resume()
    db = get_mongodb()
    
    chat_agent = ProfileChatAgent(llm_router, db)
    
    logger.info("✅ Profile chat system initialized")


@router.post("/chat/start", response_model=ChatMessageResponse)
async def start_chat(user_id: str):
    """Inicia uma nova conversa de configuração de perfil"""
    try:
        if chat_agent is None:
            raise HTTPException(status_code=503, detail="Chat agent not initialized")
        
        result = chat_agent.start_conversation(user_id)
        
        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message=result["message"],
            state=result["state"],
            progress=result["progress"]
        )
    
    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """Envia mensagem e recebe resposta da IA"""
    try:
        if chat_agent is None:
            raise HTTPException(status_code=503, detail="Chat agent not initialized")
        
        if not request.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id required")
        
        # Convert string ID to ObjectId
        conv_id = ObjectId(request.conversation_id)
        
        result = chat_agent.process_message(conv_id, request.message)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ChatMessageResponse(
            conversation_id=request.conversation_id,
            message=result["message"],
            state=result["state"],
            progress=result["progress"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{conversation_id}/history")
async def get_chat_history(conversation_id: str):
    """Retorna histórico de mensagens"""
    try:
        conv_id = ObjectId(conversation_id)
        conv = db.db.profile_conversations.find_one({"_id": conv_id})
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "messages": conv.get("messages", []),
            "state": conv.get("state"),
            "extracted_data": conv.get("extracted_data", {})
        }
    
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
