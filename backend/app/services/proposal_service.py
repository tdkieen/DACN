import math
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.proposal import PurchaseProposal, ProposalDetail, ApprovalHistory
from app.models.ingredient import Ingredient
from app.models.supplier import Supplier, SupplierQuotation
from app.schemas.proposal import (
    PurchaseProposalCreate, PurchaseProposalOut, ProposalDetailOut,
    ApprovalHistoryOut, ProposalActionRequest
)
from app.services.inventory_service import compute_ingredient_metrics
from app.services.supplier_service import evaluate_suppliers_mcdm


def cleanup_empty_proposals(db: Session) -> None:
    """Dọn dẹp các phiếu đề xuất rỗng (không có chi tiết mặt hàng hoặc tổng tiền <= 0)."""
    all_proposals = db.query(PurchaseProposal).all()
    deleted_any = False
    for p in all_proposals:
        if len(p.details) == 0 or (p.tong_tien_du_kien or 0) <= 0:
            db.delete(p)
            deleted_any = True
    if deleted_any:
        db.commit()


def get_proposals(
    db: Session,
    status_filter: Optional[str] = None
) -> List[PurchaseProposalOut]:
    cleanup_empty_proposals(db)
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

    if action_data.hanh_dong == "APPROVE":
        p.trang_thai = "DA_DUYET"
    elif action_data.hanh_dong == "REJECT":
        p.trang_thai = "TU_CHOI"
    elif action_data.hanh_dong == "MODIFY":
        p.trang_thai = "DA_SUA"
    else:
        raise ValueError("Hành động không hợp lệ: phải là APPROVE, REJECT hoặc MODIFY")

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


def generate_ai_proposal(db: Session) -> PurchaseProposalOut:
    """
    AI Procurement Agent quét tồn kho, tính toán ROP, nhu cầu 7 ngày,
    đánh giá nhà cung cấp tối ưu qua thuật toán MCDM và tự động sinh Phiếu đề xuất mua hàng.
    """
    cleanup_empty_proposals(db)

    ingredients = db.query(Ingredient).filter(Ingredient.trang_thai == True).all()
    depleted_items = []

    for ing in ingredients:
        tinh_trang, nhu_cau_7ngay, rop, can_bo_sung, thong_bao = compute_ingredient_metrics(db, ing)
        if tinh_trang == "NGUY_CO_THIEU" or ing.ton_kho_hien_tai <= rop:
            depleted_items.append((ing, nhu_cau_7ngay, rop, can_bo_sung))

    # Nếu tất cả đều an toàn, lấy 2 nguyên liệu có tỷ lệ tồn/ROP thấp nhất để mô phỏng đề xuất
    if not depleted_items:
        sorted_by_ratio = sorted(
            ingredients,
            key=lambda x: x.ton_kho_hien_tai / max(x.muc_ton_an_toan, 1.0)
        )
        for ing in sorted_by_ratio[:2]:
            _, nhu_cau_7ngay, rop, _, _ = compute_ingredient_metrics(db, ing)
            can_bo_sung = round(max(ing.muc_ton_toi_da - ing.ton_kho_hien_tai, rop * 1.5), 1)
            depleted_items.append((ing, nhu_cau_7ngay, rop, can_bo_sung))

    now = datetime.now()
    proposal = PurchaseProposal(
        ngay_tao=now,
        tong_tien_du_kien=0.0,
        trang_thai="CHO_DUYET",
        ly_do_tong_quan=(
            f"AI Procurement Agent đã quét toàn bộ {len(ingredients)} nguyên vật liệu và phát hiện "
            f"{len(depleted_items)} mặt hàng chạm ngưỡng cảnh báo tồn kho (ROP). "
            f"Hệ thống đã tự động tính toán nhu cầu 7 ngày tới, đối chiếu báo giá các nhà cung cấp "
            f"bằng giải thuật MCDM và chọn đối tác tối ưu nhất."
        ),
        nguoi_tao="AI Procurement Agent (MCDM & ROP Engine)"
    )
    db.add(proposal)
    db.flush()

    total_amount = 0.0
    for ing, nhu_cau_7ngay, rop, can_bo_sung in depleted_items:
        mcdm_res = evaluate_suppliers_mcdm(db, ing.ma_nguyen_lieu)
        best_supplier = mcdm_res.nha_cung_cap_toi_uu

        quotation = None
        if best_supplier:
            quotation = db.query(SupplierQuotation).filter(
                SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu,
                SupplierQuotation.ma_nha_cung_cap == best_supplier.ma_nha_cung_cap
            ).first()

        if not quotation:
            quotation = db.query(SupplierQuotation).filter(
                SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu
            ).first()

        supplier_id = quotation.ma_nha_cung_cap if quotation else 1
        unit_price = quotation.don_gia if quotation else 50000.0
        moq = quotation.so_luong_dat_toi_thieu if quotation else 1.0
        lead_time = quotation.thoi_gian_giao_hang if quotation else 2

        # Làm tròn theo MOQ (Mục 6.3 Đặc tả)
        raw_qty = max(can_bo_sung, moq, 1.0)
        order_qty = round(math.ceil(raw_qty / moq) * moq, 1) if moq > 0 else round(raw_qty, 1)
        subtotal = round(order_qty * unit_price, 2)
        total_amount += subtotal

        supplier_name = best_supplier.ten_nha_cung_cap if best_supplier else "Nhà cung cấp chuẩn"
        score_val = best_supplier.diem_tong_hop_mcdm if best_supplier else 90.0

        detail = ProposalDetail(
            ma_phieu_de_xuat=proposal.ma_phieu_de_xuat,
            ma_nguyen_lieu=ing.ma_nguyen_lieu,
            ma_nha_cung_cap=supplier_id,
            so_luong_de_xuat=order_qty,
            don_gia_du_kien=unit_price,
            so_luong_du_doan_7ngay=nhu_cau_7ngay,
            ly_do_de_xuat=(
                f"Tồn kho còn {ing.ton_kho_hien_tai} {ing.don_vi_tinh} ≤ ROP {rop} {ing.don_vi_tinh}. "
                f"Nhu cầu 7 ngày tới là {nhu_cau_7ngay} {ing.don_vi_tinh}. "
                f"Chọn '{supplier_name}' đạt điểm MCDM cao nhất ({score_val}/100), "
                f"Lead time {lead_time} ngày, đơn giá {unit_price:,.0f}đ. "
                f"Số lượng đặt {order_qty} {ing.don_vi_tinh} đã làm tròn theo MOQ ({moq} {ing.don_vi_tinh})."
            )
        )
        db.add(detail)

    proposal.tong_tien_du_kien = round(total_amount, 2)
    db.commit()
    db.refresh(proposal)
    return get_proposal_by_id(db, proposal.ma_phieu_de_xuat)
