from services.cultural_media_location_service import CulturalMediaLocationService
from utils.image_utils import read_url_as_base64

media_service = CulturalMediaLocationService()

async def handle_guess(image_url: str, user_guess: str, actual_province: str):
    image_base64 = read_url_as_base64(image_url)
    ai_result = await media_service.predict_province_from_base64(image_base64)
    return {
        "actual_province": actual_province,
        "user_guess": user_guess,
        "ai_guess": ai_result.province_guess,
        "ai_confidence": ai_result.confidence,
        "user_correct": user_guess.lower() == actual_province.lower(),
        "ai_correct": ai_result.province_guess.lower() == actual_province.lower(),
        "error": ai_result.error
    }