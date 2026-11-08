# Tuần 1 (12/10 – 18/10) – Khảo sát đề tài, yêu cầu và phạm vi (phần Frontend)

**Người thực hiện:** Trần Anh Hào – Frontend Developer
**Đề tài:** AI Agent mua hàng và quản lý tồn kho (AI Procurement Agent)
**GVHD:** ThS. Trịnh Công Nhựt

## 1. Khảo sát đề tài

Công tác quản lý tồn kho phải cân bằng hai rủi ro: **thiếu nguyên liệu** (gián đoạn bán hàng) và **tồn dư quá mức**
(hỏng sữa/trái cây, đọng vốn). Hệ thống giải quyết bằng 4 bước: bóc tách nguyên liệu qua BOM →
dự báo nhu cầu 7 ngày → cảnh báo & chọn nhà cung cấp tối ưu → AI Agent lập đề xuất, **quản lý duyệt cuối cùng**
(Human-in-the-loop).

Vai trò của Frontend: là nơi quản lý **nhìn thấy** tình hình tồn kho, cảnh báo, dự báo và **ra quyết định duyệt**
đề xuất mua hàng. Agent chỉ đề xuất, không tự đặt hàng.

## 2. Người dùng hệ thống

| Vai trò | Mô tả | Việc chính trên giao diện |
|---|---|---|
| `QUAN_LY` | Quản lý cửa hàng | Xem cảnh báo, xem/sửa/duyệt/từ chối phiếu đề xuất |
| `NHAN_VIEN_KHO` | Nhân viên kho | Xem tồn kho, lô hàng, hạn sử dụng; theo dõi biến động kho |
| `ADMIN` | Quản trị | Quản lý người dùng, toàn quyền xem |

## 3. Yêu cầu chức năng (góc nhìn Frontend)

| Mã | Yêu cầu | Trang | Tuần dự kiến |
|---|---|---|---|
| FR-01 | Hiển thị số liệu tổng quan: số nguyên liệu, số cảnh báo thiếu/thừa, số phiếu chờ duyệt | Dashboard | 4 |
| FR-02 | Bảng tồn kho: tồn hiện tại so với mức tồn an toàn, trạng thái sử dụng | Tồn kho | 4 |
| FR-03 | Xem lô hàng và hạn sử dụng, đánh dấu sắp hết hạn | Tồn kho | 4 |
| FR-04 | Bảng nhà cung cấp và bảng báo giá (đơn giá, lead time, MOQ, độ uy tín) | Nhà cung cấp | 4 |
| FR-05 | Cảnh báo **NGUY CƠ THIẾU HÀNG** (tồn ≤ ROP) và **NGUY CƠ TỒN DƯ ĐỌNG VỐN** | Dashboard, Tồn kho | 4 |
| FR-06 | Biểu đồ xu hướng tiêu thụ 12 tháng | Dashboard | 5–6 |
| FR-07 | Biểu đồ dự báo nhu cầu 7 ngày (T+1…T+7) kèm độ tin cậy | Dashboard, Tồn kho | 6 |
| FR-08 | Danh sách và chi tiết phiếu đề xuất mua hàng, kèm lý do tổng quan và lý do từng dòng của AI | Đề xuất mua hàng | 8 |
| FR-09 | Duyệt / Từ chối / Sửa phiếu, nhập ý kiến phản hồi | Đề xuất mua hàng | 8 |
| FR-10 | Xem lịch sử duyệt | Đề xuất mua hàng | 8 |
| FR-11 | Đăng nhập, phân quyền hiển thị theo vai trò | Toàn hệ thống | 8 |
| FR-12 | Kích hoạt AI Agent lập đề xuất và hiển thị lập luận | Đề xuất mua hàng | 9 |

## 4. Yêu cầu phi chức năng

- Giao diện tiếng Việt, rõ ràng, dễ dùng cho người quản lý kho.
- Responsive (máy tính, máy tính bảng), tối ưu ở Tuần 11.
- Tên trường dữ liệu khớp 100% với CSDL (Mục 5 đặc tả).
- **Không có chức năng gửi đơn thẳng tới nhà cung cấp**; phiếu AI tạo luôn ở `CHO_DUYET`.

## 5. Phạm vi

**Trong phạm vi (Frontend):** dashboard quản trị, tồn kho, nhà cung cấp, đề xuất mua hàng và luồng duyệt, đăng nhập – phân quyền.
**Ngoài phạm vi:** đặt hàng thật với nhà cung cấp, thanh toán, tích hợp POS thật, ứng dụng di động.

## 6. Nguồn dữ liệu

Dataset công khai kết hợp **dữ liệu giả lập 12 tháng** (do AI/Data Engineer sinh, nạp vào PostgreSQL).
Frontend **không đọc trực tiếp CSDL**, chỉ gọi REST API của FastAPI.

## 7. Công nghệ Frontend đã chọn

Next.js 14+ (App Router, TypeScript), TailwindCSS, shadcn/ui, Lucide Icons, Recharts, Axios, TanStack Query.
