import csv
import math
import os
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.models.ingredient import Ingredient
from app.models.supplier import SupplierQuotation
from app.models.inventory import InventoryTransaction
from app.models.recipe import (
    MenuItem,
    RecipeBOM,
    LichSuBanHang,
    TieuHaoNguyenLieuNgay,
    NhatKyXuLyDuLieu,
)
from app.schemas.dinh_muc_bom import (
    ChiTietDinhMucBomOut,
    MonAnKemDinhMucBomOut,
    YeuCauLuuMonAnBom,
    YeuCauMoPhongBom,
    NguyenLieuTieuHaoOut,
    KetQuaMoPhongBom,
    YeuCauTaoHoaDonPos,
    LichSuBanHangOut,
    BaoCaoChatLuongDuLieuOut,
    DiemChuoiThoiGianTieuHaoOut,
    PhanHoiChuoiThoiGianNguyenLieu,
)
from app.services.inventory_service import deduct_batches_fefo

# Đường dẫn lưu trữ dữ liệu Thô và Sạch (Tiếng Việt)
THU_MUC_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THU_MUC_DU_LIEU_THO = os.path.join(THU_MUC_BACKEND, "du_lieu", "du_lieu_tho")
THU_MUC_DU_LIEU_SACH = os.path.join(THU_MUC_BACKEND, "du_lieu", "du_lieu_sach")

TEN_FILE_POS_THO = "lich_su_ban_hang_tho_12_thang.csv"
TEN_FILE_POS_SACH = "lich_su_ban_hang_sach_12_thang.csv"
TEN_FILE_CHUOI_TIEU_HAO = "tieu_hao_nguyen_lieu_ngay_12_thang.csv"

# ==============================================================================
# 1. THỰC ĐƠN 12 MÓN ĐỒ UỐNG CHUẨN QUÁN CÀ PHÊ & MA TRẬN ĐỊNH MỨC BOM (15 NGUYÊN LIỆU)
# ==============================================================================
DANH_SACH_THUC_DON_CHUAN: List[Dict[str, Any]] = [
    {
        "ma_mon": 1,
        "ten_mon": "Cà phê Đen Đá Buôn Ma Thuột",
        "danh_muc": "Cà phê truyền thống",
        "don_gia_ban": 29000.0,
        "so_ly_co_ban": 52,
    },
    {
        "ma_mon": 2,
        "ten_mon": "Cà phê Sữa Đá Sài Gòn",
        "danh_muc": "Cà phê truyền thống",
        "don_gia_ban": 35000.0,
        "so_ly_co_ban": 76,
    },
    {
        "ma_mon": 3,
        "ten_mon": "Bạc Xỉu Đá Đà Lạt",
        "danh_muc": "Cà phê truyền thống",
        "don_gia_ban": 39000.0,
        "so_ly_co_ban": 45,
    },
    {
        "ma_mon": 4,
        "ten_mon": "Cà phê Sữa Tươi Pha Máy",
        "danh_muc": "Cà phê máy",
        "don_gia_ban": 49000.0,
        "so_ly_co_ban": 38,
    },
    {
        "ma_mon": 5,
        "ten_mon": "Cà phê Bọt Sữa Ý Cầu Đất",
        "danh_muc": "Cà phê máy",
        "don_gia_ban": 49000.0,
        "so_ly_co_ban": 26,
    },
    {
        "ma_mon": 6,
        "ten_mon": "Cà phê Socola Đá Xay",
        "danh_muc": "Đá xay",
        "don_gia_ban": 55000.0,
        "so_ly_co_ban": 22,
    },
    {
        "ma_mon": 7,
        "ten_mon": "Trà Đào Cam Sả Đặc Biệt",
        "danh_muc": "Trà trái cây",
        "don_gia_ban": 45000.0,
        "so_ly_co_ban": 54,
    },
    {
        "ma_mon": 8,
        "ten_mon": "Trà Dâu Tằm Pha Lê Tuyết",
        "danh_muc": "Trà trái cây",
        "don_gia_ban": 45000.0,
        "so_ly_co_ban": 34,
    },
    {
        "ma_mon": 9,
        "ten_mon": "Trà Sữa Ô Long Bảo Lộc",
        "danh_muc": "Trà sữa",
        "don_gia_ban": 45000.0,
        "so_ly_co_ban": 44,
    },
    {
        "ma_mon": 10,
        "ten_mon": "Trà Xanh Sữa Nhật Bản",
        "danh_muc": "Trà xanh",
        "don_gia_ban": 52000.0,
        "so_ly_co_ban": 28,
    },
    {
        "ma_mon": 11,
        "ten_mon": "Trà Xanh Đá Xay Kem Tuyết",
        "danh_muc": "Đá xay",
        "don_gia_ban": 59000.0,
        "so_ly_co_ban": 20,
    },
    {
        "ma_mon": 12,
        "ten_mon": "Cacao Socola Đắk Lắk Đá",
        "danh_muc": "Socola & Cacao",
        "don_gia_ban": 45000.0,
        "so_ly_co_ban": 24,
    },
]

# Định mức BOM chuẩn xác trên từng ly đồ uống (Bao phủ 100% cả 15 nguyên liệu)
DANH_SACH_CONG_THUC_BOM_CHUAN: List[Dict[str, Any]] = [
    # Món 1: Cà phê Đen Đá Buôn Ma Thuột
    {"ma_mon": 1, "ma_nguyen_lieu": 1, "so_luong_tieu_hao": 0.025, "ghi_chu": "25g hạt Robusta"},
    {"ma_mon": 1, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 1, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 2: Cà phê Sữa Đá Sài Gòn
    {"ma_mon": 2, "ma_nguyen_lieu": 1, "so_luong_tieu_hao": 0.022, "ghi_chu": "22g hạt Robusta"},
    {"ma_mon": 2, "ma_nguyen_lieu": 4, "so_luong_tieu_hao": 0.030, "ghi_chu": "0.03 lon sữa đặc (~38g)"},
    {"ma_mon": 2, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 2, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 3: Bạc Xỉu Đá Đà Lạt
    {"ma_mon": 3, "ma_nguyen_lieu": 1, "so_luong_tieu_hao": 0.015, "ghi_chu": "15g hạt Robusta"},
    {"ma_mon": 3, "ma_nguyen_lieu": 4, "so_luong_tieu_hao": 0.035, "ghi_chu": "0.035 lon sữa đặc"},
    {"ma_mon": 3, "ma_nguyen_lieu": 5, "so_luong_tieu_hao": 0.080, "ghi_chu": "80ml sữa thanh trùng Đà Lạt"},
    {"ma_mon": 3, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 3, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 4: Cà phê Sữa Tươi Pha Máy
    {"ma_mon": 4, "ma_nguyen_lieu": 2, "so_luong_tieu_hao": 0.020, "ghi_chu": "20g hạt Arabica Cầu Đất"},
    {"ma_mon": 4, "ma_nguyen_lieu": 3, "so_luong_tieu_hao": 0.180, "ghi_chu": "180ml sữa tươi pha chế"},
    {"ma_mon": 4, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly tiêu chuẩn"},
    {"ma_mon": 4, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 5: Cà phê Bọt Sữa Ý Cầu Đất
    {"ma_mon": 5, "ma_nguyen_lieu": 2, "so_luong_tieu_hao": 0.018, "ghi_chu": "18g hạt Arabica Cầu Đất"},
    {"ma_mon": 5, "ma_nguyen_lieu": 3, "so_luong_tieu_hao": 0.150, "ghi_chu": "150ml sữa tươi tạo bọt"},
    {"ma_mon": 5, "ma_nguyen_lieu": 9, "so_luong_tieu_hao": 0.003, "ghi_chu": "3g bột cacao rắc mặt"},
    {"ma_mon": 5, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly tiêu chuẩn"},
    {"ma_mon": 5, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 6: Cà phê Socola Đá Xay
    {"ma_mon": 6, "ma_nguyen_lieu": 2, "so_luong_tieu_hao": 0.018, "ghi_chu": "18g hạt Arabica"},
    {"ma_mon": 6, "ma_nguyen_lieu": 3, "so_luong_tieu_hao": 0.100, "ghi_chu": "100ml sữa tươi"},
    {"ma_mon": 6, "ma_nguyen_lieu": 8, "so_luong_tieu_hao": 0.025, "ghi_chu": "0.025 chai xốt Socola"},
    {"ma_mon": 6, "ma_nguyen_lieu": 11, "so_luong_tieu_hao": 0.020, "ghi_chu": "20g bột nền đá xay"},
    {"ma_mon": 6, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 6, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 7: Trà Đào Cam Sả Đặc Biệt
    {"ma_mon": 7, "ma_nguyen_lieu": 12, "so_luong_tieu_hao": 0.015, "ghi_chu": "15g cốt trà đen Phúc Long"},
    {"ma_mon": 7, "ma_nguyen_lieu": 6, "so_luong_tieu_hao": 0.040, "ghi_chu": "0.04 chai siro Đào (~28ml)"},
    {"ma_mon": 7, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 7, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 8: Trà Dâu Tằm Pha Lê Tuyết
    {"ma_mon": 8, "ma_nguyen_lieu": 13, "so_luong_tieu_hao": 0.015, "ghi_chu": "15g cốt trà Ô Long"},
    {"ma_mon": 8, "ma_nguyen_lieu": 7, "so_luong_tieu_hao": 0.040, "ghi_chu": "0.04 chai siro Dâu (~30ml)"},
    {"ma_mon": 8, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 8, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 9: Trà Sữa Ô Long Bảo Lộc
    {"ma_mon": 9, "ma_nguyen_lieu": 13, "so_luong_tieu_hao": 0.018, "ghi_chu": "18g trà Ô Long Kim Tuyên"},
    {"ma_mon": 9, "ma_nguyen_lieu": 4, "so_luong_tieu_hao": 0.025, "ghi_chu": "0.025 lon sữa đặc"},
    {"ma_mon": 9, "ma_nguyen_lieu": 5, "so_luong_tieu_hao": 0.070, "ghi_chu": "70ml sữa thanh trùng"},
    {"ma_mon": 9, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 9, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 10: Trà Xanh Sữa Nhật Bản
    {"ma_mon": 10, "ma_nguyen_lieu": 10, "so_luong_tieu_hao": 0.012, "ghi_chu": "12g bột trà xanh Nhật Bản"},
    {"ma_mon": 10, "ma_nguyen_lieu": 3, "so_luong_tieu_hao": 0.160, "ghi_chu": "160ml sữa tươi pha chế"},
    {"ma_mon": 10, "ma_nguyen_lieu": 4, "so_luong_tieu_hao": 0.015, "ghi_chu": "0.015 lon sữa đặc"},
    {"ma_mon": 10, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 10, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 11: Trà Xanh Đá Xay Kem Tuyết
    {"ma_mon": 11, "ma_nguyen_lieu": 10, "so_luong_tieu_hao": 0.015, "ghi_chu": "15g bột trà xanh Nhật Bản"},
    {"ma_mon": 11, "ma_nguyen_lieu": 5, "so_luong_tieu_hao": 0.100, "ghi_chu": "100ml sữa thanh trùng"},
    {"ma_mon": 11, "ma_nguyen_lieu": 11, "so_luong_tieu_hao": 0.025, "ghi_chu": "25g bột nền đá xay"},
    {"ma_mon": 11, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 11, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},

    # Món 12: Cacao Socola Đắk Lắk Đá
    {"ma_mon": 12, "ma_nguyen_lieu": 9, "so_luong_tieu_hao": 0.025, "ghi_chu": "25g bột Cacao nguyên chất"},
    {"ma_mon": 12, "ma_nguyen_lieu": 8, "so_luong_tieu_hao": 0.020, "ghi_chu": "0.02 chai xốt Socola"},
    {"ma_mon": 12, "ma_nguyen_lieu": 4, "so_luong_tieu_hao": 0.025, "ghi_chu": "0.025 lon sữa đặc"},
    {"ma_mon": 12, "ma_nguyen_lieu": 3, "so_luong_tieu_hao": 0.100, "ghi_chu": "100ml sữa tươi"},
    {"ma_mon": 12, "ma_nguyen_lieu": 14, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ly nhựa PET 500ml"},
    {"ma_mon": 12, "ma_nguyen_lieu": 15, "so_luong_tieu_hao": 1.0, "ghi_chu": "1 ống hút giấy"},
]

# Hệ số mùa vụ theo tháng (Tháng 1 -> Tháng 12)
HE_SO_MUA_VU_THANG: Dict[int, float] = {
    1: 1.25,
    2: 1.22,
    3: 1.02,
    4: 1.08,
    5: 1.12,
    6: 1.06,
    7: 1.04,
    8: 0.96,
    9: 0.94,
    10: 1.03,
    11: 1.18,
    12: 1.32,
}

# Hệ số chu kỳ thứ trong tuần (0=Thứ Hai ... 6=Chủ Nhật)
HE_SO_THU_TRONG_TUAN: Dict[int, float] = {
    0: 0.88,
    1: 0.92,
    2: 0.95,
    3: 1.00,
    4: 1.12,
    5: 1.36,
    6: 1.42,
}


def khoi_tao_thuc_don_va_dinh_muc_bom(db: Session) -> None:
    """Đảm bảo CSDL luôn có đủ 12 món đồ uống và 56 dòng định mức BOM phủ kín 15 nguyên liệu."""
    so_mon_hien_tai = db.query(MenuItem).count()
    so_bom_hien_tai = db.query(RecipeBOM).count()

    if so_mon_hien_tai == len(DANH_SACH_THUC_DON_CHUAN) and so_bom_hien_tai == len(DANH_SACH_CONG_THUC_BOM_CHUAN):
        return

    db.query(RecipeBOM).delete()
    db.query(MenuItem).delete()
    db.commit()

    for m in DANH_SACH_THUC_DON_CHUAN:
        db.add(
            MenuItem(
                ma_mon=m["ma_mon"],
                ten_mon=m["ten_mon"],
                danh_muc=m["danh_muc"],
                don_gia_ban=m["don_gia_ban"],
                trang_thai=True,
            )
        )
    db.commit()

    for idx, b in enumerate(DANH_SACH_CONG_THUC_BOM_CHUAN, start=1):
        db.add(
            RecipeBOM(
                ma_dinh_muc=idx,
                ma_mon=b["ma_mon"],
                ma_nguyen_lieu=b["ma_nguyen_lieu"],
                so_luong_tieu_hao=b["so_luong_tieu_hao"],
                ghi_chu=b["ghi_chu"],
            )
        )
    db.commit()


def sinh_du_lieu_ban_hang_tho_12_thang(so_ngay: int = 365, hat_giong: int = 202605) -> List[Dict[str, Any]]:
    """
    Bước 1 (Thu thập dữ liệu): Sinh tập dữ liệu bán hàng POS thô 12 tháng (365 ngày).
    Cố tình tiêm các lỗi dữ liệu thực tế từ máy bán hàng để kiểm định bộ lọc làm sạch:
      - Bản ghi trùng lặp (do lỗi mạng máy POS gửi đúp)
      - Giá trị khuyết thiếu (thiếu số lượng hoặc thiếu đơn giá)
      - Giá trị âm hoặc bằng 0 (nhập nhầm hoàn trả vào bảng bán hàng)
      - Điểm ngoại lai cực đoan (kẹt phím số lượng 850 - 1200 ly)
    """
    rng = random.Random(hat_giong)
    hom_nay = date.today()
    ngay_bat_dau = hom_nay - timedelta(days=so_ngay - 1)
    cac_ca_ban = ["SANG", "CHIEU", "TOI"]

    danh_sach_ban_ghi_tho: List[Dict[str, Any]] = []

    for chi_so_ngay in range(so_ngay):
        ngay_hien_tai = ngay_bat_dau + timedelta(days=chi_so_ngay)
        he_so_thang = HE_SO_MUA_VU_THANG.get(ngay_hien_tai.month, 1.0)
        he_so_thu = HE_SO_THU_TRONG_TUAN.get(ngay_hien_tai.weekday(), 1.0)

        for m in DANH_SACH_THUC_DON_CHUAN:
            ma_mon = m["ma_mon"]
            so_ly_co_ban = m["so_ly_co_ban"]
            nhieu_ngau_nhien = rng.uniform(0.88, 1.14)
            so_ly = max(5, int(round(so_ly_co_ban * he_so_thang * he_so_thu * nhieu_ngau_nhien)))
            ca_ban = cac_ca_ban[(chi_so_ngay + ma_mon) % len(cac_ca_ban)]
            ma_hoa_don = f"POS-{ngay_hien_tai.strftime('%Y%m%d')}-M{ma_mon:02d}"

            ban_ghi = {
                "ma_hoa_don_pos": ma_hoa_don,
                "ngay_ban": ngay_hien_tai.isoformat(),
                "ca_ban": ca_ban,
                "ma_mon": ma_mon,
                "ten_mon": m["ten_mon"],
                "so_luong_ly": so_ly,
                "don_gia_ban": m["don_gia_ban"],
            }
            danh_sach_ban_ghi_tho.append(ban_ghi)

            # 1. Tiêm bản ghi trùng lặp (16 dòng)
            if chi_so_ngay in (15, 45, 75, 105, 135, 165, 195, 225) and ma_mon in (1, 2):
                danh_sach_ban_ghi_tho.append(dict(ban_ghi))

            # 2. Tiêm bản ghi thiếu dữ liệu (10 dòng)
            if chi_so_ngay in (28, 88, 148, 208, 268) and ma_mon == 3:
                danh_sach_ban_ghi_tho.append({
                    "ma_hoa_don_pos": f"POS-THIEU-SL-{chi_so_ngay}",
                    "ngay_ban": ngay_hien_tai.isoformat(),
                    "ca_ban": "CHIEU",
                    "ma_mon": ma_mon,
                    "ten_mon": m["ten_mon"],
                    "so_luong_ly": None,
                    "don_gia_ban": m["don_gia_ban"],
                })
            if chi_so_ngay in (38, 98, 158, 218, 278) and ma_mon == 7:
                danh_sach_ban_ghi_tho.append({
                    "ma_hoa_don_pos": f"POS-THIEU-GIA-{chi_so_ngay}",
                    "ngay_ban": ngay_hien_tai.isoformat(),
                    "ca_ban": "SANG",
                    "ma_mon": ma_mon,
                    "ten_mon": m["ten_mon"],
                    "so_luong_ly": 35,
                    "don_gia_ban": "",
                })

            # 3. Tiêm bản ghi số lượng âm hoặc bằng 0 (7 dòng)
            if chi_so_ngay in (50, 110, 170, 230, 290, 320, 340) and ma_mon == 4:
                danh_sach_ban_ghi_tho.append({
                    "ma_hoa_don_pos": f"POS-LOI-AM-{chi_so_ngay}",
                    "ngay_ban": ngay_hien_tai.isoformat(),
                    "ca_ban": "TOI",
                    "ma_mon": ma_mon,
                    "ten_mon": m["ten_mon"],
                    "so_luong_ly": -15 if chi_so_ngay % 2 == 0 else 0,
                    "don_gia_ban": m["don_gia_ban"],
                })

            # 4. Tiêm ngoại lai cực đoan do kẹt phím máy POS (9 dòng)
            if chi_so_ngay in (33, 66, 99, 132, 166, 199, 233, 266, 299) and ma_mon == 2:
                ban_ghi["so_luong_ly"] = 999

    os.makedirs(THU_MUC_DU_LIEU_THO, exist_ok=True)
    duong_dan_csv_tho = os.path.join(THU_MUC_DU_LIEU_THO, TEN_FILE_POS_THO)
    with open(duong_dan_csv_tho, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ma_hoa_don_pos",
                "ngay_ban",
                "ca_ban",
                "ma_mon",
                "ten_mon",
                "so_luong_ly",
                "don_gia_ban",
            ],
        )
        writer.writeheader()
        writer.writerows(danh_sach_ban_ghi_tho)

    return danh_sach_ban_ghi_tho


def _tinh_phan_vi(gia_tri_da_sap_xep: List[float], phan_vi: float) -> float:
    if not gia_tri_da_sap_xep:
        return 0.0
    k = (len(gia_tri_da_sap_xep) - 1) * phan_vi
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return gia_tri_da_sap_xep[int(k)]
    return gia_tri_da_sap_xep[f] * (c - k) + gia_tri_da_sap_xep[c] * (k - f)


def lam_sach_du_lieu_ban_hang(
    danh_sach_ban_ghi_tho: List[Dict[str, Any]],
    bang_gia_thuc_don: Dict[int, float],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Bước 2 (Làm sạch dữ liệu):
      1. Khử trùng lặp theo khóa (ma_hoa_don_pos, ma_mon).
      2. Xử lý dữ liệu khuyết thiếu:
         - Nếu thiếu don_gia_ban -> tự động điền từ bảng giá chuẩn.
         - Nếu thiếu ngay_ban, ma_mon hoặc so_luong_ly -> loại bỏ dòng hỏng.
      3. Loại bỏ các dòng có so_luong_ly <= 0.
      4. Phát hiện và cắt ngưỡng ngoại lai bằng khoảng tứ phân vị IQR trên từng món:
         Ngưỡng trên = Q3 + 3.0 * IQR. Nếu vượt ngưỡng sẽ đưa về trung vị nhân hệ số thứ trong tuần.
    """
    thong_ke = {
        "tong_dong_tho": len(danh_sach_ban_ghi_tho),
        "so_dong_trung_lap": 0,
        "so_dong_thieu_du_lieu": 0,
        "so_dong_am_hoac_loi": 0,
        "so_dong_ngoai_lai_da_xu_ly": 0,
    }

    khoa_da_gap = set()
    danh_sach_hop_le: List[Dict[str, Any]] = []

    for dong in danh_sach_ban_ghi_tho:
        ma_hd = str(dong.get("ma_hoa_don_pos") or "").strip()
        ma_mon_tho = dong.get("ma_mon")
        ngay_tho = dong.get("ngay_ban")
        so_luong_tho = dong.get("so_luong_ly")
        don_gia_tho = dong.get("don_gia_ban")

        if not ma_hd or ma_mon_tho is None or not ngay_tho:
            thong_ke["so_dong_thieu_du_lieu"] += 1
            continue

        ma_mon = int(ma_mon_tho)
        khoa = (ma_hd, ma_mon)
        if khoa in khoa_da_gap:
            thong_ke["so_dong_trung_lap"] += 1
            continue
        khoa_da_gap.add(khoa)

        if so_luong_tho is None or str(so_luong_tho).strip() == "":
            thong_ke["so_dong_thieu_du_lieu"] += 1
            continue

        try:
            so_ly = float(so_luong_tho)
        except ValueError:
            thong_ke["so_dong_thieu_du_lieu"] += 1
            continue

        if so_ly <= 0:
            thong_ke["so_dong_am_hoac_loi"] += 1
            continue

        if don_gia_tho is None or str(don_gia_tho).strip() == "":
            thong_ke["so_dong_thieu_du_lieu"] += 1
            don_gia = bang_gia_thuc_don.get(ma_mon, 39000.0)
        else:
            try:
                don_gia = float(don_gia_tho)
                if don_gia <= 0:
                    don_gia = bang_gia_thuc_don.get(ma_mon, 39000.0)
            except ValueError:
                don_gia = bang_gia_thuc_don.get(ma_mon, 39000.0)

        ngay_parsed = date.fromisoformat(str(ngay_tho))
        danh_sach_hop_le.append({
            "ma_hoa_don_pos": ma_hd,
            "ngay_ban": ngay_parsed,
            "ca_ban": str(dong.get("ca_ban") or "SANG"),
            "ma_mon": ma_mon,
            "ten_mon": dong.get("ten_mon") or "",
            "so_luong_ly": so_ly,
            "don_gia_ban": don_gia,
        })

    # Bước 4: Xử lý ngoại lai theo phân phối IQR của từng món đồ uống
    phan_phoi_theo_mon: Dict[int, List[float]] = defaultdict(list)
    for r in danh_sach_hop_le:
        phan_phoi_theo_mon[r["ma_mon"]].append(r["so_luong_ly"])

    nguong_theo_mon: Dict[int, Tuple[float, float]] = {}
    for ma_mon, ds_sl in phan_phoi_theo_mon.items():
        ds_sap_xep = sorted(ds_sl)
        q1 = _tinh_phan_vi(ds_sap_xep, 0.25)
        trung_vi = _tinh_phan_vi(ds_sap_xep, 0.50)
        q3 = _tinh_phan_vi(ds_sap_xep, 0.75)
        iqr = max(1.0, q3 - q1)
        nguong_tren = q3 + 3.0 * iqr
        nguong_theo_mon[ma_mon] = (nguong_tren, trung_vi)

    for r in danh_sach_hop_le:
        ma_mon = r["ma_mon"]
        nguong_tren, trung_vi = nguong_theo_mon[ma_mon]
        if r["so_luong_ly"] > nguong_tren:
            thong_ke["so_dong_ngoai_lai_da_xu_ly"] += 1
            he_so_thu = HE_SO_THU_TRONG_TUAN.get(r["ngay_ban"].weekday(), 1.0)
            r["so_luong_ly"] = float(round(trung_vi * he_so_thu))
        r["thanh_tien"] = round(r["so_luong_ly"] * r["don_gia_ban"], 2)

    os.makedirs(THU_MUC_DU_LIEU_SACH, exist_ok=True)
    duong_dan_csv_sach = os.path.join(THU_MUC_DU_LIEU_SACH, TEN_FILE_POS_SACH)
    with open(duong_dan_csv_sach, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ma_hoa_don_pos",
                "ngay_ban",
                "ca_ban",
                "ma_mon",
                "ten_mon",
                "so_luong_ly",
                "don_gia_ban",
                "thanh_tien",
            ],
        )
        writer.writeheader()
        for r in danh_sach_hop_le:
            writer.writerow({
                **r,
                "ngay_ban": r["ngay_ban"].isoformat(),
            })

    return danh_sach_hop_le, thong_ke


def chay_quy_trinh_boc_tach_bom(db: Session, so_ngay: int = 365) -> BaoCaoChatLuongDuLieuOut:
    """
    Thực thi trọn vẹn Quy trình Dữ liệu Tuần 5:
      1. Đảm bảo thực đơn 12 món & 56 định mức BOM đã nạp.
      2. Sinh dữ liệu bán hàng POS thô 12 tháng -> làm sạch dữ liệu -> lưu vào bảng `lich_su_ban_hang`.
      3. Bóc tách định mức BOM theo công thức:
         Tiêu hao(nguyên_liệu_i, ngày_t) = Tổng_m [ Số_ly_bán(m, ngày_t) * Định_mức_BOM(m, i) ]
      4. Tính toán các đặc trưng chuỗi thời gian (`tieu_hao_hom_truoc`, `tieu_hao_7_ngay_truoc`,
         `trung_binh_truot_7_ngay`, `do_lech_chuan_7_ngay`, `la_cuoi_tuan`, `he_so_mua_vu`)
         và lưu vào bảng `tieu_hao_nguyen_lieu_ngay` + xuất file CSV tiếng Việt.
      5. Đồng bộ giao dịch `XUAT_BAN` theo tháng vào bảng `giao_dich_kho` và lưu nhật ký kiểm định.
    """
    khoi_tao_thuc_don_va_dinh_muc_bom(db)

    bang_gia_mon = {m.ma_mon: m.don_gia_ban for m in db.query(MenuItem).all()}
    so_do_bom: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
    for b in db.query(RecipeBOM).all():
        so_do_bom[b.ma_mon].append((b.ma_nguyen_lieu, b.so_luong_tieu_hao))

    danh_sach_ma_nguyen_lieu = sorted([i.ma_nguyen_lieu for i in db.query(Ingredient).all()])
    if not danh_sach_ma_nguyen_lieu:
        danh_sach_ma_nguyen_lieu = list(range(1, 16))

    # 1 & 2. Sinh dữ liệu POS thô và làm sạch
    du_lieu_tho = sinh_du_lieu_ban_hang_tho_12_thang(so_ngay=so_ngay)
    du_lieu_sach, thong_ke = lam_sach_du_lieu_ban_hang(du_lieu_tho, bang_gia_mon)

    # Làm mới bảng lịch sử bán hàng POS và chuỗi tiêu hao nguyên liệu ngày
    db.query(LichSuBanHang).delete()
    db.query(TieuHaoNguyenLieuNgay).delete()
    db.commit()

    danh_sach_doi_tuong_pos: List[LichSuBanHang] = []
    tieu_hao_theo_ngay: Dict[Tuple[date, int], float] = defaultdict(float)
    so_ly_theo_ngay: Dict[Tuple[date, int], int] = defaultdict(int)
    tap_ngay_du_lieu = set()

    for r in du_lieu_sach:
        d: date = r["ngay_ban"]
        tap_ngay_du_lieu.add(d)
        ma_mon: int = r["ma_mon"]
        so_ly: float = r["so_luong_ly"]

        danh_sach_doi_tuong_pos.append(
            LichSuBanHang(
                ma_hoa_don_pos=r["ma_hoa_don_pos"],
                ngay_ban=d,
                ca_ban=r["ca_ban"],
                ma_mon=ma_mon,
                so_luong_ly=so_ly,
                don_gia_ban=r["don_gia_ban"],
                thanh_tien=r["thanh_tien"],
                da_boc_tach_bom=True,
            )
        )

        # 3. Bóc tách định mức BOM
        for ma_nl, dinh_muc_1_ly in so_do_bom.get(ma_mon, []):
            tieu_hao_theo_ngay[(d, ma_nl)] += so_ly * dinh_muc_1_ly
            so_ly_theo_ngay[(d, ma_nl)] += int(round(so_ly))

    db.bulk_save_objects(danh_sach_doi_tuong_pos)
    db.commit()

    # 4. Tạo đặc trưng chuỗi thời gian cho từng nguyên liệu trên toàn bộ 365 ngày
    cac_ngay_sap_xep = sorted(tap_ngay_du_lieu)
    danh_sach_doi_tuong_tieu_hao: List[TieuHaoNguyenLieuNgay] = []
    danh_sach_dong_csv: List[Dict[str, Any]] = []

    for ma_nl in danh_sach_ma_nguyen_lieu:
        lich_su_gia_tri: List[float] = []
        for idx, d in enumerate(cac_ngay_sap_xep):
            luong_tieu_hao = round(tieu_hao_theo_ngay.get((d, ma_nl), 0.0), 3)
            so_ly_lien_quan = so_ly_theo_ngay.get((d, ma_nl), 0)
            thu = d.weekday()
            cuoi_tuan = thu in (5, 6)
            he_so_mua = HE_SO_MUA_VU_THANG.get(d.month, 1.0)

            hom_truoc = lich_su_gia_tri[-1] if idx >= 1 else luong_tieu_hao
            cach_7_ngay = lich_su_gia_tri[-7] if idx >= 7 else luong_tieu_hao

            cua_so_7_ngay = (lich_su_gia_tri[-6:] + [luong_tieu_hao]) if lich_su_gia_tri else [luong_tieu_hao]
            tb_truot_7d = round(sum(cua_so_7_ngay) / len(cua_so_7_ngay), 3)
            if len(cua_so_7_ngay) > 1:
                phuong_sai = sum((x - tb_truot_7d) ** 2 for x in cua_so_7_ngay) / len(cua_so_7_ngay)
                do_lech_chuan_7d = round(math.sqrt(phuong_sai), 3)
            else:
                do_lech_chuan_7d = 0.0

            lich_su_gia_tri.append(luong_tieu_hao)

            danh_sach_doi_tuong_tieu_hao.append(
                TieuHaoNguyenLieuNgay(
                    ngay=d,
                    ma_nguyen_lieu=ma_nl,
                    so_luong_tieu_hao=luong_tieu_hao,
                    so_ly_lien_quan=so_ly_lien_quan,
                    thu_trong_tuan=thu,
                    la_cuoi_tuan=cuoi_tuan,
                    he_so_mua_vu=he_so_mua,
                    tieu_hao_hom_truoc=hom_truoc,
                    tieu_hao_7_ngay_truoc=cach_7_ngay,
                    trung_binh_truot_7_ngay=tb_truot_7d,
                    do_lech_chuan_7_ngay=do_lech_chuan_7d,
                )
            )

            danh_sach_dong_csv.append({
                "ngay": d.isoformat(),
                "ma_nguyen_lieu": ma_nl,
                "so_luong_tieu_hao": luong_tieu_hao,
                "so_ly_lien_quan": so_ly_lien_quan,
                "thu_trong_tuan": thu,
                "la_cuoi_tuan": int(cuoi_tuan),
                "he_so_mua_vu": he_so_mua,
                "tieu_hao_hom_truoc": hom_truoc,
                "tieu_hao_7_ngay_truoc": cach_7_ngay,
                "trung_binh_truot_7_ngay": tb_truot_7d,
                "do_lech_chuan_7_ngay": do_lech_chuan_7d,
            })

    db.bulk_save_objects(danh_sach_doi_tuong_tieu_hao)
    db.commit()

    # Xuất file CSV chuỗi thời gian tiêu hao bằng Tiếng Việt chuẩn bị cho Tuần 6
    duong_dan_csv_tieu_hao = os.path.join(THU_MUC_DU_LIEU_SACH, TEN_FILE_CHUOI_TIEU_HAO)
    with open(duong_dan_csv_tieu_hao, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ngay",
                "ma_nguyen_lieu",
                "so_luong_tieu_hao",
                "so_ly_lien_quan",
                "thu_trong_tuan",
                "la_cuoi_tuan",
                "he_so_mua_vu",
                "tieu_hao_hom_truoc",
                "tieu_hao_7_ngay_truoc",
                "trung_binh_truot_7_ngay",
                "do_lech_chuan_7_ngay",
            ],
        )
        writer.writeheader()
        writer.writerows(danh_sach_dong_csv)

    # 5. Đồng bộ tổng hợp giao dịch XUAT_BAN theo tháng từ kết quả bóc tách BOM vào bảng giao_dich_kho
    db.query(InventoryTransaction).filter(
        InventoryTransaction.ma_tham_chieu.like("BOM-THANG-%")
    ).delete(synchronize_session=False)

    tong_hop_thang: Dict[Tuple[int, int, int], float] = defaultdict(float)
    ngay_cuoi_thang: Dict[Tuple[int, int], date] = {}
    for (d, ma_nl), sl in tieu_hao_theo_ngay.items():
        ym = (d.year, d.month)
        tong_hop_thang[(d.year, d.month, ma_nl)] += sl
        if ym not in ngay_cuoi_thang or d > ngay_cuoi_thang[ym]:
            ngay_cuoi_thang[ym] = d

    for (nam, thang, ma_nl), tong_sl in sorted(tong_hop_thang.items()):
        ngay_gd = ngay_cuoi_thang[(nam, thang)]
        db.add(
            InventoryTransaction(
                ma_nguyen_lieu=ma_nl,
                loai_giao_dich="XUAT_BAN",
                so_luong=round(tong_sl, 2),
                ngay_giao_dich=datetime(ngay_gd.year, ngay_gd.month, ngay_gd.day, 21, 30, 0),
                ma_tham_chieu=f"BOM-THANG-{nam}{thang:02d}-NL{ma_nl:02d}",
                ghi_chu=f"Tổng hợp tiêu hao bóc tách định mức BOM tháng {thang:02d}/{nam}",
            )
        )
    db.commit()

    tong_tho = thong_ke["tong_dong_tho"]
    tong_sach = len(du_lieu_sach)
    ty_le_sach = round((tong_sach / tong_tho * 100.0), 2) if tong_tho > 0 else 100.0

    nhat_ky = NhatKyXuLyDuLieu(
        ten_quy_trinh="QUY_TRINH_BOC_TACH_DINH_MUC_V1",
        tong_dong_tho=tong_tho,
        so_dong_trung_lap=thong_ke["so_dong_trung_lap"],
        so_dong_thieu_du_lieu=thong_ke["so_dong_thieu_du_lieu"],
        so_dong_am_hoac_loi=thong_ke["so_dong_am_hoac_loi"],
        so_dong_ngoai_lai_da_xu_ly=thong_ke["so_dong_ngoai_lai_da_xu_ly"],
        tong_dong_sach=tong_sach,
        ty_le_du_lieu_sach=ty_le_sach,
        so_ngay_xu_ly=len(cac_ngay_sap_xep),
        tong_ban_ghi_tieu_hao_sinh_ra=len(danh_sach_doi_tuong_tieu_hao),
        trang_thai="THANH_CONG",
        ghi_chu=(
            f"Đã làm sạch {tong_sach}/{tong_tho} bản ghi bán hàng POS ({ty_le_sach}%), "
            f"xử lý {thong_ke['so_dong_ngoai_lai_da_xu_ly']} ngoại lai IQR và bóc tách 12 món thành "
            f"{len(danh_sach_doi_tuong_tieu_hao)} điểm dữ liệu chuỗi thời gian của 15 nguyên liệu."
        ),
    )
    db.add(nhat_ky)
    db.commit()
    db.refresh(nhat_ky)

    return BaoCaoChatLuongDuLieuOut(
        ma_lan_chay=nhat_ky.ma_lan_chay,
        ten_quy_trinh=nhat_ky.ten_quy_trinh,
        thoi_gian_chay=nhat_ky.thoi_gian_chay,
        tong_dong_tho=nhat_ky.tong_dong_tho,
        so_dong_trung_lap=nhat_ky.so_dong_trung_lap,
        so_dong_thieu_du_lieu=nhat_ky.so_dong_thieu_du_lieu,
        so_dong_am_hoac_loi=nhat_ky.so_dong_am_hoac_loi,
        so_dong_ngoai_lai_da_xu_ly=nhat_ky.so_dong_ngoai_lai_da_xu_ly,
        tong_dong_sach=nhat_ky.tong_dong_sach,
        ty_le_du_lieu_sach=nhat_ky.ty_le_du_lieu_sach,
        so_ngay_xu_ly=nhat_ky.so_ngay_xu_ly,
        tong_ban_ghi_tieu_hao_sinh_ra=nhat_ky.tong_ban_ghi_tieu_hao_sinh_ra,
        trang_thai=nhat_ky.trang_thai,
        ghi_chu=nhat_ky.ghi_chu,
        duong_dan_file_tho=f"backend/du_lieu/du_lieu_tho/{TEN_FILE_POS_THO}",
        duong_dan_file_sach=f"backend/du_lieu/du_lieu_sach/{TEN_FILE_POS_SACH}",
        duong_dan_file_tieu_hao=f"backend/du_lieu/du_lieu_sach/{TEN_FILE_CHUOI_TIEU_HAO}",
    )


def _lay_bang_don_gia_nguyen_lieu_chuan(db: Session) -> Dict[int, float]:
    """Lấy đơn giá chuẩn (thấp nhất từ báo giá Nhà cung cấp) của từng nguyên liệu để tính giá vốn."""
    danh_sach_bao_gia = db.query(SupplierQuotation).all()
    bang_gia: Dict[int, float] = {}
    for bg in danh_sach_bao_gia:
        if bg.ma_nguyen_lieu not in bang_gia or bg.don_gia < bang_gia[bg.ma_nguyen_lieu]:
            bang_gia[bg.ma_nguyen_lieu] = bg.don_gia
    return bang_gia


def lay_thuc_don_kem_dinh_muc_bom(db: Session) -> List[MonAnKemDinhMucBomOut]:
    """Trả về toàn bộ danh sách thực đơn kèm công thức định mức BOM và tính toán giá vốn nguyên liệu."""
    khoi_tao_thuc_don_va_dinh_muc_bom(db)
    bang_gia = _lay_bang_don_gia_nguyen_lieu_chuan(db)
    bang_nguyen_lieu = {i.ma_nguyen_lieu: i for i in db.query(Ingredient).all()}
    danh_sach_mon = db.query(MenuItem).order_by(MenuItem.ma_mon.asc()).all()

    ket_qua: List[MonAnKemDinhMucBomOut] = []
    for m in danh_sach_mon:
        chi_tiet_bom: List[ChiTietDinhMucBomOut] = []
        tong_gia_von = 0.0
        for r in m.recipes:
            nl = bang_nguyen_lieu.get(r.ma_nguyen_lieu)
            don_gia_nl = bang_gia.get(r.ma_nguyen_lieu, 50000.0)
            chi_phi_dong = round(r.so_luong_tieu_hao * don_gia_nl, 2)
            tong_gia_von += chi_phi_dong

            chi_tiet_bom.append(
                ChiTietDinhMucBomOut(
                    ma_dinh_muc=r.ma_dinh_muc,
                    ma_mon=r.ma_mon,
                    ma_nguyen_lieu=r.ma_nguyen_lieu,
                    ten_nguyen_lieu=nl.ten_nguyen_lieu if nl else f"Nguyên liệu #{r.ma_nguyen_lieu}",
                    don_vi_tinh=nl.don_vi_tinh if nl else "đv",
                    so_luong_tieu_hao=r.so_luong_tieu_hao,
                    don_gia_nguyen_lieu_uoc_tinh=don_gia_nl,
                    chi_phi_dinh_muc=chi_phi_dong,
                    ghi_chu=r.ghi_chu,
                )
            )

        gia_von = round(tong_gia_von, 2)
        ty_suat_lai_gop = (
            round(((m.don_gia_ban - gia_von) / m.don_gia_ban) * 100.0, 2)
            if m.don_gia_ban > 0
            else 0.0
        )

        ket_qua.append(
            MonAnKemDinhMucBomOut(
                ma_mon=m.ma_mon,
                ten_mon=m.ten_mon,
                danh_muc=m.danh_muc,
                don_gia_ban=m.don_gia_ban,
                trang_thai=m.trang_thai,
                gia_von_nguyen_lieu=gia_von,
                ty_suat_loi_nhuan_gop=ty_suat_lai_gop,
                cong_thuc_bom=chi_tiet_bom,
            )
        )
    return ket_qua


def mo_phong_boc_tach_bom(db: Session, yeu_cau: YeuCauMoPhongBom) -> KetQuaMoPhongBom:
    """
    Bóc tách tức thì danh sách đồ uống bán ra thành tổng lượng nguyên liệu tiêu hao.
    Nếu `cap_nhat_xuat_kho=True` thì tự động trừ tồn kho thực tế theo nguyên tắc hết hạn trước xuất trước (FEFO).
    """
    khoi_tao_thuc_don_va_dinh_muc_bom(db)
    bang_gia = _lay_bang_don_gia_nguyen_lieu_chuan(db)
    bang_mon = {m.ma_mon: m for m in db.query(MenuItem).all()}
    bang_nguyen_lieu = {i.ma_nguyen_lieu: i for i in db.query(Ingredient).all()}

    luong_boc_tach: Dict[int, float] = defaultdict(float)
    tong_so_ly = 0.0
    tong_doanh_thu = 0.0

    for item in yeu_cau.danh_sach_mon_ban:
        mon_obj = bang_mon.get(item.ma_mon)
        if not mon_obj:
            raise ValueError(f"Mã món #{item.ma_mon} không tồn tại trong thực đơn")
        tong_so_ly += item.so_luong_ly
        tong_doanh_thu += item.so_luong_ly * mon_obj.don_gia_ban
        for r in mon_obj.recipes:
            luong_boc_tach[r.ma_nguyen_lieu] += item.so_luong_ly * r.so_luong_tieu_hao

    danh_sach_tieu_hao: List[NguyenLieuTieuHaoOut] = []
    tong_chi_phi_nguyen_lieu = 0.0

    for ma_nl in sorted(luong_boc_tach.keys()):
        nl = bang_nguyen_lieu.get(ma_nl)
        if not nl:
            continue
        luong_can = round(luong_boc_tach[ma_nl], 3)
        don_gia = bang_gia.get(ma_nl, 50000.0)
        chi_phi_uoc_tinh = round(luong_can * don_gia, 2)
        tong_chi_phi_nguyen_lieu += chi_phi_uoc_tinh

        ton_truoc = nl.ton_kho_hien_tai
        ton_sau = round(max(0.0, ton_truoc - luong_can), 3)
        du_dap_ung = ton_truoc >= luong_can

        if yeu_cau.cap_nhat_xuat_kho:
            nl.ton_kho_hien_tai = ton_sau
            deduct_batches_fefo(db, ma_nl, luong_can)
            db.add(
                InventoryTransaction(
                    ma_nguyen_lieu=ma_nl,
                    loai_giao_dich="XUAT_BAN",
                    so_luong=luong_can,
                    ma_tham_chieu=yeu_cau.ma_tham_chieu or "XUAT-POS-BOM",
                    ghi_chu=f"Xuất tiêu hao tự động qua bóc tách định mức BOM ({int(tong_so_ly)} ly đồ uống)",
                )
            )

        danh_sach_tieu_hao.append(
            NguyenLieuTieuHaoOut(
                ma_nguyen_lieu=ma_nl,
                ten_nguyen_lieu=nl.ten_nguyen_lieu,
                don_vi_tinh=nl.don_vi_tinh,
                tong_luong_tieu_hao=luong_can,
                ton_kho_hien_tai=ton_truoc,
                ton_kho_sau_tieu_hao=ton_sau,
                muc_ton_an_toan=nl.muc_ton_an_toan,
                du_ton_kho_dap_ung=du_dap_ung,
                chi_phi_uoc_tinh=chi_phi_uoc_tinh,
            )
        )

    if yeu_cau.cap_nhat_xuat_kho:
        db.commit()

    return KetQuaMoPhongBom(
        tong_so_ly_ban=round(tong_so_ly, 1),
        tong_doanh_thu_du_kien=round(tong_doanh_thu, 2),
        tong_chi_phi_nguyen_lieu=round(tong_chi_phi_nguyen_lieu, 2),
        loi_nhuan_gop_du_kien=round(tong_doanh_thu - tong_chi_phi_nguyen_lieu, 2),
        da_cap_nhat_kho=yeu_cau.cap_nhat_xuat_kho,
        danh_sach_nguyen_lieu_tieu_hao=danh_sach_tieu_hao,
    )


def lay_bao_cao_chat_luong_du_lieu(db: Session) -> BaoCaoChatLuongDuLieuOut:
    """Lấy báo cáo kiểm định chất lượng dữ liệu & kết quả chạy quy trình BOM gần nhất."""
    lan_chay_moi_nhat = db.query(NhatKyXuLyDuLieu).order_by(NhatKyXuLyDuLieu.ma_lan_chay.desc()).first()
    if not lan_chay_moi_nhat:
        return chay_quy_trinh_boc_tach_bom(db, so_ngay=365)

    return BaoCaoChatLuongDuLieuOut(
        ma_lan_chay=lan_chay_moi_nhat.ma_lan_chay,
        ten_quy_trinh=lan_chay_moi_nhat.ten_quy_trinh,
        thoi_gian_chay=lan_chay_moi_nhat.thoi_gian_chay,
        tong_dong_tho=lan_chay_moi_nhat.tong_dong_tho,
        so_dong_trung_lap=lan_chay_moi_nhat.so_dong_trung_lap,
        so_dong_thieu_du_lieu=lan_chay_moi_nhat.so_dong_thieu_du_lieu,
        so_dong_am_hoac_loi=lan_chay_moi_nhat.so_dong_am_hoac_loi,
        so_dong_ngoai_lai_da_xu_ly=lan_chay_moi_nhat.so_dong_ngoai_lai_da_xu_ly,
        tong_dong_sach=lan_chay_moi_nhat.tong_dong_sach,
        ty_le_du_lieu_sach=lan_chay_moi_nhat.ty_le_du_lieu_sach,
        so_ngay_xu_ly=lan_chay_moi_nhat.so_ngay_xu_ly,
        tong_ban_ghi_tieu_hao_sinh_ra=lan_chay_moi_nhat.tong_ban_ghi_tieu_hao_sinh_ra,
        trang_thai=lan_chay_moi_nhat.trang_thai,
        ghi_chu=lan_chay_moi_nhat.ghi_chu,
        duong_dan_file_tho=f"backend/du_lieu/du_lieu_tho/{TEN_FILE_POS_THO}",
        duong_dan_file_sach=f"backend/du_lieu/du_lieu_sach/{TEN_FILE_POS_SACH}",
        duong_dan_file_tieu_hao=f"backend/du_lieu/du_lieu_sach/{TEN_FILE_CHUOI_TIEU_HAO}",
    )


def lay_chuoi_thoi_gian_tieu_hao(
    db: Session,
    ma_nguyen_lieu: int,
    so_ngay: int = 90,
) -> PhanHoiChuoiThoiGianNguyenLieu:
    """Truy xuất chuỗi thời gian tiêu hao nguyên liệu theo ngày kèm các đặc trưng trễ và trung bình trượt."""
    nl = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ma_nguyen_lieu).first()
    if not nl:
        raise ValueError(f"Không tìm thấy nguyên liệu #{ma_nguyen_lieu}")

    if db.query(TieuHaoNguyenLieuNgay).count() == 0:
        chay_quy_trinh_boc_tach_bom(db, so_ngay=365)

    ngay_gioi_han = date.today() - timedelta(days=so_ngay)
    cac_dong = (
        db.query(TieuHaoNguyenLieuNgay)
        .filter(
            TieuHaoNguyenLieuNgay.ma_nguyen_lieu == ma_nguyen_lieu,
            TieuHaoNguyenLieuNgay.ngay >= ngay_gioi_han,
        )
        .order_by(TieuHaoNguyenLieuNgay.ngay.asc())
        .all()
    )

    tong_tieu_hao = sum(r.so_luong_tieu_hao for r in cac_dong)
    so_ngay_thuc_te = len(cac_dong)
    trung_binh_ngay = round(tong_tieu_hao / so_ngay_thuc_te, 3) if so_ngay_thuc_te > 0 else 0.0

    gia_tri_ngay_thuong = [r.so_luong_tieu_hao for r in cac_dong if not r.la_cuoi_tuan]
    gia_tri_cuoi_tuan = [r.so_luong_tieu_hao for r in cac_dong if r.la_cuoi_tuan]

    tb_ngay_thuong = round(sum(gia_tri_ngay_thuong) / len(gia_tri_ngay_thuong), 3) if gia_tri_ngay_thuong else 0.0
    tb_cuoi_tuan = round(sum(gia_tri_cuoi_tuan) / len(gia_tri_cuoi_tuan), 3) if gia_tri_cuoi_tuan else 0.0
    ty_le_tang_cuoi_tuan = (
        round(((tb_cuoi_tuan - tb_ngay_thuong) / tb_ngay_thuong * 100.0), 1)
        if tb_ngay_thuong > 0
        else 0.0
    )

    danh_sach_diem = [
        DiemChuoiThoiGianTieuHaoOut(
            ngay=r.ngay,
            so_luong_tieu_hao=r.so_luong_tieu_hao,
            so_ly_lien_quan=r.so_ly_lien_quan,
            thu_trong_tuan=r.thu_trong_tuan,
            la_cuoi_tuan=r.la_cuoi_tuan,
            he_so_mua_vu=r.he_so_mua_vu,
            tieu_hao_hom_truoc=r.tieu_hao_hom_truoc,
            tieu_hao_7_ngay_truoc=r.tieu_hao_7_ngay_truoc,
            trung_binh_truot_7_ngay=r.trung_binh_truot_7_ngay,
            do_lech_chuan_7_ngay=r.do_lech_chuan_7_ngay,
        )
        for r in cac_dong
    ]

    return PhanHoiChuoiThoiGianNguyenLieu(
        ma_nguyen_lieu=nl.ma_nguyen_lieu,
        ten_nguyen_lieu=nl.ten_nguyen_lieu,
        don_vi_tinh=nl.don_vi_tinh,
        so_ngay_du_lieu=so_ngay_thuc_te,
        tong_tieu_hao=round(tong_tieu_hao, 2),
        trung_binh_ngay=trung_binh_ngay,
        tieu_hao_ngay_thuong_tb=tb_ngay_thuong,
        tieu_hao_cuoi_tuan_tb=tb_cuoi_tuan,
        ty_le_tang_cuoi_tuan_pct=ty_le_tang_cuoi_tuan,
        chuoi_thoi_gian=danh_sach_diem,
    )


def luu_mon_an_kem_dinh_muc_bom(db: Session, du_lieu: YeuCauLuuMonAnBom) -> MonAnKemDinhMucBomOut:
    """Tạo mới hoặc cập nhật món đồ uống kèm công thức định mức BOM."""
    khoi_tao_thuc_don_va_dinh_muc_bom(db)
    mon_obj = None
    if du_lieu.ma_mon:
        mon_obj = db.query(MenuItem).filter(MenuItem.ma_mon == du_lieu.ma_mon).first()

    if mon_obj:
        mon_obj.ten_mon = du_lieu.ten_mon
        mon_obj.danh_muc = du_lieu.danh_muc
        mon_obj.don_gia_ban = du_lieu.don_gia_ban
        db.query(RecipeBOM).filter(RecipeBOM.ma_mon == mon_obj.ma_mon).delete()
    else:
        mon_obj = MenuItem(
            ten_mon=du_lieu.ten_mon,
            danh_muc=du_lieu.danh_muc,
            don_gia_ban=du_lieu.don_gia_ban,
            trang_thai=True,
        )
        db.add(mon_obj)
        db.commit()
        db.refresh(mon_obj)

    for b in du_lieu.cong_thuc_bom:
        db.add(
            RecipeBOM(
                ma_mon=mon_obj.ma_mon,
                ma_nguyen_lieu=b.ma_nguyen_lieu,
                so_luong_tieu_hao=b.so_luong_tieu_hao,
                ghi_chu=b.ghi_chu,
            )
        )
    db.commit()

    tat_ca_mon = lay_thuc_don_kem_dinh_muc_bom(db)
    for m in tat_ca_mon:
        if m.ma_mon == mon_obj.ma_mon:
            return m
    raise ValueError("Không thể tải lại món vừa lưu")


def ghi_nhan_hoa_don_pos_va_tru_kho(
    db: Session,
    du_lieu: YeuCauTaoHoaDonPos,
) -> KetQuaMoPhongBom:
    """
    Ghi nhận hóa đơn bán hàng POS thực tế:
      1. Lưu chi tiết từng món bán vào bảng `lich_su_ban_hang`.
      2. Bóc tách định mức BOM ra lượng nguyên liệu tiêu hao.
      3. Tự động trừ tồn kho thực tế và trừ tồn lô hàng theo nguyên tắc hết hạn trước xuất trước (FEFO).
      4. Cộng dồn vào bảng `tieu_hao_nguyen_lieu_ngay` của ngày bán.
    """
    khoi_tao_thuc_don_va_dinh_muc_bom(db)
    ngay_ban = du_lieu.ngay_ban or date.today()
    ma_hd = du_lieu.ma_hoa_don_pos or f"POS-{ngay_ban.strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
    bang_mon = {m.ma_mon: m for m in db.query(MenuItem).all()}

    for item in du_lieu.danh_sach_mon_ban:
        mon_obj = bang_mon.get(item.ma_mon)
        if not mon_obj:
            raise ValueError(f"Mã món #{item.ma_mon} không tồn tại")
        db.add(
            LichSuBanHang(
                ma_hoa_don_pos=ma_hd,
                ngay_ban=ngay_ban,
                ca_ban=du_lieu.ca_ban,
                ma_mon=item.ma_mon,
                so_luong_ly=item.so_luong_ly,
                don_gia_ban=mon_obj.don_gia_ban,
                thanh_tien=round(item.so_luong_ly * mon_obj.don_gia_ban, 2),
                da_boc_tach_bom=True,
            )
        )

    ket_qua_bom = mo_phong_boc_tach_bom(
        db,
        YeuCauMoPhongBom(
            danh_sach_mon_ban=du_lieu.danh_sach_mon_ban,
            cap_nhat_xuat_kho=True,
            ma_tham_chieu=ma_hd,
        ),
    )

    for nl_tieu_hao in ket_qua_bom.danh_sach_nguyen_lieu_tieu_hao:
        dong_ngay = (
            db.query(TieuHaoNguyenLieuNgay)
            .filter(
                TieuHaoNguyenLieuNgay.ngay == ngay_ban,
                TieuHaoNguyenLieuNgay.ma_nguyen_lieu == nl_tieu_hao.ma_nguyen_lieu,
            )
            .first()
        )
        if dong_ngay:
            dong_ngay.so_luong_tieu_hao = round(
                dong_ngay.so_luong_tieu_hao + nl_tieu_hao.tong_luong_tieu_hao, 3
            )
            dong_ngay.so_ly_lien_quan += int(round(ket_qua_bom.tong_so_ly_ban))
        else:
            db.add(
                TieuHaoNguyenLieuNgay(
                    ngay=ngay_ban,
                    ma_nguyen_lieu=nl_tieu_hao.ma_nguyen_lieu,
                    so_luong_tieu_hao=nl_tieu_hao.tong_luong_tieu_hao,
                    so_ly_lien_quan=int(round(ket_qua_bom.tong_so_ly_ban)),
                    thu_trong_tuan=ngay_ban.weekday(),
                    la_cuoi_tuan=ngay_ban.weekday() in (5, 6),
                    he_so_mua_vu=HE_SO_MUA_VU_THANG.get(ngay_ban.month, 1.0),
                    tieu_hao_hom_truoc=nl_tieu_hao.tong_luong_tieu_hao,
                    tieu_hao_7_ngay_truoc=nl_tieu_hao.tong_luong_tieu_hao,
                    trung_binh_truot_7_ngay=nl_tieu_hao.tong_luong_tieu_hao,
                    do_lech_chuan_7_ngay=0.0,
                )
            )
    db.commit()
    return ket_qua_bom


def lay_lich_su_ban_hang_pos(
    db: Session,
    ma_mon: Optional[int] = None,
    ca_ban: Optional[str] = None,
    gioi_han: int = 50,
) -> List[LichSuBanHangOut]:
    """Lấy danh sách lịch sử đơn bán hàng POS đã qua làm sạch và bóc tách định mức BOM."""
    khoi_tao_thuc_don_va_dinh_muc_bom(db)
    bang_mon = {m.ma_mon: m.ten_mon for m in db.query(MenuItem).all()}
    truy_van = db.query(LichSuBanHang)
    if ma_mon:
        truy_van = truy_van.filter(LichSuBanHang.ma_mon == ma_mon)
    if ca_ban:
        truy_van = truy_van.filter(LichSuBanHang.ca_ban == ca_ban)

    cac_dong = truy_van.order_by(LichSuBanHang.ngay_ban.desc(), LichSuBanHang.ma_ban_hang.desc()).limit(gioi_han).all()
    return [
        LichSuBanHangOut(
            ma_ban_hang=r.ma_ban_hang,
            ma_hoa_don_pos=r.ma_hoa_don_pos,
            ngay_ban=r.ngay_ban,
            ca_ban=r.ca_ban,
            ma_mon=r.ma_mon,
            ten_mon=bang_mon.get(r.ma_mon, f"Món #{r.ma_mon}"),
            so_luong_ly=r.so_luong_ly,
            don_gia_ban=r.don_gia_ban,
            thanh_tien=r.thanh_tien,
            da_boc_tach_bom=r.da_boc_tach_bom,
        )
        for r in cac_dong
    ]
