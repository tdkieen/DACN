from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ProposalDetailBase(BaseModel):
    ma_nguyen_lieu: int
    ma_nha_cung_cap: int
    so_luong_de_xuat: float
    don_gia_du_kien: float
    so_luong_du_doan_7ngay: float = 0.0
    ly_do_de_xuat: Optional[str] = None

class ProposalDetailCreate(ProposalDetailBase):
    pass

class ProposalDetailOut(ProposalDetailBase):
    ma_chi_tiet: int
    ma_phieu_de_xuat: int
    ten_nguyen_lieu: Optional[str] = None
    don_vi_tinh: Optional[str] = None
    ten_nha_cung_cap: Optional[str] = None
    thanh_tien: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class ApprovalHistoryBase(BaseModel):
    nguoi_duyet: str
    hanh_dong: str  # 'APPROVE', 'REJECT', 'MODIFY'
    y_kien: Optional[str] = None

class ApprovalHistoryCreate(ApprovalHistoryBase):
    pass

class ApprovalHistoryOut(ApprovalHistoryBase):
    ma_lich_su: int
    ma_phieu_de_xuat: int
    thoi_gian_duyet: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PurchaseProposalBase(BaseModel):
    tong_tien_du_kien: float = 0.0
    ly_do_tong_quan: Optional[str] = None

class PurchaseProposalCreate(PurchaseProposalBase):
    details: List[ProposalDetailCreate] = []

class PurchaseProposalOut(PurchaseProposalBase):
    ma_phieu_de_xuat: int
    ngay_tao: Optional[datetime] = None
    trang_thai: str  # 'CHO_DUYET', 'DA_DUYET', 'TU_CHOI', 'DA_SUA'
    nguoi_tao: str
    details: List[ProposalDetailOut] = []
    approval_history: List[ApprovalHistoryOut] = []

    model_config = ConfigDict(from_attributes=True)

class ProposalActionRequest(BaseModel):
    hanh_dong: str  # 'APPROVE', 'REJECT', 'MODIFY'
    nguoi_duyet: str = "Quản lý cửa hàng"
    y_kien: Optional[str] = None
