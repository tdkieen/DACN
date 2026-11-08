from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DemandForecast(Base):
    __tablename__ = "du_bao_nhu_cau"

    ma_du_bao = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    ngay_du_bao = Column(Date, nullable=False, index=True)  # Ngày cần dùng trong 7 ngày tới
    so_luong_du_bao = Column(Float, nullable=False)  # Nhu cầu dự báo (kg/lít/cái)
    do_tin_cay = Column(Float, default=0.95)  # 0.90 - 0.95
    phuong_phap = Column(String(50), default="Prophet_v1")
    thoi_gian_tao = Column(DateTime(timezone=True), server_default=func.now())

    ingredient = relationship("app.models.ingredient.Ingredient")
