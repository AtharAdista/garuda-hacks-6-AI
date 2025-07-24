from services.cultural_media_location_service import CulturalMediaLocationService
from models.location_guess import LocationGuessResult

class ChallengeService:
    def __init__(self, initial_threshold: float = 0.5):
        self.confidence_threshold = initial_threshold
        self.media_service = CulturalMediaLocationService()

    async def get_ai_guess_for_media(self, media_url: str) -> dict:
        """Let AI guess based on the given media URL and current difficulty level."""
        difficulty = self._map_threshold_to_difficulty()

        result: LocationGuessResult = await self.media_service.predict_province_from_input(
            media_url=media_url,
            difficulty=difficulty,
            use_chain_of_thought=True
        )

        return {
            "media_url": media_url,
            "ai_guess": result.province_guess,
            "ai_confidence": result.confidence,
            "difficulty": difficulty,
            "ai_reasoning": result.reasoning if hasattr(result, 'reasoning') else None
        }

    def update_difficulty(self, ai_correct: bool):
        if ai_correct:
            self.confidence_threshold = min(1.0, self.confidence_threshold + 0.05)

    def get_current_difficulty(self):
        return self.confidence_threshold

    def map_threshold_to_difficulty(self) -> str:
        if self.confidence_threshold < 0.7:
            return "easy"
        elif self.confidence_threshold < 0.85:
            return "medium"
        else:
            return "hard"