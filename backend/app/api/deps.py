from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _default_user(db: Session) -> User:
    """Người dùng mặc định khi tắt phân quyền: tài khoản QUAN_LY đầu tiên, hoặc 1 user tạm trong bộ nhớ."""
    user = (
        db.query(User)
        .filter(User.vai_tro == "QUAN_LY", User.trang_thai.is_(True))
        .order_by(User.ma_nguoi_dung)
        .first()
    )
    if user is None:
        user = User(ten_nguoi_dung="Quản lý cửa hàng", email="local@coffee.vn",
                    mat_khau_hash="", vai_tro="QUAN_LY", trang_thai=True)
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Đọc JWT từ header `Authorization: Bearer <token>` và trả về người dùng hiện tại.

    Khi AUTH_ENABLED=false (mặc định): bỏ qua đăng nhập, coi mọi yêu cầu là Quản lý cửa hàng.
    """
    if not settings.AUTH_ENABLED:
        return _default_user(db)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None or not user.trang_thai:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị khóa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: str):
    """Chỉ cho phép các vai trò trong `roles` (QUAN_LY, NHAN_VIEN_KHO, ADMIN)."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if not settings.AUTH_ENABLED:
            return user  # tắt phân quyền: cho qua mọi vai trò
        if user.vai_tro not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return user

    return checker
