from pydantic import BaseModel
from typing import Optional


class NodeHealthOutput(BaseModel):
    status: str                         # "success" hoặc "error"
    host: str                           # IP của node
    real_cpu: Optional[float] = None    # Metric đo được
    real_ram: Optional[float] = None    # Metric đo được
    target_service: Optional[str] = None # Dịch vụ thực sự được tác động (do tính năng auto-discovery)
    action_decided: str                 # "none", "restart_docker", "read_logs", "restart_service"
    command_run: Optional[str] = None   # Lệnh đã chạy (để AI biết tool đã làm gì)
    command_output: Optional[str] = None # ĐẶC BIỆT QUAN TRỌNG: Output của lệnh (ví dụ: nội dung log)
    error_message: Optional[str] = None # Thông báo lỗi nếu có
    
class SSHConnectionInfo(BaseModel):
    hostname: str
    port: int
    username: str
    password: str