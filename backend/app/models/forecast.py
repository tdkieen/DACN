from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DemandForecast(Base):
    """Bảng lưu kết quả dự báo nhu cầu tiêu hao 7 ngày tới cho từng nguyên liệu (DU_BAO_NHU_CAU)"""
    __tablename__ = "du_bao_nhu_cau"

    ma_du_bao = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False, index=True)
    ngay_du_bao = Column(Date, nullable=False, index=True)  # Ngày cần dùng trong 7 ngày tới
    so_luong_du_bao = Column(Float, nullable=False)  # Nhu cầu dự báo (kg/lít/cái)
    do_tin_cay = Column(Float, default=0.95)  # Độ tin cậy tính từ phần dư tập kiểm thử
    phuong_phap = Column(String(50), default="Ensemble_HW_Ridge")
    thoi_gian_tao = Column(DateTime(timezone=True), server_default=func.now())

    ingredient = relationship("app.models.ingredient.Ingredient")


class LanChayMoHinh(Base):
    """
    Bảng nhật ký các lần huấn luyện & đánh giá mô hình dự báo nhu cầu (Tuần 6).
    Lưu vết chỉ số MAE, RMSE, MAPE của mô hình tốt nhất so với mô hình cơ sở (Baseline).
    """
    __tablename__ = "lan_chay_mo_hinh"

    ma_lan_huan_luyen = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ten_phien_ban = Column(String(100), default="DU_BAO_NHU_CAU_AI_TUAN6_V1")
    thoi_gian_chay = Column(DateTime(timezone=True), server_default=func.now())
    so_nguyen_lieu = Column(Integer, default=15)
    so_ngay_lich_su = Column(Integer, default=365)
    so_ngay_train = Column(Integer, default=275)
    so_ngay_val = Column(Integer, default=45)
    so_ngay_test = Column(Integer, default=45)
    chan_troi_du_bao = Column(Integer, default=7)
    mo_hinh_tot_nhat_pho_bien = Column(String(60), default="Ensemble_HW_Ridge")
    baseline_mape_tb = Column(Float, default=0.0)
    ml_mape_tb = Column(Float, default=0.0)
    baseline_mae_tb = Column(Float, default=0.0)
    ml_mae_tb = Column(Float, default=0.0)
    baseline_rmse_tb = Column(Float, default=0.0)
    ml_rmse_tb = Column(Float, default=0.0)
    muc_giam_sai_so_mape_pct = Column(Float, default=0.0)  # % cải thiện MAPE so với Baseline_MA7
    thoi_gian_xu_ly_giay = Column(Float, default=0.0)
    trang_thai = Column(String(30), default="THANH_CONG")
    ghi_chu = Column(String(500), nullable=True)

    chi_tiet_danh_gia = relationship(
        "KetQuaDanhGiaMoHinh",
        back_populates="lan_chay",
        cascade="all, delete-orphan",
    )


class KetQuaDanhGiaMoHinh(Base):
    """
    Bảng chi tiết kết quả so sánh từng mô hình (Baseline & ML) trên từng nguyên liệu
    qua tập Validation và Holdout Test (Tuần 6).
    """
    __tablename__ = "ket_qua_danh_gia_mo_hinh"

    ma_danh_gia = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma_lan_huan_luyen = Column(Integer, ForeignKey("lan_chay_mo_hinh.ma_lan_huan_luyen"), nullable=False, index=True)
    ma_nguyen_lieu = Column(Integer, ForeignKey("nguyen_lieu.ma_nguyen_lieu"), nullable=False, index=True)
    ten_mo_hinh = Column(String(60), nullable=False, index=True)
    nhom_mo_hinh = Column(String(20), nullable=False)  # BASELINE hoặc ML
    val_mae = Column(Float, nullable=False)
    val_rmse = Column(Float, nullable=False)
    val_mape = Column(Float, nullable=False)
    test_mae = Column(Float, nullable=False)
    test_rmse = Column(Float, nullable=False)
    test_mape = Column(Float, nullable=False)
    test_smape = Column(Float, default=0.0)
    test_r2 = Column(Float, default=0.0)
    mape_ngay_thuong = Column(Float, default=0.0)
    mape_cuoi_tuan = Column(Float, default=0.0)
    do_lech_chuan_phan_du = Column(Float, default=0.0)
    cai_thien_so_voi_baseline_pct = Column(Float, default=0.0)
    la_mo_hinh_tot_nhat = Column(Boolean, default=False)
    tham_so_toi_uu = Column(Text, nullable=True)

    lan_chay = relationship("LanChayMoHinh", back_populates="chi_tiet_danh_gia")
    ingredient = relationship("app.models.ingredient.Ingredient")


# Bí danh tương thích
DuBaoNhuCau = DemandForecast
ModelTrainingRun = LanChayMoHinh
ModelEvaluationMetric = KetQuaDanhGiaMoHinh
