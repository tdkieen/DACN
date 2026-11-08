from pydantic import BaseModel
from typing import List, Optional

class DashboardStatsOut(BaseModel):
    tong_nguyen_lieu_dang_dung: int
    nguy_co_thieu_hang: int  # ton_kho <= ROP
    nguy_co_ton_du: int      # ton_kho > muc_ton_toi_da
    phieu_cho_duyet: int     # phieu_de_xuat_mua trang_thai == 'CHO_DUYET'
    tong_gia_tri_ton_kho: float
    ty_le_an_toan: float      # % số nguyên liệu ở mức an toàn

class AlertItemOut(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    muc_do: str  # 'DANGER' (Thiếu hàng / Đỏ), 'WARNING' (Tồn dư / Vàng), 'EXPIRY' (Sắp hết hạn)
    loai_canh_bao: str
    noi_dung: str
    ton_kho_hien_tai: float
    nguong_canh_bao: float
    so_luong_can_bo_sung: Optional[float] = 0.0

class MonthlyTrendPoint(BaseModel):
    thang: str  # 'Tháng 1', 'Tháng 2', ...
    tong_tieu_hao_kg: float
    chi_phi_uoc_tinh: float

class DashboardOverviewOut(BaseModel):
    stats: DashboardStatsOut
    alerts: List[AlertItemOut]
    trends_12_months: List[MonthlyTrendPoint]
