from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.ingredient import (
    IngredientCreate, IngredientUpdate, IngredientStatusOut, IngredientDetailOut
)
from app.services.inventory_service import (
    get_ingredients, get_ingredient_detail, create_ingredient, update_ingredient, delete_ingredient
)

router = APIRouter()

@router.get("", response_model=List[IngredientStatusOut], summary="Lấy danh sách nguyên liệu và trạng thái tồn kho")
def read_ingredients(
    search: Optional[str] = Query(None, description="Tìm theo tên nguyên liệu"),
    danh_muc: Optional[str] = Query(None, description="Lọc theo danh mục (Cà phê, Sữa, Siro...)"),
    tinh_trang: Optional[str] = Query(None, description="Lọc theo tình trạng: NGUY_CO_THIEU, TON_DU, AN_TOAN"),
    db: Session = Depends(get_db)
):
    return get_ingredients(db, search=search, danh_muc=danh_muc, tinh_trang=tinh_trang)

@router.get("/{ingredient_id}", response_model=IngredientDetailOut, summary="Xem chi tiết nguyên liệu, lô hàng & dự báo 7 ngày")
def read_ingredient_detail(
    ingredient_id: int,
    db: Session = Depends(get_db)
):
    detail = get_ingredient_detail(db, ingredient_id=ingredient_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên liệu")
    return detail

@router.post("", response_model=IngredientStatusOut, status_code=201, summary="Tạo mới nguyên liệu")
def add_ingredient(
    data: IngredientCreate,
    db: Session = Depends(get_db)
):
    created = create_ingredient(db, data)
    # Trả về kèm tính toán trạng thái
    detail = get_ingredient_detail(db, created.ma_nguyen_lieu)
    return detail

@router.put("/{ingredient_id}", response_model=IngredientStatusOut, summary="Cập nhật thông tin nguyên liệu")
def edit_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    db: Session = Depends(get_db)
):
    updated = update_ingredient(db, ingredient_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên liệu để cập nhật")
    return get_ingredient_detail(db, ingredient_id)

@router.delete("/{ingredient_id}", summary="Xóa (ngừng sử dụng) nguyên liệu")
def remove_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db)
):
    success = delete_ingredient(db, ingredient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên liệu để xóa")
    return {"message": "Đã ngừng sử dụng nguyên liệu thành công"}
