---
name: fetch-node-telemetry-stats
description: >-
  Truy vấn Collection 'node_telemetry_history' (Dữ liệu chuỗi thời gian - Time-series) trong MongoDB 
  để cào dữ liệu trạng thái hiệu năng của một thiết bị trong một cửa sổ thời gian (window_minutes). 
  Backend sẽ lọc các bản ghi liên tục, gom mảng số thực và áp dụng công thức Phương sai mẫu có hiệu chỉnh 
  (Bessel's Correction với n-1 bậc tự do) để tính toán ra Kỳ vọng mẫu (observed_mean) và Phương sai mẫu (observed_variance). 
  Dùng skill này BẤT CỨ KHI NÀO người dùng hoặc hệ thống muốn "thống kê tải thực tế của node", "tính toán kỳ vọng/biến động 
  của RAM/CPU", hoặc khi cần chuẩn bị số liệu đầu vào sạch, định lượng để mớm cho Tool điều chỉnh Policy ngưỡng động (Tool 3).
  Trigger cho cả tiếng Việt lẫn tiếng Anh (telemetry, stats, thống kê, biến động tải, mean, variance, time-series).
---

# Node Telemetry Stats (Performance & Time-Series Architecture)

Skill này thực hiện nhiệm vụ thu thập và xử lý số liệu nền hiệu năng hệ thống: **Đọc chuỗi thời gian liên tục trong MongoDB -> Lọc rác -> Tính toán thống kê có hiệu chỉnh bậc tự do -> Trả về phân phối mẫu thực tế**. Nó giúp hệ thống có cái nhìn toàn cảnh về hành vi hạ tầng kể cả lúc chạy bình thường lẫn lúc lỗi, triệt tiêu hoàn toàn hiện tượng sai lệch lựa chọn (Selection Bias) khi tính toán ngưỡng động.

## Cơ chế toán học tầng Backend (Hội đồng chấm điểm lưu ý)

Khi quét dữ liệu trong cửa sổ thời gian (ví dụ: 60 phút qua), Backend thu được n điểm đo từ bảng 'node_telemetry_history'. Do chúng ta lấy mẫu ngắn hạn trên một cửa sổ thời gian trượt, dữ liệu bị mất đi 1 bậc tự do để neo giữ tâm. Nếu chia cho n, phương sai sẽ bị lệch dưới (underestimate). Do đó, phương sai mẫu bắt buộc phải áp dụng Hiệu chỉnh Bessel (Bessel's Correction - chia cho n-1):

1. Kỳ vọng mẫu (observed_mean): Trung bình cộng của n điểm đo, đại diện cho mức tải nền thực tế hiện tại của Node.
2. Phương sai mẫu (observed_variance): Tính bằng tổng bình phương độ lệch chia cho (n - 1). Đại diện cho năng lượng biến động và độ ổn định của tải. Nếu phương sai cực nhỏ -> Tải xác lập trạng thái tĩnh mới (Concept Drift thật). Nếu phương sai rất lớn -> Hệ thống đang nhiễu loạn/Spam ngắn hạn.

## Tham số cần làm rõ với người dùng/Agent

Trước khi chạy, xác định (AI tự động mapping từ ngữ cảnh hoặc kết quả Tool 1, không hỏi lại nếu đã có):
1. node_identifier — IP hoặc Hostname của thiết bị cần quét số liệu (Ví dụ: LOCAL-TEST-NODE). Bắt buộc.
2. metric_type — Loại tài nguyên hiệu năng cần làm thống kê. Ràng buộc chặt chẽ trong phạm vi: ["ram_usage", "cpu_usage"]. Bắt buộc.
3. window_minutes — Cửa sổ thời gian quét ngược về quá khứ tính bằng phút để gom mẫu. Mặc định là 60 phút.

## Định dạng output

Trả kết quả cho LLM Agent dưới dạng JSON sạch để làm tham số mồi cho bước tiếp theo, gồm:
- node_identifier: Tên/IP của node.
- metric_type: Loại tài nguyên đã trích xuất.
- window_minutes: Cửa sổ thời gian lấy mẫu.
- sample_count: Số lượng mẫu đo nhặt được trong DB (Giá trị n).
- observed_mean: Giá trị trung bình float tính được từ code Python.
- observed_variance: Giá trị phương sai float (đã hiệu chỉnh n-1) tính được từ code Python.
