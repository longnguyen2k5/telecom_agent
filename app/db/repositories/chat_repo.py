from app.db.mongodb import get_database
from app.schemas.chat_dto import ToolCallRecord
from typing import Optional, List
from app.models.chat_schemas import ChatMessage

async def save_message(session_id: str, 
                       user_id: str, 
                       role: str, 
                       content: str, 
                       thought: Optional[str] = None, 
                       tool_calls: Optional[List[ToolCallRecord]] = None) -> ChatMessage:
    db = get_database()
    msg = ChatMessage(
        session_id=session_id, 
        user_id=user_id,
        role=role, 
        content=content, 
        thought=thought,
        tool_calls=tool_calls
    )
    result = await db["messages"].insert_one(msg.model_dump(by_alias=True, exclude=["id"]))
    
    msg.id = result.inserted_id
    return msg