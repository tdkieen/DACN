from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class PurchaseProposal(Base):
    __tablename__ = "phieu_de_xuat_mua"

    ma_phieu_de_xuat = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ngay_tao = Column(DateTime(timezone=True), server_default=func.now())
    tong_tien_du_kien = Column(Float, default=0.0)
    trang_thai = Column(String(30), default="CHO_DUYET", index=True)  # 'CHO_DUYET', 'DA_DUYET', 'TU_CHOI', 'DA_SUA'
    ly_do_tong_quan = Column(Text, nullable=True)  # AI Agent reasoning
    nguoi_tao = Column(String(50), default="AI Procurement Agent")

    details = relationship("ProposalDetail", back_populates="proposal", cascade="all, delete-orphan")
    approval_history = relationship("ApprovalHistory", back_populates="proposal", cascade="all, delete-orphan")


class ProposalDetail(Base):
    __tablename__ = "ct_de_xuat_mua"

    ma_chi_tiet = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_phieu_de_xuat = Column(Integer, ForeignKey("phieu_de_xuat_mua.ma_phieu_de_xuat"), nullable=False)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    ma_nha_cung_cap = Column(Integer, ForeignKey("nha_cung_cap.ma_nha_cung_cap"), nullable=False)
    so_luong_de_xuat = Column(Float, nullable=False)
    don_gia_du_kien = Column(Float, nullable=False)
    so_luong_du_doan_7ngay = Column(Float, default=0.0)
    ly_do_de_xuat = Column(Text, nullable=True)  # Lời giải thích của AI cho từng nguyên liệu

    proposal = relationship("PurchaseProposal", back_populates="details")
    ingredient = relationship("app.models.ingredient.Ingredient")
    supplier = relationship("app.models.supplier.Supplier")


class PurchaseOrder(Base):
    __tablename__ = "don_mua_hang"

    ma_don_mua = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_phieu_de_xuat = Column(Integer, ForeignKey("phieu_de_xuat_mua.ma_phieu_de_xuat"), nullable=True)
    ma_nha_cung_cap = Column(Integer, ForeignKey("nha_cung_cap.ma_nha_cung_cap"), nullable=False)
    ngay_tao = Column(DateTime(timezone=True), server_default=func.now())
    tong_tien = Column(Float, nullable=False)
    trang_thai = Column(String(30), default="DA_GUI_NCC")  # 'DA_GUI_NCC', 'DANG_GIAO', 'HOAN_THANH', 'HUY'
    ngay_giao_du_kien = Column(DateTime(timezone=True), nullable=True)

    supplier = relationship("app.models.supplier.Supplier")


class ApprovalHistory(Base):
    __tablename__ = "lich_su_duyet"

    ma_lich_su = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_phieu_de_xuat = Column(Integer, ForeignKey("phieu_de_xuat_mua.ma_phieu_de_xuat"), nullable=False)
    nguoi_duyet = Column(String(100), nullable=False)  # Quản lý cửa hàng
    hanh_dong = Column(String(20), nullable=False)  # 'APPROVE', 'REJECT', 'MODIFY'
    y_kien = Column(Text, nullable=True)  # Ý kiến đóng góp/chỉnh sửa của quản lý
    thoi_gian_duyet = Column(DateTime(timezone=True), server_default=func.now())

    proposal = relationship("PurchaseProposal", back_populates="approval_history")
