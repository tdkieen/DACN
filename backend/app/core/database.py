import os
import sys
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.dong_bo_postgres import dong_bo_bang_chu_hoa_pgadmin

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _khoi_tao_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

    # Kết nối PostgreSQL (có kiểm tra kết nối thực tế và tự động dự phòng SQLite nếu PostgreSQL chưa bật)
    try:
        pg_engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=False,
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[CSDL] Đã kết nối thành công tới PostgreSQL: {db_url.split('@')[-1]}")
        return pg_engine
    except Exception as e:
        print(f"[CSDL] Chưa kết nối được PostgreSQL ({e}). Đang dùng SQLite dự phòng cục bộ.")
        thu_muc_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        duong_dan_sqlite = os.path.join(thu_muc_backend, "coffee_inventory.db").replace("\\", "/")
        return create_engine(
            f"sqlite:///{duong_dan_sqlite}",
            connect_args={"check_same_thread": False},
            echo=False,
        )


engine = _khoi_tao_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


import threading

_pg_sync_lock = threading.Lock()


def _chay_dong_bo_pgadmin_nen() -> None:
    if not _pg_sync_lock.acquire(blocking=False):
        return
    try:
        dong_bo_bang_chu_hoa_pgadmin(engine)
    finally:
        _pg_sync_lock.release()


@event.listens_for(SessionLocal, "after_commit")
def _tu_dong_dong_bo_pgadmin(session):
    if engine.dialect.name == "postgresql":
        threading.Thread(target=_chay_dong_bo_pgadmin_nen, daemon=True).start()

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
