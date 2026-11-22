from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime


class DiemDuBaoChiTietOut(BaseModel):
    ngay_du_bao: date
    thu_trong_tuan: int  # 0=Thứ 2 ... 6=Chủ Nhật
    nhan_thu: str  # T2 .. CN
    la_cuoi_tuan: bool
    so_luong_du_bao: float
    can_duoi_95: float
    can_tren_95: float
    do_tin_cay: float
    phuong_phap: str


class DiemKiemThuThucTeVsDuBaoOut(BaseModel):
    ngay: date
    thu_trong_tuan: int
    la_cuoi_tuan: bool
    thuc_te: float
    du_bao_ml: float
    du_bao_baseline: float
    sai_so_tuyet_doi: float
    sai_so_phan_tram: float


class ChanDoanChuoiThoiGianOut(BaseModel):
    so_ngay_quan_sat: int
    so_gia_tri_khuyet_thieu: int
    trung_binh_ngay: float
    do_lech_chuan: float
    gia_tri_nho_nhat: float
    gia_tri_lon_nhat: float
    tu_tuong_quan_lag_1: float
    tu_tuong_quan_lag_7: float
    trung_binh_ngay_thuong: float
    trung_binh_cuoi_tuan: float
    ty_le_tang_cuoi_tuan_pct: float
    chenh_lech_trung_binh_hai_nua_pct: float
    danh_gia_tinh_dung: str
    danh_gia_mua_vu: str


class KetQuaSoSanhMoHinhOut(BaseModel):
    ma_danh_gia: Optional[int] = None
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    ten_mo_hinh: str
    nhom_mo_hinh: str  # BASELINE hoặc ML
    val_mae: float
    val_rmse: float
    val_mape: float
    test_mae: float
    test_rmse: float
    test_mape: float
    test_smape: float
    test_r2: float
    mape_ngay_thuong: float
    mape_cuoi_tuan: float
    do_lech_chuan_phan_du: float
    cai_thien_so_voi_baseline_pct: float
    la_mo_hinh_tot_nhat: bool
    tham_so_toi_uu: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TongHopMoHinhToanCucOut(BaseModel):
    ten_mo_hinh: str
    nhom_mo_hinh: str
    so_nguyen_lieu_thang: int
    val_mape_tb: float
    test_mape_tb: float
    test_smape_tb: float
    test_mae_tb: float
    test_rmse_tb: float
    test_r2_tb: float
    mape_ngay_thuong_tb: float
    mape_cuoi_tuan_tb: float
    cai_thien_mape_so_voi_baseline_pct: float
    khoang_tin_cay_bootstrap_95_mape: List[float] = []


class DuBao7NgayNguyenLieuOut(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    danh_muc: Optional[str] = None
    don_vi_tinh: str
    ton_kho_hien_tai: float
    muc_ton_an_toan: float
    mo_hinh_duoc_chon: str
    test_mape: float
    test_mae: float
    cai_thien_so_voi_baseline_pct: float
    tong_du_bao_7_ngay: float
    trung_binh_du_bao_ngay: float
    ngay_cao_diem: str
    du_bao_chi_tiet: List[DiemDuBaoChiTietOut]


class ChiTietDuBaoNguyenLieuOut(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    danh_muc: Optional[str] = None
    don_vi_tinh: str
    mo_hinh_duoc_chon: str
    tham_so_toi_uu: Dict[str, Any] = {}
    chan_doan_chuoi: ChanDoanChuoiThoiGianOut
    so_sanh_cac_mo_hinh: List[KetQuaSoSanhMoHinhOut]
    kiem_thu_thuc_te_vs_du_bao: List[DiemKiemThuThucTeVsDuBaoOut]
    du_bao_7_ngay_toi: List[DiemDuBaoChiTietOut]
    tong_du_bao_7_ngay: float


class LanChayMoHinhOut(BaseModel):
    ma_lan_huan_luyen: int
    ten_phien_ban: str
    thoi_gian_chay: Optional[datetime] = None
    so_nguyen_lieu: int
    so_ngay_lich_su: int
    so_ngay_train: int
    so_ngay_val: int
    so_ngay_test: int
    chan_troi_du_bao: int
    mo_hinh_tot_nhat_pho_bien: str
    baseline_mape_tb: float
    ml_mape_tb: float
    baseline_mae_tb: float
    ml_mae_tb: float
    baseline_rmse_tb: float
    ml_rmse_tb: float
    muc_giam_sai_so_mape_pct: float
    thoi_gian_xu_ly_giay: float
    trang_thai: str
    ghi_chu: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BaoCaoTongQuanDuBaoAIOut(BaseModel):
    lan_huan_luyen: LanChayMoHinhOut
    bang_xep_hang_mo_hinh: List[TongHopMoHinhToanCucOut]
    danh_sach_du_bao_7_ngay: List[DuBao7NgayNguyenLieuOut]
    duong_dan_file_du_bao: Optional[str] = None
    duong_dan_file_so_sanh: Optional[str] = None
    duong_dan_file_bao_cao_json: Optional[str] = None
