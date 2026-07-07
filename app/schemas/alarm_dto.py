from app.models.infrastructure_schemas import AlarmHistoryModel, NeInventoryModel
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AlarmRepoQueryResult(BaseModel): 
    data: List[AlarmHistoryModel] 
    debug_query: Optional[str] = None
    
class NeInventoryRepoQueryResult(BaseModel):
    data: List[NeInventoryModel] 
    debug_query: Optional[str] = None
    
class EnrichedAlarmItem(BaseModel):
    alarm_id: str
    content: str
    ne_name: str
    severity: str
    last_seen: Optional[str] = None
    extracted: Dict[str, List[str]] = Field(default_factory=dict)
    lookup_keys: List[str] = Field(default_factory=list)
    enrichment: Dict[str, Any] = Field(default_factory=dict)

class AlarmEnrichmentOutput(BaseModel):
    status: str
    message: Optional[str] = None
    sql_step_1: Optional[str] = None
    sql_step_3: Optional[str] = None
    data: List[EnrichedAlarmItem] = Field(default_factory=list)