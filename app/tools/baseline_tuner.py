# app/tools/adaptive_policy_tuner.py
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from langfuse import observe
from app.schemas.baseline_dto import BaselineStatsTuned
from app.services.baseline_service import evaluate_and_adapt_policy

class PolicyTunerParam(BaseModel):
    node_id: str = Field(..., description="IP hoặc tên định danh của Node cần căn chỉnh cấu hình.")
    metric_type: Literal["ram_usage", "cpu_usage"] = Field(..., description="Loại metric cần hiệu chỉnh.")
    observed_mean: float = Field(..., description="Kỳ vọng trung bình thực tế tính toán được từ chuỗi log quá khứ.")
    observed_variance: float = Field(..., description="Phương sai thực tế tính toán được từ chuỗi log quá khứ.")

def get_tools_declaration():
    schema = PolicyTunerParam.model_json_schema()
    return {
        "name": "adaptive_policy_tuner",
        "description": (
            "Kích hoạt công cụ này khi người dùng than phiền về cảnh báo ảo hoặc yêu cầu tối ưu/hiệu chỉnh ngưỡng an toàn cho thiết bị. "
            "Tool áp dụng cơ chế Elastic Tether sử dụng khoảng cách KL Divergence và Z-score để kiểm soát việc cập nhật Policy một cách an toàn."
        ),
        "parameters": {
            "type": "object",
            "properties": schema['properties'],
            "required": schema.get('required', [])
        }
    }

@observe()
async def execute(args_dict: dict) -> BaselineStatsTuned:
    try:
        validated_args = PolicyTunerParam(**args_dict)
        result = await evaluate_and_adapt_policy(
            node_identifier=validated_args.node_id,
            metric_type=validated_args.metric_type,
            observed_mean=validated_args.observed_mean,
            observed_variance=validated_args.observed_variance
        )
        return result.model_dump(exclude_none=True)
    except ValidationError as ve:
        return {"status": "error", "message": f"AI cung cấp sai định dạng tham số: {ve}"}
    except Exception as e:
        return {"status": "error", "message": f"Thất bại trong quá trình tính toán thích ứng: {str(e)}"}