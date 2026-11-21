# DACN – AI Procurement Agent & Quản Lý Tồn Kho Quán Cà Phê

> **Đồ án Chuyên ngành – Khoa Công nghệ Thông tin – Trường Đại học Công nghệ TP.HCM (HUTECH)**  
> **Giảng viên hướng dẫn:** ThS. Trịnh Công Nhựt  
> **Lớp:** 23DTHD1  

### Thành viên nhóm thực hiện:
| STT | Họ và tên | MSSV | Vai trò chính |
| :---: | :--- | :---: | :--- |
| 1 | **Ngô Kế Nhật Trường** | `2380602390` | **AI & Data Engineer** (Dự báo nhu cầu, Thuật toán MCDM, LLM Agent) |
| 2 | **Tăng Duy Kiên** | `2380601131` | **Backend & Database Architect** (FastAPI, SQLAlchemy, PostgreSQL, Docker) |
| 3 | **Trần Anh Hào** | `2380600595` | **Frontend Engineer** (Reflex Python Framework, UI/UX Dashboard, Recharts) |

---

## 1. GIỚI THIỆU DỰ ÁN & GIÁ TRỊ CỐT LÕI

Hệ thống giải quyết bài toán sống còn trong quản lý vận hành chuỗi F&B (Quán cà phê): **Cân bằng giữa việc KHÔNG ĐƯỢC THIẾU HÀNG** (làm gián đoạn phục vụ khách) và **KHÔNG ĐƯỢC TỒN DƯ QUÁ MỨC** (tránh hư hỏng hạn dùng ngắn của sữa, trái cây và chống đọng vốn lưu động).

```
[POS Bán hàng] ──> [Định mức BOM] ──> [Tồn kho thực tế] ──> [Dự báo 7 ngày (Prophet/XGBoost)]
                                                                     │
[Quản lý duyệt (Human-in-the-loop)] <── [AI Procurement Agent] <──────┴── [MCDM So sánh NCC]
```

### 4 Nghiệp vụ cốt lõi:
1. **Bóc tách định mức BOM (Bill of Materials):** Quy đổi tự động từ số ly đồ uống bán ra thành lượng gram/ml/đơn vị nguyên liệu tiêu hao thực tế.
2. **Dự báo nhu cầu 7 ngày tới (AI Forecasting):** Sử dụng các mô hình chuỗi thời gian phân tích mùa vụ, thời tiết, sự kiện cuối tuần để dự báo chính xác nhu cầu 7 ngày kế tiếp.
3. **Cảnh báo tồn kho & Điểm đặt hàng lại (ROP):**  
   $$\text{ROP} = \text{Lead Time Demand} + \text{Safety Stock}$$
   Tự động phát hiện cảnh báo **ĐỎ** (Nguy cơ thiếu hàng), **VÀNG** (Tồn dư đọng vốn / Sắp hết hạn) và **XANH** (An toàn).
4. **Trợ lý mua hàng thông minh (AI Procurement Agent):**  
   Tự động so sánh các Nhà cung cấp dựa trên Đơn giá, Thời gian giao hàng (Lead time), Số lượng đặt tối thiểu (MOQ) và Độ uy tín (Thuật toán MCDM). AI Agent lập luận rõ lý do đề xuất để **Quản lý cửa hàng phê duyệt (Human-in-the-loop)**.

---

## 2. KIẾN TRÚC CÔNG NGHỆ (FULL-STACK PYTHON)

Toàn bộ hệ thống được xây dựng trên hệ sinh thái **Python hiện đại**, giúp đồng nhất mã nguồn giữa AI, Backend và Frontend:

* **Backend RESTful API:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12), Pydantic v2, SQLAlchemy 2.0 ORM.
* **Frontend Web App:** [Reflex](https://reflex.dev/) (Python Full-stack) – Viết 100% bằng Python nhưng biên dịch ngầm ra React, TailwindCSS, Radix Themes và Recharts.
* **Cơ sở dữ liệu:** PostgreSQL 16 (Môi trường Docker/Production) & SQLite (Môi trường Local Dev tiện lợi).
* **AI & Machine Learning:** Pandas, NumPy, Scikit-learn, Prophet, XGBoost, LangChain / Function Calling.
* **Hạ tầng & Đóng gói:** Docker, Docker Compose, GitHub Actions CI tự động kiểm tra cú pháp và build.

---

## 3. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
DACN/
├── .github/workflows/          # CI/CD Workflows (Backend & Frontend CI)
├── backend/                    # FASTAPI BACKEND (Python 3.12)
│   ├── alembic/                # Quản lý phiên bản Migration cơ sở dữ liệu
│   ├── app/
│   │   ├── api/v1/endpoints/   # Các Router API (dashboard, ingredients, suppliers...)
│   │   ├── core/               # Cấu hình Settings, Database Engine, JWT Security
│   │   ├── models/             # Khai báo SQLAlchemy Models (10 bảng)
│   │   ├── schemas/            # Pydantic v2 Schemas (Validation Request/Response)
│   │   ├── seed/               # Kịch bản sinh dữ liệu mẫu thực tế 12 tháng
│   │   ├── services/           # Nghiệp vụ: Thuật toán ROP, MCDM so sánh NCC
│   │   └── main.py             # Entrypoint FastAPI, CORS Middleware
│   ├── Dockerfile              # Dockerfile chạy Backend FastAPI
│   ├── requirements.txt        # Thư viện phụ thuộc Backend
│   └── test_api.py             # Bộ test tự động kiểm thử 100% các endpoint
├── frontend/                   # REFLEX FRONTEND (Python 3.12)
│   ├── frontend/
│   │   ├── components/         # UI Components: Sidebar, Header, KPI StatCard
│   │   ├── pages/              # 5 Trang giao diện: Dashboard, Inventory, Forecast...
│   │   ├── state.py            # Quản lý State tập trung, kết nối API qua HTTPX
│   │   └── frontend.py         # Entrypoint Reflex App, Theme & Route Registry
│   ├── Dockerfile              # Dockerfile chạy Frontend Reflex
│   ├── requirements.txt        # Thư viện phụ thuộc Frontend
│   └── rxconfig.py             # Cấu hình cổng Frontend (3000) & Event Backend (8001)
├── frontend_backup/            # Bản sao lưu toàn bộ mã nguồn Next.js 14 cũ
├── database_seed.sql           # File SQL dữ liệu khởi tạo nạp trực tiếp vào Postgres
├── docker-compose.yml          # Đóng gói PostgreSQL, pgAdmin, Backend, Frontend
└── README.md                   # Hướng dẫn kỹ thuật và vận hành hệ thống
```

---

## 4. HƯỚNG DẪN CÀI ĐẶT & CHẠY HỆ THỐNG

### Cách 1: Chạy trọn gói bằng Docker Compose (Khuyên dùng)
Yêu cầu máy tính đã cài đặt [Docker Desktop](https://www.docker.com/).

```bash
# 1. Khởi động toàn bộ dịch vụ (PostgreSQL, pgAdmin, Backend, Frontend)
docker compose up --build
```

Sau khi các container khởi động hoàn tất:
* **Giao diện Dashboard (Frontend Reflex):** [http://localhost:3000](http://localhost:3000)
* **Tài liệu Swagger API (FastAPI Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Trình quản lý CSDL pgAdmin 4:** [http://localhost:5050](http://localhost:5050)
  * *Email:* `admin@coffee.vn`
  * *Mật khẩu:* `admin`

---

### Cách 2: Chạy cục bộ từng phần (Local Development)

#### Bước 1: Khởi chạy Backend (FastAPI)
```bash
cd backend

# Cài đặt thư viện
pip install -r requirements.txt

# Nạp dữ liệu mẫu vào cơ sở dữ liệu
python app/seed/seed_data.py

# Chạy server FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> Backend API và tài liệu tương tác sẵn sàng tại: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Bước 2: Khởi chạy Frontend (Reflex Python)
Mở một cửa sổ Terminal mới:
```bash
cd frontend

# Cài đặt thư viện frontend
pip install -r requirements.txt

# Khởi chạy ứng dụng Reflex
reflex run
```
> Truy cập giao diện ứng dụng tại: [http://localhost:3000](http://localhost:3000)

---

## 5. DANH SÁCH CÁC API ENDPOINTS CHÍNH

Hệ thống cung cấp đầy đủ RESTful API theo chuẩn OpenAPI 3.0:

| Nhóm chức năng | Phương thức | Endpoint | Mô tả chi tiết |
| :--- | :---: | :--- | :--- |
| **Tổng quan** | `GET` | `/api/v1/dashboard/stats` | Thống kê số lượng nguyên liệu, thiếu ROP, tồn dư, phiếu chờ duyệt |
| | `GET` | `/api/v1/dashboard/alerts` | Danh sách cảnh báo đỏ (thiếu), vàng (tồn dư / hạn dùng) |
| | `GET` | `/api/v1/dashboard/trends` | Dữ liệu tiêu thụ và chi phí BOM quy đổi 12 tháng |
| | `GET` | `/api/v1/dashboard/forecast-summary` | Tóm tắt đường cong dự báo 7 ngày tới theo nguyên liệu |
| **Tồn kho** | `GET` | `/api/v1/ingredients` | Danh sách nguyên liệu kèm trạng thái tính toán ROP tự động |
| | `GET` | `/api/v1/ingredients/{id}` | Chi tiết nguyên liệu, lịch sử nhập lô và dự báo chuỗi thời gian |
| | `GET` | `/api/v1/inventory/batches` | Danh sách các lô hàng kèm cảnh báo hạn sử dụng |
| | `POST` | `/api/v1/inventory/transactions` | Ghi nhận giao dịch xuất / nhập / hao hụt / kiểm kê kho |
| **Nhà cung cấp**| `GET` | `/api/v1/suppliers` | Danh sách nhà cung cấp kèm báo giá chi tiết |
| | `GET` | `/api/v1/suppliers/compare/{id}` | **Thuật toán MCDM** xếp hạng nhà cung cấp tối ưu cho nguyên liệu |
| **AI Đề xuất** | `GET` | `/api/v1/proposals` | Danh sách phiếu đề xuất mua hàng do AI Agent tự động lập |
| | `POST` | `/api/v1/proposals/{id}/action` | **Human-in-the-loop:** Quản lý Phê duyệt / Từ chối / Ghi ý kiến |
| **Xác thực** | `POST` | `/api/v1/auth/login` | Đăng nhập hệ thống, cấp mã JWT Access Token |
| | `GET` | `/api/v1/auth/me` | Lấy thông tin tài khoản và vai trò người dùng hiện tại |

---

## 6. TÀI KHOẢN ĐĂNG NHẬP THỬ NGHIỆM

Hệ thống đã chuẩn bị sẵn các tài khoản phân quyền mẫu:

| Email đăng nhập | Mật khẩu | Vai trò phân quyền | Phạm vi quyền hạn |
| :--- | :---: | :--- | :--- |
| `quanly@coffee.vn` | `admin123` | **Quản lý cửa hàng (QUAN_LY)** | Toàn quyền xem Dashboard, Duyệt/Từ chối đề xuất mua hàng của AI |
| `kho@coffee.vn` | `admin123` | **Nhân viên kho (NHAN_VIEN_KHO)** | Theo dõi tồn kho thực tế, nhập lô hàng mới, ghi nhận hao hụt |
| `admin@coffee.vn` | `admin123` | **Quản trị hệ thống (ADMIN)** | Quản lý người dùng, thiết lập định mức công thức BOM và cấu hình |

---

## 7. KIỂM THỬ HỆ THỐNG (AUTOMATED TEST SUITE)

Hệ thống tích hợp sẵn kịch bản kiểm thử toàn diện kiểm tra tính đúng đắn của toàn bộ logic nghiệp vụ (ROP, MCDM, Duyệt đề xuất, Seed Data):

```bash
# Chạy bộ kiểm thử tự động
python backend/test_api.py
```

Kết quả kỳ vọng: **100% các endpoint và business logic đều đạt chuẩn PASS.**
