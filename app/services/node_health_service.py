from app.schemas.node_health_dto import NodeHealthOutput, SSHConnectionInfo
from app.db.repositories.node_repo import find_node_by_identifier
import os
import paramiko
import shlex
import time

async def get_ssh_connection_info(host_identifier: str) -> SSHConnectionInfo:
    node_info = await find_node_by_identifier(host_identifier)
    if not node_info:
        raise ValueError(f"Báo động: Không tìm thấy thông tin node cho {host_identifier}!")
    
    real_password = os.getenv(node_info.credential_key)
    
    if not real_password:
        raise ValueError(f"Báo động: Không tìm thấy mật khẩu cho biến {node_info.credential_key}!")

    return SSHConnectionInfo(
        hostname=node_info.ip,
        port=node_info.ssh_port,
        username=node_info.ssh_user,
        password=real_password
    )

def get_real_metrics(ssh_client):
    """
    Đo RAM và CPU qua SSH bằng ĐÚNG 1 KÊNH (Single Channel).
    Giảm tải tối đa cho sshd của Docker, tránh lỗi Banner.
    """
    try:
        # Gộp tất cả các lệnh đọc cgroups v2 vào 1 kịch bản bash duy nhất
        combined_cmd = (
            "ram_curr=$(sudo cat /sys/fs/cgroup/memory.current) && "
            "ram_max=$(sudo cat /sys/fs/cgroup/memory.max) && "
            "cpu_s1=$(sudo grep 'usage_usec' /sys/fs/cgroup/cpu.stat | awk '{print $2}') && "
            "sleep 0.5 && "
            "cpu_s2=$(sudo grep 'usage_usec' /sys/fs/cgroup/cpu.stat | awk '{print $2}') && "
            "echo \"$ram_curr $ram_max $cpu_s1 $cpu_s2\""
        )
        
        stdin, stdout, stderr = ssh_client.exec_command(combined_cmd)
        output = stdout.read().decode().strip()
        
        if not output:
            error_msg = stderr.read().decode().strip()
            raise RuntimeError(f"Không lấy được dữ liệu từ cgroups: {error_msg}")
            
        # Tách các giá trị trả về
        ram_current, ram_max, cpu_start, cpu_end = map(float, output.split())
        
        # Tính toán % RAM
        ram_pct = (ram_current / ram_max) * 100.0
        ram_pct = min(ram_pct, 100.0)
        
        # Tính toán % CPU (Delta thời gian chạy trong 0.5 giây của lệnh sleep)
        cpu_delta_seconds = (cpu_end - cpu_start) / 1000000.0
        time_delta_seconds = 0.5  # Khoảng thời gian sleep cứng trong lệnh bash
        cpu_pct = (cpu_delta_seconds / time_delta_seconds) * 100.0
        
        return round(ram_pct, 1), round(cpu_pct, 1)
    except Exception as e:
        raise RuntimeError(f"Lỗi khi xử lý metric qua Single Channel: {str(e)}")
    
def execute_health_action(host: str, port: int, user: str, password: str, 
                          service_name: str, ram_threshold: float, cpu_threshold: float, 
                          is_execute: bool) -> NodeHealthOutput:
    """SSH vào server, kiểm tra danh sách container thực tế trước để đưa ra quyết định an toàn."""
    
    CRITICAL_SERVICES = ["agent-mongo", "keycloak", "keycloak-db", "telecom_mongodb"]
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ssh.connect(hostname=host, port=port, username=user, password=password, timeout=5)
            break 
        except (paramiko.SSHException, OSError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            else:
                return NodeHealthOutput(
                    status="error", 
                    host=host, 
                    action_decided="failed", 
                    error_message=f"Lỗi kết nối SSH sau {max_retries} lần thử: {str(e)}"
                )
    
    try:
        # 1. Đo tải thực tế qua cgroups v2
        real_ram, real_cpu = get_real_metrics(ssh)
        
        # ----------------------------------------------------------------
        # 🎯 BƯỚC CẢI TIẾN: QUÉT DOCKER PS TRƯỚC ĐỂ KIỂM TRA TÍNH TỒN TẠI
        # ----------------------------------------------------------------
        # Lấy danh sách TẤT CẢ container đang có trên hệ thống
        stdin, stdout, stderr = ssh.exec_command("sudo docker ps -a --format '{{.Names}}'")
        all_services = [s.strip() for s in stdout.read().decode().split('\n') if s.strip()]
        
        # ----------------------------------------------------------------
        # 🎯 LOGIC PHÂN LỚP ĐỊNH DANH DỊCH VỤ LỖI CHÍNH XÁC
        # ----------------------------------------------------------------
        target_service = None
        discovery_reason = ""
        
        # Lớp 1: Nếu Agent truyền lên một tên cụ thể VÀ tên đó THỰC SỰ TỒN TẠI trong hệ thống
        if service_name and service_name != "unknown" and service_name in all_services:
            target_service = service_name
            discovery_reason = f"Xác thực thành công dịch vụ chỉ định từ Agent: [{target_service}]"
        
        # Lớp 2: Nếu Agent đoán sai/truyền unknown/hoặc container chỉ định không tồn tại thực tế
        else:
            if service_name and service_name != "unknown" and service_name not in all_services:
                discovery_reason = f"Cảnh báo: Dịch vụ Agent chỉ định [{service_name}] không tồn tại thực tế! "
            else:
                discovery_reason = "Không có chỉ định dịch vụ cụ thể. "
                
            # Khởi động Service Discovery: Quét tìm con chiếm CPU cao nhất (HIGH_LOAD kịch bản)
            cmd_top_cpu = "sudo docker stats --no-stream --format '{{.CPUPerc}}\t{{.Names}}' | sort -rn | head -n 1"
            stdin, stdout, stderr = ssh.exec_command(cmd_top_cpu)
            top_cpu_output = stdout.read().decode().strip()
            
            if top_cpu_output and '\t' in top_cpu_output:
                try:
                    cpu_val_str, top_name = top_cpu_output.split('\t')
                    target_service = top_name.strip()
                    discovery_reason += f"Tự động định vị container ngốn CPU đỉnh điểm: [{target_service}] ({cpu_val_str} CPU)"
                except Exception:
                    pass
        
        # Thao tác bọc lót an toàn cuối cùng
        if not target_service:
            target_service = "app-service-crashed"
            discovery_reason += " -> Sử dụng cấu hình bọc lót mặc định."
            
        # ----------------------------------------------------------------
        # 🎯 RA QUYẾT ĐỊNH XỬ LÝ DỰA TRÊN THỰC TRẠNG VÀ QoS PROTECTION
        # ----------------------------------------------------------------
        safe_service = shlex.quote(target_service)
        is_critical = target_service in CRITICAL_SERVICES
        action = "none"
        command = None
        # Kịch bản Xử lý quá tải hiệu năng thông thường
        if real_ram > ram_threshold and real_cpu > cpu_threshold:
            if is_critical:
                action = "read_logs"
                command = f"sudo docker logs --tail 200 {safe_service}"
                discovery_reason += " | [QoS WARNING] Dịch vụ chí mạng! Chuyển hướng hạ cấp sang trích xuất logs."
            else:
                action = "restart_docker"
                command = "sudo -n systemctl restart docker"
                
        elif real_ram > ram_threshold and real_cpu <= cpu_threshold:
            action = "read_logs"
            command = f"sudo docker logs --tail 200 {safe_service}"
            
        elif real_ram <= ram_threshold and real_cpu > cpu_threshold:
            if is_critical:
                action = "read_logs"
                command = f"sudo docker logs --tail 200 {safe_service}"
                discovery_reason += " | [QoS WARNING] Dịch vụ chí mạng! Chuyển hướng hạ cấp sang trích xuất logs."
            else:
                action = "restart_service"
                command = f"sudo docker restart {safe_service}"
                
        cmd_output = ""
        if command: 
            if is_execute:
                stdin, stdout, stderr = ssh.exec_command(command)
                cmd_output = stdout.read().decode().strip()
                error_output = stderr.read().decode().strip()
                if error_output and action != "read_logs": 
                    raise RuntimeError(f"Lệnh cứu hộ báo lỗi: {error_output}")
                if not cmd_output and "start" in command:
                    cmd_output = f"Container {target_service} đã được khôi phục trạng thái trực tuyến thành công."
            else:
                cmd_output = f"[DRY-RUN] Phát hiện lỗi. Lệnh dự kiến chạy: {command}. Chờ kỹ sư phê duyệt."
                
        return NodeHealthOutput(
            status="success",
            host=host,
            real_cpu=real_cpu,
            real_ram=real_ram,
            target_service=target_service,
            action_decided=action,
            command_run=command,
            command_output=f"🔍 Báo cáo NOC: {discovery_reason}\n📝 Kết quả: {cmd_output}"
        )
        
    except Exception as e:
        return NodeHealthOutput(status="error", host=host, action_decided="failed", error_message=str(e))
    finally:
        ssh.close()
