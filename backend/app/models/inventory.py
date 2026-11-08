from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Batch(Base):
    __tablename__ = "lo_hang"

    ma_lo_hang = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    ma_lo_nha_cung_cap = Column(String(50), nullable=True)
    so_luong_nhap = Column(Float, nullable=False)
    so_luong_con_lai = Column(Float, nullable=False)
    ngay_nhap_kho = Column(DateTime(timezone=True), server_default=func.now())
    han_su_dung = Column(Date, nullable=True)
    don_gia_nhap = Column(Float, nullable=False)

    ingredient = relationship("app.models.ingredient.Ingredient")


class InventoryTransaction(Base):
    __tablename__ = "giao_dich_kho"

    ma_giao_dich = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    loai_giao_dich = Column(String(20), nullable=False)  # 'NHAP', 'XUAT_BAN', 'HAO_HUT', 'KIEM_KE'
    so_luong = Column(Float, nullable=False)
    ngay_giao_dich = Column(DateTime(timezone=True), server_default=func.now())
    ma_tham_chieu = Column(String(50), nullable=True)  # Mã hóa đơn hoặc mã phiếu nhập
    ghi_chu = Column(String(255), nullable=True)

    ingredient = relationship("app.models.ingredient.Ingredient")
