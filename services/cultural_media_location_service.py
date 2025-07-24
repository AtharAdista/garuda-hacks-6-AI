import logging
from typing import Tuple
from services.gemini.base_service import BaseLangChainService
from models.location_guess import LocationGuessResult
from services.gemini.exceptions import GeminiServiceException
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


logger = logging.getLogger(__name__)

class CulturalMediaLocationService(BaseLangChainService):
    """Service to predict origin province of a cultural image using Gemini."""

    def __init__(self):
        super().__init__()

    async def predict_province_from_base64(self, image_base64: str) -> LocationGuessResult:
        """Use Gemini Vision to predict from which Indonesian province the cultural media originated."""
        if not image_base64:
            logger.error("No image provided.")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error="No image provided"
            )

        try:
            prompt = self._build_cultural_origin_prompt()

            response_text = await self._invoke_multimodal_model(prompt, image_base64)
            province, confidence = self._parse_text_response(response_text)

            return LocationGuessResult(
                province_guess=province,
                confidence=confidence
            )

        except GeminiServiceException:
            raise
        except Exception as e:
            logger.error(f"Error during province prediction: {e}")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error=str(e)
            )

    def _build_cultural_origin_prompt(self) -> str:
        return """
        Kamu adalah pakar budaya Indonesia.

        Berdasarkan gambar budaya berikut (bisa berupa pakaian adat, tarian tradisional, makanan, rumah adat, arsitektur, alat musik), tentukan dari provinsi mana gambar ini kemungkinan besar berasal.

        Berikan hasil sebagai objek JSON TANPA markdown code block, TANPA penjelasan tambahan, dan TANPA tanda ```json.

        Jawab hanya dengan seperti ini:
        {
        "province": "Jawa Barat",
        "confidence": 0.85
        }

        Jawab hanya dengan format JSON, tanpa penjelasan lain. 
        Confidence harus bernilai antara 0.0 - 1.0 sesuai tingkat keyakinanmu.
        """

    def _parse_text_response(self, response_text: str) -> Tuple[str, float]:
        try:
            # Clean up markdown ```json ... ``` if present
            response_text = response_text.strip()

            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.IGNORECASE)
                response_text = re.sub(r"\s*```$", "", response_text)

            logger.debug(f"Cleaned response for JSON parsing:\n{response_text}")

            data = json.loads(response_text)
            province = data.get("province", "Unknown")
            confidence = float(data.get("confidence", 0.0))
            return province, confidence
        except Exception as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            return "Unknown", 0.0

    def _estimate_confidence(self, guess: str) -> float:
        # Placeholder: maybe based on keyword certainty or later via model calibration
        return 0.85 if guess and guess != "Unknown" else 0.0
