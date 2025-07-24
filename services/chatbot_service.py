import os
from models.cultural_item import CulturalItem, ChatTurn
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

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

    summary_text, recent_turns = compact_chat_history(history)

    if summary_text:
        base_context += summary_text + "\n"

    if recent_turns:
        base_context += "Here is the recent conversation:\n"
        for turn in recent_turns:
            speaker = "User" if turn.role == "user" else "Bot"
            base_context += f"{speaker}: {turn.message}\n"

    return base_context

def get_chat_response(item: CulturalItem, user_message: Optional[str] = None, history: Optional[List[ChatTurn]] = None) -> str:
    prompt = build_prompt(item, user_message, history)
    response = model.generate_content(prompt)
    return response.text.strip()

def compact_chat_history(history: List[ChatTurn], max_turns: int = 6) -> tuple[str, List[ChatTurn]]:
    """
    Returns (summary_string, recent_turns)
    - Summarizes old turns if len(history) > max_turns
    - Keeps last few turns for verbatim context
    """
    if len(history) <= max_turns:
        return "", history

    summary_turns = history[:-max_turns]
    recent_turns = history[-max_turns:]

    summary = "Conversation so far (summarized):\n"
    for turn in summary_turns:
        speaker = "User" if turn.role == "user" else "Bot"
        summary += f"{speaker} said something about {turn.message[:50]}...\n"

    return summary, recent_turns
