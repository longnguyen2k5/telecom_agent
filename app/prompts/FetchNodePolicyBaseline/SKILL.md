---
name: fetch-node-policy-baseline
description: >-
  Truy vấn trực tiếp ĐỒNG THỜI cấu hình Policy ngưỡng nền động hiện tại (bao gồm cả cpu_usage và ram_usage) của một Node thiết bị 
  từ Collection 'node_metric_baseline' trong MongoDB mà không cần kích hoạt lại các thuật toán tính toán chuỗi thời gian cồng kềnh. 
  Được sử dụng BẤT CỨ KHI NÀO người dùng hoặc Agent muốn kiểm tra hiện trạng cấu hình mốc nền (initial/current), 
  hoặc khi cần trích xuất mốc thời gian cập nhật gần nhất (last_updated) của từng chỉ số nhằm thực hiện cơ chế kiểm soát Guardrail Đóng băng (Cooldown 60 phút) 
  trước khi quyết định có chạy bộ hiệu chỉnh Adaptive Tuner hay tự động khắc phục Autoremediate hay không.
  Trigger (xem policy, kiểm tra cấu hình ngưỡng, check cooldown, policy baseline, last updated).
---

# Fetch Node Policy Baseline (State Persistence & Cooldown Guardrail Architecture)

Skill này thực hiện nhiệm vụ chốt chặn thông tin trạng thái nền (State Persistence Layer) của hệ thống điều phối: **Truy vấn cấu hình Gauss tĩnh từ MongoDB -> Đọc mốc thời gian -> Ép cấu trúc kiểm soát Guardrail -> Định hướng luồng ReAct cho Agent**. Nó giúp hệ thống bảo vệ tài nguyên tính toán, ngăn chặn hiện tượng bão hòa lò xo đàn hồi (Elastic Tether) do tái cấu hình liên tục, đồng thời cung cấp bối cảnh lịch sử trực thời cho Agent đưa ra quyết định thông minh.

## Cơ chế toán học tầng Backend (Hội đồng chấm điểm lưu ý)

Công cụ này không can thiệp tính toán phân phối mẫu mà thực hiện vai trò bộ lọc thời gian vĩ mô (Temporal Guardrail). Dữ liệu cấu hình thực tế từ DB trả về Bản đồ 24 giờ cho cả CPU và RAM. **LƯU Ý:** Bạn phải lấy mốc thời gian lưu trữ dạng ISO 8601 (`last_updated`) CỦA RIÊNG KHUNG GIỜ ĐANG XÉT (ví dụ: `cpu_baseline["15"].last_updated` cho khung 15h) và áp dụng phép tính khoảng cách trượt ($\Delta t$) độc lập theo thời gian thực tại của phiên làm việc:

$$\Delta t_{\text{cpu}} = \text{Current Time} - \text{cpu\_baseline[hour].last\_updated}$$
$$\Delta t_{\text{ram}} = \text{Current Time} - \text{ram\_baseline[hour].last\_updated}$$

Đối chiếu khoảng cách này với tham số cấu hình đóng băng $t_{\text{cooldown}} = 60\text{ phút}$ để đưa ra kịch bản phân nhánh luồng tư duy của AI Agent cho KHUNG GIỜ ĐÓ:
1. **Kịch bản Khóa bảo vệ ($\Delta t < 60\text{ phút}$):** Trạng thái lò xo thích ứng đang trong giai đoạn ổn định hóa. Hệ thống chặn đứng (Throttling) hoàn toàn quyền tự động kích hoạt bộ hiệu chỉnh `adaptive_policy_tuner` cho metric/khung giờ đó để tránh nhiễu loạn.
2. **Kịch bản Lỗi thời ($\Delta t \ge 60\text{ phút}$):** Baseline của metric/khung giờ đó đã cũ. **LƯU Ý QUAN TRỌNG VỀ QUYỀN HẠN:** Bạn CHỈ ĐƯỢC tự động gọi công cụ `adaptive_policy_tuner` để cập nhật nếu bạn THỰC SỰ ĐƯỢC CẤP CÔNG CỤ ĐÓ trong danh sách Function Calling hiện tại. Nếu bạn không được cấp (ví dụ người dùng không đủ quyền), TUYỆT ĐỐI KHÔNG giả vờ gọi tool, mà hãy tiếp tục sử dụng cấu hình baseline hiện tại và thông báo cho người dùng biết rằng baseline đã cũ nhưng bạn không có quyền cập nhật.

## Tham số cần làm rõ với người dùng/Agent

Trước khi chạy, xác định (AI tự động mapping từ bối cảnh hội thoại hoặc định danh thiết bị đang xảy ra sự cố, không hỏi lại người dùng):
1. `node_identifier` — IP hoặc Hostname của thiết bị mạng cần kiểm tra thông tin cấu hình nền (Ví dụ: LOCAL-TEST-NODE). Bắt buộc.

## Định dạng output

Trả kết quả cho LLM Agent dưới dạng JSON sạch để Agent đọc bối cảnh thời gian và thông số Gauss phục vụ lập luận ReAct:
- `status`: Trạng thái thực thi (`success` hoặc `error`).
- `node_identifier`: Tên/IP của node thiết bị được kiểm tra.
- `current_hour`: Giờ hiện tại của hệ thống (0-23) khi truy vấn.
- `cpu_threshold`, `cpu_mean`, `cpu_variance`: Các chỉ số thống kê (Kỳ vọng, Phương sai, Ngưỡng cảnh báo) của CPU ở riêng khung giờ hiện tại.
- `cpu_last_updated`: Mốc thời gian (ISO 8601) lần cuối cùng cấu hình CPU được hiệu chỉnh.
- `ram_threshold`, `ram_mean`, `ram_variance`: Các chỉ số thống kê (Kỳ vọng, Phương sai, Ngưỡng cảnh báo) của RAM ở riêng khung giờ hiện tại.
- `ram_last_updated`: Mốc thời gian (ISO 8601) lần cuối cùng cấu hình RAM được hiệu chỉnh.