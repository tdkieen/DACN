from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.dinh_muc_bom import (
    MonAnKemDinhMucBomOut,
    YeuCauLuuMonAnBom,
    YeuCauMoPhongBom,
    KetQuaMoPhongBom,
    YeuCauTaoHoaDonPos,
    LichSuBanHangOut,
    BaoCaoChatLuongDuLieuOut,
    PhanHoiChuoiThoiGianNguyenLieu,
)
from app.services.dich_vu_dinh_muc_bom import (
    lay_thuc_don_kem_dinh_muc_bom,
    luu_mon_an_kem_dinh_muc_bom,
    mo_phong_boc_tach_bom,
    ghi_nhan_hoa_don_pos_va_tru_kho,
    lay_lich_su_ban_hang_pos,
    chay_quy_trinh_boc_tach_bom,
    lay_bao_cao_chat_luong_du_lieu,
    lay_chuoi_thoi_gian_tieu_hao,
)

router = APIRouter()


@router.get(
    "/thuc-don-bom",
    response_model=List[MonAnKemDinhMucBomOut],
    summary="Danh sách thực đơn đồ uống và định mức công thức pha chế BOM (kèm giá vốn nguyên liệu)",
)
def doc_thuc_don_kem_dinh_muc_bom(db: Session = Depends(get_db)):
    return lay_thuc_don_kem_dinh_muc_bom(db)


@router.post(
    "/thuc-don-bom",
    response_model=MonAnKemDinhMucBomOut,
    summary="Tạo mới hoặc cập nhật món đồ uống kèm công thức định mức BOM",
)
def cap_nhat_thuc_don_kem_dinh_muc_bom(
    du_lieu: YeuCauLuuMonAnBom,
    db: Session = Depends(get_db),
):
    try:
        return luu_mon_an_kem_dinh_muc_bom(db, du_lieu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/mo-phong-bom",
    response_model=KetQuaMoPhongBom,
    summary="Mô phỏng bóc tách định mức nguyên liệu từ số lượng ly đồ uống bán ra",
)
def mo_phong_boc_tach_dinh_muc(
    du_lieu: YeuCauMoPhongBom,
    db: Session = Depends(get_db),
):
    try:
        return mo_phong_boc_tach_bom(db, du_lieu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/hoa-don-pos",
    response_model=KetQuaMoPhongBom,
    status_code=201,
    summary="Ghi nhận hóa đơn bán hàng tại quầy (POS), tự động bóc tách BOM và trừ kho lô hàng (hết hạn trước xuất trước)",
)
def tao_hoa_don_ban_hang_pos(
    du_lieu: YeuCauTaoHoaDonPos,
    db: Session = Depends(get_db),
):
    try:
        return ghi_nhan_hoa_don_pos_va_tru_kho(db, du_lieu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/lich-su-pos",
    response_model=List[LichSuBanHangOut],
    summary="Danh sách lịch sử hóa đơn bán hàng POS đã làm sạch và bóc tách BOM",
)
def doc_lich_su_ban_hang_pos(
    ma_mon: Optional[int] = Query(None, description="Lọc theo mã món đồ uống"),
    ca_ban: Optional[str] = Query(None, description="Lọc theo ca bán: SANG, CHIEU, TOI"),
    gioi_han: int = Query(30, ge=5, le=200),
    db: Session = Depends(get_db),
):
    return lay_lich_su_ban_hang_pos(db, ma_mon=ma_mon, ca_ban=ca_ban, gioi_han=gioi_han)


@router.post(
    "/chay-quy-trinh",
    response_model=BaoCaoChatLuongDuLieuOut,
    summary="Kích hoạt chạy quy trình Thu thập - Làm sạch dữ liệu POS - Bóc tách định mức BOM 12 tháng",
)
def kich_hoat_quy_trinh_du_lieu_bom(
    so_ngay: int = Query(365, ge=30, le=730, description="Số ngày lịch sử bán hàng cần xử lý"),
    db: Session = Depends(get_db),
):
    return chay_quy_trinh_boc_tach_bom(db, so_ngay=so_ngay)


@router.get(
    "/bao-cao-chat-luong",
    response_model=BaoCaoChatLuongDuLieuOut,
    summary="Xem báo cáo kiểm định chất lượng dữ liệu bán hàng POS & kết quả làm sạch gần nhất",
)
def doc_bao_cao_chat_luong_du_lieu(db: Session = Depends(get_db)):
    return lay_bao_cao_chat_luong_du_lieu(db)


@router.get(
    "/chuoi-thoi-gian/{ma_nguyen_lieu}",
    response_model=PhanHoiChuoiThoiGianNguyenLieu,
    summary="Lấy chuỗi thời gian tiêu hao nguyên liệu theo ngày kèm trung bình trượt 7 ngày",
)
def doc_chuoi_thoi_gian_nguyen_lieu(
    ma_nguyen_lieu: int,
    so_ngay: int = Query(90, ge=14, le=365, description="Số ngày gần nhất cần lấy"),
    db: Session = Depends(get_db),
):
    try:
        return lay_chuoi_thoi_gian_tieu_hao(db, ma_nguyen_lieu=ma_nguyen_lieu, so_ngay=so_ngay)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
