from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import date, datetime


class ChiTietDinhMucBomOut(BaseModel):
    ma_dinh_muc: int
    ma_mon: int
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    so_luong_tieu_hao: float
    don_gia_nguyen_lieu_uoc_tinh: float = 0.0
    chi_phi_dinh_muc: float = 0.0
    ghi_chu: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MonAnKemDinhMucBomOut(BaseModel):
    ma_mon: int
    ten_mon: str
    danh_muc: Optional[str] = None
    don_gia_ban: float
    trang_thai: bool = True
    gia_von_nguyen_lieu: float = 0.0
    ty_suat_loi_nhuan_gop: float = 0.0  # Tỷ suất lợi nhuận gộp (%)
    cong_thuc_bom: List[ChiTietDinhMucBomOut] = []

    model_config = ConfigDict(from_attributes=True)


class ChiTietCapNhatDinhMucBom(BaseModel):
    ma_nguyen_lieu: int
    so_luong_tieu_hao: float = Field(..., gt=0)
    ghi_chu: Optional[str] = None


class YeuCauLuuMonAnBom(BaseModel):
    ma_mon: Optional[int] = None
    ten_mon: str
    danh_muc: str = "Cà phê truyền thống"
    don_gia_ban: float = Field(..., gt=0)
    cong_thuc_bom: List[ChiTietCapNhatDinhMucBom]


class MonBanDauVao(BaseModel):
    ma_mon: int = Field(..., description="Mã món đồ uống trong thực đơn")
    so_luong_ly: float = Field(..., gt=0, description="Số lượng ly bán ra hoặc dự kiến bán")


class YeuCauMoPhongBom(BaseModel):
    danh_sach_mon_ban: List[MonBanDauVao]
    cap_nhat_xuat_kho: bool = Field(
        False,
        description="Nếu True sẽ tự động ghi nhận giao dịch XUAT_BAN và trừ tồn kho thực tế theo nguyên tắc hết hạn trước xuất trước"
    )
    ma_tham_chieu: Optional[str] = "MO-PHONG-POS"


class NguyenLieuTieuHaoOut(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    tong_luong_tieu_hao: float
    ton_kho_hien_tai: float
    ton_kho_sau_tieu_hao: float
    muc_ton_an_toan: float
    du_ton_kho_dap_ung: bool
    chi_phi_uoc_tinh: float


class KetQuaMoPhongBom(BaseModel):
    tong_so_ly_ban: float
    tong_doanh_thu_du_kien: float
    tong_chi_phi_nguyen_lieu: float
    loi_nhuan_gop_du_kien: float
    da_cap_nhat_kho: bool
    danh_sach_nguyen_lieu_tieu_hao: List[NguyenLieuTieuHaoOut]


class YeuCauTaoHoaDonPos(BaseModel):
    ma_hoa_don_pos: Optional[str] = None
    ngay_ban: Optional[date] = None
    ca_ban: str = "SANG"
    danh_sach_mon_ban: List[MonBanDauVao]


class LichSuBanHangOut(BaseModel):
    ma_ban_hang: int
    ma_hoa_don_pos: str
    ngay_ban: date
    ca_ban: str
    ma_mon: int
    ten_mon: Optional[str] = None
    so_luong_ly: float
    don_gia_ban: float
    thanh_tien: float
    da_boc_tach_bom: bool

    model_config = ConfigDict(from_attributes=True)


class BaoCaoChatLuongDuLieuOut(BaseModel):
    ma_lan_chay: int
    ten_quy_trinh: str
    thoi_gian_chay: Optional[datetime] = None
    tong_dong_tho: int
    so_dong_trung_lap: int
    so_dong_thieu_du_lieu: int
    so_dong_am_hoac_loi: int
    so_dong_ngoai_lai_da_xu_ly: int
    tong_dong_sach: int
    ty_le_du_lieu_sach: float
    so_ngay_xu_ly: int
    tong_ban_ghi_tieu_hao_sinh_ra: int
    trang_thai: str
    ghi_chu: Optional[str] = None
    duong_dan_file_tho: Optional[str] = None
    duong_dan_file_sach: Optional[str] = None
    duong_dan_file_tieu_hao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DiemChuoiThoiGianTieuHaoOut(BaseModel):
    ngay: date
    so_luong_tieu_hao: float
    so_ly_lien_quan: int
    thu_trong_tuan: int
    la_cuoi_tuan: bool
    he_so_mua_vu: float
    tieu_hao_hom_truoc: Optional[float] = None
    tieu_hao_7_ngay_truoc: Optional[float] = None
    trung_binh_truot_7_ngay: Optional[float] = None
    do_lech_chuan_7_ngay: Optional[float] = None


class PhanHoiChuoiThoiGianNguyenLieu(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    so_ngay_du_lieu: int
    tong_tieu_hao: float
    trung_binh_ngay: float
    tieu_hao_ngay_thuong_tb: float
    tieu_hao_cuoi_tuan_tb: float
    ty_le_tang_cuoi_tuan_pct: float
    chuoi_thoi_gian: List[DiemChuoiThoiGianTieuHaoOut]
