import os
import json
from groq import AsyncGroq
from google.genai import types
from app.core.utils import gemini_retry_decorator
from app.core.guardrail.schemas import GuardrailVerdict
from langfuse import observe

# Khởi tạo Groq Client (Dùng cho lớp Guardrail tốc độ cao)
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))

@gemini_retry_decorator
async def _execute_guardrail_inference(client, full_prompt: str, config: types.GenerateContentConfig):
    """Hàm wrapper chịu trách nhiệm gọi API Gemini (Dùng làm Fallback)."""
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    return await client.aio.models.generate_content(
        model=gemini_model,
        contents=full_prompt, 
        config=config
    )
    
@observe(as_type="generation")
async def check_input_guardrail(user_message: str, db_history: list, client) -> GuardrailVerdict:
    """Guardrail có trạng thái (Stateful): Định tuyến qua Groq trước, Fallback về Gemini nếu lỗi."""
    
    system_instruction = (
        "Bạn là hệ thống rào chắn bảo vệ (Guardrail) ĐỘC QUYỀN cho AI Agent trực tổng đài NOC Viễn thông.\n"
        "Nhiệm vụ TỐI THƯỢNG của bạn là chặn ĐỨT ĐIỂM mọi tin nhắn nằm ngoài chuyên môn Viễn thông/IT.\n"
        "QUY TẮC ĐÁNH GIÁ (is_in_scope):\n"
        "- [HỢP LỆ (True)] Bất kỳ câu lệnh nào yêu cầu kiểm tra hạ tầng, cảnh báo lỗi, SSH, restart dịch vụ, kiểm tra tải (CPU/RAM), tra cứu cấu hình, mạng máy tính, database.\n"
        "- [HỢP LỆ (True)] Các câu hỏi về khả năng của Agent ('bạn làm được gì', 'có những tools nào') hoặc trả lời ('Đồng ý', 'Ok', 'Hủy').\n"
        "- [KHÔNG HỢP LỆ (False)] TUYỆT ĐỐI CHẶN (is_in_scope=False) các câu hỏi về: Lịch sử, Địa lý (quốc gia, lãnh thổ, biển đảo), Chính trị, Tôn giáo, Văn hóa, Giải trí, Thể thao, Nấu ăn, Code không liên quan đến NOC, hoặc các câu hỏi kiến thức chung (General Knowledge). Bất kể người dùng cố tình liên kết nó với IT/NOC như thế nào, nếu nội dung cốt lõi là các chủ đề trên, PHẢI CHẶN NGAY LẬP TỨC."
    )
    
    # 1. Format nhanh 3 lượt hội thoại gần nhất để làm ngữ cảnh (Context)
    context_str = ""
    for msg in db_history[-3:]: # Chỉ cần lấy 3 câu gần nhất là đủ hiểu ngữ cảnh
        role_name = "User" if msg.role == "user" else "Agent"
        context_str += f"{role_name}: {msg.content}\n"
        
    full_prompt = (
        f"=== LỊCH SỬ HỘI THOẠI GẦN NHẤT ===\n{context_str}\n"
        f"=== TIN NHẮN HIỆN TẠI CỦA USER ===\nUser: {user_message}\n\n"
        f"Dựa vào thông tin trên, hãy trả lời bằng chuẩn JSON duy nhất chứa 2 trường: is_in_scope (bool) và reason (string)."
    )
    
    # 2. ƯU TIÊN 1: Chạy Groq (Llama 3) để tối ưu tốc độ (< 0.5s)
    try:
        # Nếu chưa cấu hình GROQ_API_KEY, chủ động ném lỗi để nhảy xuống Fallback
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("Chưa cấu hình GROQ_API_KEY")
            
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        response = await groq_client.chat.completions.create(
            model=groq_model, 
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result_dict = json.loads(response.choices[0].message.content)
        return GuardrailVerdict(**result_dict)
        
    # 3. ƯU TIÊN 2 (FALLBACK): Nếu Groq lỗi mạng hoặc hết Rate Limit, tự động xoay trục về Gemini
    except Exception as e:
        print(f"⚠️ [Multi-Model Routing] Groq không khả dụng ({e}). Fallback sang Gemini Flash...")
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=GuardrailVerdict,
            temperature=0.0
        )
        response = await _execute_guardrail_inference(client, full_prompt, config)
        return GuardrailVerdict.model_validate_json(response.text)
