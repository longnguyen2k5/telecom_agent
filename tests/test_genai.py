import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

client = genai.Client()

def add_numbers(a: float, b: float) -> float:
    return a + b

tools = [{"function_declarations": [add_numbers]}]

chat = client.chats.create(model='gemini-3.1-flash-lite', config={'tools': tools})

stream = chat.send_message_stream("What is 10 + 25?")

tool_calls = []
for chunk in stream:
    if chunk.function_calls:
        tool_calls.extend(chunk.function_calls)
        # break

print("History after iteration:", chat.history)

if tool_calls:
    print("Tool calls found")
    parts = []
    for call in tool_calls:
        parts.append(types.Part.from_function_response(name=call.name, response={"result": 35}))
    try:
        response = chat.send_message(parts)
        print("Success! Output:", response.text)
    except Exception as e:
        print("Error:", e)
