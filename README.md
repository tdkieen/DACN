# DCCN – AI Procurement Agent & Quản lý tồn kho

Đồ án chuyên ngành – Khoa CNTT – Đại học HUTECH. GVHD: ThS. Trịnh Công Nhựt.
Nhóm: Ngô Kế Nhật Trường, Tăng Duy Kiên, Trần Anh Hào (lớp 23DTHD1).

> Bản này chứa phần **Frontend (Tuần 1–3)**. Thư mục `backend/` và `ai_agent/` do các thành viên khác bổ sung vào monorepo.

## Cấu trúc

```
DCCN/
├── .github/workflows/frontend-ci.yml
├── docs/                       # Tài liệu Tuần 1, 2, 3 (Frontend)
└── frontend/                   # Next.js 14 + TypeScript + Tailwind
```

## Chạy Frontend

```bash
cd frontend
cp .env.example .env.local      # chỉnh NEXT_PUBLIC_API_URL nếu cần
npm install
npm run dev                     # http://localhost:3000
```

## Quy ước

- Tên trường trong `src/types/index.ts` khớp lược đồ CSDL; không tự đổi tên.
- Git Flow: nhánh `main`, `develop`; làm việc trên nhánh `feature/*` rồi tạo Pull Request vào `develop`.
- Phiếu do AI tạo luôn ở trạng thái `CHO_DUYET`; giao diện không có chức năng gửi đơn tự động tới nhà cung cấp.
