from fastapi import APIRouter, Form
from services.cultural_media_location_service import CulturalMediaLocationService
from services.challenge_service import ChallengeService

competitor_router =  APIRouter(prefix="/game", tags=["Game"])

media_service = CulturalMediaLocationService()
challenge_service = ChallengeService()

@competitor_router.post("/guess")
async def guess_province(
    input_url: str = Form(...),
    user_guess: str = Form(...),
    actual_province: str = Form(...)
):
    # AI Prediction with difficulty
    ai_result = await media_service.predict_province_from_input(
        media_url=input_url,
        difficulty=challenge_service.map_threshold_to_difficulty(),
        use_chain_of_thought=True
    )

    # Evaluation
    user_correct = user_guess.lower() == actual_province.lower()
    ai_correct = ai_result.province_guess.lower() == actual_province.lower()

    # Update difficulty
    challenge_service.update_difficulty(ai_correct)

    return {
        "actual_province": actual_province,
        "user_guess": user_guess,
        "ai_guess": ai_result.province_guess,
        "ai_confidence": ai_result.confidence,
        "user_correct": user_correct,
        "ai_correct": ai_correct,
        "current_difficulty": challenge_service.get_current_difficulty(),
        "ai_reasoning": ai_result.reasoning,
        "error": ai_result.error
    }