# tools/node_policy_fetcher.py
import asyncio
import math
from datetime import datetime
from pydantic import BaseModel, Field
from langfuse import observe
from app.services.baseline_service import get_policy
from app.schemas.node_policy_dto import NodePolicyOutput

class FetchAllPoliciesArgs(BaseModel):
    node_identifier: str = Field(
        ..., 
        description="IP hoặc Hostname của thiết bị mạng cần lấy toàn bộ cấu hình policy baseline (Ví dụ: LOCAL-TEST-NODE)"
    )

def get_tools_declaration() -> dict: 
    """
    Sinh cấu trúc JSON Schema chuẩn của Tool fetch_node_policy_baseline
    để nạp vào API Function Calling của Gemini Agent.
    """
    schema = FetchAllPoliciesArgs.model_json_schema()
    
    return {
        "name": "fetch_node_policy_baseline", 
        "description": (
            "Truy vấn ĐỒNG THỜI toàn bộ cấu hình chính sách ngưỡng nền động (bao gồm cả cpu_usage và ram_usage) "
            "của một Node mạng trong Database mà không cần tính toán lại. Sử dụng công cụ này BẤT CỨ KHI NÀO "
            "cần kiểm tra thông số cấu hình nền hiện tại, so sánh bối cảnh hiệu năng, hoặc trích xuất mốc thời gian "
            "cập nhật gần nhất (last_updated) của từng chỉ số để phục vụ cơ chế kiểm soát Guardrail Cooldown."
        ), 
        "parameters": {
            "type": "object", 
            "properties": schema.get('properties', {}), 
            "required": schema.get('required', [])
        }
    }

@observe()
async def execute(args_dict: dict) -> dict: 
    try: 
        validated_args = FetchAllPoliciesArgs(**args_dict)
        node_id = validated_args.node_identifier
        
        # 2. 🎯 TỐI ƯU HIỆU NĂNG: Gọi truy vấn song song cả 2 metric độc lập từ tầng Service
        # Tránh việc await tuần tự gây nghẽn I/O bound
        cpu_task = get_policy(node_identifier=node_id, metric_type="cpu_usage")
        ram_task = get_policy(node_identifier=node_id, metric_type="ram_usage")
        
        cpu_model, ram_model = await asyncio.gather(cpu_task, ram_task)
        
        now_hour_str = str(datetime.now().hour)
        
        def extract_stats(stats):
            if now_hour_str in stats:
                current_stat = stats[now_hour_str].current
                last_updated = stats[now_hour_str].last_updated
                std_dev = math.sqrt(max(current_stat.variance, 0))
                threshold = round(current_stat.mean + 1.645 * std_dev, 2)
                return {
                    "threshold": threshold,
                    "mean": round(current_stat.mean, 2),
                    "variance": round(current_stat.variance, 4),
                    "last_updated": last_updated
                }
            return {"threshold": 0.0, "mean": 0.0, "variance": 0.0, "last_updated": ""}

        cpu_data = extract_stats(cpu_model.baseline_stats)
        ram_data = extract_stats(ram_model.baseline_stats)
        
        return NodePolicyOutput(
            status="success",
            node_identifier=node_id,
            current_hour=now_hour_str,
            cpu_threshold=cpu_data["threshold"],
            cpu_mean=cpu_data["mean"],
            cpu_variance=cpu_data["variance"],
            cpu_last_updated=cpu_data["last_updated"],
            ram_threshold=ram_data["threshold"],
            ram_mean=ram_data["mean"],
            ram_variance=ram_data["variance"],
            ram_last_updated=ram_data["last_updated"]
        ).model_dump(exclude_none=True)
    
    except ValueError as ve:
        return {"status": "error", "message": str(ve)}
    except Exception as e:
        return {"status": "error", "message": str(e)}