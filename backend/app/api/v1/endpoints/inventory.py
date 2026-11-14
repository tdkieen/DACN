from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.inventory import (
    BatchCreate, BatchOut, InventoryTransactionCreate, InventoryTransactionOut
)
from app.services.inventory_service import (
    get_batches, create_batch, get_inventory_transactions, record_transaction
)

router = APIRouter()


@router.get("/batches", response_model=List[BatchOut], summary="Danh sách lô hàng nhập kho (sắp xếp FEFO)")
def read_batches(
    ingredient_id: Optional[int] = Query(None, description="Lọc theo mã nguyên liệu"),
    canh_bao_het_han: bool = Query(False, description="Chỉ lấy các lô hàng sắp hoặc đã hết hạn (<= 7 ngày)"),
    db: Session = Depends(get_db)
):
    return get_batches(db, ingredient_id=ingredient_id, canh_bao_het_han_chi_dinh=canh_bao_het_han)


@router.post("/batches", response_model=BatchOut, status_code=201, summary="Nhập lô hàng nguyên liệu mới vào kho")
def create_new_batch(
    data: BatchCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_batch(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=List[InventoryTransactionOut], summary="Lịch sử biến động xuất nhập tồn kho")
def read_transactions(
    ingredient_id: Optional[int] = Query(None, description="Lọc theo mã nguyên liệu"),
    loai_giao_dich: Optional[str] = Query(None, description="Loại: NHAP, XUAT_BAN, HAO_HUT, KIEM_KE"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    return get_inventory_transactions(db, ingredient_id=ingredient_id, loai_giao_dich=loai_giao_dich, limit=limit)


@router.post("/transactions", response_model=InventoryTransactionOut, status_code=201, summary="Ghi nhận giao dịch kho mới (tự động trừ lô FEFO khi XUAT_BAN/HAO_HUT)")
def create_transaction(
    data: InventoryTransactionCreate,
    db: Session = Depends(get_db)
):
    try:
        return record_transaction(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
