# ☕ DACN – AI Procurement Agent & Quản Lý Tồn Kho Quán Cà Phê

> **Đồ án Chuyên ngành – Khoa Công nghệ Thông tin – Trường Đại học Công nghệ TP.HCM (HUTECH)**  
> **Giảng viên hướng dẫn:** ThS. Trịnh Công Nhựt  
> **Lớp:** 23DTHD1  
> **Nhóm sinh viên thực hiện:**
> 1. **Ngô Kế Nhật Trường** – MSSV: `2380602390` *(AI & Data Engineer)*
> 2. **Tăng Duy Kiên** – MSSV: `2380601131` *(Backend Developer)*
> 3. **Trần Anh Hào** – MSSV: `2380600595` *(Frontend Developer)*

---

## 📌 1. Bối cảnh & Giá trị Cốt lõi của Đề tài

Hệ thống giải quyết bài toán tối ưu hóa chuỗi cung ứng trong ngành **F&B (Quán cà phê)**: Cân bằng giữa việc **KHÔNG ĐƯỢC THIẾU NGUYÊN LIỆU** (làm gián đoạn bán hàng) và **KHÔNG ĐƯỢC TỒN DƯ ĐỌNG VỐN** (gây hỏng sữa, siro, hoa quả hết hạn sử dụng).

### 4 Bước nghiệp vụ cốt lõi:
1. **Bóc tách nguyên liệu qua BOM (Bill of Materials):** Quy đổi từ đơn bán đồ uống (POS Sales) thành định mức tiêu hao thực tế (gram/ml/cái).
2. **Dự báo nhu cầu 7 ngày tới:** Sử dụng các mô hình chuỗi thời gian (Prophet, XGBoost) có xét đến chu kỳ cuối tuần và cao điểm.
3. **Cảnh báo tồn kho & Tối ưu hóa Nhà cung cấp:**
   * Cảnh báo **ĐỎ** khi $Tồn\_kho \le ROP$ (Điểm đặt hàng lại).
   * Cảnh báo **VÀNG** khi tồn vượt mức tối đa hoặc vượt gấp 3 lần nhu cầu tuần.
   * Xếp hạng đối tác cung ứng tối ưu bằng giải thuật **MCDM** (Đơn giá, Lead time, Điểm chất lượng, Điểm uy tín).
4. **AI Procurement Agent (Human-in-the-loop):** Trợ lý LLM tự động truy vấn dữ liệu, sinh phiếu đề xuất mua hàng kèm lý do giải thích chi tiết; Quản lý cửa hàng là người bấm duyệt cuối cùng.

---

## 🛠️ 2. Công Nghệ Áp Dụng (Tech Stack)

| Thành phần | Công nghệ | Ghi chú vai trò |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI (Python 3.11+)** | RESTful API hiệu năng cao, Clean Architecture, Pydantic v2 |
| **Database & ORM** | **PostgreSQL 16, SQLite, SQLAlchemy 2.0** | Hỗ trợ cả PostgreSQL production và SQLite local development |
| **Migrations** | **Alembic** | Quản lý phiên bản và lược đồ cơ sở dữ liệu |
| **Frontend** | **Next.js 14+ (App Router, TypeScript)** | Giao diện hiện đại, Server/Client components, SSR |
| **UI Components** | **TailwindCSS, shadcn/ui, Lucide Icons** | Giao diện tinh gọn, UX chuyên biệt cho quản lý kho F&B |
| **State & Fetching**| **TanStack React Query v5, Axios** | Cache dữ liệu tự động, đồng bộ hóa thời gian thực |
| **AI / Thuật toán** | **MCDM Scoring, Prophet, XGBoost** | Đánh giá xếp hạng NCC, dự báo chuỗi thời gian |
| **Hạ tầng DevOps** | **Docker, Docker Compose** | Đóng gói đồng bộ môi trường PostgreSQL, PgAdmin, Backend, Frontend |

---

## 📂 3. Cấu Trúc Monorepo

```text
DACN/
├── .github/workflows/          # CI/CD pipelines (Lint, Typecheck)
├── docker-compose.yml          # Triển khai trọn gói: PostgreSQL, PgAdmin, Backend, Frontend
├── database_seed.sql           # File SQL dump 100% CSDL nạp trực tiếp qua pgAdmin / Docker
├── .gitignore                  # Cấu hình chuẩn bỏ qua file nhị phân .db và file tạm
├── backend/                    # FASTAPI BACKEND SERVICE
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint, CORS, tự động init DB & seed
│   │   ├── core/               # Cấu hình Settings, Database Engine, Bcrypt/JWT Security
│   │   ├── models/             # 10 bảng SQLAlchemy ORM theo sơ đồ ERD chuẩn
│   │   ├── schemas/            # Pydantic Schemas Request/Response validation
│   │   ├── services/           # Clean Architecture (ROP, MCDM, Dashboard, Proposal workflow)
│   │   ├── api/v1/             # RESTful API Routers (/ingredients, /suppliers, /inventory...)
│   │   └── seed/               # Script sinh 12 tháng dữ liệu mẫu F&B chân thực
│   ├── alembic/                # Database migrations
│   ├── requirements.txt        # Thư viện Backend
│   ├── test_api.py             # Bộ test cases tự động kiểm thử toàn diện
│   └── Dockerfile
└── frontend/                   # NEXT.JS 14 FRONTEND SERVICE
    ├── src/
    │   ├── app/                # App Router (dashboard, inventory, suppliers, proposals)
    │   ├── components/         # UI components & Shared layout (Sidebar, Header, Cards)
    │   ├── lib/                # Axios instance trỏ tới FastAPI, React Query client
    │   └── types/              # TypeScript interfaces khớp chuẩn 100% với Backend
    ├── package.json
    └── Dockerfile
```

---

## 📊 4. Lược Đồ Cơ Sở Dữ Liệu (10 Bảng Chuẩn ERD)

Dữ liệu được tổ chức theo quan hệ khóa ngoại chặt chẽ:
1. `nguyen_lieu`: Danh mục nguyên liệu, đơn vị tính, mức tồn an toàn, tồn kho hiện tại.
2. `nha_cung_cap`: Thông tin liên hệ, lead time giao hàng, điểm uy tín, điểm chất lượng.
3. `cc_nguyen_lieu`: Báo giá đa tiêu chuẩn của các NCC (đơn giá, MOQ, lead time riêng).
4. `lo_hang`: Chi tiết lô hàng nhập kho, số lượng còn lại, hạn sử dụng (cảnh báo $\le 7$ ngày).
5. `giao_dich_kho`: Lịch sử biến động kho (`NHAP`, `XUAT_BAN`, `HAO_HUT`, `KIEM_KE`).
6. `du_bao_nhu_cau`: Kết quả dự báo tiêu thụ 7 ngày tới (T+1 đến T+7) của mô hình AI.
7. `phieu_de_xuat_mua`: Phiếu mua hàng do AI Agent tạo (`CHO_DUYET`, `DA_DUYET`, `TU_CHOI`).
8. `ct_de_xuat_mua`: Chi tiết nguyên liệu đề xuất, số lượng, đơn giá và lập luận giải thích của AI.
9. `lich_su_duyet`: Nhật ký phê duyệt của Quản lý cửa hàng (Human-in-the-loop).
10. `nguoi_dung`: Quản lý tài khoản và phân quyền (`QUAN_LY`, `NHAN_VIEN_KHO`, `ADMIN`).
* Kèm 2 bảng hỗ trợ bóc tách BOM: `menu_items` (món bán) và `recipes_bom` (định mức nguyên liệu).

---

## 🧮 5. Các Công Thức & Thuật Toán Đã Cài Đặt

### 5.1. Điểm đặt hàng lại (Reorder Point - ROP)
$$ROP = (\text{Nhu cầu dự báo trung bình/ngày} \times \text{Lead Time NCC}) + \text{Mức tồn an toàn (Safety Stock)}$$
* **Cảnh báo ĐỎ (`NGUY_CO_THIEU`):** $Tồn\_kho \le ROP \rightarrow$ Tự động tính số lượng cần đặt bổ sung.
* **Cảnh báo VÀNG (`TON_DU`):** $Tồn\_kho > Mức\_tối\_đa$ hoặc $Tồn / Nhu\_cầu\_7\_ngày > 3$.
* **Trạng thái XANH (`AN_TOAN`):** Tồn kho nằm trong ngưỡng an toàn.

### 5.2. Thuật toán Đánh giá Nhà cung cấp Đa tiêu chuẩn (MCDM)
$$\text{Score}(k) = 0.4 \times \frac{\text{Giá}_{\min}}{\text{Giá}_k} + 0.3 \times \frac{\text{LeadTime}_{\min}}{\text{LeadTime}_k} + 0.15 \times \frac{\text{Chất lượng}_k}{5} + 0.15 \times \frac{\text{Uy tín}_k}{\text{Max Uy tín}}$$
Hệ thống chuẩn hóa thang điểm 100 và tự động chọn nhà cung cấp có điểm số cao nhất cho phiếu đề xuất mua hàng.

---

## 🚀 6. Hướng Dẫn Cài Đặt & Vận Hành

### Cách 1: Chạy trực tiếp trên máy (Local Development)

#### Bước 1: Khởi động Backend (FastAPI)
```bash
cd backend

# Cài đặt thư viện
pip install -r requirements.txt

# Nạp dữ liệu mẫu 12 tháng (tự động tạo bảng & nạp 15 nguyên liệu, 5 NCC, lô hàng, dự báo)
python app/seed/seed_data.py

# Khởi chạy server API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
* **Swagger UI API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc API Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

#### Bước 2: Khởi động Frontend (Next.js)
```bash
cd frontend

# Tạo file cấu hình trỏ tới Backend API
cp .env.example .env.local

# Cài đặt thư viện & chạy dev server
npm install
npm run dev
```
* **Giao diện Dashboard:** [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
* **Quản lý Tồn kho & ROP:** [http://localhost:3000/inventory](http://localhost:3000/inventory)
* **Nhà Cung Cấp & Báo giá:** [http://localhost:3000/suppliers](http://localhost:3000/suppliers)
* **Đề xuất mua hàng (AI):** [http://localhost:3000/proposals](http://localhost:3000/proposals)

---

### Cách 2: Chạy trọn gói bằng Docker Compose (Khuyên dùng)

Chỉ cần cài Docker Desktop, mở thư mục gốc dự án và gõ đúng 1 lệnh:
```bash
docker compose up --build
```
Hệ thống sẽ tự động khởi động:
1. **PostgreSQL 16:** Tự động nạp sẵn toàn bộ cấu trúc bảng và dữ liệu từ `database_seed.sql`.
2. **PgAdmin 4:** [http://localhost:5050](http://localhost:5050) (User: `admin@coffee.vn` / Pass: `admin`).
3. **FastAPI Backend:** [http://localhost:8000/docs](http://localhost:8000/docs).
4. **Next.js Frontend:** [http://localhost:3000](http://localhost:3000).

---

### Cách 3: Nạp dữ liệu vào pgAdmin bằng file `database_seed.sql`

Nếu bạn đang dùng pgAdmin 4 ngoài máy chủ:
1. Mở **pgAdmin 4** $\rightarrow$ chọn Database của bạn (ví dụ: `AI agent` hoặc `coffee_inventory`).
2. Chuột phải vào Database $\rightarrow$ chọn **Query Tool**.
3. Bấm nút **Open File** (biểu tượng mở thư mục) $\rightarrow$ chọn file `database_seed.sql` ở thư mục gốc.
4. Nhấn phím **F5** (Execute).
5. Toàn bộ 10 bảng và dữ liệu mẫu sẽ lập tức hiển thị tại mục **Schemas $\rightarrow$ public $\rightarrow$ Tables**.

---

## 🔐 7. Tài Khoản Mặc Định Đăng Nhập Hệ Thống

| Tài khoản Email | Mật khẩu | Vai trò | Quyền hạn |
| :--- | :---: | :---: | :--- |
| `quanly@coffee.vn` | `admin123` | `QUAN_LY` | Toàn quyền Dashboard, xem kho, duyệt/từ chối/sửa phiếu đề xuất AI |
| `kho@coffee.vn` | `admin123` | `NHAN_VIEN_KHO` | Xem tồn kho, lô hàng, kiểm kê, lịch sử giao dịch |
| `admin@coffee.vn` | `admin123` | `ADMIN` | Quản trị hệ thống, phân quyền người dùng |

---

## 🧪 8. Kiểm Thử Tự Động (Automated Testing)

Dự án tích hợp sẵn test suite kiểm thử toàn diện toàn bộ 16 kịch bản API, logic ROP, xếp hạng MCDM và quy trình duyệt phiếu:

```bash
python backend/test_api.py
```

**Kết quả kiểm thử:**
```text
[TEST] Bat dau kiem tra toan bo endpoints Backend API...
  [OK] read_dashboard_stats: 15 nguyen lieu, thieu: 4, cho duyet: 1
  [OK] read_dashboard_alerts: 6 alerts (Nguy co thieu / Ton du / Het han)
  [OK] read_dashboard_trends: 12 thang tieu thu
  [OK] read_forecast_summary: 6 nguyen lieu co du lieu du bao 7 ngay
  [OK] read_ingredients (all): 15 items
  [OK] read_ingredients (NGUY_CO_THIEU): 4 items cham ROP
  [OK] read_ingredient_detail(1): Hạt cà phê Robusta, ROP: 25.08, Tinh trang: NGUY_CO_THIEU
  [OK] read_suppliers: 5 nha cung cap
  [OK] compare_suppliers(1) MCDM: Toi uu la 'Vinbar' voi Score=95.32/100
  [OK] read_batches: 6 lo hang
  [OK] read_transactions: 28 giao dich kho
  [OK] read_proposals: 2 phieu de xuat
  [OK] action_proposal(1): Trang thai moi -> DA_DUYET
  [OK] auth.login: Dang nhap thanh cong, nhan JWT Token
[SUCCESS] TOAN BO 100% CAC ENDPOINT VA BUSINESS LOGIC BACKEND DA PASS HOAN HAO!
```

---

## 📅 9. Lộ Trình 12 Tuần & Tiến Độ Dự Án

* [x] **Tuần 1:** Khảo sát đề tài, xác định phạm vi hệ thống, nguồn dữ liệu & công thức BOM quán cà phê.
* [x] **Tuần 2:** Phân tích Use Case, thiết kế lược đồ ERD (10 bảng), thiết kế wireframe Figma.
* [x] **Tuần 3:** Khởi tạo PostgreSQL trên Docker, sinh dữ liệu giả lập 12 tháng, FastAPI CRUD nền tảng.
* [x] **Tuần 4:** Hoàn thiện Backend Core (ROP, MCDM, cảnh báo hạn dùng), kết nối Next.js Dashboard hiển thị dữ liệu thật.
* [ ] **Tuần 5:** Thu thập, làm sạch dữ liệu và xây dựng Pipeline bóc tách định mức nguyên liệu (BOM ETL Pipeline).
* [ ] **Tuần 6:** Huấn luyện mô hình chuỗi thời gian dự báo nhu cầu 7 ngày tới (Prophet / XGBoost).
* [ ] **Tuần 7:** Tối ưu hóa thuật toán tính lượng nguyên liệu cần bổ sung và chọn NCC đa tiêu chuẩn.
* [ ] **Tuần 8:** Phát triển hoàn chỉnh quy trình quản lý và phê duyệt đề xuất mua hàng (Workflow duyệt).
* [ ] **Tuần 9:** Tích hợp AI Procurement Agent với LLM API và Tool Calling.
* [ ] **Tuần 10:** Tích hợp toàn hệ thống, kiểm thử End-to-End chu trình mua hàng thông minh.
* [ ] **Tuần 11:** Tối ưu hóa hiệu năng, giao diện, hoàn thiện báo cáo và slide demo.
* [ ] **Tuần 12:** Kiểm thử toàn diện, chuẩn bị bảo vệ đồ án trước hội đồng.
