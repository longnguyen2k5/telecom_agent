---
name: noc-alarm-enrichment
description: >-
  Điều tra và làm giàu (enrich) cảnh báo NOC theo quy trình 3 bước sử dụng MongoDB: 
  (1) Query Collection cảnh báo từ MongoDB trong một cửa sổ thời gian, 
  (2) chạy hàm trích xuất entity (IP, tên NE, interface, AS, VLAN) từ trường content,
  (3) dùng các entity đó tra cứu chéo với Collection hạ tầng (ne_inventory) để lấy
  site_id, segment, vendor, đội trực... 
  Dùng skill này BẤT CỨ KHI NÀO người dùng muốn soi/điều tra/đào sâu một loại cảnh báo, 
  "lọc cảnh báo theo type", bóc thông tin trong content cảnh báo, map cảnh báo sang site/đội trực.
  Trigger cho cả tiếng Việt lẫn tiếng Anh (alarm, alert, NOC, cảnh báo, enrich, correlation).
---

# NOC Alarm Enrichment (MongoDB Architecture)

Skill này thực hiện một pipeline điều tra cảnh báo NOC quen thuộc: **lọc theo loại → bóc
thông tin trong content → tra bảng tham chiếu để biết cảnh báo này thuộc về đâu**. Mục tiêu
là biến một đống cảnh báo free-text thành bảng có cấu trúc, gắn được vào site/topology để
phục vụ điều tra và correlation.

Pipeline gồm 3 bước, chạy tuần tự, mỗi bước feed bước sau:

```text
[Bước 1] MongoDB (core_alarm_history): lấy cảnh báo theo alarm_type + cửa sổ thời gian
            │  (alarm_id, content, ne_name, ...)
            ▼
[Bước 2] extract_content.py: bóc entity từ content
            │  (ips, ne_names, interfaces, cell_ids, as_numbers, vlans, kv) + lookup_keys
            ▼
[Bước 3] MongoDB (ne_inventory): tra cứu Collection hạ tầng bằng lookup_keys ($in)
            │  (site_id, segment, vendor, oncall_team, ...)
            ▼
        Cảnh báo đã enrich (map ngược về từng alarm_id)
```

## Tham số cần làm rõ với người dùng

Trước khi chạy, xác định (hỏi nếu thiếu, nhưng đừng hỏi cái đã suy ra được):

1. **alarm_type** — loại cảnh báo cần điều tra (vd `LINK_DOWN`, `HIGH_LOAD`). Bắt buộc.
2. **window_min** — cửa sổ thời gian tính bằng phút. Mặc định `10` (khớp ngưỡng tương quan 10 phút).
3. **Collection thật** — tên Collection cảnh báo (mặc định `core_alarm_history`) và tham chiếu
   (mặc định `ne_inventory`), cùng tên trường. Đây là thứ HAY khác nhau giữa các môi trường.
4. **Khoá lookup** — field nào trong kết quả bước 2 dùng để tra bước 3. Mặc định `ips,ne_names`.
5. **"Lấy ra cái gì"** ở bước 3 — các trường muốn enrich (site_id, segment, vendor, oncall_team...).

## Cách chạy

Hai script nằm trong `scripts/`. Có thể chạy thủ công từng bước hoặc dùng orchestrator.

### Bước 2 — hàm trích xuất (chạy độc lập được)

`scripts/extract_content.py` chỉ dùng thư viện chuẩn, luôn chạy được.

```bash
# Một chuỗi content
python3 scripts/extract_content.py --text "<nội dung cảnh báo>"

# Batch: file JSONL, mỗi dòng 1 cảnh báo có trường content
python3 scripts/extract_content.py --input alarms.jsonl --content-field content
```

Output (chế độ batch) là JSONL: mỗi bản ghi gốc được thêm `extracted` và `lookup_keys`.
Danh sách khoá gộp của cả batch in ra **stderr** dạng `LOOKUP_KEYS=[...]` để copy nhanh sang bước 3.

Mở rộng/ghi đè pattern mà KHÔNG sửa code: tạo file JSON rồi truyền `--patterns`:

```json
{ "circuit_id": { "regex": "(?i)\\bcircuit[ :=#-]*([A-Z0-9-]+)", "group": 1 } }
```

`group: 0` = lấy toàn bộ khớp; `group: 1` = lấy nhóm bắt. Field trùng tên sẽ ghi đè mặc định.

### Cả pipeline — orchestrator

`scripts/run_enrichment.py` nối cả 3 bước. **Xem Query trước khi bắn thật** bằng `--dry-run`
(không cần kết nối DB thực):

```bash
python3 scripts/run_enrichment.py --alarm-type LINK_DOWN --window-min 10 --dry-run
```

Chạy thật cần đảm bảo MongoDB đang hoạt động ở Localhost (chi tiết trong đầu file script):

```bash
pip install pymongo
python3 scripts/run_enrichment.py --alarm-type LINK_DOWN --window-min 10 --limit 500
```

Các đối tượng truy vấn MongoDB của bước 1 và bước 3 được định nghĩa trực tiếp trong script (`query_step_1`, `query_step_3`). Hệ thống sử dụng toán tử `$gte` cho thời gian và `$in` với mảng `lookup_keys` để tối ưu hóa việc tra cứu chéo.

## Định dạng output

Trả kết quả cuối cho người dùng dưới dạng JSON (một object cho mỗi cảnh báo), gồm:

- Các trường gốc từ bước 1: `alarm_id`, `content`, `ne_name`, `severity`, `last_seen`.
- `extracted`: dict các entity bóc được ở bước 2.
- `lookup_keys`: danh sách khoá đã dùng để tra bước 3.
- `enrichment`: danh sách bản ghi tham chiếu khớp được (site_id, segment, vendor, oncall_team...).
- Các chuỗi mô phỏng truy vấn MongoDB để hỗ trợ debug.

Khi tóm tắt cho người dùng, ngoài JSON hãy nêu ngắn gọn các phát hiện đáng chú ý: ví dụ
nhiều cảnh báo cùng trỏ về một `site_id`, hay một `oncall_team` đang ôm phần lớn cảnh báo —
đó thường là tín hiệu cho bước correlation hoặc autoremediate tiếp theo.

**QUY TRÌNH CHUẨN XỬ LÝ CẢNH BÁO HIGH_LOAD:**
Tuyệt đối KHÔNG đề xuất thực hiện SSH (`node_health_autoremediate`) ngay lập tức khi thấy `HIGH_LOAD`. BẮT BUỘC phải đề xuất kiểm tra xem đây có phải cảnh báo ảo hay không bằng cách sử dụng `fetch_node_policy_baseline` và `fetch_node_telemetry_stats`. Chỉ khi xác định tải thực tế vượt ngưỡng quy định, mới đề xuất SSH để can thiệp.

## Ví dụ

**Input (yêu cầu người dùng):**
> "Soi giúp tôi cảnh báo LINK_DOWN trong 10 phút qua, xem chúng rơi vào site/đội nào."

**Cách skill xử lý:**
1. Bước 1: query `core_alarm_history` với `alarm_type='LINK_DOWN'`, logic `$gte` time.
2. Bước 2: với mỗi `content`, chạy `extract_content` → thu `ips` + `ne_names` làm `lookup_keys`.
3. Bước 3: query `ne_inventory` dùng toán tử `$or` kết hợp `$in` → lấy `site_id`,
   `segment`, `oncall_team`.
4. Map ngược `enrichment` về từng cảnh báo, in JSON + tóm tắt site/đội nổi bật.

**Một dòng content và entity bóc được:**
Input: `Interface GigabitEthernet0/0/1 on NE HNI-CORE-01 (10.211.140.16) is DOWN; peer AS65001; cell HNI_0231`
Output: `ips=["10.211.140.16"]`, `ne_names=["HNI-CORE-01"]`, `interfaces=["GigabitEthernet0/0/1"]`,
`cell_ids=["HNI_0231"]`, `as_numbers=["65001"]`, `lookup_keys=["10.211.140.16","HNI-CORE-01"]`.

## Lưu ý & xử lý sự cố

- **Bước 3 không khớp gì** thường do (a) định dạng tên NE trong content khác trong inventory
  (vd có hậu tố domain, viết hoa/thường khác), hoặc (b) pattern `ne_names` bỏ sót dạng tên lạ.
  Cách xử lý: thêm pattern qua `--patterns`, hoặc đổi `--key-fields` sang chỉ `ips` nếu IP đáng tin hơn.
- **Pattern `ne_names` mặc định** yêu cầu ≥3 đoạn (REGION-ROLE-INDEX) để giảm nhiễu và đã loại
  các token kiểu `AS-xxxx`/`VLAN-xxxx`. Nếu hệ thống dùng tên 2 đoạn (vd `CORE-01`), hãy nới
  pattern qua `--patterns`.
- **Luôn `--dry-run` trước** khi chạy thật để soát lại cú pháp Query và tên Collection — đây là chỗ dễ sai nhất.
- **Đừng nối chuỗi khi tra cứu.** Bước 3 sử dụng cơ chế gom toàn bộ khóa truyền vào mảng `$in` để giải quyết vấn đề hiệu suất N+1 thay vì mở connection liên tục cho từng cảnh báo.
- **Mở rộng sang cross-segment correlation:** sau khi có `site_id`, bạn có thể chỉ định Agent tổng hợp cảnh báo theo
  `(site_id, time_bucket)` trên RAM để bắt nhiều segment cùng kêu tại một site.