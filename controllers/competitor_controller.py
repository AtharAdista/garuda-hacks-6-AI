from services.cultural_media_location_service import CulturalMediaLocationService

media_service = CulturalMediaLocationService()

async def handle_guess(media_url: str, user_guess: str, actual_province: str):
    ai_result = await media_service.predict_province_from_input(media_url)
    return {
        "actual_province": actual_province,
        "user_guess": user_guess,
        "ai_guess": ai_result.province_guess,
        "ai_confidence": ai_result.confidence,
        "user_correct": user_guess.lower() == actual_province.lower(),
        "ai_correct": ai_result.province_guess.lower() == actual_province.lower(),
        "error": ai_result.error
    }