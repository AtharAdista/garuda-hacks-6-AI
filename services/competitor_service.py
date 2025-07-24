from services.base_langchain import BaseLangChainService
import logging

logger = logging.getLogger(__name__)

class CompetitorService(BaseLangChainService):
    def __init__(self):
        super().__init__(model_name="models/gemini-2.0-flash")
        logger.info("CompetitorService initialized")
