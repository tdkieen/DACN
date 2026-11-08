from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class SupplierQuotationBase(BaseModel):
    ma_nha_cung_cap: int
    ma_nguyen_lieu: int
    don_gia: float
    so_luong_dat_toi_thieu: float = 1.0  # MOQ
    thoi_gian_giao_hang: int = 2  # Lead time (ngày)

class SupplierQuotationCreate(SupplierQuotationBase):
    pass

class SupplierQuotationOut(SupplierQuotationBase):
    ngay_cap_nhat_gia: Optional[datetime] = None
    ten_nha_cung_cap: Optional[str] = None
    ten_nguyen_lieu: Optional[str] = None
    diem_danh_gia_mcdm: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class SupplierBase(BaseModel):
    ten_nha_cung_cap: str
    nguoi_lien_he: Optional[str] = None
    email: Optional[str] = None
    sdt: Optional[str] = None
    dia_chi: Optional[str] = None
    thoi_gian_giao_du_kien: int = 2
    diem_uy_tin: float = 4.5  # 1.0 đến 5.0
    diem_chat_luong: float = 4.5  # 1.0 đến 5.0
    trang_thai: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    ten_nha_cung_cap: Optional[str] = None
    nguoi_lien_he: Optional[str] = None
    email: Optional[str] = None
    sdt: Optional[str] = None
    dia_chi: Optional[str] = None
    thoi_gian_giao_du_kien: Optional[int] = None
    diem_uy_tin: Optional[float] = None
    diem_chat_luong: Optional[float] = None
    trang_thai: Optional[bool] = None

class SupplierOut(SupplierBase):
    ma_nha_cung_cap: int
    ngay_tao: Optional[datetime] = None
    quotations: List[SupplierQuotationOut] = []

    model_config = ConfigDict(from_attributes=True)

class SupplierMCDMScore(BaseModel):
    ma_nha_cung_cap: int
    ten_nha_cung_cap: str
    don_gia: float
    thoi_gian_giao_hang: int
    so_luong_dat_toi_thieu: float
    diem_chat_luong: float
    diem_uy_tin: float
    diem_tong_hop_mcdm: float
    xep_hang: int
    de_xuat: bool

class SupplierCompareResult(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    nha_cung_cap_toi_uu: Optional[SupplierMCDMScore] = None
    danh_sach_so_sanh: List[SupplierMCDMScore] = []
