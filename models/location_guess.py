from pydantic import BaseModel
from typing import Optional

class LocationGuessResult(BaseModel):
    province_guess: str
    confidence: float
    error: Optional[str] = None
    reasoning: Optional[str] = None  