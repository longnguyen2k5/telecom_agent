# scripts/seed_baseline.py
import os
import sys
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.infrastructure_schemas import NodeMetricBaselineModel, BaselineHourStats, HourStat

def seed_baseline_data():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["telecom_agent_db"]
    
    # 1. Tạo sẵn khung xương 24 giờ mặc định phẳng
    default_hour_stats = {}
    for hour in range(24):
        default_hour_stats[str(hour)] = BaselineHourStats(
            initial=HourStat(mean=50.0, variance=25.0),
            current=HourStat(mean=50.0, variance=25.0)
        )
        
    # 2. Chạy vòng lặp seed cho cả CPU và RAM để hạ tầng đồng bộ tuyệt đối
    metrics = ["cpu_usage", "ram_usage"]
    
    for metric in metrics:
        mock_baseline = NodeMetricBaselineModel(
            node_identifier="LOCAL-TEST-NODE",
            metric_type=metric,
            season_context="WEEKDAY",
            baseline_stats=default_hour_stats
        )
        
        query = {
            "node_identifier": mock_baseline.node_identifier,
            "metric_type": mock_baseline.metric_type,
            "season_context": mock_baseline.season_context
        }
        
        db["node_metric_baseline"].update_one(
            query, 
            {"$set": mock_baseline.model_dump()}, 
            upsert=True
        )
        print(f"🟢 [SEED] Đã khởi tạo cấu hình Baseline 24h cho {metric}!")

if __name__ == "__main__":
    seed_baseline_data()