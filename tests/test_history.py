import sys
from app.core.agent.agent import safe_send_message_stream, build_system_instruction, get_allowed_tools
from google import genai
from google.genai import types

def run_agent_history():
    client = genai.Client()
    agent_instruction = build_system_instruction("admin")
    config = types.GenerateContentConfig(
        tools=get_allowed_tools("admin"),
        temperature=0.0, 
        system_instruction=agent_instruction
    ) 
    chat = client.chats.create(model='gemini-3.1-flash-lite', config=config)
    
    response_stream = chat.send_message_stream("kiểm tra xem gần đây có event HIGH_LOAD không?")
    tool_calls_to_execute = []
    
    for chunk in response_stream:
        if chunk.function_calls:
            tool_calls_to_execute.extend(chunk.function_calls)

    hist = chat.get_history()
    print("History length:", len(hist))
    for i, msg in enumerate(hist):
        print(f"msg[{i}] role: {msg.role}")
        if msg.parts:
            for part in msg.parts:
                if part.function_call:
                    print("  function_call:", part.function_call.name)
                elif part.text:
                    print("  text:", part.text)
                else:
                    print("  part:", part)
                
    if tool_calls_to_execute:
        parts = []
        for call in tool_calls_to_execute:
            parts.append(types.Part.from_function_response(name=call.name, response={"status": "success"}))
            
        print("Sending tool response...")
        try:
            res = chat.send_message_stream(parts)
            for r in res:
                pass
            print("Success!")
        except Exception as e:
            print("Error:", e)

run_agent_history()
