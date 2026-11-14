"""
Tệp kiểm tra kết nối, tự động khởi tạo Database và đồng bộ dữ liệu sang PostgreSQL (kể cả các bảng viết HOA trong pgAdmin 4).
Cách chạy:
    cd backend
    python ket_noi_postgres.py
"""
import os
import sys
from urllib.parse import urlparse, unquote

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.config import settings
from app.core.dong_bo_postgres import (
    chuyen_du_lieu_sqlite_sang_postgres,
    dong_bo_bang_chu_hoa_pgadmin,
    DANH_SACH_BANG_DONG_BO,
)


def kiem_tra_va_khoi_tao_postgres():
    print("=" * 80)
    print("  KIỂM TRA KẾT NỐI & ĐỒNG BỘ CƠ SỞ DỮ LIỆU POSTGRESQL (pgAdmin 4)")
    print("=" * 80)

    db_url = settings.DATABASE_URL
    print(f"[1] Chuỗi kết nối hiện tại trong backend/.env:\n    {db_url}")

    if not db_url.startswith("postgresql"):
        print("[LỖI] DATABASE_URL trong backend/.env chưa phải là postgresql://...")
        return

    # Phân tích thông tin kết nối để tự động tạo Database nếu chưa có
    parsed = urlparse(db_url)
    user = unquote(parsed.username or "postgres")
    password = unquote(parsed.password or "")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    ten_db = unquote((parsed.path or "/coffee_inventory").lstrip("/"))

    print(f"[2] Đang kết nối tới máy chủ PostgreSQL tại {host}:{port} (CSDL: '{ten_db}')...")
    try:
        import psycopg
        with psycopg.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
            autocommit=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (ten_db,))
                da_ton_tai = cur.fetchone()
                if not da_ton_tai:
                    print(f"[3] Chưa có cơ sở dữ liệu '{ten_db}'. Đang tự động tạo mới...")
                    cur.execute(f'CREATE DATABASE "{ten_db}" ENCODING \'UTF8\';')
                    print(f"    -> Đã tạo cơ sở dữ liệu '{ten_db}' thành công!")
                else:
                    print(f"[3] Cơ sở dữ liệu '{ten_db}' đã tồn tại trên PostgreSQL.")
    except Exception as e:
        print(f"\n[LỖI KẾT NỐI POSTGRESQL] Không thể kết nối tới {host}:{port}:")
        print(f"    Chi tiết: {e}")
        return

    # Tạo toàn bộ các bảng, chuyển dữ liệu từ Web (SQLite) sang PostgreSQL và đồng bộ bảng viết HOA
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base
    from app.seed.seed_data import seed_database
    from app.services.dich_vu_dinh_muc_bom import chay_quy_trinh_boc_tach_bom

    print(f"[4] Đang khởi tạo bảng và đồng bộ dữ liệu Web sang PostgreSQL ('{ten_db}')...")
    pg_engine = create_engine(db_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=pg_engine)

    PgSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
    db = PgSession()
    try:
        seed_database(db)
        chuyen_du_lieu_sqlite_sang_postgres(pg_engine)
        bao_cao = chay_quy_trinh_boc_tach_bom(db, so_ngay=365)
        dong_bo_bang_chu_hoa_pgadmin(pg_engine)

        print(
            f"[5] Hoàn tất nạp dữ liệu Tuần 5: {bao_cao.tong_dong_sach}/{bao_cao.tong_dong_tho} "
            f"dòng bán hàng POS sạch ({bao_cao.ty_le_du_lieu_sach}%), "
            f"{bao_cao.tong_ban_ghi_tieu_hao_sinh_ra} dòng chuỗi thời gian tiêu hao nguyên liệu!"
        )

        print("\n[6] Thống kê số dòng dữ liệu hiện có trong PostgreSQL / pgAdmin 4:")
        with pg_engine.connect() as conn:
            for ten_thuong, ten_hoa, _ in DANH_SACH_BANG_DONG_BO:
                so_thuong = conn.execute(text(f'SELECT COUNT(*) FROM public."{ten_thuong}"')).scalar() or 0
                ton_tai_hoa = conn.execute(
                    text("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=:t"),
                    {"t": ten_hoa},
                ).fetchone()
                if ton_tai_hoa:
                    so_hoa = conn.execute(text(f'SELECT COUNT(*) FROM public."{ten_hoa}"')).scalar() or 0
                    print(f'    - public."{ten_hoa}": {so_hoa} dòng (đồng bộ với public.{ten_thuong}: {so_thuong} dòng)')
                else:
                    print(f"    - public.{ten_thuong}: {so_thuong} dòng")

        print("=" * 80)
        print("[THÀNH CÔNG] HỆ THỐNG ĐÃ KẾT NỐI VÀ ĐỒNG BỘ 100% VỚI POSTGRESQL (pgAdmin 4)!")
        print("=" * 80)
    finally:
        db.close()


if __name__ == "__main__":
    kiem_tra_va_khoi_tao_postgres()
