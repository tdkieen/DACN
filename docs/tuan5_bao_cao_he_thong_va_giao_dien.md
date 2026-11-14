# Tuần 5 – Báo Cáo Triển Khai Hệ Thống (Backend) & Giao Diện (Frontend)

**Đề tài:** Hệ thống Quản lý tồn kho và Đề xuất mua hàng thông minh cho Quán cà phê  
**Giảng viên hướng dẫn:** ThS. Trịnh Công Nhựt  
**Thành viên thực hiện:**
* **Tăng Duy Kiên** – MSSV: `2380601131` *(Phụ trách Hệ thống & Cơ sở dữ liệu)*
* **Trần Anh Hào** – MSSV: `2380600595` *(Phụ trách Giao diện Người dùng)*

---

## 1. Hạng mục hoàn thành phần Hệ thống (Tuần 5)

### 1.1. Cơ chế Xuất Kho Theo Nguyên Tắc Hết Hạn Trước – Xuất Trước (FEFO)
* Cài đặt hàm [`deduct_batches_fefo`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/backend/app/services/inventory_service.py#L172-L194) trong [`backend/app/services/inventory_service.py`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/backend/app/services/inventory_service.py):
  * Khi phát sinh giao dịch `XUAT_BAN` (từ đơn bán tại quầy qua bóc tách định mức BOM) hoặc `HAO_HUT`, hệ thống tự động truy vấn các lô hàng còn tồn (`so_luong_con_lai > 0`) sắp xếp theo `han_su_dung` tăng dần (lô hết hạn trước được ưu tiên trừ trước) để trừ dần số lượng thực tế trên từng lô.
* Bổ sung điểm cuối nhập lô hàng mới `POST /api/v1/inventory/batches`:
  * Tự động khởi tạo bản ghi lô hàng (`lo_hang`), cộng dồn `ton_kho_hien_tai` của nguyên liệu và ghi nhận giao dịch `NHAP` vào bảng `giao_dich_kho`.

### 1.2. Hệ thống Giao tiếp Quản lý Thực đơn Định mức BOM & Hóa đơn Bán hàng
Triển khai trong [`backend/app/api/v1/endpoints/dinh_muc_bom.py`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/backend/app/api/v1/endpoints/dinh_muc_bom.py) và [`backend/app/services/dich_vu_dinh_muc_bom.py`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/backend/app/services/dich_vu_dinh_muc_bom.py):
* `GET /api/v1/dinh-muc-bom/thuc-don-bom`: Lấy danh sách 12 món đồ uống kèm chi tiết định mức nguyên liệu, tự động tính giá vốn nguyên liệu (`gia_von_nguyen_lieu`) dựa trên đơn giá báo giá thấp nhất và tỷ suất lợi nhuận gộp (`ty_suat_loi_nhuan_gop` %).
* `POST /api/v1/dinh-muc-bom/thuc-don-bom`: Tạo mới hoặc cập nhật món đồ uống và định mức công thức pha chế.
* `POST /api/v1/dinh-muc-bom/mo-phong-bom`: Mô phỏng bóc tách danh sách đồ uống bán ra thành nguyên liệu tiêu hao và kiểm tra khả năng đáp ứng của tồn kho hiện tại.
* `POST /api/v1/dinh-muc-bom/hoa-don-pos`: Ghi nhận hóa đơn bán hàng thực tế vào `lich_su_ban_hang`, tự động bóc tách định mức BOM, trừ tồn kho nguyên liệu + trừ lô hàng hết hạn trước, và sinh giao dịch `XUAT_BAN`.
* `GET /api/v1/dinh-muc-bom/lich-su-pos`: Truy xuất lịch sử các hóa đơn bán hàng đã làm sạch và bóc tách định mức (lọc theo món, ca bán `SANG`/`CHIEU`/`TOI`).
* `POST /api/v1/dinh-muc-bom/chay-quy-trinh` & `GET /api/v1/dinh-muc-bom/bao-cao-chat-luong`: Kích hoạt và xem báo cáo kiểm định chất lượng dữ liệu.
* `GET /api/v1/dinh-muc-bom/chuoi-thoi-gian/{ma_nguyen_lieu}`: Truy xuất chuỗi thời gian tiêu hao kèm trung bình trượt 7 ngày.

---

## 2. Hạng mục hoàn thành phần Giao diện (Tuần 5)

### 2.1. Biểu đồ Xu hướng Tiêu thụ Nguyên liệu 12 Tháng trên Trang Tổng quan
* Cập nhật [`frontend/src/app/dashboard/page.tsx`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/frontend/src/app/dashboard/page.tsx):
  * Tích hợp biểu đồ kết hợp hiển thị song song cột khối lượng tiêu hao (kg/đv) và đường chi phí nguyên liệu ước tính (triệu VNĐ) qua 12 tháng.
  * Hiển thị độ tin cậy (`do_tin_cay` %) trên từng mốc ngày dự báo và nút điều hướng nhanh sang trang Định mức BOM & Làm sạch dữ liệu.

### 2.2. Trang Quản lý Định mức BOM, Làm sạch Dữ liệu & Chuỗi Thời Gian (`/bom`)
* Xây dựng mới trang [`frontend/src/app/bom/page.tsx`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/frontend/src/app/bom/page.tsx) và bổ sung vào thanh điều hướng:
  * **Bảng Kiểm định & Làm sạch Dữ liệu Bán hàng 12 Tháng:** Hiển thị tổng số dòng thô (`4,413`), số dòng sạch (`4,385` – `99.37%`), số dòng trùng lặp/khuyết thiếu/ngoại lai đã xử lý, kèm nút **"Chạy lại Quy trình Dữ liệu BOM"**.
  * **Bộ Mô phỏng Bóc tách Định mức & Xuất bán tại Quầy:** Cho phép nhập số lượng ly bán của từng món đồ uống để tính tức thì doanh thu, lợi nhuận gộp, lượng nguyên liệu cần dùng và bấm ghi nhận trừ kho tự động.
  * **Biểu đồ Chuỗi Thời Gian Tiêu Hao & Trung Bình Trượt 7 Ngày:** Biểu đồ trực quan cho toàn bộ 15 nguyên liệu trong 30/60/90 ngày, thống kê mức tăng trưởng tiêu thụ cuối tuần so với ngày thường.
  * **Bảng Ma trận 12 Món & Định mức Pha chế** và **Bảng Lịch sử Hóa đơn Bán hàng**.

### 2.3. Nâng cấp Trang Quản lý Tồn kho 3 Phân khu (`/inventory`)
* Cập nhật [`frontend/src/app/inventory/page.tsx`](file:///c:/Users/truon/OneDrive/Máy tính/DACN/frontend/src/app/inventory/page.tsx) với 3 thẻ nghiệp vụ:
  1. **Danh mục Tồn kho & Điểm đặt hàng lại (ROP):** Tra cứu, lọc nguyên liệu theo trạng thái `NGUY_CO_THIEU`, `TON_DU`, `AN_TOAN`.
  2. **Lô hàng & Hạn sử dụng:** Xem danh sách lô hàng sắp xếp theo hạn dùng, lọc nhanh các lô sắp hết hạn ($\le 7$ ngày) và Biểu mẫu nhập lô hàng mới vào kho.
  3. **Nhật ký Biến động Kho (`GIAO_DICH_KHO`):** Lọc lịch sử giao dịch theo `XUAT_BAN`, `NHAP`, `KIEM_KE`, `HAO_HUT` và Biểu mẫu ghi nhận kiểm kê/hao hụt trực tiếp.
