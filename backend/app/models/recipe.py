from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MenuItem(Base):
    """Bảng danh mục các món đồ uống trong thực đơn quán cà phê"""
    __tablename__ = "menu_items"

    ma_mon = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_mon = Column(String(100), nullable=False, index=True)
    danh_muc = Column(String(50), nullable=True)  # Cà phê truyền thống, Cà phê máy, Trà trái cây, Đá xay
    don_gia_ban = Column(Float, nullable=False)
    trang_thai = Column(Boolean, default=True)

    recipes = relationship("RecipeBOM", back_populates="menu_item", cascade="all, delete-orphan")


class RecipeBOM(Base):
    """Bảng định mức công thức pha chế (BOM) quy đổi từ 1 ly đồ uống sang nguyên liệu"""
    __tablename__ = "recipes_bom"

    ma_dinh_muc = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_mon = Column(Integer, ForeignKey("menu_items.ma_mon"), nullable=False)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False)
    so_luong_tieu_hao = Column(Float, nullable=False)  # ví dụ 0.025 (kg hạt), 0.03 (lon sữa đặc), 1 (cái ly)
    ghi_chu = Column(String(100), nullable=True)

    menu_item = relationship("MenuItem", back_populates="recipes")
    ingredient = relationship("app.models.ingredient.Ingredient")


class LichSuBanHang(Base):
    """Bảng lưu lịch sử hóa đơn bán hàng tại quầy (POS) đã qua làm sạch dữ liệu"""
    __tablename__ = "lich_su_ban_hang"

    ma_ban_hang = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_hoa_don_pos = Column(String(50), nullable=False, index=True)
    ngay_ban = Column(Date, nullable=False, index=True)
    ca_ban = Column(String(20), default="SANG")  # SANG, CHIEU, TOI
    ma_mon = Column(Integer, ForeignKey("menu_items.ma_mon"), nullable=False, index=True)
    so_luong_ly = Column(Float, nullable=False)
    don_gia_ban = Column(Float, nullable=False)
    thanh_tien = Column(Float, nullable=False)
    da_boc_tach_bom = Column(Boolean, default=True)
    thoi_gian_tao = Column(DateTime(timezone=True), server_default=func.now())

    menu_item = relationship("MenuItem")


class TieuHaoNguyenLieuNgay(Base):
    """
    Bảng chuỗi thời gian tiêu hao nguyên liệu theo ngày sau khi chạy quy trình bóc tách định mức BOM.
    Dùng làm kho đặc trưng đầu vào trực tiếp để huấn luyện mô hình dự báo nhu cầu (Tuần 6).
    """
    __tablename__ = "tieu_hao_nguyen_lieu_ngay"

    ma_tieu_hao = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ngay = Column(Date, nullable=False, index=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False, index=True)
    so_luong_tieu_hao = Column(Float, nullable=False)
    so_ly_lien_quan = Column(Integer, default=0)
    thu_trong_tuan = Column(Integer, nullable=False)  # 0=Thứ Hai ... 6=Chủ Nhật
    la_cuoi_tuan = Column(Boolean, default=False)
    he_so_mua_vu = Column(Float, default=1.0)
    tieu_hao_hom_truoc = Column(Float, nullable=True)
    tieu_hao_7_ngay_truoc = Column(Float, nullable=True)
    trung_binh_truot_7_ngay = Column(Float, nullable=True)
    do_lech_chuan_7_ngay = Column(Float, nullable=True)
    thoi_gian_cap_nhat = Column(DateTime(timezone=True), server_default=func.now())

    ingredient = relationship("app.models.ingredient.Ingredient")


class NhatKyXuLyDuLieu(Base):
    """Bảng nhật ký chạy quy trình Thu thập - Làm sạch - Bóc tách định mức nguyên liệu"""
    __tablename__ = "nhat_ky_xu_ly_du_lieu"

    ma_lan_chay = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_quy_trinh = Column(String(100), default="QUY_TRINH_BOC_TACH_DINH_MUC_V1")
    thoi_gian_chay = Column(DateTime(timezone=True), server_default=func.now())
    tong_dong_tho = Column(Integer, default=0)
    so_dong_trung_lap = Column(Integer, default=0)
    so_dong_thieu_du_lieu = Column(Integer, default=0)
    so_dong_am_hoac_loi = Column(Integer, default=0)
    so_dong_ngoai_lai_da_xu_ly = Column(Integer, default=0)
    tong_dong_sach = Column(Integer, default=0)
    ty_le_du_lieu_sach = Column(Float, default=100.0)
    so_ngay_xu_ly = Column(Integer, default=365)
    tong_ban_ghi_tieu_hao_sinh_ra = Column(Integer, default=0)
    trang_thai = Column(String(30), default="THANH_CONG")
    ghi_chu = Column(String(500), nullable=True)


# Bí danh tương thích
MonAn = MenuItem
CongThucBom = RecipeBOM
PosSalesHistory = LichSuBanHang
DailyIngredientConsumption = TieuHaoNguyenLieuNgay
EtlPipelineRun = NhatKyXuLyDuLieu
