from fastapi import APIRouter

from app.api.routes import assistant, health, research

api_router = APIRouter()
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(research.router, prefix="/research", tags=["research"])

