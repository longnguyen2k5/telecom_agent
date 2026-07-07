from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from bson import ObjectId 

class PyObjectId(ObjectId): 
    @classmethod
    def __get_validators__(cls): 
        yield cls.validate 
    
    @classmethod
    def validate(cls, v, values, **kwargs): 
        if not ObjectId.is_valid(v): 
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, *arg, **kwargs): 
        field_schema.update(type="string") 
        
        
class ChatSession(BaseModel): 
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id : str
    title : str = "New Chat"
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config: 
        populate_by_name = True
        json_encoders = {ObjectId: str} 
        
class ToolCallRecord(BaseModel):
    name: str
    args: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None 
    status: Literal['success', 'error'] = 'success'
    error_message: Optional[str] = None

class ChatMessage(BaseModel): 
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    session_id : str
    user_id : str
    role : str
    content : str
    thought: Optional[str] = None
    tool_calls : Optional[List[ToolCallRecord]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config: 
        populate_by_name = True
        json_encoders = {ObjectId: str}
        