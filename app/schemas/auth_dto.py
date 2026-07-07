from pydantic import BaseModel
from typing import Optional, Literal

class TokenResponse(BaseModel): 
    token_type: Literal["bearer"] = "bearer"
    access_token: str 
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None