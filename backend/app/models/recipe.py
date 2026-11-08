from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    ma_mon = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_mon = Column(String(100), nullable=False, index=True)
    danh_muc = Column(String(50), nullable=True)  # Cà phê truyền thống, Espresso, Trà trái cây, Đá xay
    don_gia_ban = Column(Float, nullable=False)
    trang_thai = Column(Boolean, default=True)

    recipes = relationship("RecipeBOM", back_populates="menu_item", cascade="all, delete-orphan")


class RecipeBOM(Base):
    __tablename__ = "recipes_bom"

    ma_dinh_muc = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_mon = Column(Integer, ForeignKey("menu_items.ma_mon"), nullable=False)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    so_luong_tieu_hao = Column(Float, nullable=False)  # ví dụ 0.025 (kg hạt), 0.03 (lít sữa đặc), 1 (cái ly)
    ghi_chu = Column(String(100), nullable=True)

    menu_item = relationship("MenuItem", back_populates="recipes")
    ingredient = relationship("app.models.ingredient.Ingredient")
