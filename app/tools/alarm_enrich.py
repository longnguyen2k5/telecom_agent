from pydantic import BaseModel, Field, ValidationError
from typing import Literal, List
from dotenv import load_dotenv
from langfuse import observe
from app.services.alarm.alarm_service import run_noc_alarm_enrichment

load_dotenv()

class AlarmEnrichParam(BaseModel): 
    alarm_type: Literal["HIGH_LOAD", "LINK_DOWN", "NODE_OFFLINE", "OSPF_FLAP"] = Field(
        ..., 
        description="Loại cảnh báo chính xác cần lọc từ MongoDB. Bắt buộc phải có."
    )
    window_min: int = Field(
        default=10, 
        description="Cửa sổ thời gian (phút) để tính toán logic toán tử $gte đối với event_time."
    )
    alarm_table: str = Field(
        default="core_alarm_history", 
        description="Tên Collection MongoDB chứa cảnh báo gốc."
    )
    inventory_table: str = Field(
        default="ne_inventory", 
        description="Tên Collection MongoDB danh mục hạ tầng để tra cứu chéo tham chiếu."
    )
    
    key_fields: List[Literal["ips", "ne_names", "interfaces", "cell_ids", "as_numbers", "vlans"]] = Field(
        default=["ips", "ne_names"], 
        description="Các trường thực thể dùng làm chìa khóa gộp tra cứu chéo (Lookup Keys)."
    )
    
    enrich_fields: List[Literal["site_id", "segment", "vendor", "oncall_team", "ssh_port"]] = Field(
        default=["site_id", "segment", "vendor", "oncall_team"], 
        description="Danh sách các trường thông tin hạ tầng muốn lấy ra từ Collection danh mục."
    )
    
    limit: int = Field(
        default=500, 
        description="Giới hạn (Limit) số lượng bản ghi trả về tối đa để tránh quá tải RAM hệ thống."
    )
    
def get_tools_declaration():
    schema = AlarmEnrichParam.model_json_schema()
    return {
        "name": "noc_alarm_enrichment",
        "description": (
            "Điều tra và làm giàu (enrich) cảnh báo NOC theo quy trình 3 bước sử dụng MongoDB: "
            "(1) Lọc cảnh báo theo type bằng toán tử $gte thời gian, "
            "(2) Chạy hàm bóc tách entity (IP, tên NE, interface...) từ content log, "
            "(3) Dùng cơ chế gộp mảng khóa truyền vào toán tử $in/$or tra cứu bảng ne_inventory để giải quyết bài toán N+1."
        ),
        "parameters": {
            "type": "object",
            "properties": schema['properties'],
            "required": schema.get('required', [])
        }
    }
    
@observe()
async def execute(args_dict):
    try:
        validated_args = AlarmEnrichParam(**args_dict)
        
        result_obj = await run_noc_alarm_enrichment(
            alarm_type=validated_args.alarm_type,
            window_min=validated_args.window_min,
            limit=validated_args.limit,
            alarm_table=validated_args.alarm_table,
            inventory_table=validated_args.inventory_table,
            key_fields=validated_args.key_fields,
            enrich_fields=validated_args.enrich_fields
        )
        
        return result_obj.model_dump(exclude_none=True)
    except ValidationError as ve:
        return {"error": f"Lỗi định dạng dữ liệu đầu vào từ AI: {ve}"}
    except Exception as e:
        return {"error": f"Lỗi thực thi tool: {str(e)}"}