import os
from models.cultural_item import CulturalItem, ChatTurn
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

def build_prompt(item: Optional[CulturalItem] = None, user_message: Optional[str] = None, history: Optional[List[ChatTurn]] = None) -> str:
    if user_message is None:
        if item is None:
            return (
                "You are a friendly and approachable cultural chatbot.\n"
                "The user has just opened the homepage and has not selected any specific cultural item yet.\n"
                "Your task is to greet the user in a short, warm, and casual way, and encourage them to ask something.\n\n"
                "CRITICAL CONSTRAINTS:\n"
                "- Maximum 2 sentences only\n"
                "- No explanations, no examples, no elaboration\n"
                "- Do NOT use Markdown formatting (*, **) or code blocks\n"
                "- Be conversational but BRIEF\n\n"
                "Example format:\n"
                "Hi there! 👋 Ask me anything about Indonesian culture! 😊"
            )
        else:
            return (
                f"You are a friendly cultural chatbot.\n"
                f"The user just opened this cultural page:\n"
                f"Title: {item.title}\n"
                f"Type: {item.type}\n"
                f"Province: {item.province}\n"
                f"Description: {item.description}\n\n"
                f"CRITICAL CONSTRAINTS:\n"
                f"- Maximum 2 sentences only\n"
                f"- Just greet and invite questions about this specific item\n"
                f"- No background info, no details, no explanations\n"
                f"- No bullet points, no Markdown formatting\n"
            )

    if item is None:
        base_context = (
            "You are a cultural chatbot assistant helping users understand Indonesian culture.\n"
            "The user has not selected any specific cultural item yet.\n\n"
        )
    else:
        base_context = (
            f"You are a cultural chatbot assistant helping users understand Indonesian culture.\n"
            f"The user is currently viewing:\n"
            f"Title: {item.title}\n"
            f"Type: {item.type}\n"
            f"Province: {item.province}\n"
            f"Description: {item.description}\n\n"
        )

    # Add strong anti-yapping constraints
    base_context += (
        "RESPONSE RULES (MANDATORY):\n"
        "- Keep responses under 3 sentences maximum\n"
        "- Answer directly without long introductions\n"
        "- No repetitive explanations or unnecessary details\n"
        "- If asked a simple question, give a simple answer\n"
        "- No bullet points or lists unless specifically requested\n"
        "- No Markdown formatting\n"
        "- Be helpful but concise\n\n"
    )

    summary_text, recent_turns = compact_chat_history(history)

    if summary_text:
        base_context += summary_text + "\n"

    if recent_turns:
        base_context += "Recent conversation:\n"
        for turn in recent_turns:
            speaker = "User" if turn.role == "user" else "Bot"
            base_context += f"{speaker}: {turn.message}\n"

    base_context += f"\nUser: {user_message}\n"
    base_context += "Bot (respond in 1-3 sentences max):"
    return base_context


def get_chat_response(item: Optional[CulturalItem] = None, user_message: Optional[str] = None, history: Optional[List[ChatTurn]] = None) -> str:
    prompt = build_prompt(item, user_message, history)
    response = model.generate_content(prompt)
    
    # Additional safeguard: truncate if response is too long
    response_text = response.text.strip()
    sentences = response_text.split('. ')
    if len(sentences) > 3:
        response_text = '. '.join(sentences[:3]) + '.'
    
    return response_text

def compact_chat_history(history: List[ChatTurn], max_turns: int = 4) -> tuple[str, List[ChatTurn]]:
    """
    Returns (summary_string, recent_turns)
    - Reduced max_turns from 6 to 4 to keep context shorter
    - Summarizes old turns if len(history) > max_turns
    - Keeps last few turns for verbatim context
    """
    if len(history) <= max_turns:
        return "", history

    summary_turns = history[:-max_turns]
    recent_turns = history[-max_turns:]

    # Make summary more concise
    summary = "Earlier: "
    summary_points = []
    for turn in summary_turns[-3:]:  # Only summarize last 3 old turns
        if turn.role == "user":
            summary_points.append(f"User asked about {turn.message[:30]}...")
    
    summary += " | ".join(summary_points) + "\n"
    return summary, recent_turns