import sys
from app.core.agent.agent import run_telecom_agent
import json

async def run():
    print("Starting agent...")
    stream = await run_telecom_agent(
        user_message="kiểm tra xem gần đây có event HIGH_LOAD không?",
        session_id="test_123",
        history=[],
        user_role="admin",
        user_id="test_user"
    )
    for event in stream:
        print(event, end="")
run()
