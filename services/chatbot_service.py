import os
from models.cultural_item import CulturalItem, ChatTurn
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

def build_prompt(item: CulturalItem, user_message: Optional[str] = None, history: Optional[List[ChatTurn]] = None) -> str:
    if user_message is None:
        return (
            f"You are a friendly cultural chatbot.\n"
            f"The user just opened this cultural page:\n"
            f"Title: {item.title}\n"
            f"Type: {item.type}\n"
            f"Province: {item.province}\n"
            f"Description: {item.description}\n\n"
            f"Greet the user warmly, and invite them to ask about this item."
        )

    base_context = (
        f"You are a cultural chatbot assistant helping users understand Indonesian culture.\n"
        f"The user is currently viewing:\n"
        f"Title: {item.title}\n"
        f"Type: {item.type}\n"
        f"Province: {item.province}\n"
        f"Description: {item.description}\n\n"
    )

    if history:
        base_context += "Here is the previous conversation:\n"
        for turn in history:
            speaker = "User" if turn.role == "user" else "Bot"
            base_context += f"{speaker}: {turn.message}\n"

    base_context += f"\nUser: {user_message}\nBot:"
    return base_context

def get_chat_response(item: CulturalItem, user_message: Optional[str] = None, history: Optional[List[ChatTurn]] = None) -> str:
    prompt = build_prompt(item, user_message, history)
    response = model.generate_content(prompt)
    return response.text.strip()