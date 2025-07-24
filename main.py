import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.scrape_controller import scrape_router
from controllers.competitor_controller import competitor_router
from controllers.game_controller import game_router
import uvicorn

app = FastAPI(
    title="Culturate Garuda Hacks 6 AI",
    description="Culturate AI API for Garuda Hacks 6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)
app.include_router(competitor_router)
app.include_router(game_router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)