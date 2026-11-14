# DACN – AI Procurement Agent & Quản Lý Tồn Kho

Đồ án Chuyên ngành – Khoa CNTT – Đại học HUTECH  
**GVHD:** ThS. Trịnh Công Nhựt  
**Nhóm sinh viên thực hiện (Lớp 23DTHD1):**
* Ngô Kế Nhật Trường – 2380602390 (AI & Data)
* Tăng Duy Kiên – 2380601131 (Backend)
* Trần Anh Hào – 2380600595 (Frontend)

---

## 1. Cấu trúc dự án

```text
DACN/
├── backend/            # FastAPI (Python) - RESTful API, ORM, BOM ETL Pipeline, Seed data
├── frontend/           # Next.js 14 (TypeScript, TailwindCSS) - Dashboard
├── docs/               # Tài liệu báo cáo tiến độ theo tuần
├── database_seed.sql   # Dữ liệu mẫu nạp vào PostgreSQL / pgAdmin
├── docker-compose.yml  # Chạy trọn gói PostgreSQL, Backend, Frontend
└── README.md
```

---

## 2. Hướng dẫn chạy

### Chạy Backend (FastAPI) & Quy trình Dữ liệu BOM (Tuần 5)
```bash
cd backend
pip install -r requirements.txt
python app/seed/seed_data.py          # Nạp dữ liệu mẫu & tự động chạy quy trình dữ liệu BOM 12 tháng
python chay_quy_trinh_bom.py          # Chạy riêng quy trình làm sạch bán hàng & bóc tách định mức BOM (Tuần 5)
python test_api.py                    # Kiểm thử tự động toàn bộ API & Quy trình dữ liệu
python -m uvicorn app.main:app --reload  # http://localhost:8000/docs
```

### Chạy Frontend (Next.js)
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                           # http://localhost:3000
```

### Hoặc chạy toàn bộ bằng Docker
```bash
docker compose up --build
```
* **Frontend:** http://localhost:3000
* **API Docs (Swagger):** http://localhost:8000/docs
* **PgAdmin:** http://localhost:5050 (`admin@coffee.vn` / `admin`)

---

## 3. Tài khoản đăng nhập thử nghiệm

| Email | Mật khẩu | Vai trò |
| :--- | :---: | :--- |
| `quanly@coffee.vn` | `admin123` | Quản lý cửa hàng |
| `kho@coffee.vn` | `admin123` | Nhân viên kho |
| `admin@coffee.vn` | `admin123` | Quản trị viên |
