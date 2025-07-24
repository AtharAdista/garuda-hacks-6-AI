"""
Base service class for Gemini API integration using LangChain.
"""

import base64
import os
import binascii
import logging
from typing import Dict, Any, cast
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from services.gemini.exceptions import GeminiAPIKeyMissingError, InvalidImageError

# Configure logger
logger = logging.getLogger(__name__)


class BaseLangChainService:
    """Base service for Gemini services using LangChain."""

    def __init__(
        self,
        text_model_name: str = "models/gemini-1.5-pro",
        multimodal_model_name: str = "models/gemini-1.5-pro",
    ):
        """Initialize the service.

        Args:
            text_model_name: The name of the text model.
            multimodal_model_name: The name of the multimodal model.

        Raises:
            GeminiAPIKeyMissingError: If the API key is not set in environment variables.
        """
        self.text_model_name = text_model_name
        self.multimodal_model_name = multimodal_model_name

        # Get API key from environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("Google API key not found in environment variables")
            raise GeminiAPIKeyMissingError()

        logger.info(
            f"Initializing BaseLangChainService with text model: {text_model_name}"
        )
        logger.info(
            f"Initializing BaseLangChainService with multimodal model: {multimodal_model_name}"
        )

        # Create text LLM
        self.text_llm = ChatGoogleGenerativeAI(
            model=self.text_model_name, api_key=SecretStr(api_key), temperature=0.1
        )

        # Create multimodal LLM
        self.multimodal_llm = ChatGoogleGenerativeAI(
            model=self.multimodal_model_name,
            api_key=SecretStr(api_key),
            temperature=0.1,
        )

    def _read_image_bytes(self, image_file) -> str:
        """Read the image bytes from a file and return base64 encoding.

        Args:
            image_file: The image file (file-like object).

        Returns:
            The base64-encoded image bytes.

        Raises:
            InvalidImageError: If the image cannot be processed.
        """
        try:
            # Read file content
            image_content = image_file.read()

            # Ensure we have bytes
            if not isinstance(image_content, bytes):
                if isinstance(image_content, str):  # pragma: no cover
                    image_content = image_content.encode("utf-8")
                else:  # pragma: no cover
                    # For other types, try to convert to bytes
                    image_content = bytes(image_content)

            if len(image_content) == 0:
                logger.error("Empty image file received")
                raise InvalidImageError("Image file is empty")

            # Encode as base64
            b64_bytes = base64.b64encode(image_content)
            b64_string = b64_bytes.decode("utf-8")

            # Ensure valid padding
            padding = 4 - (len(b64_string) % 4) if len(b64_string) % 4 else 0
            b64_string = b64_string + ("=" * padding)

            # Validate the result by trying to decode it (catch bad encodings)
            try:
                base64.b64decode(b64_string)
            except binascii.Error as e:  # pragma: no cover
                logger.error(f"Invalid base64 encoding: {str(e)}")
                raise InvalidImageError(
                    "Generated invalid base64 string. Check image data."
                )

            logger.debug(
                f"Successfully encoded image file to base64 (length: {len(b64_string)})"
            )
            return b64_string

        except InvalidImageError as e:
            # Re-raise specific image errors
            raise e
        except Exception as e:
            logger.error(f"Error in _read_image_bytes: {str(e)}")
            raise InvalidImageError(f"Failed to process image: {str(e)}")

    async def _invoke_text_model(self, prompt: str) -> str:
        """Invoke the text model with a prompt.

        Args:
            prompt: The prompt to send to the model.

        Returns:
            The model's response as a string.
        """
        try:
            logger.debug(f"Invoking text model with prompt: {prompt[:100]}...")
            human_message = HumanMessage(content=prompt)
            response = await self.text_llm.ainvoke([human_message])
            print(f"AI API Response (Text Model): {response.content[:500]}...")
            return cast(str, response.content)
        except Exception as e:
            logger.error(f"Error invoking text model: {str(e)}")
            raise

    async def _invoke_multimodal_model(
        self, text_prompt: str, image_base64: str
    ) -> str:
        """Invoke the multimodal model with text and image.

        Args:
            text_prompt: The text prompt to send to the model.
            image_base64: The base64-encoded image.

        Returns:
            The model's response as a string.
        """
        try:
            logger.debug(
                f"Invoking multimodal model with prompt: {text_prompt[:100]}..."
            )

            # Create multipart message with image and text
            human_message = HumanMessage(
                content=[
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )

            response = await self.multimodal_llm.ainvoke([human_message])
            print(f"AI API Response (Multimodal Model): {response.content[:500]}...")
            return cast(str, response.content)
        except Exception as e:
            logger.error(f"Error invoking multimodal model: {str(e)}")
            raise
