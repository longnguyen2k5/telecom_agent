from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class CreateSessionRequest(BaseModel): 
    title: str = Field(..., min_length=1, max_length=100)

class RenameSessionRequest(BaseModel): 
    title: str = Field(..., min_length=1, max_length=100)
    
class SessionResponse(BaseModel):
    id: str  # Convert ObjectId sang string
    title: str
    created_at: datetime

# Dùng cho tin nhắn trong chat
class MessageResponse(BaseModel):
    role: str
    content: str
    thought: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    created_at: datetime