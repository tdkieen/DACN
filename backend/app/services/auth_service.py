from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.core.security import verify_password, hash_password, create_access_token
from app.schemas.user import UserLogin, Token, UserOut, UserCreate

def authenticate_user(db: Session, credentials: UserLogin) -> Optional[User]:
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        return None
    if not verify_password(credentials.mat_khau, user.mat_khau_hash):
        return None
    return user

def create_user(db: Session, data: UserCreate) -> User:
    hashed = hash_password(data.mat_khau)
    user = User(
        ten_nguoi_dung=data.ten_nguoi_dung,
        email=data.email,
        mat_khau_hash=hashed,
        vai_tro=data.vai_tro,
        trang_thai=data.trang_thai
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def login_and_generate_token(db: Session, credentials: UserLogin) -> Optional[Token]:
    user = authenticate_user(db, credentials)
    if not user:
        return None
    token_str = create_access_token(subject=user.email, role=user.vai_tro)
    return Token(
        access_token=token_str,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )
