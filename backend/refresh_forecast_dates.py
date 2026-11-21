"""Dời ngày của dữ liệu dự báo mẫu (seed) để luôn nằm trong 7 ngày tới.

Dữ liệu dự báo hiện là dữ liệu seed gắn với ngày nạp DB. Qua vài ngày, các dòng này
nằm trong quá khứ nên API tự chuyển sang số "ước tính tạm". Chạy file này để dời lại
mốc ngày cho demo (KHÔNG phải mô hình dự báo thật):

    cd backend
    python refresh_forecast_dates.py
"""
import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.forecast import DemandForecast


def main() -> None:
    db = SessionLocal()
    try:
        start = date.today() + timedelta(days=1)
        ids = [r[0] for r in db.query(DemandForecast.ma_nguyen_lieu).distinct().all()]
        moved = 0
        for ing_id in ids:
            rows = (
                db.query(DemandForecast)
                .filter(DemandForecast.ma_nguyen_lieu == ing_id)
                .order_by(DemandForecast.ngay_du_bao.asc())
                .all()
            )
            if not rows or rows[0].ngay_du_bao >= start:
                continue  # đã nằm trong tương lai, giữ nguyên
            delta = start - rows[0].ngay_du_bao
            for r in rows:
                r.ngay_du_bao = r.ngay_du_bao + delta
                moved += 1
        db.commit()
        print(f"Đã dời {moved} dòng dự báo của {len(ids)} nguyên liệu về T+1..T+7 (từ {start}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
