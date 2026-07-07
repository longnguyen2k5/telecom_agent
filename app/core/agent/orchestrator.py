import os
from google.genai import types
from dotenv import load_dotenv
from app.schemas.chat_dto import StreamTextChunk, StreamToolStartChunk, StreamToolResultChunk, StreamDoneChunk, StreamThoughtChunk
from datetime import datetime
from langfuse import observe
from app.models.chat_schemas import ToolCallRecord
import inspect 
from app.core.gemini import get_client
from app.core.agent.registry import TOOL_REGISTRY, get_allowed_tools
from app.core.agent.prompt_factory import build_system_instruction
from app.core.utils import gemini_retry_decorator

load_dotenv()

@gemini_retry_decorator
async def safe_send_message_stream(chat_session, message_content):
    return await chat_session.send_message_stream(message_content)
            
@observe()
async def run_telecom_agent(user_message: str, session_id: str, history: list, user_role: str, user_id: str):
    # print("DEBUG: Bắt đầu gọi API Gemini...", flush=True)
    client = get_client()
    
    agent_instruction = build_system_instruction(user_role)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    agent_instruction = agent_instruction.replace("{CURRENT_TIME}", now_str)
    
    config = types.GenerateContentConfig(
        tools=get_allowed_tools(user_role),
        temperature=0.0, 
        system_instruction=agent_instruction
    ) 
    
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    chat = client.aio.chats.create(model=gemini_model, config=config, history=history)
    
    response_stream = await safe_send_message_stream(chat, user_message)
    # print("DEBUG: Đã nhận được response_stream!", flush=True)
    full_text_response = ""
    current_thought = ""  
    is_thinking = False
    executed_tools = []
    MAX_STEPS = 10  
    
    for _ in range(MAX_STEPS):
        # Danh sách để gom các tool cần gọi trong nhịp này
        tool_calls_to_execute = []
        is_thinking = False
        
        # 1. VÒNG LẶP HỨNG STREAM: Hứng hết toàn bộ để Gemini cập nhật History
        async for chunk in response_stream:
            # print(f"DEBUG: Nhận chunk: {chunk}")
            
            if chunk.function_calls:
                tool_calls_to_execute.extend(chunk.function_calls)
            
            chunk_text = ""
            if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        chunk_text += part.text

            if chunk_text:
                if "Thought:" in chunk_text: 
                    is_thinking = True
                if is_thinking:
                    if "Action:" in chunk_text or "Tool:" in chunk_text:
                        is_thinking = False
                    else:
                        current_thought += chunk_text
                        yield f"data: {StreamThoughtChunk(content=chunk_text).model_dump_json()}\n\n"
                else:  
                    full_text_response += chunk_text
                    yield f"data: {StreamTextChunk(content=chunk_text).model_dump_json()}\n\n"

        # 2. THỰC THI TOOL (Chạy sau khi đã hứng xong stream của nhịp trước)
        if tool_calls_to_execute:
            tool_response_parts = []
            
            for func_call in tool_calls_to_execute:
                start_tool = StreamToolStartChunk(name=func_call.name, args=func_call.args or {})
                yield f"data: {start_tool.model_dump_json()}\n\n"
                
            for func_call in tool_calls_to_execute:
                func_name = func_call.name
                func_args = func_call.args if func_call.args else {}
                
                
                if func_name in TOOL_REGISTRY:
                    tool_action = TOOL_REGISTRY[func_name]
                    if inspect.iscoroutinefunction(tool_action):
                        tool_result = await tool_action(func_args) # Nếu là async tool (như alarm enrich) thì await
                    else:
                        tool_result = tool_action(func_args) # Nếu là sync tool cũ thì gọi bình thường
                else:
                    tool_result = {"error": "Tool undefined"}
                    
                # Bắn tín hiệu Tool hoàn tất
                tool_results = StreamToolResultChunk(name=func_name, result=tool_result)
                
                yield f"data: {tool_results.model_dump_json()}\n\n"
                
                tool_call_record = ToolCallRecord(
                    name=func_name,
                    args=func_args,
                    result=tool_result,
                    status='success' if 'error' not in tool_result else 'error',
                    error_message=tool_result.get('error') if 'error' in tool_result else None
                )
                executed_tools.append(tool_call_record)
                
                # Đóng gói kết quả
                tool_response_parts.append(
                    types.Part.from_function_response(name=func_name, response=tool_result)
                )
                
            response_stream = await safe_send_message_stream(chat, tool_response_parts)
            
        else:
            # Nếu chạy xong vòng lặp mà không có Tool nào được gọi -> AI đã nói xong.
            break

    # 3. KẾT THÚC
    done_event = StreamDoneChunk(full_text=full_text_response, thought=current_thought, tools_used=executed_tools)
    
    yield f"data: {done_event.model_dump_json()}\n\n"

