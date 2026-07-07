from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.db.mongodb import db
from app.api.router import api_router 
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware 

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # Kết nối DB
    db.client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = db.client["telecom_agent_db"]
    
    # Tạo Index
    await database["messages"].create_index("session_id")
    await database["sessions"].create_index("user_id")
    print("✅ MongoDB connected & Indexes created.")
    
    yield  # Ứng dụng chạy ở đây
    
    # --- SHUTDOWN ---
    db.client.close()
    print("🔌 MongoDB connection closed.")

app = FastAPI(title="Telecom AI Agent API", lifespan=lifespan)

origins = [
    "http://localhost:3000",    # Port mặc định của React CRA
    "http://localhost:5173",    # Port mặc định của React Vite (để sẵn cho chắc)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Cho phép các URL React này gọi tới
    allow_credentials=True,           # Cho phép gửi kèm Cookie/Token xác thực
    allow_methods=["*"],              # Cho phép tất cả các hàm GET, POST, PUT, DELETE
    allow_headers=["*"],              # Cho phép tất cả các Header (Authorization, Content-Type...)
)

# Register routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Telecom AI Agent is running!"}