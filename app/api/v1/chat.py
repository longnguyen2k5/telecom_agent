from fastapi import APIRouter, Depends, BackgroundTasks
from app.schemas.chat_dto import ChatRequest
from app.core.auth import get_current_user
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    return await ChatService.process_chat(request, user, background_tasks)
    