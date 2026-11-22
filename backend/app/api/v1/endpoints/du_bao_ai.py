from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.du_bao_ai import (
    BaoCaoTongQuanDuBaoAIOut,
    ChiTietDuBaoNguyenLieuOut,
    DuBao7NgayNguyenLieuOut,
    KetQuaSoSanhMoHinhOut,
    LanChayMoHinhOut,
)
from app.services.dich_vu_du_bao_ai import (
    chay_huan_luyen_va_du_bao_ai,
    lay_bang_so_sanh_mo_hinh,
    lay_chi_tiet_du_bao_nguyen_lieu,
    lay_du_bao_7_ngay_tat_ca,
    lay_lich_su_huan_luyen,
    lay_tong_quan_du_bao_ai,
)

router = APIRouter()


@router.post(
    "/huan-luyen",
    response_model=BaoCaoTongQuanDuBaoAIOut,
    summary="Kích hoạt huấn luyện & so sánh 5 mô hình dự báo (Baseline vs ML) và cập nhật dự báo 7 ngày cho 15 nguyên liệu",
)
def kich_hoat_huan_luyen_mo_hinh(
    chan_troi_du_bao: int = Query(7, ge=3, le=14, description="Số ngày tương lai cần dự báo (mặc định 7 ngày)"),
    db: Session = Depends(get_db),
):
    try:
        return chay_huan_luyen_va_du_bao_ai(db, chan_troi_du_bao=chan_troi_du_bao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/tong-quan",
    response_model=BaoCaoTongQuanDuBaoAIOut,
    summary="Báo cáo tổng quan lần huấn luyện gần nhất, bảng xếp hạng mô hình và dự báo 7 ngày 15 nguyên liệu",
)
def doc_tong_quan_du_bao_ai(db: Session = Depends(get_db)):
    return lay_tong_quan_du_bao_ai(db)


@router.get(
    "/so-sanh-mo-hinh",
    response_model=List[KetQuaSoSanhMoHinhOut],
    summary="Bảng so sánh chi tiết MAE / RMSE / MAPE / R2 giữa các mô hình Baseline và ML",
)
def doc_bang_so_sanh_mo_hinh(
    ma_nguyen_lieu: Optional[int] = Query(None, description="Lọc theo mã nguyên liệu cụ thể"),
    chi_lay_tot_nhat: bool = Query(False, description="Chỉ lấy mô hình thắng cuộc của từng nguyên liệu"),
    db: Session = Depends(get_db),
):
    return lay_bang_so_sanh_mo_hinh(
        db,
        ma_nguyen_lieu=ma_nguyen_lieu,
        chi_lay_tot_nhat=chi_lay_tot_nhat,
    )


@router.get(
    "/du-bao-7-ngay",
    response_model=List[DuBao7NgayNguyenLieuOut],
    summary="Danh sách dự báo nhu cầu 7 ngày tới (kèm khoảng tin cậy 95%) cho toàn bộ 15 nguyên liệu",
)
def doc_du_bao_7_ngay_tat_ca(
    danh_muc: Optional[str] = Query(None, description="Lọc theo danh mục nguyên liệu"),
    db: Session = Depends(get_db),
):
    return lay_du_bao_7_ngay_tat_ca(db, danh_muc=danh_muc)


@router.get(
    "/nguyen-lieu/{ma_nguyen_lieu}",
    response_model=ChiTietDuBaoNguyenLieuOut,
    summary="Phân tích chuyên sâu 1 nguyên liệu: chẩn đoán chuỗi thời gian, Actual vs Predicted trên tập Test & dự báo 7 ngày",
)
def doc_chi_tiet_du_bao_nguyen_lieu(
    ma_nguyen_lieu: int,
    db: Session = Depends(get_db),
):
    try:
        return lay_chi_tiet_du_bao_nguyen_lieu(db, ma_nguyen_lieu=ma_nguyen_lieu)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/lich-su-huan-luyen",
    response_model=List[LanChayMoHinhOut],
    summary="Lịch sử các lần huấn luyện & đánh giá mô hình dự báo (LAN_CHAY_MO_HINH)",
)
def doc_lich_su_huan_luyen(
    gioi_han: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return lay_lich_su_huan_luyen(db, gioi_han=gioi_han)
