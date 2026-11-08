from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierOut,
    SupplierQuotationCreate, SupplierQuotationOut,
    SupplierCompareResult
)
from app.services.supplier_service import (
    get_suppliers, get_supplier_by_id, create_supplier, update_supplier,
    create_or_update_quotation, evaluate_suppliers_mcdm
)

router = APIRouter()

@router.get("", response_model=List[SupplierOut], summary="Lấy danh sách nhà cung cấp kèm báo giá")
def read_suppliers(
    search: Optional[str] = Query(None, description="Tìm theo tên nhà cung cấp"),
    db: Session = Depends(get_db)
):
    return get_suppliers(db, search=search)

@router.get("/compare/{ingredient_id}", response_model=SupplierCompareResult, summary="Đánh giá & Xếp hạng Nhà cung cấp tối ưu (MCDM)")
def compare_suppliers(
    ingredient_id: int,
    db: Session = Depends(get_db)
):
    try:
        return evaluate_suppliers_mcdm(db, ingredient_id=ingredient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{supplier_id}", response_model=SupplierOut, summary="Xem chi tiết nhà cung cấp")
def read_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    supplier = get_supplier_by_id(db, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    return supplier

@router.post("", response_model=SupplierOut, status_code=201, summary="Tạo mới nhà cung cấp")
def add_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db)
):
    s = create_supplier(db, data)
    return get_supplier_by_id(db, s.ma_nha_cung_cap)

@router.put("/{supplier_id}", response_model=SupplierOut, summary="Cập nhật thông tin nhà cung cấp")
def edit_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db)
):
    updated = update_supplier(db, supplier_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp để cập nhật")
    return get_supplier_by_id(db, supplier_id)

@router.post("/quotations", response_model=SupplierQuotationOut, summary="Cập nhật hoặc thêm báo giá nguyên liệu cho NCC")
def set_quotation(
    data: SupplierQuotationCreate,
    db: Session = Depends(get_db)
):
    q = create_or_update_quotation(db, data)
    return SupplierQuotationOut(
        ma_nha_cung_cap=q.ma_nha_cung_cap,
        ma_nguyen_lieu=q.ma_nguyen_lieu,
        don_gia=q.don_gia,
        so_luong_dat_toi_thieu=q.so_luong_dat_toi_thieu,
        thoi_gian_giao_hang=q.thoi_gian_giao_hang,
        ngay_cap_nhat_gia=q.ngay_cap_nhat_gia,
        ten_nha_cung_cap=q.supplier.ten_nha_cung_cap if q.supplier else None,
        ten_nguyen_lieu=q.ingredient.ten_nguyen_lieu if q.ingredient else None
    )
