# scripts/alarm_simulator.py
import os
import sys
import time
import subprocess
from datetime import datetime
from pymongo import MongoClient

# Thêm đường dẫn gốc để import được các Model chung
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.infrastructure_schemas import NodeTelemetryRawModel, TelemetryMetricsData, AlarmHistoryModel, NodeMetricBaselineModel

def get_container_metrics():
    """Đo tải thực tế của Container bằng lệnh docker stats."""
    try:
        cmd = "docker stats mock-target-node --no-stream --format '{{.CPUPerc}},{{.MemPerc}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout.strip().replace("%", "")
        if not output:
            return None, None
        cpu_str, mem_str = output.split(",")
        return float(cpu_str), float(mem_str)
    except Exception:
        return None, None

def get_current_baseline_threshold(db, metric_type: str, hour_key: str) -> float:
    """
    Truy vấn Database để lấy cấu hình Baseline động của giờ hiện tại.
    Công thức tính ngưỡng kích nổ Alarm: Threshold = Mean + 1.645 * StdDev (Z-score = 1.645)
    """
    try:
        query = {
            "node_identifier": "LOCAL-TEST-NODE",
            "metric_type": metric_type,
            "season_context": "WEEKDAY"
        }
        raw_doc = db["node_metric_baseline"].find_one(query)
        
        if raw_doc:
            # Ép vào Model chung để lấy dữ liệu chuẩn chỉ
            baseline_model = NodeMetricBaselineModel(**raw_doc)
            hour_stats = baseline_model.baseline_stats.get(hour_key)
            
            if hour_stats:
                mean = hour_stats.current.mean
                variance = hour_stats.current.variance
                std_dev = variance ** 0.5 # Tính σ từ σ^2
                
                dynamic_threshold = mean + (1.645 * std_dev)
                return min(dynamic_threshold, 100.0) # Không vượt quá 100%
                
    except Exception as e:
        print(f"⚠️ Không lấy được baseline động cho {metric_type}: {e}")
        
    return 80.0 # Thao tác bọc lót nếu không có DB

def main():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["telecom_agent_db"]
    
    print("🚀 [DYNAMIC MONITOR] Bộ mô phỏng cảnh báo thời gian thực đang chạy...")
    print("📊 Trạng thái quét được sẽ lưu trực tiếp vào bảng 'node_telemetry' phục vụ Tools.")
    print("Nhấn Ctrl+C để dừng.\n")
    
    alarm_counter = 2000

    while True:
        try:
            cpu_load, ram_load = get_container_metrics()
            now = datetime.now()
            current_hour_str = str(now.hour) # Lấy múi giờ thực tế (0 - 23)
            event_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # ----------------------------------------------------------------
            # 1. 🎯 GHI DATA CHUẨN VÀO BẢNG 'node_telemetry' PHỤC VỤ REPOSITORY
            # ----------------------------------------------------------------
            if cpu_load is not None:
                telemetry_obj = NodeTelemetryRawModel(
                    timestamp=now,
                    metrics=TelemetryMetricsData(cpu_usage=cpu_load, ram_usage=ram_load)
                )
                
                # Biến đổi thành dict thô để đẩy xuống Mongo
                telemetry_doc = telemetry_obj.model_dump()
                
                # 🌟 THÊM KHÓA ĐỊNH DANH NODE: Để khớp với điều kiện 'node_identifier' của hàm get_node_telemetry
                telemetry_doc["node_identifier"] = "LOCAL-TEST-NODE"
                
                db["node_telemetry"].insert_one(telemetry_doc)
                print(f"📊 [{event_time_str}] [Telemetry] Đã lưu trạng thái vào node_telemetry.")

            # ----------------------------------------------------------------
            # 2. TRUY VẤN BASELINE ĐỂ TÍNH NGƯỠNG ĐỘNG
            # ----------------------------------------------------------------
            cpu_threshold = get_current_baseline_threshold(db, "cpu_usage", current_hour_str)
            ram_threshold = get_current_baseline_threshold(db, "ram_usage", current_hour_str)

            # ----------------------------------------------------------------
            # 3. ĐỐI CHIẾU VÀ BẮN ALARM
            # ----------------------------------------------------------------
            # Tình huống A: Container chết hẳn
            if cpu_load is None:
                alarm_counter += 1
                alarm_doc = AlarmHistoryModel(
                    alarm_id=f"ALM-{alarm_counter}",
                    alarm_type="LINK_DOWN",
                    ne_name="LOCAL-TEST-NODE",
                    severity="CRITICAL",
                    content="Interface GigabitEthernet0/1 on LOCAL-TEST-NODE is DOWN (Ping timeout).",
                    event_time=event_time_str
                )
                db["core_alarm_history"].insert_one(alarm_doc.model_dump(by_alias=True))
                print(f"⚠️ [{event_time_str}] [ALERT] Container sập! Bắn sự kiện LINK_DOWN.")
                
            # Tình huống B: Đục thủng ngưỡng động của phân phối Gauss
            elif cpu_load > cpu_threshold or ram_load > ram_threshold:
                alarm_counter += 1
                reason_parts = []
                if cpu_load > cpu_threshold:
                    reason_parts.append(f"CPU: {cpu_load}% > Ngưỡng {cpu_threshold:.1f}%")
                if ram_load > ram_threshold:
                    reason_parts.append(f"RAM: {ram_load}% > Ngưỡng {ram_threshold:.1f}%")
                
                alarm_doc = AlarmHistoryModel(
                    alarm_id=f"ALM-{alarm_counter}",
                    alarm_type="HIGH_LOAD",
                    ne_name="LOCAL-TEST-NODE",
                    severity="MAJOR",
                    content= f"High resource utilization detected on LOCAL-TEST-NODE (127.0.0.1). Real CPU: {cpu_load}%, RAM: {ram_load}%",
                    event_time=event_time_str
                )
                db["core_alarm_history"].insert_one(alarm_doc.model_dump(by_alias=True))
                print(f"🔥 [{event_time_str}] [ALERT] Quá tải động! Ngưỡng bị phá vỡ: " + " & ".join(reason_parts))
                
            else:
                print(f"🟢 [{event_time_str}] [Safe] Giờ {current_hour_str}h: CPU={cpu_load}% (Ngưỡng {cpu_threshold:.1f}%), RAM={ram_load}% (Ngưỡng {ram_threshold:.1f}%) -> Vùng an toàn.")

        except Exception as e:
            print(f"❌ Lỗi vòng lặp monitor: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    main()