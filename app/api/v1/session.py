from fastapi import APIRouter, Depends
from app.schemas.session_dto import CreateSessionRequest, RenameSessionRequest
from app.core.auth import get_current_user
from app.services.session_service import SessionService

router = APIRouter()

@router.get("/")
async def list_sessions(user: dict = Depends(get_current_user)):
    return await SessionService.get_user_sessions(user["id"])
    
@router.post("/")
async def new_session(request: CreateSessionRequest, user: dict = Depends(get_current_user)):
    return await SessionService.create_session(user["id"], request.title)

@router.put("/{session_id}")
async def rename_session(session_id: str, request: RenameSessionRequest, user: dict = Depends(get_current_user)):
    await SessionService.rename_session(session_id, user["id"], request.title)
    return {"message": "Session renamed successfully"}

@router.delete("/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    await SessionService.delete_session(session_id, user["id"])
    return {"message": "Session deleted successfully"}

@router.get("/{session_id}/messages")
async def session_history(session_id: str, limit: int = 20, before_id: str = None, user: dict = Depends(get_current_user)):
    return await SessionService.get_session_history(session_id, user["id"], limit, before_id)