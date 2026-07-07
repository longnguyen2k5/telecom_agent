import sys
from app.core.agent.agent import safe_send_message_stream, build_system_instruction, get_allowed_tools
from google import genai
from google.genai import types

client = genai.Client()
agent_instruction = build_system_instruction("admin")
config = types.GenerateContentConfig(
    tools=get_allowed_tools("admin"),
    temperature=0.0, 
    system_instruction=agent_instruction
) 
chat = client.chats.create(model='gemini-3.1-flash-lite', config=config)

response_stream = chat.send_message_stream("kiểm tra xem gần đây có event HIGH_LOAD không?")
for chunk in response_stream:
    print(f"--- Chunk ---")
    if chunk.candidates:
        for candidate in chunk.candidates:
            for part in candidate.content.parts:
                print(f"Part type: text={bool(part.text)}, function_call={bool(part.function_call)}")
                if part.text:
                    print(f"Text content: {part.text!r}")
