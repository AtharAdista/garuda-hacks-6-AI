from services.base_langchain import BaseLangChainService
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ScrapeService(BaseLangChainService):
    def __init__(self):
        super().__init__(model_name="models/gemini-2.0-flash")
        logger.info("ScrapeService initialized")