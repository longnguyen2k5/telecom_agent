from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langfuse import observe
from app.services.node_health_service import get_ssh_connection_info, execute_health_action
import asyncio

load_dotenv()

class CheckNodeHealthParam(BaseModel): 
    host: str = Field(..., description='IP hoặc Hostname của server cần kiểm tra')
    ram_threshold: float = Field(..., description='Ngưỡng RAM %. LƯU Ý: BẮT BUỘC phải trích xuất từ công cụ fetch_node_policy_baseline. Tuyệt đối KHÔNG tự bịa hoặc dùng số mặc định.')
    cpu_threshold: float = Field(..., description='Ngưỡng CPU %. LƯU Ý: BẮT BUỘC phải trích xuất từ công cụ fetch_node_policy_baseline. Tuyệt đối KHÔNG tự bịa hoặc dùng số mặc định.')
    service: str = Field(..., pattern=r"^[A-Za-z0-9\-_]+$", description='Tên service hoặc docker container')
    is_execute: bool = Field(False, description='Mặc định là False. Đặt True để thực sự sửa lỗi sau khi user đồng ý.')

def get_tools_declaration(): 
    schema = CheckNodeHealthParam.model_json_schema()
    return {
        "name": "node_health_autoremediate", 
        "description" : "Kiểm tra sức khỏe node qua SSH, đo RAM/CPU. QUY TẮC SỐNG CÒN: Bạn BẮT BUỘC phải gọi công cụ fetch_node_policy_baseline ĐẦU TIÊN để lấy ngưỡng ram_threshold và cpu_threshold rồi mới được phép gọi công cụ này.", 
        "parameters" : {
            "type": "object", 
            "properties": schema['properties'], 
            "required": schema.get('required', [])
        }
    }

@observe()
async def execute(args_dict): 
    """Hàm này là nơi Agent gọi vào truyền tham số."""
    try: 
        # 1. Ép kiểu tham số do AI truyền vào
        validated_args = CheckNodeHealthParam(**args_dict)
        
        # 2. Lấy user, pass, port từ Database (AI không hề biết bước này)
        ssh_info = await get_ssh_connection_info(validated_args.host)
        
        # 3. Gọi trực tiếp hàm xử lý (Không dùng subprocess nữa)
        result_obj = await asyncio.to_thread(
            execute_health_action, 
            host=ssh_info.hostname,
            port=ssh_info.port,
            user=ssh_info.username,
            password=ssh_info.password,
            service_name=validated_args.service,
            ram_threshold=validated_args.ram_threshold,
            cpu_threshold=validated_args.cpu_threshold,
            is_execute=validated_args.is_execute
        )
        
        # 4. Trả kết quả về dạng Dictionary chuẩn để AI đọc được
        return result_obj.model_dump(exclude_none=True)
    
    except Exception as e:
        return {"status": "error", "message": str(e)}