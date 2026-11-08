from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.dashboard import (
    DashboardStatsOut, AlertItemOut, MonthlyTrendPoint, DashboardOverviewOut
)
from app.schemas.forecast import ForecastSummaryItem
from app.services.dashboard_service import (
    get_dashboard_stats, get_active_alerts, get_consumption_trends_12_months,
    get_forecast_summary_7_days, get_dashboard_overview
)

router = APIRouter()

@router.get("/stats", response_model=DashboardStatsOut, summary="Thống kê tổng quan cho các thẻ Dashboard")
def read_dashboard_stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)

@router.get("/alerts", response_model=List[AlertItemOut], summary="Danh sách cảnh báo thiếu hàng, tồn dư và hết hạn")
def read_dashboard_alerts(db: Session = Depends(get_db)):
    return get_active_alerts(db)

@router.get("/trends", response_model=List[MonthlyTrendPoint], summary="Biểu đồ xu hướng tiêu thụ 12 tháng")
def read_dashboard_trends(db: Session = Depends(get_db)):
    return get_consumption_trends_12_months(db)

@router.get("/forecast-summary", response_model=List[ForecastSummaryItem], summary="Dữ liệu đường dự báo nhu cầu 7 ngày tới")
def read_forecast_summary(db: Session = Depends(get_db)):
    return get_forecast_summary_7_days(db)

@router.get("/overview", response_model=DashboardOverviewOut, summary="Tổng hợp toàn bộ dữ liệu trang Dashboard")
def read_dashboard_overview(db: Session = Depends(get_db)):
    return get_dashboard_overview(db)
