from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class DemandForecastBase(BaseModel):
    ma_nguyen_lieu: int
    ngay_du_bao: date
    so_luong_du_bao: float
    do_tin_cay: float = 0.95
    phuong_phap: str = "Prophet_v1"

class DemandForecastCreate(DemandForecastBase):
    pass

class DemandForecastOut(DemandForecastBase):
    ma_du_bao: int
    thoi_gian_tao: Optional[datetime] = None
    ten_nguyen_lieu: Optional[str] = None
    don_vi_tinh: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ForecastChartPoint(BaseModel):
    ngay: str
    so_luong: float
    do_tin_cay: float

class ForecastSummaryItem(BaseModel):
    ma_nguyen_lieu: int
    ten_nguyen_lieu: str
    don_vi_tinh: str
    tong_nhu_cau_7ngay: float
    trung_binh_ngay: float
    du_lieu_7ngay: List[ForecastChartPoint] = []
