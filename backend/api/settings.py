from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from models import User, UserSettings, get_db
from config import settings


router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings")
def get_user_settings(
    user_id: int = 1,  # Временно хардкод, потом будет из JWT
    db: Session = Depends(get_db)
):
    """Получение настроек пользователя"""
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()
    
    if not user_settings:
        # Создаем настройки по умолчанию
        user_settings = UserSettings(
            user_id=user_id,
            operation_mode="manual",
            response_length="medium",
            tone_of_voice="business",
            parse_interval="30m",
            alert_email=settings.alert_email,
            alert_telegram_id=settings.alert_telegram_id
        )
        db.add(user_settings)
        db.commit()
        db.refresh(user_settings)
    
    return {
        "user_id": user_settings.user_id,
        "operation_mode": user_settings.operation_mode,
        "response_length": user_settings.response_length,
        "tone_of_voice": user_settings.tone_of_voice,
        "parse_interval": user_settings.parse_interval,
        "alert_email": user_settings.alert_email,
        "alert_telegram_id": user_settings.alert_telegram_id,
        "updated_at": user_settings.updated_at.isoformat() if user_settings.updated_at else None
    }


@router.put("/settings")
def update_user_settings(
    operation_mode: Optional[str] = None,
    response_length: Optional[str] = None,
    tone_of_voice: Optional[str] = None,
    parse_interval: Optional[str] = None,
    alert_email: Optional[str] = None,
    alert_telegram_id: Optional[str] = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Обновление настроек пользователя"""
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()
    
    if not user_settings:
        user_settings = UserSettings(user_id=user_id)
        db.add(user_settings)
    
    # Обновление полей
    if operation_mode is not None:
        if operation_mode not in ["manual", "autopilot"]:
            raise HTTPException(status_code=400, detail="Неверный режим работы")
        user_settings.operation_mode = operation_mode
    
    if response_length is not None:
        if response_length not in ["short", "medium", "long"]:
            raise HTTPException(status_code=400, detail="Неверная длина ответа")
        user_settings.response_length = response_length
    
    if tone_of_voice is not None:
        if tone_of_voice not in ["business", "friendly", "reserved"]:
            raise HTTPException(status_code=400, detail="Неверная тональность")
        user_settings.tone_of_voice = tone_of_voice
    
    if parse_interval is not None:
        if parse_interval not in ["30m", "2h", "24h"]:
            raise HTTPException(status_code=400, detail="Неверный интервал парсинга")
        user_settings.parse_interval = parse_interval
    
    if alert_email is not None:
        user_settings.alert_email = alert_email
    
    if alert_telegram_id is not None:
        user_settings.alert_telegram_id = alert_telegram_id
    
    user_settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_settings)
    
    return {
        "message": "Настройки успешно обновлены",
        "settings": {
            "user_id": user_settings.user_id,
            "operation_mode": user_settings.operation_mode,
            "response_length": user_settings.response_length,
            "tone_of_voice": user_settings.tone_of_voice,
            "parse_interval": user_settings.parse_interval,
            "alert_email": user_settings.alert_email,
            "alert_telegram_id": user_settings.alert_telegram_id,
            "updated_at": user_settings.updated_at.isoformat()
        }
    }


@router.get("/users/me")
def get_current_user(
    user_id: int = 1,  # Временно хардкод
    db: Session = Depends(get_db)
):
    """Получение информации о текущем пользователе"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Создаем тестового пользователя
        user = User(
            username="manager",
            email="manager@hotel.com",
            hashed_password="hashed_password_here",
            full_name="Алексей Иванов",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
