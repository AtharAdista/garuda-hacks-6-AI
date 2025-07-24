from fastapi import APIRouter
from models.cultural_item import ChatRequest, CulturalItem
from services.chatbot_service import get_chat_response

chatbot_router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@chatbot_router.post("/ask")
def chat_with_gemini(request: ChatRequest):
    return {
        "response": get_chat_response(
            item=request.cultural_item,
            user_message=request.user_message,
            history=request.chat_history
        )
    }