"""Bảng phân quyền giao diện theo vai trò (khớp 3 tài khoản mẫu trong README)."""

import os

# Bật/tắt đăng nhập + phân quyền ở giao diện. Mặc định TẮT. Bật lại: AUTH_ENABLED=true
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")

ROLE_LABELS = {
    "QUAN_LY": "Quản lý cửa hàng",
    "NHAN_VIEN_KHO": "Nhân viên kho",
    "ADMIN": "Quản trị hệ thống",
}

# Vai trò nào được mở trang nào
PAGE_ACCESS = {
    "/": {"QUAN_LY", "ADMIN"},
    "/dashboard": {"QUAN_LY", "ADMIN"},
    "/inventory": {"QUAN_LY", "NHAN_VIEN_KHO", "ADMIN"},
    "/forecast": {"QUAN_LY", "ADMIN"},
    "/suppliers": {"QUAN_LY", "NHAN_VIEN_KHO", "ADMIN"},
    "/proposals": {"QUAN_LY", "ADMIN"},
}

# Trang đầu tiên sau khi đăng nhập
HOME_PAGE = {
    "QUAN_LY": "/dashboard",
    "ADMIN": "/dashboard",
    "NHAN_VIEN_KHO": "/inventory",
}

# Chỉ các vai trò này được Phê duyệt / Từ chối phiếu đề xuất mua hàng
CAN_APPROVE = {"QUAN_LY"}
