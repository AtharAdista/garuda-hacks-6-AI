import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def analyze_match_performance(rounds_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rounds_data:
        return {
            "feedback": "No data available to analyze performance."
        }
    
    feedback = generate_all_rounds_feedback(rounds_data)
    
    return {
        "feedback": feedback
    }

def generate_all_rounds_feedback(rounds_data: List[Dict[str, Any]]) -> str:
    total_rounds = len(rounds_data)
    correct_count = sum(1 for round in rounds_data if round.get("playerCorrect", False))
    
    context = f"Complete Game Analysis ({total_rounds} rounds, {correct_count} correct):\n\n"
    
    for i, round in enumerate(rounds_data, 1):
        result = "✓ CORRECT" if round.get("playerCorrect", False) else "✗ WRONG"
        province = round.get("correctAnswer", "Unknown")
        player_guess = round.get("playerAnswer", "No answer")
        category = round["culturalData"].get("cultural_category", "culture") if round.get("culturalData") else "culture"
        cultural_context = round["culturalData"].get("cultural_context", "") if round.get("culturalData") else ""
        
        context += f"Round {i}: {result}\n"
        context += f"  Province: {province}\n"
        context += f"  Category: {category}\n"
        context += f"  Your guess: {player_guess}\n"
        if cultural_context:
            context += f"  Context: {cultural_context[:80]}...\n"
        context += "\n"
    
    prompt = f"""
    You are an Indonesian culture expert providing comprehensive feedback on a complete game session.

    {context}

    Provide feedback that:
    1. Acknowledges their overall performance across ALL rounds
    2. Identifies patterns in their correct/incorrect answers (which categories they're strong/weak in)
    3. Includes 2-3 fascinating cultural fun facts about provinces they got wrong
    4. Gives specific advice for improvement based on the categories they struggled with
    5. Ends with encouragement

    Keep it educational, engaging, and focused on Indonesian cultural learning. Maximum 5-6 sentences.
    Make the fun facts memorable and tied to the specific provinces/categories they missed.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        accuracy = (correct_count / total_rounds) * 100 if total_rounds > 0 else 0
        if accuracy >= 70:
            return f"Great performance across all {total_rounds} rounds! You correctly identified {correct_count} provinces, showing strong knowledge of Indonesian culture. Keep exploring to learn even more about Indonesia's diverse heritage!"
        elif accuracy >= 50:
            return f"Solid effort across {total_rounds} rounds with {correct_count} correct answers! Indonesian culture spans 33 provinces, each with unique traditions. Focus on studying the cultural categories you missed to improve your recognition skills."
        else:
            return f"Thanks for playing all {total_rounds} rounds! Indonesian culture is wonderfully complex with diverse traditions across 33 provinces. Study traditional dances, regional foods, and local arts to build your cultural knowledge. Keep exploring!"