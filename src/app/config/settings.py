from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+aiomysql://user:password@localhost:3306/delivery_db"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SESSION_SECRET: str = secrets.token_urlsafe(32)
    SESSION_TTL: int = 3600
    
    CURRENCY_API_URL: str = "https://www.cbr-xml-daily.ru/daily_json.js"
    CURRENCY_CACHE_TTL: int = 300
    
    DELIVERY_CALCULATION_INTERVAL: int = 300
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    LOG_LEVEL: str = "INFO"
    
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()