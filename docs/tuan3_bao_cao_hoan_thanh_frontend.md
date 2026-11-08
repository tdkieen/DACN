# Tuần 3 (26/10 – 1/11) – Khởi tạo khung Frontend Dashboard

**Người thực hiện:** Trần Anh Hào – Frontend Developer

## 1. Công việc đã hoàn thành (phần Frontend)

- [x] Khởi tạo khung Next.js 14 (App Router, TypeScript) trong `frontend/`.
- [x] Chuẩn hóa cấu trúc: `src/app`, `src/components`, `src/lib`, `src/types`.
- [x] Cấu hình TailwindCSS, theme bằng biến CSS, components kiểu shadcn/ui (`Button`, `Card`, `Badge`) và `components.json`.
- [x] Layout chung: Sidebar, Header, điều hướng responsive; trang Tổng quan, Tồn kho, Nhà cung cấp, Đề xuất mua hàng (khung).
- [x] `lib/api.ts`: Axios instance, cấu hình `NEXT_PUBLIC_API_URL`, gắn JWT, xử lý 401.
- [x] `lib/query-client.ts` + `Providers` (TanStack Query).
- [x] `types/index.ts`: interface khớp 100% lược đồ CSDL Mục 5.
- [x] ESLint (`next/core-web-vitals`), Prettier, script `typecheck`.
- [x] CI/Linting: `.github/workflows/frontend-ci.yml` (lint → typecheck → build).
- [x] `Dockerfile` cho frontend và đoạn cấu hình `docker-compose` (`docs/docker-compose.frontend.snippet.yml`).
- [x] Đã kiểm tra: `npm run lint`, `npm run typecheck`, `npm run build` đều thành công.

## 2. Phần do thành viên khác phụ trách trong tuần 3

Backend (PostgreSQL, Alembic, FastAPI, Swagger) và AI/Data (Data Generator, seed dữ liệu 12 tháng) – cùng nhóm tích hợp vào monorepo.

## 3. Cách chạy

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev        # http://localhost:3000
```

Kiểm tra chất lượng: `npm run lint && npm run typecheck && npm run build`.

## 4. Kế hoạch Tuần 4

Nối Dashboard với API thật: bảng tồn kho, bảng nhà cung cấp và báo giá, thẻ thống kê, cảnh báo thiếu/thừa.
Cần Backend cung cấp trước các endpoint đọc `ingredients`, `suppliers`, và báo giá.
