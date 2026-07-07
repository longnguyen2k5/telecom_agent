from motor import AsyncIOMotorClient
from app.db.mongodb import db as shared_db
from app.core.agent.orchestrator import run_telecom_agent
import json 
import asyncio


async def main():
    shared_db.client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    print("🤖 Telecom Agent đã sẵn sàng! Gõ 'exit' để thoát.\n")
    history_mock = []
    try:
        while True:
            user_prompt = input("\n👤 NOC Engineer: ")
            if user_prompt.lower() == 'exit':
                break

            print("🤖 Telecom Agent: ", end="", flush=True)
            
            # SỬA TẠI ĐÂY: Nhận ra async generator
            agent_stream = run_telecom_agent(
                user_message=user_prompt, 
                session_id="test_123", 
                history=history_mock, 
                user_role="admin",
                user_id="user_001"
            )
            
            async for event in agent_stream:
                json_str = event.replace("data: ", "").strip()
                if not json_str: 
                    continue
                    
                try:
                    event_data = json.loads(json_str) 
                    event_type = event_data.get("type")
                    
                    if event_type == "thought":
                        print(f"\n   🧠 [Thought]: {event_data.get('content', '')}", end="", flush=True)
                    elif event_type == "tool_start":
                        print(f"\n   ⚙️ [Đang chạy Tool: {event_data.get('name', '')}...]", end="", flush=True)
                    elif event_type == "tool_result":
                        print(" ✅ [Hoàn tất]", end="", flush=True)
                    elif event_type == "text":
                        print(event_data.get("content", ""), end="", flush=True)
                        
                except json.JSONDecodeError:
                    print(f"\n❌ Lỗi parse JSON: {json_str}")
            print("\n")
    finally: 
        shared_db.client.close()
        print("🔌 Đóng kết nối MongoDB. Kết thúc chương trình.")
        
if __name__ == "__main__":
    asyncio.run(main())