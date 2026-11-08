import os
import json
from typing import List

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Coffee AI Procurement Agent")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./coffee_inventory.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "coffee_super_secret_jwt_key_hutech_dacn_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv("BACKEND_CORS_ORIGINS", '["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000"]')
        try:
            return json.loads(raw)
        except Exception:
            return ["*"]

settings = Settings()
