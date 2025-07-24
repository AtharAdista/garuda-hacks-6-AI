import os
from dotenv import load_dotenv

from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from googleapiclient.discovery import build

import logging

load_dotenv()

logger = logging.getLogger(__name__)

class BaseLangChainService:

    def __init__(
        self,
        model_name: str = "models/gemini-2.0-flash"
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
        
        # Initialize YouTube API client
        try:
            self.youtube_client = build('youtube', 'v3', developerKey=api_key)
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            self.youtube_client = None