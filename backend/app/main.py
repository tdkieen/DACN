from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1.api import api_router
from app.seed.seed_data import seed_database

# Khởi tạo bảng cơ sở dữ liệu nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

# Tự động nạp dữ liệu mẫu nếu DB đang trống
db = SessionLocal()
try:
    seed_database(db)
except Exception as e:
    print(f"[WARN] Luu y khi khoi tao seed data: {e}")
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Hệ thống AI Procurement Agent & Quản lý tồn kho Quán cà phê
    Đồ án Chuyên ngành Khoa CNTT - Đại học HUTECH
    
    ### Tính năng chính (Đến Tuần 4):
    * **Quản lý tồn kho & Điểm đặt hàng lại (ROP):** Cảnh báo ĐỎ (Nguy cơ thiếu), VÀNG (Tồn dư), XANH (An toàn).
    * **Quản lý Nhà cung cấp & Bảng báo giá đa tiêu chuẩn:** So sánh giá, lead time, MOQ, điểm chất lượng.
    * **Thuật toán MCDM:** Đánh giá xếp hạng Nhà cung cấp tối ưu.
    * **Quản lý Lô hàng & Cảnh báo hạn sử dụng:** Theo dõi chi tiết HSD từng lô.
    * **Thống kê & Dự báo Dashboard:** Thẻ chỉ số tổng quan, biểu đồ xu hướng 12 tháng, dự báo 7 ngày.
    * **Phiếu đề xuất mua hàng AI (Human-in-the-loop):** Phê duyệt / Từ chối / Sửa đề xuất.
    """,
    version="1.0.0"
)

# Cấu hình CORS cho Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hỗ trợ linh hoạt cho localhost:3000 và các IP nội bộ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Router API V1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Hệ thống"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_v1": settings.API_V1_STR
    }

@app.get("/health", tags=["Hệ thống"])
def health_check():
    return {"status": "healthy"}
