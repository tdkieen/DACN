from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date

class BatchBase(BaseModel):
    ma_nguyen_lieu: int
    ma_lo_nha_cung_cap: Optional[str] = None
    so_luong_nhap: float
    so_luong_con_lai: float
    han_su_dung: Optional[date] = None
    don_gia_nhap: float

class BatchCreate(BatchBase):
    pass

class BatchOut(BatchBase):
    ma_lo_hang: int
    ngay_nhap_kho: Optional[datetime] = None
    ten_nguyen_lieu: Optional[str] = None
    so_ngay_con_han: Optional[int] = None
    canh_bao_het_han: bool = False

    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionBase(BaseModel):
    ma_nguyen_lieu: int
    loai_giao_dich: str  # 'NHAP', 'XUAT_BAN', 'HAO_HUT', 'KIEM_KE'
    so_luong: float
    ma_tham_chieu: Optional[str] = None
    ghi_chu: Optional[str] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransactionOut(InventoryTransactionBase):
    ma_giao_dich: int
    ngay_giao_dich: Optional[datetime] = None
    ten_nguyen_lieu: Optional[str] = None
    don_vi_tinh: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
