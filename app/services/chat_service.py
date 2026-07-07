from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from app.db.repositories.session_repo import get_session_history
from app.db.repositories.chat_repo import save_message
from app.core.agent.orchestrator import run_telecom_agent
from google.genai import types
from app.core.gemini import get_client
from app.core.guardrail.guardrail import check_input_guardrail
from app.schemas.chat_dto import StreamTextChunk, StreamDoneChunk
import json


class ChatService: 
    @staticmethod
    async def process_chat(request, user, background_tasks: BackgroundTasks): 
        db_history = await get_session_history(request.session_id, user.get("id"), limit=10)
        client = get_client()
        verdict = await check_input_guardrail(request.message, db_history, client)
        
        if not verdict.is_in_scope:
            async def reject_response_generator():
                content_msg = f"❌ **Yêu cầu bị chặn:** {verdict.reason}"
                yield f"data: {StreamTextChunk(content=content_msg).model_dump_json()}\n\n"
                yield f"data: {StreamDoneChunk(full_text=content_msg, thought='', tools_used=[]).model_dump_json()}\n\n"
            return StreamingResponse(reject_response_generator(), media_type="text/event-stream")
        
        history_for_sdk = []
        for msg in db_history: 
            role = "model" if msg.role in ["assistant", "model"] else "user"
            history_for_sdk.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        
        safe_user_id = getattr(user, "id", user.get('sub'))
        background_tasks.add_task(save_message, request.session_id, safe_user_id, role='user', content=request.message)
        
        roles = getattr(user,'realm_roles', user.get('roles', ['tier2']))
        current_role = 'tier1' if set(['admin', 'tier1']).intersection(roles) else 'tier2'
        
        agent_results = run_telecom_agent(
            user_message=request.message,
            session_id=request.session_id,
            history=history_for_sdk,
            user_role=current_role,
            user_id=safe_user_id
        )
        async def response_generator(): 
            full_assistant_data = {} 
            
            async for event in agent_results:
                yield event
                
                data = json.loads(event.replace("data: ", ""))
                if data['type'] == 'done': 
                    full_assistant_data = data
            
            if full_assistant_data:
                background_tasks.add_task(
                    save_message, 
                    request.session_id, 
                    safe_user_id, 
                    role='assistant', 
                    content=full_assistant_data['full_text'],
                    thought=full_assistant_data.get('thought'),
                    tool_calls=full_assistant_data.get('tools_used')
                )
                
        return StreamingResponse(response_generator(), media_type="text/event-stream")
    