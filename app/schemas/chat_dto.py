from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal, Annotated
from app.models.chat_schemas import ToolCallRecord

class ChatRequest(BaseModel): 
    session_id: str
    message: str
     
    
# Response 
class StreamTextChunk(BaseModel): 
    type: Literal['text'] = 'text' # <--- Sửa thành Literal
    content: str 
    
class StreamThoughtChunk(BaseModel): 
    type: Literal['thought'] = 'thought' # <--- Sửa thành Literal
    content: str

class StreamToolStartChunk(BaseModel): 
    type: Literal['tool_start'] = 'tool_start' # <--- Sửa thành Literal
    name: str
    args: Dict[str, Any]
    
class StreamToolResultChunk(BaseModel): 
    type: Literal['tool_result'] = 'tool_result' # <--- Sửa thành Literal
    name: str
    result: Dict[str, Any]

class StreamDoneChunk(BaseModel): 
    type: Literal['done'] = 'done' # <--- Sửa thành Literal
    full_text: str
    thought: Optional[str] = None
    tools_used: List[ToolCallRecord] 
    
ChatEvent = Annotated[
    Union[StreamTextChunk, StreamThoughtChunk, StreamToolStartChunk, StreamToolResultChunk, StreamDoneChunk],
    Field(discriminator='type')
]