from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class IngredientBase(BaseModel):
    ten_nguyen_lieu: str
    danh_muc: Optional[str] = None
    don_vi_tinh: str
    muc_ton_an_toan: float = 10.0
    muc_ton_toi_da: float = 100.0
    ton_kho_hien_tai: float = 0.0
    trang_thai: bool = True

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    ten_nguyen_lieu: Optional[str] = None
    danh_muc: Optional[str] = None
    don_vi_tinh: Optional[str] = None
    muc_ton_an_toan: Optional[float] = None
    muc_ton_toi_da: Optional[float] = None
    ton_kho_hien_tai: Optional[float] = None
    trang_thai: Optional[bool] = None

class IngredientOut(IngredientBase):
    ma_nguyen_lieu: int
    ngay_tao: Optional[datetime] = None
    ngay_cap_nhat: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class IngredientStatusOut(IngredientOut):
    tinh_trang: str  # 'NGUY_CO_THIEU' (Đỏ), 'TON_DU' (Vàng), 'AN_TOAN' (Xanh)
    nhu_cau_du_bao_7ngay: float = 0.0
    diem_dat_hang_lai_rop: float = 0.0
    so_luong_can_bo_sung: float = 0.0
    thong_bao_canh_bao: Optional[str] = None

class BatchSimpleOut(BaseModel):
    ma_lo_hang: int
    ma_lo_nha_cung_cap: Optional[str] = None
    so_luong_nhap: float
    so_luong_con_lai: float
    ngay_nhap_kho: Optional[datetime] = None
    han_su_dung: Optional[date] = None
    don_gia_nhap: float

    model_config = ConfigDict(from_attributes=True)

class ForecastSimpleOut(BaseModel):
    ngay_du_bao: date
    so_luong_du_bao: float
    do_tin_cay: float

    model_config = ConfigDict(from_attributes=True)

class IngredientDetailOut(IngredientStatusOut):
    batches: List[BatchSimpleOut] = []
    forecasts: List[ForecastSimpleOut] = []
