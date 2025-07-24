from fastapi import APIRouter, HTTPException
from services.scrape_service import ScrapeService
from typing import Dict, Union

scrape_router = APIRouter()
scrape_service = ScrapeService()

@scrape_router.get("/scrape/cultural-media")
async def scrape_cultural_media() -> Dict[str, Union[str, float]]:
    """Scrape a valid cultural image. Auto-retries until confidence >= 0.75. Returns province, image_url, and confidence_score."""
    try:
        result = scrape_service.scrape_until_valid()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")