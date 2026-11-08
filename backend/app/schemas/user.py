from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    ten_nguoi_dung: str
    email: str
    vai_tro: str = "QUAN_LY"  # 'QUAN_LY', 'NHAN_VIEN_KHO', 'ADMIN'
    trang_thai: bool = True

class UserCreate(UserBase):
    mat_khau: str

class UserLogin(BaseModel):
    email: str
    mat_khau: str

class UserOut(UserBase):
    ma_nguoi_dung: int
    ngay_tao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
