/**
 * TypeScript interfaces khớp CHÍNH XÁC với lược đồ CSDL (Mục 5 – đặc tả dự án)
 * và Pydantic Schemas của Backend. Không tự đổi tên trường.
 * DECIMAL từ Backend (Pydantic v2) có thể trả về string hoặc number → dùng `Decimal`.
 */

export type Decimal = number | string;
export type ID = number | string; // INT hoặc UUID
export type ISODateTime = string;
export type ISODate = string;

/* 5.1 NGUYEN_LIEU */
export interface NguyenLieu {
  ma_nguyen_lieu: ID;
  ten_nguyen_lieu: string;
  don_vi_tinh: string; // kg, lít, hộp, cái
  muc_ton_an_toan: Decimal;
  ton_kho_hien_tai: Decimal;
  trang_thai: boolean; // true: đang sử dụng
}

/* 5.2 NHA_CUNG_CAP */
export interface NhaCungCap {
  ma_nha_cung_cap: ID;
  ten_nha_cung_cap: string;
  nguoi_lien_he: string | null;
  email: string | null;
  sdt: string | null;
  dia_chi: string | null;
  thoi_gian_giao_du_kien: number; // ngày
  diem_uy_tin: Decimal; // 1–5 sao
}

/* 5.3 CC_NGUYEN_LIEU (khóa chính tổ hợp) */
export interface CcNguyenLieu {
  ma_nha_cung_cap: ID;
  ma_nguyen_lieu: ID;
  don_gia: Decimal;
  so_luong_dat_toi_thieu: Decimal; // MOQ
  thoi_gian_giao_hang: number; // ngày
  ngay_cap_nhat_gia: ISODateTime;
}

/* 5.4 LO_HANG */
export interface LoHang {
  ma_lo_hang: ID;
  ma_nguyen_lieu: ID;
  ma_lo_nha_cung_cap: string;
  so_luong_nhap: Decimal;
  so_luong_con_lai: Decimal;
  ngay_nhap_kho: ISODateTime;
  han_su_dung: ISODate;
  don_gia_nhap: Decimal;
}

export interface LoHangOut extends LoHang {
  ten_nguyen_lieu?: string | null;
  so_ngay_con_han?: number | null;
  canh_bao_het_han: boolean;
}

/* 5.5 GIAO_DICH_KHO */
export type LoaiGiaoDich = "NHAP" | "XUAT_BAN" | "HAO_HUT" | "KIEM_KE";

export interface GiaoDichKho {
  ma_giao_dich: ID;
  ma_nguyen_lieu: ID;
  loai_giao_dich: LoaiGiaoDich;
  so_luong: Decimal;
  ngay_giao_dich: ISODateTime;
  ma_tham_chieu: string | null;
  ghi_chu: string | null;
}

export interface GiaoDichKhoOut extends GiaoDichKho {
  ten_nguyen_lieu?: string | null;
  don_vi_tinh?: string | null;
}

/* 5.6 DU_BAO_NHU_CAU */
export interface DuBaoNhuCau {
  ma_du_bao: ID;
  ma_nguyen_lieu: ID;
  ngay_du_bao: ISODate; // T+1 … T+7
  so_luong_du_bao: Decimal;
  do_tin_cay: Decimal;
  phuong_phap: string;
}

/* 5.7 PHIEU_DE_XUAT_MUA & CT_DE_XUAT_MUA */
export type TrangThaiPhieu = "CHO_DUYET" | "DA_DUYET" | "TU_CHOI" | "DA_SUA";

export interface PhieuDeXuatMua {
  ma_phieu_de_xuat: ID;
  ngay_tao: ISODateTime;
  tong_tien_du_kien: Decimal;
  trang_thai: TrangThaiPhieu;
  ly_do_tong_quan: string;
}

export interface CtDeXuatMua {
  ma_phieu_de_xuat: ID;
  ma_nguyen_lieu: ID;
  ma_nha_cung_cap: ID;
  so_luong_de_xuat: Decimal;
  don_gia_du_kien: Decimal;
  ly_do_de_xuat: string;
}

/* 5.8 LICH_SU_DUYET & NGUOI_DUNG */
export type HanhDongDuyet = "APPROVE" | "REJECT" | "EDIT";

export interface LichSuDuyet {
  ma_phieu_de_xuat: ID;
  nguoi_duyet: ID; // FK → NGUOI_DUNG
  hanh_dong: HanhDongDuyet;
  y_kien: string | null;
  thoi_gian_duyet: ISODateTime;
}

export type VaiTro = "QUAN_LY" | "NHAN_VIEN_KHO" | "ADMIN";

export interface NguoiDung {
  ma_nguoi_dung: ID;
  ten_nguoi_dung: string;
  email: string;
  vai_tro: VaiTro;
}

/* TÍCH HỢP TUẦN 4 */
export interface NguyenLieuStatus extends NguyenLieu {
  danh_muc?: string | null;
  muc_ton_toi_da?: number;
  tinh_trang: "NGUY_CO_THIEU" | "TON_DU" | "AN_TOAN";
  nhu_cau_du_bao_7ngay: number;
  diem_dat_hang_lai_rop: number;
  so_luong_can_bo_sung: number;
  thong_bao_canh_bao?: string | null;
}

export interface SupplierQuotationItem {
  ma_nha_cung_cap: ID;
  ma_nguyen_lieu: ID;
  don_gia: number;
  so_luong_dat_toi_thieu: number;
  thoi_gian_giao_hang: number;
  ngay_cap_nhat_gia?: string | null;
  ten_nha_cung_cap?: string | null;
  ten_nguyen_lieu?: string | null;
}

export interface NhaCungCapWithQuotations extends NhaCungCap {
  diem_chat_luong?: number;
  quotations: SupplierQuotationItem[];
}

export interface DashboardStats {
  tong_nguyen_lieu_dang_dung: number;
  nguy_co_thieu_hang: number;
  nguy_co_ton_du: number;
  phieu_cho_duyet: number;
  tong_gia_tri_ton_kho: number;
  ty_le_an_toan: number;
}

export interface AlertItem {
  ma_nguyen_lieu: ID;
  ten_nguyen_lieu: string;
  don_vi_tinh: string;
  muc_do: "DANGER" | "WARNING" | "EXPIRY";
  loai_canh_bao: string;
  noi_dung: string;
  ton_kho_hien_tai: number;
  nguong_canh_bao: number;
  so_luong_can_bo_sung?: number;
}

export interface MonthlyTrend {
  thang: string;
  tong_tieu_hao_kg: number;
  chi_phi_uoc_tinh: number;
}

export interface ForecastPoint {
  ngay: string;
  so_luong: number;
  do_tin_cay: number;
}

export interface ForecastSummary {
  ma_nguyen_lieu: ID;
  ten_nguyen_lieu: string;
  don_vi_tinh: string;
  tong_nhu_cau_7ngay: number;
  trung_binh_ngay: number;
  du_lieu_7ngay: ForecastPoint[];
}

export interface ProposalDetailItem {
  ma_chi_tiet: ID;
  ma_phieu_de_xuat: ID;
  ma_nguyen_lieu: ID;
  ma_nha_cung_cap: ID;
  so_luong_de_xuat: number;
  don_gia_du_kien: number;
  so_luong_du_doan_7ngay: number;
  ly_do_de_xuat: string;
  ten_nguyen_lieu?: string;
  don_vi_tinh?: string;
  ten_nha_cung_cap?: string;
  thanh_tien: number;
}

export interface ProposalWithDetails extends PhieuDeXuatMua {
  nguoi_tao: string;
  details: ProposalDetailItem[];
  approval_history: LichSuDuyet[];
}

/* TUẦN 4 - Lô hàng & hạn sử dụng (GET /inventory/batches) */
export interface LoHangStatus {
  ma_lo_hang: ID;
  ma_nguyen_lieu: ID;
  ma_lo_nha_cung_cap?: string | null;
  so_luong_nhap: number;
  so_luong_con_lai: number;
  ngay_nhap_kho?: string | null;
  han_su_dung?: string | null;
  don_gia_nhap: number;
  ten_nguyen_lieu?: string | null;
  so_ngay_con_han?: number | null;
  canh_bao_het_han: boolean;
}

/* TÍCH HỢP TUẦN 5 – BÓC TÁCH ĐỊNH MỨC BOM & LÀM SẠCH DỮ LIỆU (100% TIẾNG VIỆT) */
export interface ChiTietDinhMucBom {
  ma_dinh_muc: number;
  ma_mon: number;
  ma_nguyen_lieu: number;
  ten_nguyen_lieu: string;
  don_vi_tinh: string;
  so_luong_tieu_hao: number;
  don_gia_nguyen_lieu_uoc_tinh: number;
  chi_phi_dinh_muc: number;
  ghi_chu?: string | null;
}

export interface MonAnKemDinhMucBom {
  ma_mon: number;
  ten_mon: string;
  danh_muc?: string | null;
  don_gia_ban: number;
  trang_thai: boolean;
  gia_von_nguyen_lieu: number;
  ty_suat_loi_nhuan_gop: number;
  cong_thuc_bom: ChiTietDinhMucBom[];
}

export interface NguyenLieuTieuHao {
  ma_nguyen_lieu: number;
  ten_nguyen_lieu: string;
  don_vi_tinh: string;
  tong_luong_tieu_hao: number;
  ton_kho_hien_tai: number;
  ton_kho_sau_tieu_hao: number;
  muc_ton_an_toan: number;
  du_ton_kho_dap_ung: boolean;
  chi_phi_uoc_tinh: number;
}

export interface KetQuaMoPhongBom {
  tong_so_ly_ban: number;
  tong_doanh_thu_du_kien: number;
  tong_chi_phi_nguyen_lieu: number;
  loi_nhuan_gop_du_kien: number;
  da_cap_nhat_kho: boolean;
  danh_sach_nguyen_lieu_tieu_hao: NguyenLieuTieuHao[];
}

export interface BaoCaoChatLuongDuLieu {
  ma_lan_chay: number;
  ten_quy_trinh: string;
  thoi_gian_chay?: string | null;
  tong_dong_tho: number;
  so_dong_trung_lap: number;
  so_dong_thieu_du_lieu: number;
  so_dong_am_hoac_loi: number;
  so_dong_ngoai_lai_da_xu_ly: number;
  tong_dong_sach: number;
  ty_le_du_lieu_sach: number;
  so_ngay_xu_ly: number;
  tong_ban_ghi_tieu_hao_sinh_ra: number;
  trang_thai: string;
  ghi_chu?: string | null;
  duong_dan_file_tho?: string | null;
  duong_dan_file_sach?: string | null;
  duong_dan_file_tieu_hao?: string | null;
}

export interface DiemChuoiThoiGianTieuHao {
  ngay: string;
  so_luong_tieu_hao: number;
  so_ly_lien_quan: number;
  thu_trong_tuan: number;
  la_cuoi_tuan: boolean;
  he_so_mua_vu: number;
  tieu_hao_hom_truoc?: number | null;
  tieu_hao_7_ngay_truoc?: number | null;
  trung_binh_truot_7_ngay?: number | null;
  do_lech_chuan_7_ngay?: number | null;
}

export interface ChuoiThoiGianNguyenLieu {
  ma_nguyen_lieu: number;
  ten_nguyen_lieu: string;
  don_vi_tinh: string;
  so_ngay_du_lieu: number;
  tong_tieu_hao: number;
  trung_binh_ngay: number;
  tieu_hao_ngay_thuong_tb: number;
  tieu_hao_cuoi_tuan_tb: number;
  ty_le_tang_cuoi_tuan_pct: number;
  chuoi_thoi_gian: DiemChuoiThoiGianTieuHao[];
}

export interface LichSuBanHangPos {
  ma_ban_hang: number;
  ma_hoa_don_pos: string;
  ngay_ban: string;
  ca_ban: string;
  ma_mon: number;
  ten_mon?: string | null;
  so_luong_ly: number;
  don_gia_ban: number;
  thanh_tien: number;
  da_boc_tach_bom: boolean;
}
