from pydantic import BaseModel
from typing import Optional
from typing import List, Literal

class CulturalItem(BaseModel):
    id: str
    title: str
    type: str
    province: str
    description: str
    image: str

class ChatTurn(BaseModel):
    role: Literal["user", "bot"]
    message: str

class ChatRequest(BaseModel):
    cultural_item: Optional[CulturalItem] = None
    user_message: str
    chat_history: List[ChatTurn] = []
