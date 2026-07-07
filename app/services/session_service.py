from typing import List
from fastapi import HTTPException
from app.db.repositories.session_repo import create_new_session, get_session_history, get_user_sessions, rename_session, delete_session
from app.schemas.session_dto import SessionResponse, MessageResponse

class SessionService(): 
    @staticmethod
    async def create_session(user_id: str, title: str) -> SessionResponse: 
        if not title: 
            title = "New Chat"        
        session_db = await create_new_session(user_id, title)
        return SessionResponse(id=str(session_db.id), title=session_db.title, created_at=session_db.created_at)
        
    @staticmethod
    async def rename_session(session_id: str, user_id: str, new_title: str) -> bool:
        if not new_title or not new_title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        success = await rename_session(session_id, user_id, new_title.strip())
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or not modified")
        return True

    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        success = await delete_session(session_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or already deleted")
        return True

    @staticmethod
    async def get_session_history(session_id: str, user_id: str, limit: int = 20, before_id: str = None) -> List[MessageResponse]: 
        history = await get_session_history(session_id, user_id, limit, before_id)
        if history is None: 
            raise HTTPException(status_code=404, detail="Session not found or no messages available.")
        return [MessageResponse(role=msg.role, 
                                content=msg.content, 
                                thought=msg.thought, 
                                tool_calls=[call.model_dump() for call in msg.tool_calls] if msg.tool_calls else None, 
                                created_at=msg.created_at) for msg in history]
    
    @staticmethod
    async def get_user_sessions(user_id: str) -> List[SessionResponse]: 
        sessions = await get_user_sessions(user_id)
        if sessions is None: 
            raise HTTPException(status_code=404, detail="No sessions found for the user.")
        return [SessionResponse(id=str(session.id), 
                                title=session.title, 
                                created_at=session.created_at) for session in sessions]

    