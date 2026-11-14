import os
import sys
import glob
import json
from typing import List


def _nap_driver_postgres_cuc_bo() -> None:
    """Tự động nạp thư viện psycopg và libpq.dll từ bộ cài PostgreSQL trên Windows nếu Python chưa cài."""
    os.environ.setdefault("PSYCOPG_IMPL", "python")
    cac_thu_muc_bin = glob.glob("C:/Program Files/PostgreSQL/*/bin")
    for thu_muc_bin in sorted(cac_thu_muc_bin, reverse=True):
        if os.path.isdir(thu_muc_bin):
            try:
                if hasattr(os, "add_dll_directory"):
                    os.add_dll_directory(thu_muc_bin)
            except Exception:
                pass
            if thu_muc_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = thu_muc_bin + os.pathsep + os.environ.get("PATH", "")

    cac_site_packages = glob.glob("C:/Program Files/PostgreSQL/*/pgAdmin 4/python/Lib/site-packages")
    for sp in sorted(cac_site_packages, reverse=True):
        if os.path.isdir(sp) and sp not in sys.path:
            sys.path.append(sp)


_nap_driver_postgres_cuc_bo()


# Tự động nạp biến môi trường từ file backend/.env (hoặc .env ở thư mục gốc)
def _nap_file_env() -> None:
    thu_muc_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    thu_muc_goc = os.path.dirname(thu_muc_backend)
    cac_duong_dan = [
        os.path.join(thu_muc_backend, ".env"),
        os.path.join(thu_muc_goc, ".env"),
    ]
    for duong_dan in cac_duong_dan:
        if os.path.exists(duong_dan):
            with open(duong_dan, "r", encoding="utf-8") as f:
                for dong in f:
                    dong = dong.strip()
                    if not dong or dong.startswith("#") or "=" not in dong:
                        continue
                    khoa, gia_tri = dong.split("=", 1)
                    khoa = khoa.strip()
                    gia_tri = gia_tri.strip().strip('"').strip("'")
                    if khoa and khoa not in os.environ:
                        os.environ[khoa] = gia_tri


_nap_file_env()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Coffee AI Procurement Agent")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://coffee_admin:coffee_secret_password@localhost:5432/coffee_inventory",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "coffee_super_secret_jwt_key_hutech_dacn_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv(
            "BACKEND_CORS_ORIGINS",
            '["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000"]',
        )
        try:
            return json.loads(raw)
        except Exception:
            return ["*"]


settings = Settings()
