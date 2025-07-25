from fastapi import APIRouter, Body
from services.cultural_media_location_service import CulturalMediaLocationService
from services.challenge_service import ChallengeService
from models.guess_request import GuessRequest

competitor_router =  APIRouter(prefix="/game", tags=["Game"])

media_service = CulturalMediaLocationService()
challenge_service = ChallengeService()

@competitor_router.post("/guess")
async def guess_province(request: GuessRequest = Body(...)):
    input_url = request.input_url
    actual_province = request.actual_province

    # AI Prediction with difficulty
    ai_result = await media_service.predict_province_from_input(
        media_url=input_url,
        difficulty=challenge_service.map_threshold_to_difficulty(),
        use_chain_of_thought=True
    )

    # Evaluation
    ai_correct = ai_result.province_guess.lower() == actual_province.lower()

    # Update difficulty
    challenge_service.update_difficulty(ai_correct)

    return {
        "actual_province": actual_province,
        "ai_guess": ai_result.province_guess,
        "ai_confidence": ai_result.confidence,
        "ai_correct": ai_correct,
        "current_difficulty": challenge_service.get_current_difficulty(),
        "ai_reasoning": ai_result.reasoning,
        "error": ai_result.error
    }