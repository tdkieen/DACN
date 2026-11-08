from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserLogin, Token, UserOut
from app.services.auth_service import login_and_generate_token

router = APIRouter()

@router.post("/login", response_model=Token, summary="Đăng nhập nhận JWT Token")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    token = login_and_generate_token(db, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )
    return token

@router.get("/me", response_model=UserOut, summary="Thông tin người dùng hiện tại")
def get_me():
    # Phục vụ mock / kiểm thử tuần 4 trước khi bật strict JWT interceptor
    return UserOut(
        ma_nguoi_dung=1,
        ten_nguoi_dung="Quản lý trưởng",
        email="quanly@coffee.vn",
        vai_tro="QUAN_LY",
        trang_thai=True
    )
