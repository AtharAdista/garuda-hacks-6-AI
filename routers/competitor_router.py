from fastapi import APIRouter, UploadFile, File, Form
from controllers import competitor_controller

competitor_router =  APIRouter(prefix="/game", tags=["Game"])

@competitor_router.post("/guess")
async def guess_province(
    image_url: str = Form(...),
    user_guess: str = Form(...),
    actual_province: str = Form(...)
):
    return await competitor_controller.handle_guess(image_url, user_guess, actual_province)