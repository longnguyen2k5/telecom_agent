# Telecom Agent

**Telecom Agent** là một hệ thống AI Agent dành cho lĩnh vực viễn thông. Hệ thống có khả năng tự động giám sát, chẩn đoán lỗi (self-healing diagnostics), khám phá dịch vụ tự động (auto-discovery) và điều chỉnh chính sách cảnh báo linh hoạt (adaptive policy tuning) dựa trên dữ liệu telemetry.

## 🌟 Tính năng chính

- **Chatbot AI tương tác:** Giao diện người dùng trực quan, hỗ trợ quản lý session (tạo mới, đổi tên, xóa mềm - soft delete).
- **Tự động chẩn đoán (Self-healing Diagnostics):** Thu thập dữ liệu từ các node mạng, phân tích sức khỏe (Node Health Output) và tự động đưa ra phương án xử lý hoặc phát hiện lỗi.
- **Điều chỉnh chính sách tự động (Adaptive Policy Tuner):** Phân tích dữ liệu lịch sử và thay đổi ngưỡng cảnh báo một cách thông minh nhằm hạn chế báo động giả.
- **Giám sát & Log (Langfuse):** Tích hợp Langfuse để theo dõi lịch sử tương tác của LLM, hỗ trợ đánh giá và debug hiệu quả.
- **Quản lý Định danh & Truy cập (IAM):** Sử dụng Keycloak để quản lý xác thực và phân quyền người dùng.

## 💻 Công nghệ sử dụng

- **Frontend:** React (Vite), Tailwind CSS, React Router, Lucide React, Axios.
- **Backend:** FastAPI (Python), Motor (Async MongoDB Driver).
- **Cơ sở dữ liệu:** MongoDB (lưu trữ session/tin nhắn), PostgreSQL (dành cho Keycloak).
- **Hạ tầng & Triển khai:** Docker & Docker Compose.
- **Bảo mật / Auth:** Keycloak.
- **Khác:** Langfuse (LLM Observability).

## 📂 Cấu trúc dự án

```text
telecom-agent/
├── app/                  # Mã nguồn Backend (FastAPI)
│   ├── api/              # Định nghĩa các Router API
│   ├── core/             # Cấu hình lõi (Settings, Security)
│   ├── db/               # Kết nối Database (MongoDB)
│   ├── models/           # Các Model Pydantic / DB
│   ├── prompts/          # Chứa các file system prompt, SKILL.md cho Agent
│   ├── scripts/          # Script phụ trợ (VD: alarm_simulator.py)
│   ├── services/         # Logic xử lý nghiệp vụ, giao tiếp với LLM
│   ├── tools/            # Các công cụ (tools) mà Agent có thể gọi
│   └── main.py           # Điểm vào (Entry point) của FastAPI
├── frontend/             # Mã nguồn Frontend (React + Vite)
│   ├── src/
│   │   ├── components/   # Các UI Component (SessionList, ChatBubble,...)
│   │   └── ...
│   └── package.json
├── infrastructure/       # Các file cấu hình hạ tầng
│   ├── keycloak/         # Cấu hình realm và data cho Keycloak
│   └── mock_target_node/ # Container giả lập một node mạng đích qua SSH
├── docs/                 # Tài liệu dự án (Slide Reveal.js, báo cáo kỹ thuật, v.v.)
├── tests/                # Các kịch bản kiểm thử (Testing scripts)
├── docker-compose.yml    # Cấu hình chạy các dịch vụ hạ tầng (MongoDB, Keycloak, Mock Node)
├── requirements.txt      # Các thư viện Python cần thiết cho Backend
└── .env                  # Biến môi trường
```

## ⚙️ Yêu cầu hệ thống

- **Docker & Docker Compose** (để chạy database và hệ thống giả lập)
- **Node.js** (>= 18.x) và **npm/yarn/pnpm** (để chạy Frontend)
- **Python** (>= 3.10) (để chạy Backend)

## 🚀 Hướng dẫn cài đặt và chạy ứng dụng

### 1. Khởi chạy hạ tầng (Database, Keycloak, Mock Node)

Chạy các container môi trường thông qua Docker Compose:

```bash
docker-compose up -d
```
> **Lưu ý:** Lần đầu chạy có thể mất một chút thời gian để tải image và Keycloak import cấu hình ban đầu. Các dịch vụ sẽ bao gồm: MongoDB (Port 27017), Keycloak (Port 8080), PostgreSQL (cho Keycloak) và một Mock Target Node (Port 2222).

### 2. Cài đặt và khởi chạy Backend (FastAPI)

Tạo môi trường ảo và cài đặt thư viện:

```bash
# Tạo và kích hoạt môi trường ảo (Virtual Environment)
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Khởi chạy server Backend
uvicorn app.main:app --reload --port 8000
```
Backend sẽ chạy tại: `http://localhost:8000` (API documentation tại `http://localhost:8000/docs`).

### 3. Cài đặt và khởi chạy Frontend (React Vite)

Mở một terminal mới:

```bash
cd frontend

# Cài đặt thư viện
npm install

# Khởi chạy server Frontend
npm run dev
```
Frontend sẽ chạy tại: `http://localhost:5173` (hoặc port được hiển thị trên terminal).

## 🛠️ Biến môi trường (.env)

Đảm bảo bạn đã cấu hình file `.env` tại thư mục gốc của dự án. Một số biến quan trọng cần có (tham khảo `.env.example` nếu có):

```env
# LLM
GEMINI_MODEL=gemini-3.1-flash-lite
GOOGLE_API_KEY=google-api-key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=groq-api-key

# Langfuse
LANGFUSE_SECRET_KEY=langfuse-secret-key
LANGFUSE_PUBLIC_KEY=langfuse-public-key
LANGFUSE_BASE_URL=langfuse-base-url

# Mật khẩu của các node mà mình định nghĩa nó để có thể lấy được bằng credential key trong db
PASS_LOCAL_TEST=your_pass_local_test

# Keycloak
KEYCLOAK_URL=http://localhost:8080
REALM_NAME=your_realm_name
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
ADMIN_CLIENT_ID=your_admin_client_id
ADMIN_CLIENT_SECRET=your_admin_client_secret
KEYCLOAK_CALLBACK_URL=http://localhost:5173

# MongoDB
MONGODB_URL=mongodb://localhost:27017
```
