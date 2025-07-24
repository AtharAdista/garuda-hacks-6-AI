from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.scrape_controller import scrape_router
from controllers.competitor_controller import competitor_router

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