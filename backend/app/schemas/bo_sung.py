"""
Schemas Pydantic cho Tuần 7:
- Kế hoạch bổ sung tồn kho (ROP, Safety Stock động, số lượng cần đặt chuẩn hóa MOQ & đơn vị rời rạc)
- Đánh giá và chọn nhà cung cấp tối ưu theo MCDM kèm giải trình lý do
- Kiến trúc Kết hợp Đa Mô hình (Hybrid Multi-Model AI Agent: Time-Series ML + ROP/MCDM + Gemini Function Calling)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NhaCungCapChonOut(BaseModel):
    ma_nha_cung_cap: int
    ten_nha_cung_cap: str
    don_gia: float
    thoi_gian_giao_hang: int
    so_luong_dat_toi_thieu: float
    diem_chat_luong: float = 4.5
    diem_uy_tin: float = 4.5
    diem_tong_hop_mcdm: float


class KeHoachBoSungNguyenLieuOut(BaseModel):
    """Cấu trúc khớp 100% với Frontend `replenishment.py` (Tuần 7) và bổ sung thông tin Đa Mô hình AI."""

    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    danh_muc: Optional[str] = ""
    don_vi_tinh: str
    ton_kho_hien_tai: float
    nhu_cau_tb_ngay: float
    nhu_cau_du_bao_7ngay: float = 0.0
    mo_hinh_du_bao: str = "Ensemble_HW_Ridge"
    do_tin_cay_du_bao_pct: float = 93.0
    thoi_gian_giao_hang: int
    muc_ton_an_toan: float
    ton_an_toan_goi_y_ai: float = 0.0
    diem_dat_hang_lai_rop: float
    so_luong_can_dat: float
    can_dat_hang: bool
    da_lam_tron_moq: bool = False
    canh_bao_lo_sap_het_han: Optional[str] = None
    nha_cung_cap_chon: Optional[NhaCungCapChonOut] = None
    ly_do_chon_ncc: str = ""
    thanh_tien_du_kien: float = 0.0


class YeuCauTaoDeXuatBoSung(BaseModel):
    """Body cho POST /api/v1/bo-sung/tao-de-xuat (khớp `replenishment.py` & `state.py`)."""

    ma_nguyen_lieu: int = Field(..., description="Mã nguyên liệu cần lập đề xuất mua")
    so_luong: Optional[float] = Field(None, description="Số lượng đề xuất đặt (nếu bỏ trống sẽ lấy từ kế hoạch ROP)")
    ma_nha_cung_cap: Optional[int] = Field(None, description="Mã nhà cung cấp (nếu bỏ trống sẽ chọn NCC tối ưu theo MCDM)")
    ghi_chu_them: Optional[str] = Field(None, description="Ghi chú hoặc yêu cầu bổ sung cho AI Agent")


class BuocGoiToolAgentOut(BaseModel):
    buoc: int
    ten_tool: str
    mo_hinh_con: str
    tham_so: Dict[str, Any] = {}
    tom_tat_ket_qua: str


class YeuCauChayAiAgent(BaseModel):
    yeu_cau: str = Field(
        default="Quét toàn bộ tồn kho, đối chiếu dự báo nhu cầu 7 ngày của mô hình ML, kiểm tra điểm đặt hàng lại (ROP), lô hàng sắp hết hạn (FEFO), xếp hạng nhà cung cấp bằng MCDM và lập phiếu đề xuất mua hàng chờ duyệt.",
        description="Câu lệnh điều khiển AI Procurement Agent",
    )
    ma_nguyen_lieu: Optional[int] = Field(
        None,
        description="Nếu truyền mã nguyên liệu, Agent sẽ tập trung phân tích & lập phiếu cho nguyên liệu đó",
    )
    tao_phieu_de_xuat: bool = Field(
        default=True,
        description="Cho phép Agent gọi tool `tao_phieu_de_xuat_mua` tạo phiếu ở trạng thái CHO_DUYET",
    )
    su_dung_mo_hinh_suy_luan_sau: bool = Field(
        default=False,
        description="Nếu True sẽ ưu tiên dùng gemini-4-argon cho phân tích chiến lược phức tạp, ngược lại dùng gemini-3.8-flash",
    )


class KetQuaAiAgentOut(BaseModel):
    ma_nhat_ky: int
    thoi_gian: datetime
    che_do_agent: str
    mo_hinh_llm: str
    da_ket_noi_gemini_cloud: bool
    cac_mo_hinh_ket_hop: List[str]
    so_buoc_suy_luan: int
    danh_sach_tool_da_goi: List[BuocGoiToolAgentOut]
    ma_phieu_de_xuat: Optional[int] = None
    tong_tien_de_xuat: float = 0.0
    so_mat_hang_de_xuat: int = 0
    phan_hoi_agent: str
    thoi_gian_xu_ly_giay: float


class NhatKyAiAgentOut(BaseModel):
    ma_nhat_ky: int
    thoi_gian: Optional[datetime] = None
    yeu_cau_dau_vao: str
    che_do_agent: str
    mo_hinh_llm: str
    cac_mo_hinh_ket_hop: str
    so_buoc_suy_luan: int
    ma_phieu_de_xuat: Optional[int] = None
    phan_hoi_agent: str
    thoi_gian_xu_ly_giay: float

    model_config = ConfigDict(from_attributes=True)


class ThanhPhanMoHinhAiOut(BaseModel):
    tang_kien_truc: str
    ten_mo_hinh: str
    loai_mo_hinh: str
    vai_tro_trong_he_thong: str
    dau_vao: str
    dau_ra: str
    trang_thai_hoat_dong: str


class KienTrucMultiModelOut(BaseModel):
    ten_kien_truc: str
    mo_ta_tong_quan: str
    da_cau_hinh_gemini_api_key: bool
    mo_hinh_agent_mac_dinh: str
    mo_hinh_suy_luan_sau: str
    danh_sach_4_tools_an_toan: List[str]
    cam_ket_human_in_the_loop: str
    cac_mo_hinh_ket_hop: List[ThanhPhanMoHinhAiOut]
