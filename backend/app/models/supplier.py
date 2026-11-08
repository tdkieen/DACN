from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Supplier(Base):
    __tablename__ = "nha_cung_cap"

    ma_nha_cung_cap = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_nha_cung_cap = Column(String(150), nullable=False, index=True)
    nguoi_lien_he = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    sdt = Column(String(20), nullable=True)
    dia_chi = Column(String(255), nullable=True)
    thoi_gian_giao_du_kien = Column(Integer, default=2)  # Lead time (ngày)
    diem_uy_tin = Column(Float, default=4.5)  # 1.0 đến 5.0
    diem_chat_luong = Column(Float, default=4.5)  # 1.0 đến 5.0
    trang_thai = Column(Boolean, default=True)
    ngay_tao = Column(DateTime(timezone=True), server_default=func.now())

    quotations = relationship("SupplierQuotation", back_populates="supplier", cascade="all, delete-orphan")


class SupplierQuotation(Base):
    __tablename__ = "cc_nguyen_lieu"

    ma_nha_cung_cap = Column(Integer, ForeignKey("nha_cung_cap.ma_nha_cung_cap"), primary_key=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), primary_key=True)
    don_gia = Column(Float, nullable=False)
    so_luong_dat_toi_thieu = Column(Float, default=1.0)  # MOQ
    thoi_gian_giao_hang = Column(Integer, default=2)  # Lead time cụ thể (ngày)
    ngay_cap_nhat_gia = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    supplier = relationship("Supplier", back_populates="quotations")
    ingredient = relationship("app.models.ingredient.Ingredient")
