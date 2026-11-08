from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta

from app.models.ingredient import Ingredient
from app.models.inventory import Batch, InventoryTransaction
from app.models.forecast import DemandForecast
from app.models.supplier import SupplierQuotation
from app.schemas.ingredient import (
    IngredientCreate, IngredientUpdate, IngredientStatusOut, IngredientDetailOut,
    BatchSimpleOut, ForecastSimpleOut
)
from app.schemas.inventory import (
    BatchCreate, BatchOut, InventoryTransactionCreate, InventoryTransactionOut
)

def compute_ingredient_metrics(db: Session, ingredient: Ingredient) -> Tuple[str, float, float, float, Optional[str]]:
    """
    Tính toán ROP và đánh giá tình trạng kho:
    - ROP = (Nhu cầu dự báo TB ngày * Lead Time NCC) + Mức tồn an toàn
    - Cảnh báo ĐỎ (NGUY_CO_THIEU): Tồn hiện tại <= ROP
    - Cảnh báo VÀNG (TON_DU): Tồn hiện tại > Max Stock hoặc Tồn / Nhu cầu 7 ngày > 3
    - AN TOÀN (AN_TOAN): Nằm trong khoảng an toàn
    """
    # 1. Lấy dự báo 7 ngày tới
    today = date.today()
    forecasts = db.query(DemandForecast).filter(
        DemandForecast.ma_nguyen_lieu == ingredient.ma_nguyen_lieu,
        DemandForecast.ngay_du_bao >= today
    ).order_by(DemandForecast.ngay_du_bao.asc()).limit(7).all()
    
    if forecasts:
        tong_du_bao_7ngay = sum(f.so_luong_du_bao for f in forecasts)
        nhu_cau_tb_ngay = tong_du_bao_7ngay / len(forecasts)
    else:
        # Giả định tiêu hao mặc định nếu chưa chạy mô hình dự báo
        nhu_cau_tb_ngay = max(ingredient.muc_ton_an_toan * 0.4, 2.0)
        tong_du_bao_7ngay = nhu_cau_tb_ngay * 7

    # 2. Lấy Lead Time trung bình từ báo giá của các NCC cho nguyên liệu này
    quotation = db.query(SupplierQuotation).filter(
        SupplierQuotation.ma_nguyen_lieu == ingredient.ma_nguyen_lieu
    ).first()
    lead_time = quotation.thoi_gian_giao_hang if quotation else 2

    # 3. Tính ROP: (Nhu cầu TB/ngày * Lead Time) + Mức tồn an toàn
    rop = round((nhu_cau_tb_ngay * lead_time) + ingredient.muc_ton_an_toan, 2)

    # 4. Xác định tình trạng và lượng cần bổ sung
    can_bo_sung = 0.0
    thong_bao = None

    if ingredient.ton_kho_hien_tai <= rop:
        tinh_trang = "NGUY_CO_THIEU"
        # Bổ sung tới mức tối đa hoặc ít nhất gấp 1.5 lần ROP
        can_bo_sung = round(max(ingredient.muc_ton_toi_da - ingredient.ton_kho_hien_tai, rop * 1.5 - ingredient.ton_kho_hien_tai), 2)
        thong_bao = f"Tồn kho ({ingredient.ton_kho_hien_tai} {ingredient.don_vi_tinh}) ≤ Điểm ROP ({rop} {ingredient.don_vi_tinh}). Cần đặt thêm!"
    elif ingredient.ton_kho_hien_tai > ingredient.muc_ton_toi_da or (tong_du_bao_7ngay > 0 and (ingredient.ton_kho_hien_tai / tong_du_bao_7ngay) > 3.0):
        tinh_trang = "TON_DU"
        thong_bao = f"Tồn kho ({ingredient.ton_kho_hien_tai} {ingredient.don_vi_tinh}) vượt mức trần hoặc vượt 3 lần nhu cầu tuần. Nguy cơ đọng vốn/hết hạn!"
    else:
        tinh_trang = "AN_TOAN"

    return tinh_trang, round(tong_du_bao_7ngay, 2), rop, can_bo_sung, thong_bao

def get_ingredients(
    db: Session,
    search: Optional[str] = None,
    danh_muc: Optional[str] = None,
    tinh_trang: Optional[str] = None
) -> List[IngredientStatusOut]:
    query = db.query(Ingredient).filter(Ingredient.trang_thai == True)
    
    if search:
        query = query.filter(Ingredient.ten_nguyen_lieu.ilike(f"%{search}%"))
    if danh_muc:
        query = query.filter(Ingredient.danh_muc == danh_muc)

    ingredients = query.order_by(Ingredient.ma_nguyen_lieu.asc()).all()
    results = []

    for ing in ingredients:
        status, demand_7d, rop, replenish, alert = compute_ingredient_metrics(db, ing)
        if tinh_trang and status != tinh_trang:
            continue
        
        item = IngredientStatusOut(
            ma_nguyen_lieu=ing.ma_nguyen_lieu,
            ten_nguyen_lieu=ing.ten_nguyen_lieu,
            danh_muc=ing.danh_muc,
            don_vi_tinh=ing.don_vi_tinh,
            muc_ton_an_toan=ing.muc_ton_an_toan,
            muc_ton_toi_da=ing.muc_ton_toi_da,
            ton_kho_hien_tai=ing.ton_kho_hien_tai,
            trang_thai=ing.trang_thai,
            ngay_tao=ing.ngay_tao,
            ngay_cap_nhat=ing.ngay_cap_nhat,
            tinh_trang=status,
            nhu_cau_du_bao_7ngay=demand_7d,
            diem_dat_hang_lai_rop=rop,
            so_luong_can_bo_sung=replenish,
            thong_bao_canh_bao=alert
        )
        results.append(item)

    return results

def get_ingredient_detail(db: Session, ingredient_id: int) -> Optional[IngredientDetailOut]:
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ingredient_id).first()
    if not ing:
        return None

    status, demand_7d, rop, replenish, alert = compute_ingredient_metrics(db, ing)

    # Lấy các lô hàng còn tồn
    batches = db.query(Batch).filter(
        Batch.ma_nguyen_lieu == ingredient_id,
        Batch.so_luong_con_lai > 0
    ).order_by(Batch.han_su_dung.asc().nullslast()).all()

    # Lấy dự báo 7 ngày
    today = date.today()
    forecasts = db.query(DemandForecast).filter(
        DemandForecast.ma_nguyen_lieu == ingredient_id,
        DemandForecast.ngay_du_bao >= today
    ).order_by(DemandForecast.ngay_du_bao.asc()).limit(7).all()

    return IngredientDetailOut(
        ma_nguyen_lieu=ing.ma_nguyen_lieu,
        ten_nguyen_lieu=ing.ten_nguyen_lieu,
        danh_muc=ing.danh_muc,
        don_vi_tinh=ing.don_vi_tinh,
        muc_ton_an_toan=ing.muc_ton_an_toan,
        muc_ton_toi_da=ing.muc_ton_toi_da,
        ton_kho_hien_tai=ing.ton_kho_hien_tai,
        trang_thai=ing.trang_thai,
        ngay_tao=ing.ngay_tao,
        ngay_cap_nhat=ing.ngay_cap_nhat,
        tinh_trang=status,
        nhu_cau_du_bao_7ngay=demand_7d,
        diem_dat_hang_lai_rop=rop,
        so_luong_can_bo_sung=replenish,
        thong_bao_canh_bao=alert,
        batches=[BatchSimpleOut.model_validate(b) for b in batches],
        forecasts=[ForecastSimpleOut.model_validate(f) for f in forecasts]
    )

def create_ingredient(db: Session, data: IngredientCreate) -> Ingredient:
    ing = Ingredient(**data.model_dump())
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return ing

def update_ingredient(db: Session, ingredient_id: int, data: IngredientUpdate) -> Optional[Ingredient]:
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ingredient_id).first()
    if not ing:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ing, k, v)
    db.commit()
    db.refresh(ing)
    return ing

def delete_ingredient(db: Session, ingredient_id: int) -> bool:
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ingredient_id).first()
    if not ing:
        return False
    ing.trang_thai = False  # Soft delete
    db.commit()
    return True

# --- BATCHES & TRANSACTIONS ---

def get_batches(
    db: Session,
    ingredient_id: Optional[int] = None,
    canh_bao_het_han_chi_dinh: bool = False
) -> List[BatchOut]:
    query = db.query(Batch).join(Ingredient)
    if ingredient_id:
        query = query.filter(Batch.ma_nguyen_lieu == ingredient_id)

    batches = query.order_by(Batch.han_su_dung.asc().nullslast()).all()
    today = date.today()
    results = []

    for b in batches:
        so_ngay_con = None
        is_warning = False
        if b.han_su_dung:
            delta = (b.han_su_dung - today).days
            so_ngay_con = delta
            if delta <= 7 and b.so_luong_con_lai > 0:
                is_warning = True

        if canh_bao_het_han_chi_dinh and not is_warning:
            continue

        item = BatchOut(
            ma_lo_hang=b.ma_lo_hang,
            ma_nguyen_lieu=b.ma_nguyen_lieu,
            ma_lo_nha_cung_cap=b.ma_lo_nha_cung_cap,
            so_luong_nhap=b.so_luong_nhap,
            so_luong_con_lai=b.so_luong_con_lai,
            ngay_nhap_kho=b.ngay_nhap_kho,
            han_su_dung=b.han_su_dung,
            don_gia_nhap=b.don_gia_nhap,
            ten_nguyen_lieu=b.ingredient.ten_nguyen_lieu if b.ingredient else None,
            so_ngay_con_han=so_ngay_con,
            canh_bao_het_han=is_warning
        )
        results.append(item)

    return results

def get_inventory_transactions(
    db: Session,
    ingredient_id: Optional[int] = None,
    loai_giao_dich: Optional[str] = None,
    limit: int = 50
) -> List[InventoryTransactionOut]:
    query = db.query(InventoryTransaction).join(Ingredient)
    if ingredient_id:
        query = query.filter(InventoryTransaction.ma_nguyen_lieu == ingredient_id)
    if loai_giao_dich:
        query = query.filter(InventoryTransaction.loai_giao_dich == loai_giao_dich)

    txs = query.order_by(desc(InventoryTransaction.ngay_giao_dich)).limit(limit).all()
    results = []
    for t in txs:
        results.append(
            InventoryTransactionOut(
                ma_giao_dich=t.ma_giao_dich,
                ma_nguyen_lieu=t.ma_nguyen_lieu,
                loai_giao_dich=t.loai_giao_dich,
                so_luong=t.so_luong,
                ngay_giao_dich=t.ngay_giao_dich,
                ma_tham_chieu=t.ma_tham_chieu,
                ghi_chu=t.ghi_chu,
                ten_nguyen_lieu=t.ingredient.ten_nguyen_lieu if t.ingredient else None,
                don_vi_tinh=t.ingredient.don_vi_tinh if t.ingredient else None
            )
        )
    return results

def record_transaction(db: Session, data: InventoryTransactionCreate) -> InventoryTransactionOut:
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == data.ma_nguyen_lieu).first()
    if not ing:
        raise ValueError("Nguyên liệu không tồn tại")

    # Cập nhật tồn kho thực tế
    if data.loai_giao_dich == "NHAP":
        ing.ton_kho_hien_tai += data.so_luong
    elif data.loai_giao_dich in ["XUAT_BAN", "HAO_HUT"]:
        ing.ton_kho_hien_tai = max(0.0, ing.ton_kho_hien_tai - data.so_luong)
    elif data.loai_giao_dich == "KIEM_KE":
        ing.ton_kho_hien_tai = data.so_luong

    tx = InventoryTransaction(**data.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return InventoryTransactionOut(
        ma_giao_dich=tx.ma_giao_dich,
        ma_nguyen_lieu=tx.ma_nguyen_lieu,
        loai_giao_dich=tx.loai_giao_dich,
        so_luong=tx.so_luong,
        ngay_giao_dich=tx.ngay_giao_dich,
        ma_tham_chieu=tx.ma_tham_chieu,
        ghi_chu=tx.ghi_chu,
        ten_nguyen_lieu=ing.ten_nguyen_lieu,
        don_vi_tinh=ing.don_vi_tinh
    )
