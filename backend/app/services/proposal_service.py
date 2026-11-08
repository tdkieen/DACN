from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.proposal import PurchaseProposal, ProposalDetail, ApprovalHistory
from app.models.ingredient import Ingredient
from app.models.supplier import Supplier
from app.schemas.proposal import (
    PurchaseProposalCreate, PurchaseProposalOut, ProposalDetailOut,
    ApprovalHistoryOut, ProposalActionRequest
)

def get_proposals(
    db: Session,
    status_filter: Optional[str] = None
) -> List[PurchaseProposalOut]:
    query = db.query(PurchaseProposal)
    if status_filter:
        query = query.filter(PurchaseProposal.trang_thai == status_filter)

    proposals = query.order_by(PurchaseProposal.ma_phieu_de_xuat.desc()).all()
    results = []

    for p in proposals:
        detail_outs = []
        for d in p.details:
            detail_outs.append(ProposalDetailOut(
                ma_chi_tiet=d.ma_chi_tiet,
                ma_phieu_de_xuat=d.ma_phieu_de_xuat,
                ma_nguyen_lieu=d.ma_nguyen_lieu,
                ma_nha_cung_cap=d.ma_nha_cung_cap,
                so_luong_de_xuat=d.so_luong_de_xuat,
                don_gia_du_kien=d.don_gia_du_kien,
                so_luong_du_doan_7ngay=d.so_luong_du_doan_7ngay,
                ly_do_de_xuat=d.ly_do_de_xuat,
                ten_nguyen_lieu=d.ingredient.ten_nguyen_lieu if d.ingredient else None,
                don_vi_tinh=d.ingredient.don_vi_tinh if d.ingredient else None,
                ten_nha_cung_cap=d.supplier.ten_nha_cung_cap if d.supplier else None,
                thanh_tien=round(d.so_luong_de_xuat * d.don_gia_du_kien, 2)
            ))

        history_outs = []
        for h in p.approval_history:
            history_outs.append(ApprovalHistoryOut(
                ma_lich_su=h.ma_lich_su,
                ma_phieu_de_xuat=h.ma_phieu_de_xuat,
                nguoi_duyet=h.nguoi_duyet,
                hanh_dong=h.hanh_dong,
                y_kien=h.y_kien,
                thoi_gian_duyet=h.thoi_gian_duyet
            ))

        p_out = PurchaseProposalOut(
            ma_phieu_de_xuat=p.ma_phieu_de_xuat,
            ngay_tao=p.ngay_tao,
            tong_tien_du_kien=p.tong_tien_du_kien,
            trang_thai=p.trang_thai,
            ly_do_tong_quan=p.ly_do_tong_quan,
            nguoi_tao=p.nguoi_tao,
            details=detail_outs,
            approval_history=history_outs
        )
        results.append(p_out)

    return results

def get_proposal_by_id(db: Session, proposal_id: int) -> Optional[PurchaseProposalOut]:
    p = db.query(PurchaseProposal).filter(PurchaseProposal.ma_phieu_de_xuat == proposal_id).first()
    if not p:
        return None

    detail_outs = []
    for d in p.details:
        detail_outs.append(ProposalDetailOut(
            ma_chi_tiet=d.ma_chi_tiet,
            ma_phieu_de_xuat=d.ma_phieu_de_xuat,
            ma_nguyen_lieu=d.ma_nguyen_lieu,
            ma_nha_cung_cap=d.ma_nha_cung_cap,
            so_luong_de_xuat=d.so_luong_de_xuat,
            don_gia_du_kien=d.don_gia_du_kien,
            so_luong_du_doan_7ngay=d.so_luong_du_doan_7ngay,
            ly_do_de_xuat=d.ly_do_de_xuat,
            ten_nguyen_lieu=d.ingredient.ten_nguyen_lieu if d.ingredient else None,
            don_vi_tinh=d.ingredient.don_vi_tinh if d.ingredient else None,
            ten_nha_cung_cap=d.supplier.ten_nha_cung_cap if d.supplier else None,
            thanh_tien=round(d.so_luong_de_xuat * d.don_gia_du_kien, 2)
        ))

    history_outs = []
    for h in p.approval_history:
        history_outs.append(ApprovalHistoryOut(
            ma_lich_su=h.ma_lich_su,
            ma_phieu_de_xuat=h.ma_phieu_de_xuat,
            nguoi_duyet=h.nguoi_duyet,
            hanh_dong=h.hanh_dong,
            y_kien=h.y_kien,
            thoi_gian_duyet=h.thoi_gian_duyet
        ))

    return PurchaseProposalOut(
        ma_phieu_de_xuat=p.ma_phieu_de_xuat,
        ngay_tao=p.ngay_tao,
        tong_tien_du_kien=p.tong_tien_du_kien,
        trang_thai=p.trang_thai,
        ly_do_tong_quan=p.ly_do_tong_quan,
        nguoi_tao=p.nguoi_tao,
        details=detail_outs,
        approval_history=history_outs
    )

def handle_proposal_action(
    db: Session,
    proposal_id: int,
    action_data: ProposalActionRequest
) -> PurchaseProposalOut:
    p = db.query(PurchaseProposal).filter(PurchaseProposal.ma_phieu_de_xuat == proposal_id).first()
    if not p:
        raise ValueError("Phiếu đề xuất không tồn tại")

    # Cập nhật trạng thái phiếu
    if action_data.hanh_dong == "APPROVE":
        p.trang_thai = "DA_DUYET"
    elif action_data.hanh_dong == "REJECT":
        p.trang_thai = "TU_CHOI"
    elif action_data.hanh_dong == "MODIFY":
        p.trang_thai = "DA_SUA"
    else:
        raise ValueError("Hành động không hợp lệ: phải là APPROVE, REJECT hoặc MODIFY")

    # Lưu lịch sử phê duyệt (Human-in-the-loop)
    history = ApprovalHistory(
        ma_phieu_de_xuat=proposal_id,
        nguoi_duyet=action_data.nguoi_duyet,
        hanh_dong=action_data.hanh_dong,
        y_kien=action_data.y_kien,
        thoi_gian_duyet=datetime.now()
    )
    db.add(history)
    db.commit()

    return get_proposal_by_id(db, proposal_id)
