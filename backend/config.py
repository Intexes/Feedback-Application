from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/feedbacket_db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # ML Models
    rubert_model_path: str = "sbert_large_nlu_ru"
    rugpt_model_path: str = "rugpt3_c_200M"
    
    # Parser
    parser_interval_minutes: int = 30
    synthetic_reviews_count: int = 3000
    
    # Notifications
    alert_email: str = "alert@hotel-corp.ru"
    alert_telegram_id: str = "@hotel_ops_bot"
    
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
