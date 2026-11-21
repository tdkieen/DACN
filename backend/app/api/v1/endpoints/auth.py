from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
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

@router.get("/me", response_model=UserOut, summary="Thông tin người dùng hiện tại (theo JWT)")
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
