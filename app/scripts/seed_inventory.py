from pymongo import MongoClient

def seed_database():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["telecom_agent_db"]
    
    # Xóa dữ liệu cũ nếu chạy lại
    db["ne_inventory"].drop()
    
    inventory_data = [
        {
            "ne_name": "LOCAL-TEST-NODE", 
            "ip": "127.0.0.1", 
            "site_id": "SITE_LOCAL_01", 
            "segment": "TEST_ENV", 
            "oncall_team": "NOC_DEV_TEAM",
            # Thêm cấu hình hạ tầng cho Tool 2
            "ssh_user": "noc", # Hoặc user của container
            "ssh_port": 2222,
            "credential_key": "PASS_LOCAL_TEST" # Khóa để tra mật khẩu trong .env
        },
        {
            "ne_name": "HNI-AGG-02", 
            "ip": "10.1.2.2", 
            "site_id": "SITE_HNI_02", 
            "segment": "AGGREGATION", 
            "oncall_team": "NOC_CORE_T2",
            "ssh_user": "noc_admin",
            "ssh_port": 22,
            "credential_key": "PASS_HNI_AGG"
        }
    ]
    
    db["ne_inventory"].insert_many(inventory_data)
    print("✅ Đã tạo thành công danh mục hạ tầng trong MongoDB!")

if __name__ == "__main__":
    seed_database()