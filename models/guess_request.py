from pydantic import BaseModel
from typing import Optional

class GuessRequest(BaseModel):
    input_url: str
    actual_province: Optional[str] = None
