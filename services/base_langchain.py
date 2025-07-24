import os

from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

import logging

logger = logging.getLogger(__name__)

class BaseLangChainService:

    def __init__(
        self,
        model_name: str = "models/gemini-2.5-flash"
    ):
        self.model_name = model_name

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("Google API key not found in environment variables")

        logger.info(
            f"Initializing BaseLangChainService with model: {model_name}"
        )

        self.text_llm = ChatGoogleGenerativeAI(
            model=self.model_name, api_key=SecretStr(api_key), temperature=0.1
        )