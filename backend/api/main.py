"""
FastAPI приложение для управления отзывами.
Предоставляет REST API для фронтенда.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio

from pipeline import ReviewProcessingPipeline
from database.db_manager import DatabaseManager

app = FastAPI(title="Feedbacket API", description="Система обработки отзывов отелей")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация компонентов
db = DatabaseManager()
pipeline = ReviewProcessingPipeline()


# Модели данных
class UserSettings(BaseModel):
    dark_mode: bool = False
    font_size: int = 14
    language: str = "ru"
    notifications_enabled: bool = True
    email_notifications: bool = False
    auto_generate_responses: bool = True


class HotelCreate(BaseModel):
    id: str
    name: str
    address: Optional[str] = ""
    sources_config: Optional[List[str]] = ["TripAdvisor", "google", "yandex"]


class ResponseUpdate(BaseModel):
    response_text: str
    manager_id: Optional[str] = "system"


# Эндпоинты
@app.get("/")
async def root():
    return {"message": "Feedbacket API v1.0", "status": "running"}


@app.get("/api/statistics")
async def get_statistics():
    """Получить статистику по отзывам"""
    return db.get_statistics()


@app.get("/api/reviews")
async def get_reviews(
    sentiment: Optional[str] = None,
    topic: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=500)
):
    """Получить отзывы с фильтрацией"""
    filters = {}
    if sentiment:
        filters["sentiment"] = sentiment
    if topic:
        filters["topic"] = topic
    if source:
        filters["source"] = source
    if status:
        filters["status"] = status
    
    reviews = db.get_all_reviews(filters)
    return reviews[:limit]


@app.get("/api/reviews/pending")
async def get_pending_reviews(limit: int = Query(default=50, le=500)):
    """Получить отзывы, требующие ответа"""
    return db.get_reviews_without_response(limit)


@app.post("/api/reviews/{review_id}/response")
async def update_response(review_id: str, data: ResponseUpdate):
    """Обновить ответ на отзыв"""
    db.update_review_response(review_id, data.response_text, data.manager_id)
    return {"status": "success", "review_id": review_id}


@app.post("/api/reviews/{review_id}/regenerate")
async def regenerate_response(review_id: str):
    """Перегенерировать ответ с помощью AI"""
    reviews = db.get_all_reviews({"status": "all"})
    review = next((r for r in reviews if r["id"] == review_id), None)
    
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Генерация нового ответа
    from generation.response_generator import RuGPT3ResponseGenerator
    generator = RuGPT3ResponseGenerator()
    
    new_response = generator.generate_response(review)
    db.update_review_response(review_id, new_response, "ai_auto")
    
    return {"status": "success", "response": new_response}


@app.get("/api/settings/{user_id}")
async def get_user_settings(user_id: str):
    """Получить настройки пользователя"""
    settings = db.get_user_settings(user_id)
    if not settings:
        # Возвращаем настройки по умолчанию
        return {
            "user_id": user_id,
            "dark_mode": False,
            "font_size": 14,
            "language": "ru",
            "notifications_enabled": True,
            "email_notifications": False,
            "auto_generate_responses": True
        }
    return settings


@app.post("/api/settings/{user_id}")
async def save_user_settings(user_id: str, settings: UserSettings):
    """Сохранить настройки пользователя"""
    db.save_user_settings(user_id, settings.dict())
    return {"status": "success", "user_id": user_id}


@app.get("/api/hotels")
async def get_hotels():
    """Получить список отелей"""
    return db.get_hotels()


@app.post("/api/hotels")
async def create_hotel(hotel: HotelCreate):
    """Добавить новый отель"""
    db.add_hotel(hotel.id, hotel.name, hotel.address, hotel.sources_config)
    return {"status": "success", "hotel_id": hotel.id}


@app.post("/api/pipeline/run")
async def run_pipeline(hotel_id: str, synthetic_count: int = 3000):
    """Запустить полный пайплайн обработки отзывов"""
    # Запускаем в фоне, чтобы не блокировать запрос
    asyncio.create_task(pipeline.run_full_pipeline(hotel_id, synthetic_count))
    return {
        "status": "started",
        "message": "Пайплайн запущен в фоновом режиме",
        "hotel_id": hotel_id
    }


@app.post("/api/parse")
async def parse_reviews(hotel_id: str, sources: Optional[List[str]] = None):
    """Запустить парсинг отзывов"""
    from parsers.review_collectors import run_all_parsers
    
    reviews = await run_all_parsers(hotel_id, sources)
    return {
        "status": "success",
        "count": len(reviews),
        "reviews": reviews[:10]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
