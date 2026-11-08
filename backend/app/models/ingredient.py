from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Ingredient(Base):
    __tablename__ = "nguyen_lieu"

    ma_nguyen_lieu = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_nguyen_lieu = Column(String(100), nullable=False, index=True)
    danh_muc = Column(String(50), nullable=True)  # Cà phê, Sữa, Siro, Trà, Bao bì...
    don_vi_tinh = Column(String(20), nullable=False)  # kg, lít, hộp, cái...
    muc_ton_an_toan = Column(Float, default=10.0, nullable=False)  # Safety Stock threshold
    ton_kho_hien_tai = Column(Float, default=0.0, nullable=False)
    muc_ton_toi_da = Column(Float, default=100.0, nullable=False)  # Max Stock
    trang_thai = Column(Boolean, default=True)  # Đang dùng / Ngừng dùng
    ngay_tao = Column(DateTime(timezone=True), server_default=func.now())
    ngay_cap_nhat = Column(DateTime(timezone=True), onupdate=func.now())
