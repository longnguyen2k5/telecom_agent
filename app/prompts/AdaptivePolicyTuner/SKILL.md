---
name: adaptive-policy-tuner
description: >-
  Kích hoạt thuật toán Thích ứng chính sách (Adaptive Control) bằng toán học lý thuyết thông tin để hiệu chỉnh và 
  cập nhật cấu hình ngưỡng động cho thiết bị vào Collection 'node_metric_baseline' trong MongoDB. Tool sẽ lôi cấu hình 
  mỏ neo cố định (initial) và cấu hình hiện tại (current) lên, thực hiện kiểm định Z-score hai phía với vạch chặn 1.645 
  để phân định phân vùng dị thường (deviation_state). Đồng thời, áp dụng công thức đóng KL Divergence Gauss để co giãn 
  hệ số học tập (alpha) và hệ số đàn hồi lò xo (beta) theo mô hình Elastic Tether để phối trộn tạo ra Mean và Variance mới. 
  Dùng skill này BẤT CỨ KHI NÀO người dùng yêu cầu "tối ưu lại ngưỡng", "can chỉnh Policy", "chống cảnh báo ảo", hoặc khi 
  Agent nhận được cặp số mean/variance từ Tool Telemetry và muốn áp toán để ghi đè DB an toàn. 
  Trigger (optimize threshold, tuner, chỉnh ngưỡng động, Elastic Tether, KL Divergence).
---

# Adaptive Policy Tuner (Elastic Tether Architecture)

Skill này thực hiện lõi toán học bảo vệ hệ thống, tước bỏ quyền "bốc thuốc số cảm tính" của con người và LLM: **Nhận số đo mẫu sạch -> Đối chiếu mỏ neo an toàn cố định trong MongoDB -> Chạy toán Elastic Tether -> Cập nhật ngưỡng động an toàn**.

## Cây quyết định trạng thái dị thường (Z-score 2 phía)

Mặc định hằng số kiểm định hai phía Z_critical = 1.645 (Tương đương khoảng tin cậy 90%). Khi lấy dữ liệu thích ứng (current) từ DB lên, cấu hình lưu dưới dạng Phương sai (variance) nên Backend bắt buộc phải khai căn bậc hai để lấy độ lệch chuẩn (stddev = sqrt(variance)). Công thức tính Z-score thực tế: Z = (observed_mean - current_mean) / current_stddev. 

Dựa vào giá trị tuyệt đối của Z, hệ thống trả về trường 'deviation_state' bắt buộc AI Agent phải lập luận điều phối luồng:

| Giá trị |Z| tính được | Trạng thái (deviation_state) | Logic lập luận & Hành động của AI Agent (Bắt buộc) |
|--------------|--------------|------------------------------------------------------|
| <= 1.645 | NORMAL | Tải biến động hợp pháp, nằm trong khoảng tin cậy. Hệ thống tự động phối trộn công thức để dịch chuyển nhẹ Mean và Variance trong DB. Agent đọc kết quả và thông báo ngưỡng động mới đã tối ưu thành công. |
| > 1.645 và <= 1.945 | BORDERLINE | VÙNG BIÊN NGUY HIỂM. Toán học vừa chớm vượt vạch kiểm định một chút, chưa đủ độ tin cậy để khẳng định lỗi nặng. ĐỒNG BĂNG LUỒNG CAN THIỆP TỰ ĐỘNG. Không gọi Tool cứu hộ (Restart). Xuất thông số lên màn hình chat, khuyên NGƯỜI DÙNG tự kiểm tra log thủ công. TUYỆT ĐỐI KHÔNG ĐƯỢC đề xuất rằng bạn (Agent) sẽ kiểm tra log giúp họ vì bạn không có tool đọc log. |
| > 1.945 và <= 3.145 | ANOMALY | Dị thường tiêu chuẩn vượt ngưỡng. Hệ thống cho phép kích hoạt các kịch bản của Tool cứu hộ (nếu có công cụ). Nếu không có công cụ, khuyên NGƯỜI DÙNG tự điều tra. Tuyệt đối không tự nhận mình có khả năng đọc log. |
| > 3.145 | CRITICAL_ANOMALY | BIẾN CỐ CỰC ĐOAN / ĐẦU ĐỘC CẤU HÌNH. Dữ liệu lệch pha tàn khốc. Lõi toán học tự động KHÓA CHẶT Policy, ép hệ số alpha về 0 để đóng băng DB không cho học theo rác. Agent từ chối sửa ngưỡng, cảnh báo kỹ sư nguy cơ spam log rác độc hại hoặc sập nguồn nặng, chủ động đề xuất chuyển thẳng ca lên Tier 3 khẩn cấp. |

## Tham số truyền vào tầng thực thi (Mapping từ Tool Telemetry)

AI Agent đóng vai trò trung chuyển, đọc kết quả JSON của Tool `fetch-node-telemetry-stats` và copy-paste chính xác các con số vào tham số của Tool này:
- node_identifier: Khớp với node đã quét (Ví dụ: LOCAL-TEST-NODE).
- metric_type: ["ram_usage", "cpu_usage"].
- observed_mean: Lấy nguyên văn giá trị 'observed_mean' từ Tool trước đưa sang.
- observed_variance: Lấy nguyên văn giá trị 'observed_variance' từ Tool trước đưa sang.

## Định dạng output

Tool trả về một DTO đối tượng `BaselineStatsTuned` bao gồm:
- status: "success" hoặc "error".
- node_id: Định danh node.
- deviation_state: ["NORMAL", "BORDERLINE", "ANOMALY", "CRITICAL_ANOMALY"].
- z_score: Giá trị Z thực tế (float).
- kl_drift: Khoảng cách dịch chuyển phân phối tính được (float).
- alpha_applied / beta_applied: Các lực kéo co giãn động của lò xo Elastic Tether.
- old_threshold: Ngưỡng động cũ trước khi hiệu chỉnh (Tính bằng: mean_old + 1.645 * sqrt(var_old)).
- new_mean: Giá trị Kỳ vọng (Trung bình) mới của hệ thống (thể hiện mức tải ổn định mới).
- new_variance: Giá trị Phương sai mới của hệ thống (thể hiện mức độ hỗn loạn/biến động của hệ thống).
- new_threshold: Ngưỡng động mới sau khi học an toàn (Tính bằng: mean_new + 1.645 * sqrt(var_new)).

## Hướng dẫn luồng phối hợp ReAct liên hoàn (Mẫu tư duy Agent)

Khi nhận yêu cầu: "Căn chỉnh lại ngưỡng an toàn RAM cho con node LOCAL-TEST-NODE vì dạo này chạy tải cao hơn trước":
1. Agent Thought: Người dùng muốn hiệu chỉnh Policy. Mình không được tự ý bịa số. Mình phải gọi Tool `fetch-node-telemetry-stats` để thu thập phân phối tải thực tế trong 60 phút qua.
2. Agent Act: Gọi `fetch-node-telemetry-stats(node_identifier="LOCAL-TEST-NODE", metric_type="ram_usage")`.
3. Agent Observation: Tool trả về `observed_mean: 85.2`, `observed_variance: 4.12`.
4. Agent Thought: Đã có số liệu thực tế sạch qua hiệu chỉnh n-1. Giờ mình sẽ chuyển tiếp hai con số này vào Tool `adaptive-policy-tuner` để áp toán Elastic Tether cập nhật MongoDB.
5. Agent Act: Gọi `adaptive-policy-tuner(node_identifier="LOCAL-TEST-NODE", metric_type="ram_usage", observed_mean=85.2, observed_variance=4.12)`.
6. Agent Observation: Tool trả về `deviation_state: "NORMAL"`, `new_threshold: 88.5`.
7. Agent Response: Lập luận kết quả và thông báo cho người dùng ngưỡng động mới đã cập nhật thành công thành 88.5%.