from pydantic import BaseModel, Field
from typing import Dict, Optional
from app.models.infrastructure_schemas import BaselineHourStats

class NodePolicyOutput(BaseModel):
    status: str = Field(..., description="Trạng thái phản hồi (success/error)")
    node_identifier: str = Field(..., description="Định danh IP/Hostname của Node thiết bị")
    
    current_hour: str = Field(..., description="Giờ hiện tại của hệ thống (0-23)")
    
    cpu_threshold: float = Field(..., description="Ngưỡng cảnh báo CPU ở giờ hiện tại (Mean + 1.645 * StdDev)")
    cpu_mean: float = Field(..., description="Kỳ vọng CPU hiện tại")
    cpu_variance: float = Field(..., description="Phương sai CPU hiện tại")
    cpu_last_updated: str = Field(..., description="Thời gian cập nhật CPU cuối cùng cho múi giờ này")
    
    ram_threshold: float = Field(..., description="Ngưỡng cảnh báo RAM ở giờ hiện tại (Mean + 1.645 * StdDev)")
    ram_mean: float = Field(..., description="Kỳ vọng RAM hiện tại")
    ram_variance: float = Field(..., description="Phương sai RAM hiện tại")
    ram_last_updated: str = Field(..., description="Thời gian cập nhật RAM cuối cùng cho múi giờ này")