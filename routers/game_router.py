# routers/game_router.py
from fastapi import APIRouter, Query
from game.challenge_manager import ChallengeManager

game_router = APIRouter()
challenge_manager = ChallengeManager()

@game_router.get("/game/simulate")
async def simulate_ai_guess(media_url: str = Query(...)):
    result = await challenge_manager.get_ai_guess_for_media(media_url)
    return {
        "media_url": result["media_url"],
        "ai_guess": result["ai_guess"],
        "ai_confidence": result["ai_confidence"],
        "difficulty": result["difficulty"],
        "ai_reasoning": result["ai_reasoning"],
    }

@game_router.get("/game/difficulty")
async def get_current_difficulty():
    return {
        "confidence_threshold": challenge_manager.get_current_difficulty()
    }
