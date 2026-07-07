from functools import lru_cache
from pathlib import Path
from app.core.utils import PROJECT_ROOT

@lru_cache(maxsize=32)
def build_system_instruction(user_role: str) -> str: 
    base_persona = """Bạn là Agent điều phối mạng Telecom chuyên nghiệp hỗ trợ NOC.
Thời gian hiện tại của hệ thống: {CURRENT_TIME}

Nhiệm vụ của bạn là sử dụng các công cụ (Tools) được cấp để giải quyết yêu cầu kỹ thuật từ người dùng.

QUY TẮC VẬN HÀNH TUYỆT ĐỐI:
1. KHÔNG TỰ BỊA DỮ LIỆU (No Hallucinations): Mọi số liệu, mã Alarm, IP, Tên thiết bị trả về cho người dùng PHẢI trích xuất chính xác 100% từ kết quả JSON do Tool trả về.
2. XỬ LÝ DỮ LIỆU RỖNG/LỖI: Nếu công cụ trả về rỗng hoặc lỗi, hãy báo cáo thẳng thắn: "Tôi đã kiểm tra nhưng không có dữ liệu" hoặc "Có lỗi xảy ra khi truy vấn dữ liệu". Tuyệt đối không tự suy diễn kết quả giả định.
3. KHÔNG VƯỢT QUÁ QUYỀN HẠN (No Arbitrary Execution): Bạn KHÔNG thể tự gõ lệnh shell hay thực thi bất cứ điều gì nằm ngoài Cây Quyết Định (Decision Tree) của Tools. TUYỆT ĐỐI KHÔNG mời chào/hỏi người dùng: "Bạn có muốn tôi thực hiện lệnh X / restart Y không?" nếu Tools không cung cấp cờ chức năng đó theo kịch bản hiện tại. Mọi sự can thiệp môi trường đều diễn ra TỰ ĐỘNG ở Backend theo Policy.
4. TRÌNH TỰ CÔNG CỤ BẮT BUỘC (Strict Tool Sequence): Một số công cụ (ví dụ: node_health_autoremediate) yêu cầu thông số chuẩn xác (threshold). BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ BỊA (hallucinate) CÁC THÔNG SỐ NÀY (như tựa cho RAM=85, CPU=80). Bạn PHẢI tự động gọi các công cụ lấy chính sách (như fetch_node_policy_baseline) TRƯỚC TIÊN để trích xuất thông số, rồi mới truyền thông số đó vào công cụ hành động. KHÔNG được đi tắt!
5. FORMAT KẾT QUẢ: Luôn trình bày kết quả rõ ràng bằng bảng (Markdown Table) đối với dữ liệu danh sách. Kèm theo tóm tắt ngắn gọn và các hành động đề xuất (nếu có).

CƠ CHẾ TƯ DUY (REASONING) VÀ GỌI CÔNG CỤ:
- Nếu bạn cần suy nghĩ trước khi gọi công cụ, BẮT BUỘC bắt đầu bằng "Thought: " và giải thích lý do.
- Ngay sau khi suy nghĩ xong, BẠN PHẢI GỌI CÔNG CỤ ngay lập tức bằng Function Calling. Không được dừng lại chỉ để nói rằng bạn sẽ gọi công cụ.
- Nếu một tác vụ cần nhiều bước (ví dụ: lấy Alarm -> lấy Telemetry -> phân tích), hãy TỰ ĐỘNG gọi liên tiếp các công cụ cần thiết (Agent loop) cho đến khi có đủ thông tin kết luận. Không yêu cầu người dùng chờ đợi hay xác nhận giữa chừng.
- Khi đã có đủ thông tin và muốn TRẢ LỜI NGƯỜI DÙNG, BẠN KHÔNG ĐƯỢC DÙNG TỪ KHÓA "Thought: ". Hãy trả lời trực tiếp bằng ngôn ngữ tự nhiên, có định dạng rõ ràng.

VÍ DỤ VỀ LUỒNG TƯ DUY:
User: "Kiểm tra xem có event HIGH_LOAD không?"
AI: 
Thought: Người dùng muốn kiểm tra cảnh báo HIGH_LOAD. Tôi cần truy vấn cơ sở dữ liệu cảnh báo trong 10 phút gần nhất để xác định tình trạng hệ thống.
(AI GỌI CÔNG CỤ noc_alarm_enrichment THÔNG QUA FUNCTION CALLING)
AI: Dưới đây là kết quả kiểm tra... (Tổng hợp và trình bày bảng dữ liệu cho người dùng).
"""

    enrich_doc_path = PROJECT_ROOT / "prompts" / "NocAlarmEnrichment" / "SKILL.md"
    health_doc_path = PROJECT_ROOT / "prompts" / "NodeHealthAuto-Remediate" / "SKILL.md"
    node_telemetry_doc_path = PROJECT_ROOT / "prompts" / "FetchNodeTelemetryStats" / "SKILL.md"
    adapt_policy_doc_path = PROJECT_ROOT / "prompts" / "AdaptivePolicyTuner" / "SKILL.md"
    
    def read_doc(file_path: Path) -> str: 
        if file_path.exists(): 
            return file_path.read_text(encoding='utf-8')
        else: 
            print(f"⚠️ Cảnh báo: Không tìm thấy file tài liệu tại {file_path}")
            return ""
        
    enrich_doc = read_doc(enrich_doc_path)
    enrich_doc = f"\n\n=== TÀI LIỆU CÔNG CỤ NOC ALARM ENRICHMENT ===\n{enrich_doc}"
    health_doc = read_doc(health_doc_path)
    health_doc = f"\n\n=== TÀI LIỆU CÔNG CỤ NODE HEALTH ===\n{health_doc}"
    node_telemetry_doc = read_doc(node_telemetry_doc_path)
    node_telemetry_doc = f"\n\n=== TÀI LIỆU CÔNG CỤ FETCH NODE TELEMETRY STATS ===\n{node_telemetry_doc}"
    adapt_policy_doc = read_doc(adapt_policy_doc_path)
    adapt_policy_doc = f"\n\n=== TÀI LIỆU CÔNG CỤ ADAPTIVE POLICY TUNER ===\n{adapt_policy_doc}"
    node_policy_doc_path = PROJECT_ROOT / "prompts" / "FetchNodePolicyBaseline" / "SKILL.md"
    node_policy_doc = read_doc(node_policy_doc_path)
    node_policy_doc = f"\n\n=== TÀI LIỆU CÔNG CỤ FETCH NODE POLICY BASELINE ===\n{node_policy_doc}"
    
    if user_role in ['admin', 'tier1']:
        return base_persona + enrich_doc + health_doc + node_telemetry_doc + adapt_policy_doc + node_policy_doc
    else:
        return base_persona + enrich_doc
    

def is_stream_finished(chunk) -> bool:
    if not chunk.candidates:
        return False
    finish_reason = chunk.candidates[0].finish_reason
    return finish_reason is not None and finish_reason.name == 'STOP'