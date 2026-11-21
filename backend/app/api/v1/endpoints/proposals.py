from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.proposal import (
    PurchaseProposalOut, ProposalActionRequest
)
from app.services.proposal_service import (
    get_proposals, get_proposal_by_id, handle_proposal_action
)

router = APIRouter()

@router.get("", response_model=List[PurchaseProposalOut], summary="Danh sách đề xuất mua hàng do AI tạo")
def read_proposals(
    trang_thai: Optional[str] = Query(None, description="Lọc trạng thái: CHO_DUYET, DA_DUYET, TU_CHOI, DA_SUA"),
    db: Session = Depends(get_db)
):
    return get_proposals(db, status_filter=trang_thai)

@router.get("/{proposal_id}", response_model=PurchaseProposalOut, summary="Chi tiết phiếu đề xuất mua hàng")
def read_proposal_detail(
    proposal_id: int,
    db: Session = Depends(get_db)
):
    proposal = get_proposal_by_id(db, proposal_id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đề xuất")
    return proposal

@router.post("/{proposal_id}/action", response_model=PurchaseProposalOut, summary="Phê duyệt, Từ chối hoặc Sửa đề xuất (Human-in-the-loop)")
def action_proposal(
    proposal_id: int,
    data: ProposalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("QUAN_LY")),
):
    data.nguoi_duyet = current_user.ten_nguoi_dung  # ghi đúng tên người đang đăng nhập
    try:
        return handle_proposal_action(db, proposal_id=proposal_id, action_data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
