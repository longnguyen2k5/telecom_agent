import asyncio
from app.core.agent.agent import run_telecom_agent
from app.db.mongodb import db as shared_db
from motor.motor_asyncio import AsyncIOMotorClient

async def test_agent():
    shared_db.client = AsyncIOMotorClient("mongodb://localhost:27017")
    try:
        agent_stream = run_telecom_agent(
            user_message="hello",
            session_id="test",
            history=[],
            user_role="admin",
            user_id="user1"
        )
        print("Got stream generator:", agent_stream)
        async for event in agent_stream:
            print("EVENT:", repr(event))
    except Exception as e:
        print("EXCEPTION:", e)
        import traceback
        traceback.print_exc()
    finally:
        shared_db.client.close()

if __name__ == "__main__":
    asyncio.run(test_agent())
