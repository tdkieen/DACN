from fastapi import APIRouter
from app.api.v1.endpoints import (
    ingredients, suppliers, inventory, dashboard, proposals, auth
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & Thống kê"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["Nguyên Liệu"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Nhà Cung Cấp & Báo Giá"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Kho & Lô Hàng"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["Đề Xuất Mua Hàng (AI)"])
api_router.include_router(auth.router, prefix="/auth", tags=["Xác Thực & Người Dùng"])
