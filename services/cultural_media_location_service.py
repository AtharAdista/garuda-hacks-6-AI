import logging
import json
import os
import re

from typing import Tuple

from dotenv import load_dotenv
from google import generativeai as genai
from google.ai.generativelanguage_v1beta.types import Content, Part, FileData

from services.gemini.base_service import BaseLangChainService
from services.gemini.exceptions import GeminiServiceException
from models.location_guess import LocationGuessResult
from utils.image_utils import read_url_as_base64

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

logger = logging.getLogger(__name__)


class CulturalMediaLocationService(BaseLangChainService):
    def __init__(self):
        super().__init__()
        self.model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

    async def predict_province_from_input(self, media_url: str, difficulty: str = "easy", use_chain_of_thought: bool = False) -> LocationGuessResult:
        try:
            if self._is_video_or_youtube(media_url):
                return await self._predict_from_video_url(media_url, difficulty, use_chain_of_thought)
            else:
                image_base64 = read_url_as_base64(media_url)
                return await self.predict_province_from_base64(image_base64, difficulty, use_chain_of_thought)
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error=str(e)
            )

    def _is_video_or_youtube(self, url: str) -> bool:
        return any(x in url.lower() for x in ["youtube.com", "youtu.be", ".mp4", ".mov", ".webm"])

    async def _predict_from_video_url(self, url: str, difficulty: str, use_chain_of_thought: bool) -> LocationGuessResult:
        prompt = self._build_cultural_origin_prompt(difficulty, use_chain_of_thought)

        try:
            response = self.model.generate_content(
                contents=Content(parts=[
                    Part(file_data=FileData(file_uri=url)),
                    Part(text=prompt)
                ])
            )

            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"Error in video prediction: {e}")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error=str(e)
            )


    async def predict_province_from_base64(self, image_base64: str, difficulty: str, use_chain_of_thought: bool) -> LocationGuessResult:
        """Use Gemini Vision to predict from which Indonesian province the cultural media originated."""
        if not image_base64:
            logger.error("No image provided.")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error="No image provided"
            )

        try:
            prompt = self._build_cultural_origin_prompt(difficulty, use_chain_of_thought)

            response_text = await self._invoke_multimodal_model(prompt, image_base64)
            return self._parse_response(response_text)

        except GeminiServiceException:
            raise
        except Exception as e:
            logger.error(f"Error during province prediction: {e}")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error=str(e)
            )


    def _parse_response(self, response_text: str) -> LocationGuessResult:
        try:
            cleaned = response_text.strip()

            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            logger.debug(f"Cleaned Gemini response:\n{cleaned}")

            data = json.loads(cleaned)

            return LocationGuessResult(
                province_guess=data.get("province", "Unknown"),
                confidence=float(data.get("confidence", 0.0)),
                error=None,
                reasoning=data.get("reasoning")
            )
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return LocationGuessResult(
                province_guess="Unknown",
                confidence=0.0,
                error=str(e)
            )

    def _build_cultural_origin_prompt(self, difficulty: str = "easy", use_chain_of_thought: bool = False) -> str:
        base_instruction = "Kamu adalah pakar budaya Indonesia."

        # Optional chain of thought reasoning per difficulty level
        if use_chain_of_thought:
            if difficulty == "easy":
                reasoning = "Langsung tebak berdasarkan visual yang terlihat."
            elif difficulty == "medium":
                reasoning = "Jelaskan ciri-ciri visual terlebih dahulu seperti pakaian, bentuk bangunan, atau alat musik sebelum menebak."
            elif difficulty == "hard":
                reasoning = (
                    "Analisis mendalam ciri-ciri visual budaya pada media ini. Bandingkan dengan budaya dari beberapa provinsi lain terlebih dahulu sebelum membuat kesimpulan."
                )
            else:
                reasoning = "Langsung berikan tebakan."
        else:
            reasoning = ""

        output_format = """
        Berikan hasil sebagai objek JSON TANPA markdown code block, TANPA penjelasan tambahan, dan TANPA tanda ```json.

        Jawab hanya dengan seperti ini:
        {
        "province": "Jawa Barat",
        "confidence": 0.85,
        "reasoning": "Berdasarkan pakaian tradisional yang terlihat, ini kemungkinan berasal dari Jawa Barat."
        }

        Jawab hanya dengan format JSON, tanpa penjelasan lain. 
        Confidence harus bernilai antara 0.0 - 1.0 sesuai tingkat keyakinanmu."""

        return f"{base_instruction}\n\n{reasoning}\n\n{output_format}"
