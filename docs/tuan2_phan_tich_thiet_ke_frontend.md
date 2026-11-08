# Tuần 2 (19/10 – 25/10) – Phân tích & thiết kế (phần Frontend)

**Người thực hiện:** Trần Anh Hào – Frontend Developer

## 1. Use Case

| Mã | Use case | Tác nhân | Mô tả ngắn |
|---|---|---|---|
| UC-01 | Đăng nhập | Tất cả | Nhập email/mật khẩu, nhận JWT |
| UC-02 | Xem tổng quan | Quản lý, Admin | Xem thống kê, cảnh báo, biểu đồ |
| UC-03 | Xem tồn kho | Quản lý, Nhân viên kho | Xem tồn so với mức an toàn, lô hàng, HSD |
| UC-04 | Xem nhà cung cấp & báo giá | Quản lý, Nhân viên kho | So sánh đơn giá, lead time, MOQ, uy tín |
| UC-05 | Xem dự báo nhu cầu 7 ngày | Quản lý | Biểu đồ dự báo theo nguyên liệu |
| UC-06 | Xem đề xuất mua hàng | Quản lý | Xem phiếu và lập luận của AI |
| UC-07 | Duyệt / Từ chối / Sửa đề xuất | Quản lý | Ra quyết định, ghi ý kiến, lưu lịch sử duyệt |
| UC-08 | Kích hoạt AI Agent lập đề xuất | Quản lý | Yêu cầu Agent phân tích và tạo phiếu `CHO_DUYET` |
| UC-09 | Quản lý người dùng | Admin | Xem và phân vai trò |

**Phân quyền giao diện:** `QUAN_LY` dùng được UC-02…UC-08; `NHAN_VIEN_KHO` chỉ UC-03, UC-04; `ADMIN` toàn bộ.
Chỉ `QUAN_LY` thấy nút Duyệt/Từ chối/Sửa.

## 2. Sơ đồ trang (Sitemap)

```
/login
/dashboard                  Tổng quan
/inventory                  Tồn kho
   └─ /inventory/[id]       Chi tiết nguyên liệu: lô hàng, giao dịch kho, dự báo 7 ngày
/suppliers                  Nhà cung cấp
   └─ /suppliers/[id]       Chi tiết NCC + bảng báo giá
/proposals                  Danh sách đề xuất mua hàng
   └─ /proposals/[id]       Chi tiết phiếu + duyệt + lịch sử duyệt
```

## 3. Wireframe (mô tả bố cục)

**Bố cục chung:** thanh bên trái (điều hướng), thanh trên cùng, vùng nội dung bên phải.

**Dashboard**
```
┌──────────┬────────────────────────────────────────────────┐
│ Sidebar  │ Tổng quan                                      │
│          │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│ Tổng quan│ │NL dùng │ │Thiếu   │ │Tồn dư  │ │Chờ duyệt│    │
│ Tồn kho  │ └────────┘ └────────┘ └────────┘ └────────┘    │
│ NCC      │ ┌─────────────────────┐ ┌─────────────────────┐│
│ Đề xuất  │ │ Xu hướng 12 tháng   │ │ Dự báo 7 ngày       ││
│          │ └─────────────────────┘ └─────────────────────┘│
│          │ Danh sách cảnh báo (nguyên liệu, tồn, ROP)     │
└──────────┴────────────────────────────────────────────────┘
```

**Tồn kho:** bộ lọc (tên, trạng thái cảnh báo) → bảng: Tên | Đơn vị | Tồn hiện tại | Mức an toàn | Trạng thái (Bình thường / Sắp thiếu / Tồn dư).

**Nhà cung cấp:** bảng NCC (Tên | Liên hệ | Lead time | Điểm uy tín); chi tiết có bảng báo giá (Nguyên liệu | Đơn giá | MOQ | Lead time | Ngày cập nhật giá).

**Chi tiết phiếu đề xuất:**
```
Phiếu #… [Chờ duyệt]            Tổng tiền dự kiến: …
Lý do tổng quan (AI): …
┌ Nguyên liệu │ NCC │ SL đề xuất │ Đơn giá │ Lý do ┐
└──────────────────────────────────────────────────┘
Ý kiến: [________]   [Duyệt] [Sửa] [Từ chối]
Lịch sử duyệt: người duyệt | hành động | ý kiến | thời gian
```

## 4. Ánh xạ ERD → TypeScript

Toàn bộ interface nằm ở `frontend/src/types/index.ts`, đặt tên trường **giống hệt** Mục 5 đặc tả:

| Bảng | Interface |
|---|---|
| NGUYEN_LIEU | `NguyenLieu` |
| NHA_CUNG_CAP | `NhaCungCap` |
| CC_NGUYEN_LIEU | `CcNguyenLieu` |
| LO_HANG | `LoHang` |
| GIAO_DICH_KHO | `GiaoDichKho` (+ `LoaiGiaoDich`) |
| DU_BAO_NHU_CAU | `DuBaoNhuCau` |
| PHIEU_DE_XUAT_MUA / CT_DE_XUAT_MUA | `PhieuDeXuatMua`, `CtDeXuatMua` (+ `TrangThaiPhieu`) |
| LICH_SU_DUYET | `LichSuDuyet` (+ `HanhDongDuyet`) |
| NGUOI_DUNG | `NguoiDung` (+ `VaiTro`), **không** có `mat_khau_hash` |

## 5. Quy tắc nghiệp vụ hiển thị

- Cảnh báo **thiếu hàng** khi `ton_kho_hien_tai <= ROP`, với `ROP = nhu cầu dự báo TB/ngày × lead time + muc_ton_an_toan`.
- Cảnh báo **tồn dư** khi tồn > Max Stock hoặc tồn / nhu cầu dự báo 7 ngày > 3 lần.
- Phiếu mới của AI luôn `CHO_DUYET`; sau khi quản lý thao tác chuyển thành `DA_DUYET`, `TU_CHOI` hoặc `DA_SUA`, đồng thời ghi `LICH_SU_DUYET` (`APPROVE` / `REJECT` / `EDIT`).
- Frontend chỉ hiển thị kết quả ROP và điểm NCC do Backend tính; không tự tính lại.

## 6. Giao diện (thiết kế thị giác)

Tông xanh rêu đậm cho màu chủ đạo, nền xám xanh nhạt; vàng hổ phách cho cảnh báo thiếu, đỏ gạch cho nguy cơ,
xanh lá cho trạng thái tốt. Màu được khai báo bằng biến CSS trong `globals.css` để đổi theme dễ dàng.
Bản mockup Figma sẽ được vẽ dựa trên bố cục ở mục 3.

## 7. Điểm cần thống nhất với Backend / AI

1. Thang điểm `diem_uy_tin`: đặc tả ghi 1–5 sao (Mục 5.2) nhưng công thức Score (6.3) chia cho 100.
2. Danh sách endpoint, định dạng phân trang và lỗi của API.
3. Backend có cung cấp sẵn trạng thái cảnh báo (thiếu/thừa) hay Frontend tự so sánh tồn với ROP.
4. Cơ chế đăng nhập: JWT trả về ở endpoint nào, thời hạn token.
