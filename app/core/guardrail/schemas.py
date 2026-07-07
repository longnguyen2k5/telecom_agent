from pydantic import BaseModel, Field

class GuardrailVerdict(BaseModel):
    is_in_scope: bool = Field(description="True nếu câu hỏi liên quan đến giám sát mạng, hạ tầng, lệnh Linux, báo động viễn thông. False nếu là chủ đề khác.")
    reason: str = Field(description="Lý do ngắn gọn tại sao duyệt hoặc từ chối câu hỏi này bằng tiếng Việt.")
