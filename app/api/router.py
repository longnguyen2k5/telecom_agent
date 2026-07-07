from fastapi import APIRouter
from app.api.v1 import chat, session, auth

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(session.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(auth.router, prefix="/login", tags=["Authentication"])