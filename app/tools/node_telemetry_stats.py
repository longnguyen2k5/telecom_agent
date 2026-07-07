from pydantic import BaseModel, Field
from typing import Literal
from langfuse import observe
from app.services.node_telemetry_service import calculate_telemetry_distribution

class NodeTelemetryStatsArgs(BaseModel):
    node_identifier: str = Field(
        ..., 
        description="IP hoặc Hostname của thiết bị mạng cần quét số liệu hiệu năng (Ví dụ: LOCAL-TEST-NODE)"
    )
    metric_type: Literal["ram_usage", "cpu_usage"] = Field(
        ..., 
        description="Loại tài nguyên hiệu năng hệ thống cần làm thống kê định lượng"
    )
    window_minutes: int = Field(
        default=60, 
        description="Cửa sổ thời gian quét ngược về quá khứ tính bằng phút để gom mẫu dữ liệu chuỗi thời gian"
    )
    
def get_tools_declaration() -> dict: 
    """
    Sinh cấu trúc JSON Schema chuẩn của Tool fetch-node-telemetry-stats 
    để nạp vào API Function Calling của Gemini Agent.
    """
    schema = NodeTelemetryStatsArgs.model_json_schema()
    
    return {
        "name": "fetch_node_telemetry_stats", 
        "description": (
            "Truy vấn dữ liệu hiệu năng chuỗi thời gian (Time-series) trong MongoDB để "
            "tính toán observed_mean và observed_variance có hiệu chỉnh n-1. "
            "Dùng BẤT CỨ KHI NÀO cần lấy số liệu thực tế của một Node mạng để làm đầu vào cho việc chỉnh ngưỡng Policy."
        ), 
        "parameters": {
            "type": "object", 
            "properties": schema.get('properties', {}), 
            "required": schema.get('required', [])
        }
    }
    

@observe()
async def execute(args_dict): 
    try: 
        validated_args = NodeTelemetryStatsArgs(**args_dict)
        result = await calculate_telemetry_distribution(
            node_identifier=validated_args.node_identifier,
            metric_type=validated_args.metric_type,
            window_minutes=validated_args.window_minutes
        )
        return result.model_dump(exclude_none=True)
    
    except Exception as e:
        return {"status": "error", "message": str(e)}