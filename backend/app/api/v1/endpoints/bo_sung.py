"""
API Endpoints cho Tuần 7:
- `GET  /api/v1/bo-sung/ke-hoach`: Kế hoạch bổ sung hàng (ROP, Safety Stock, số lượng cần đặt, NCC được chọn theo MCDM & dự báo ML)
- `POST /api/v1/bo-sung/tao-de-xuat`: Tạo phiếu đề xuất chờ duyệt cho 1 nguyên liệu từ bảng ROP
- `POST /api/v1/bo-sung/ai-agent/chay`: Kích hoạt Hybrid Multi-Model AI Agent (Time-Series ML + ROP/MCDM + Gemini Function Calling 4 Tools)
- `GET  /api/v1/bo-sung/ai-agent/kien-truc`: Xem cấu hình Kiến trúc Kết hợp Đa Mô hình (3 tầng AI)
- `GET  /api/v1/bo-sung/ai-agent/nhat-ky`: Xem lịch sử các bước suy luận và gọi Tool của AI Agent
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bo_sung import (
    KeHoachBoSungNguyenLieuOut,
    KetQuaAiAgentOut,
    KienTrucMultiModelOut,
    NhatKyAiAgentOut,
    YeuCauChayAiAgent,
    YeuCauTaoDeXuatBoSung,
)
from app.schemas.proposal import PurchaseProposalOut
from app.services.dich_vu_ke_hoach_bo_sung import (
    chay_ai_procurement_agent,
    lay_lich_su_nhat_ky_agent,
    lay_thong_tin_kien_truc_multi_model,
    tao_de_xuat_bo_sung_mot_nguyen_lieu,
    xay_dung_ke_hoach_bo_sung,
)

router = APIRouter()


@router.get(
    "/ke-hoach",
    response_model=List[KeHoachBoSungNguyenLieuOut],
    summary="Lấy kế hoạch bổ sung hàng Tuần 7 (ROP, Safety Stock, MCDM & Dự báo ML 7 ngày)",
)
def doc_ke_hoach_bo_sung(
    chi_lay_can_dat: bool = Query(
        False,
        description="Nếu True, chỉ trả về các nguyên liệu có Tồn hiện tại <= ROP cần đặt hàng",
    ),
    db: Session = Depends(get_db),
):
    return xay_dung_ke_hoach_bo_sung(db=db, chi_lay_can_dat=chi_lay_can_dat)


@router.post(
    "/tao-de-xuat",
    response_model=PurchaseProposalOut,
    summary="Tạo phiếu đề xuất mua hàng (CHO_DUYET) cho 1 nguyên liệu từ bảng ROP Tuần 7",
)
def tao_de_xuat_bo_sung(
    yeu_cau: YeuCauTaoDeXuatBoSung,
    db: Session = Depends(get_db),
):
    try:
        return tao_de_xuat_bo_sung_mot_nguyen_lieu(db=db, yeu_cau=yeu_cau)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo phiếu đề xuất bổ sung: {str(e)}")


@router.post(
    "/ai-agent/chay",
    response_model=KetQuaAiAgentOut,
    summary="Thực thi Hybrid Multi-Model AI Agent (Dự báo ML + ROP/MCDM + Gemini Function Calling 4 Tools)",
)
def kich_hoat_hybrid_ai_agent(
    yeu_cau: Optional[YeuCauChayAiAgent] = None,
    db: Session = Depends(get_db),
):
    try:
        return chay_ai_procurement_agent(db=db, yeu_cau=yeu_cau)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi thực thi Hybrid Multi-Model AI Agent: {str(e)}")


@router.get(
    "/ai-agent/kien-truc",
    response_model=KienTrucMultiModelOut,
    summary="Thông tin Kiến trúc Kết hợp Đa Mô hình (3 tầng AI & 4 Tools an toàn)",
)
def doc_kien_truc_multi_model():
    return lay_thong_tin_kien_truc_multi_model()


@router.get(
    "/ai-agent/nhat-ky",
    response_model=List[NhatKyAiAgentOut],
    summary="Nhật ký suy luận và các bước gọi Tool (Function Calling) của AI Agent",
)
def doc_nhat_ky_ai_agent(
    gioi_han: int = Query(20, ge=1, le=100, description="Số bản ghi nhật ký tối đa cần lấy"),
    db: Session = Depends(get_db),
):
    return lay_lich_su_nhat_ky_agent(db=db, gioi_han=gioi_han)
