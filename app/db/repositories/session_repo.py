import pymongo
from app.db.mongodb import get_database
from app.models.chat_schemas import ChatSession, ChatMessage
from bson import ObjectId
from typing import List

async def create_new_session(user_id: str, title: str = "New Chat") -> ChatSession:
    db = get_database()
    new_session = ChatSession(user_id=user_id, title=title)
    
    # model_dump(by_alias=True) giúp đổi "id" thành "_id" cho MongoDB
    result = await db["sessions"].insert_one(new_session.model_dump(by_alias=True, exclude=["id"]))
    new_session.id = result.inserted_id 
    return new_session

async def rename_session(session_id: str, user_id: str, new_title: str) -> bool:
    db = get_database()
    result = await db["sessions"].update_one(
        {"_id": ObjectId(session_id), "user_id": user_id},
        {"$set": {"title": new_title}}
    )
    return result.modified_count > 0

async def delete_session(session_id: str, user_id: str) -> bool:
    db = get_database()
    result = await db["sessions"].update_one(
        {"_id": ObjectId(session_id), "user_id": user_id},
        {"$set": {"is_deleted": True}}
    )
    return result.modified_count > 0


async def get_user_sessions(user_id: str) -> List[ChatSession]: 
    db = get_database()
    query = {
        "user_id": user_id,
        "$or": [{"is_deleted": False}, {"is_deleted": {"$exists": False}}]
    }
    cursor = db["sessions"].find(query).sort("created_at", pymongo.DESCENDING)
    
    sessions = []
    async for document in cursor:
        sessions.append(ChatSession(**document))
        
    return sessions

async def get_session_history(session_id: str, user_id: str, limit: int = 20, before_id: str = None) -> List[ChatMessage]:
    db = get_database()
    
    query = {"session_id": session_id, "user_id": user_id}
    
    if before_id:
        query["_id"] = {"$lt": ObjectId(before_id)}

    cursor = db["messages"].find(query).sort("_id", pymongo.DESCENDING).limit(limit)
    
    history = []
    async for document in cursor:
        history.append(ChatMessage(**document))
        
    history.reverse()
    
    return history