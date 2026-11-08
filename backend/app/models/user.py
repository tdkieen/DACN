from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "nguoi_dung"

    ma_nguoi_dung = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_nguoi_dung = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    mat_khau_hash = Column(String(255), nullable=False)
    vai_tro = Column(String(30), default="QUAN_LY")  # 'QUAN_LY', 'NHAN_VIEN_KHO', 'ADMIN'
    trang_thai = Column(Boolean, default=True)
    ngay_tao = Column(DateTime(timezone=True), server_default=func.now())
