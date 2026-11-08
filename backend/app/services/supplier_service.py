from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.supplier import Supplier, SupplierQuotation
from app.models.ingredient import Ingredient
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierOut, SupplierQuotationCreate,
    SupplierQuotationOut, SupplierCompareResult, SupplierMCDMScore
)

def get_suppliers(db: Session, search: Optional[str] = None) -> List[SupplierOut]:
    query = db.query(Supplier).filter(Supplier.trang_thai == True)
    if search:
        query = query.filter(Supplier.ten_nha_cung_cap.ilike(f"%{search}%"))

    suppliers = query.order_by(Supplier.ma_nha_cung_cap.asc()).all()
    results = []
    for s in suppliers:
        quotation_outs = []
        for q in s.quotations:
            q_out = SupplierQuotationOut(
                ma_nha_cung_cap=q.ma_nha_cung_cap,
                ma_nguyen_lieu=q.ma_nguyen_lieu,
                don_gia=q.don_gia,
                so_luong_dat_toi_thieu=q.so_luong_dat_toi_thieu,
                thoi_gian_giao_hang=q.thoi_gian_giao_hang,
                ngay_cap_nhat_gia=q.ngay_cap_nhat_gia,
                ten_nha_cung_cap=s.ten_nha_cung_cap,
                ten_nguyen_lieu=q.ingredient.ten_nguyen_lieu if q.ingredient else None
            )
            quotation_outs.append(q_out)

        s_out = SupplierOut(
            ma_nha_cung_cap=s.ma_nha_cung_cap,
            ten_nha_cung_cap=s.ten_nha_cung_cap,
            nguoi_lien_he=s.nguoi_lien_he,
            email=s.email,
            sdt=s.sdt,
            dia_chi=s.dia_chi,
            thoi_gian_giao_du_kien=s.thoi_gian_giao_du_kien,
            diem_uy_tin=s.diem_uy_tin,
            diem_chat_luong=s.diem_chat_luong,
            trang_thai=s.trang_thai,
            ngay_tao=s.ngay_tao,
            quotations=quotation_outs
        )
        results.append(s_out)
    return results

def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[SupplierOut]:
    s = db.query(Supplier).filter(Supplier.ma_nha_cung_cap == supplier_id).first()
    if not s:
        return None

    quotation_outs = []
    for q in s.quotations:
        quotation_outs.append(
            SupplierQuotationOut(
                ma_nha_cung_cap=q.ma_nha_cung_cap,
                ma_nguyen_lieu=q.ma_nguyen_lieu,
                don_gia=q.don_gia,
                so_luong_dat_toi_thieu=q.so_luong_dat_toi_thieu,
                thoi_gian_giao_hang=q.thoi_gian_giao_hang,
                ngay_cap_nhat_gia=q.ngay_cap_nhat_gia,
                ten_nha_cung_cap=s.ten_nha_cung_cap,
                ten_nguyen_lieu=q.ingredient.ten_nguyen_lieu if q.ingredient else None
            )
        )

    return SupplierOut(
        ma_nha_cung_cap=s.ma_nha_cung_cap,
        ten_nha_cung_cap=s.ten_nha_cung_cap,
        nguoi_lien_he=s.nguoi_lien_he,
        email=s.email,
        sdt=s.sdt,
        dia_chi=s.dia_chi,
        thoi_gian_giao_du_kien=s.thoi_gian_giao_du_kien,
        diem_uy_tin=s.diem_uy_tin,
        diem_chat_luong=s.diem_chat_luong,
        trang_thai=s.trang_thai,
        ngay_tao=s.ngay_tao,
        quotations=quotation_outs
    )

def create_supplier(db: Session, data: SupplierCreate) -> Supplier:
    s = Supplier(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def update_supplier(db: Session, supplier_id: int, data: SupplierUpdate) -> Optional[Supplier]:
    s = db.query(Supplier).filter(Supplier.ma_nha_cung_cap == supplier_id).first()
    if not s:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

def create_or_update_quotation(db: Session, data: SupplierQuotationCreate) -> SupplierQuotation:
    quotation = db.query(SupplierQuotation).filter(
        SupplierQuotation.ma_nha_cung_cap == data.ma_nha_cung_cap,
        SupplierQuotation.ma_nguyen_lieu == data.ma_nguyen_lieu
    ).first()

    if quotation:
        quotation.don_gia = data.don_gia
        quotation.so_luong_dat_toi_thieu = data.so_luong_dat_toi_thieu
        quotation.thoi_gian_giao_hang = data.thoi_gian_giao_hang
        quotation.ngay_cap_nhat_gia = datetime.now()
    else:
        quotation = SupplierQuotation(**data.model_dump())
        db.add(quotation)

    db.commit()
    db.refresh(quotation)
    return quotation

def evaluate_suppliers_mcdm(db: Session, ingredient_id: int) -> SupplierCompareResult:
    """
    Thuật toán Đánh giá Nhà cung cấp đa tiêu chuẩn (MCDM) theo Mục 6.3 Đặc tả:
    Score(k) = 0.4 * (Gia_min / Gia_k)
             + 0.3 * (LeadTime_min / LeadTime_k)
             + 0.15 * (ChatLuong_k / 5.0)
             + 0.15 * (UyTin_k / Max_UyTin)
    """
    ingredient = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ingredient_id).first()
    if not ingredient:
        raise ValueError("Nguyên liệu không tồn tại")

    quotations = db.query(SupplierQuotation).join(Supplier).filter(
        SupplierQuotation.ma_nguyen_lieu == ingredient_id,
        Supplier.trang_thai == True
    ).all()

    if not quotations:
        return SupplierCompareResult(
            ma_nguyen_lieu=ingredient.ma_nguyen_lieu,
            ten_nguyen_lieu=ingredient.ten_nguyen_lieu,
            nha_cung_cap_toi_uu=None,
            danh_sach_so_sanh=[]
        )

    min_price = min(q.don_gia for q in quotations)
    min_lead_time = min(q.thoi_gian_giao_hang for q in quotations)

    scored_list = []
    for q in quotations:
        s = q.supplier
        # Điểm giá (Càng thấp càng tốt, chuẩn hóa tỷ lệ Giá_min / Giá_k)
        price_score = min_price / q.don_gia if q.don_gia > 0 else 0
        # Điểm Lead time (Càng nhanh càng tốt, chuẩn hóa tỷ lệ LeadTime_min / LeadTime_k)
        lead_time_score = min_lead_time / q.thoi_gian_giao_hang if q.thoi_gian_giao_hang > 0 else 0
        # Điểm chất lượng (thang 5)
        quality_score = min(max(s.diem_chat_luong / 5.0, 0.0), 1.0)
        # Điểm uy tín (chuẩn hóa thang 5 hoặc thang 100)
        reputation_base = 5.0 if s.diem_uy_tin <= 5.0 else 100.0
        reputation_score = min(max(s.diem_uy_tin / reputation_base, 0.0), 1.0)

        # Tính tổng điểm MCDM
        total_score = (
            0.40 * price_score +
            0.30 * lead_time_score +
            0.15 * quality_score +
            0.15 * reputation_score
        )

        scored_list.append({
            "ma_nha_cung_cap": s.ma_nha_cung_cap,
            "ten_nha_cung_cap": s.ten_nha_cung_cap,
            "don_gia": q.don_gia,
            "thoi_gian_giao_hang": q.thoi_gian_giao_hang,
            "so_luong_dat_toi_thieu": q.so_luong_dat_toi_thieu,
            "diem_chat_luong": s.diem_chat_luong,
            "diem_uy_tin": s.diem_uy_tin,
            "diem_tong_hop_mcdm": round(total_score * 100, 2)  # Quy đổi về thang điểm 100 để trực quan
        })

    # Sắp xếp giảm dần theo điểm tổng hợp MCDM
    scored_list.sort(key=lambda x: x["diem_tong_hop_mcdm"], reverse=True)

    result_items = []
    for rank, item in enumerate(scored_list, start=1):
        is_recommended = (rank == 1)
        score_obj = SupplierMCDMScore(
            ma_nha_cung_cap=item["ma_nha_cung_cap"],
            ten_nha_cung_cap=item["ten_nha_cung_cap"],
            don_gia=item["don_gia"],
            thoi_gian_giao_hang=item["thoi_gian_giao_hang"],
            so_luong_dat_toi_thieu=item["so_luong_dat_toi_thieu"],
            diem_chat_luong=item["diem_chat_luong"],
            diem_uy_tin=item["diem_uy_tin"],
            diem_tong_hop_mcdm=item["diem_tong_hop_mcdm"],
            xep_hang=rank,
            de_xuat=is_recommended
        )
        result_items.append(score_obj)

    return SupplierCompareResult(
        ma_nguyen_lieu=ingredient.ma_nguyen_lieu,
        ten_nguyen_lieu=ingredient.ten_nguyen_lieu,
        nha_cung_cap_toi_uu=result_items[0] if result_items else None,
        danh_sach_so_sanh=result_items
    )
