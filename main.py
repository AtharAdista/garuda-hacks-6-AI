from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.scrape_controller import scrape_router
from routers.competitor_router import competitor_router
from routers.game_router import game_router
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)