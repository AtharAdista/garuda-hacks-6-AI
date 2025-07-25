from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.match_summary_service import analyze_match_performance

match_summary_router = APIRouter()

@match_summary_router.post("/match-summary")
async def get_match_summary(rounds_data: List[Dict[str, Any]]):
    try:
        result = analyze_match_performance(rounds_data)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing match: {str(e)}")
