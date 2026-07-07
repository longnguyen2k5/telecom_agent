from pydantic import BaseModel, Field
from typing import Literal, Dict
from datetime import datetime

class AlarmHistoryModel(BaseModel):
    alarm_id: str
    alarm_type: str 
    ne_name: str
    severity: str   
    content: str = ""
    last_seen: str = Field(..., alias="event_time")
    
    model_config = {
        "populate_by_name": True
    }
    
class NeInventoryModel(BaseModel):
    ne_name: str
    ip: str
    site_id: str = "UNKNOWN" 
    oncall_team: str = "UNKNOWN" 
    vendor: str = "UNKNOWN"
    segment: str = "UNKNOWN"
    
    ssh_user: str = "root"      
    ssh_port: int = Field(default=22, ge=1, le=65535)
    credential_key: str
    
class HourStat(BaseModel): 
    mean: float = Field(..., description="Giá trị kỳ vọng (μ)")
    variance: float = Field(..., description="Phương sai (σ^2) đại diện cho năng lượng biến động")  
      
class BaselineHourStats(BaseModel): 
    initial: HourStat = Field(..., description="Gia tri thống kê ban đầu (Initial) của giờ đang xét")
    current: HourStat = Field(..., description="Giá trị thống kê hiện tại (Current) của giờ đang xét")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Thời điểm cập nhật policy cho khung giờ này (ISO 8601)")
    
class NodeMetricBaselineModel(BaseModel): 
    node_identifier: str = Field(..., description="IP hoặc Hostname của node")
    metric_type: Literal["ram_usage", "cpu_usage"] = Field(..., description="Loại metric cần lấy baseline (ram hoặc cpu)")
    season_context: Literal['WEEKDAY', 'WEEKEND', 'HOLIDAY'] = Field(..., description="Ngữ cảnh mùa vụ để lấy baseline")
    baseline_stats: Dict[str, BaselineHourStats] = Field(..., description="Các giá trị thống kê baseline của giờ đang xét")
    
    
class TelemetryMetricsData(BaseModel):
    cpu_usage: float
    ram_usage: float

class NodeTelemetryRawModel(BaseModel):
    timestamp: datetime
    metrics: TelemetryMetricsData