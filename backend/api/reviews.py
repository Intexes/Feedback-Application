from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models import Review, UserSettings, SentimentType, PlatformSource, get_db
from ml.rubert_analyzer import get_analyzer
from ml.rugpt_generator import get_generator
from ml.synthetic_generator import get_synthetic_generator
from parsers.review_parsers import get_parser_service
from config import settings


router = APIRouter(prefix="/api", tags=["reviews"])


@router.get("/reviews")
def get_reviews(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    sentiment: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получение списка отзывов с фильтрацией"""
    query = db.query(Review)
    
    if status_filter:
        query = query.filter(Review.status == status_filter)
    if sentiment:
        query = query.filter(Review.sentiment == SentimentType(sentiment))
    if platform:
        query = query.filter(Review.platform == PlatformSource(platform))
    
    reviews = query.order_by(Review.parsed_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": query.count(),
        "reviews": [
            {
                "id": r.id,
                "platform": r.platform.value,
                "author_name": r.author_name,
                "rating": r.rating,
                "review_text": r.review_text,
                "sentiment": r.sentiment.value if r.sentiment else None,
                "sentiment_score": r.sentiment_score,
                "classes": r.classes,
                "status": r.status,
                "ai_response": r.ai_response,
                "parsed_at": r.parsed_at.isoformat() if r.parsed_at else None,
                "is_synthetic": r.is_synthetic
            }
            for r in reviews
        ]
    }


@router.get("/reviews/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Получение одного отзыва по ID"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    return {
        "id": review.id,
        "platform": review.platform.value,
        "external_id": review.external_id,
        "author_name": review.author_name,
        "rating": review.rating,
        "review_text": review.review_text,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "sentiment": review.sentiment.value if review.sentiment else None,
        "sentiment_score": review.sentiment_score,
        "classes": review.classes,
        "status": review.status,
        "ai_response": review.ai_response,
        "manager_edited_response": review.manager_edited_response,
        "parsed_at": review.parsed_at.isoformat() if review.parsed_at else None,
        "sent_at": review.sent_at.isoformat() if review.sent_at else None,
        "is_synthetic": review.is_synthetic
    }


@router.post("/reviews/analyze/{review_id}")
def analyze_review(review_id: int, db: Session = Depends(get_db)):
    """Анализ тональности отзыва через ruBERT"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    analyzer = get_analyzer(settings.rubert_model_path)
    analysis = analyzer.analyze_review(review.review_text)
    
    # Обновление записи
    review.sentiment = SentimentType(analysis["sentiment"])
    review.sentiment_score = analysis["sentiment_score"]
    review.classes = analysis["classes_json"]
    review.status = "analyzed"
    
    db.commit()
    db.refresh(review)
    
    return {
        "review_id": review.id,
        "sentiment": analysis["sentiment"],
        "sentiment_score": analysis["sentiment_score"],
        "classes": analysis["classes"]
    }


@router.post("/reviews/generate-response/{review_id}")
def generate_response(review_id: int, db: Session = Depends(get_db)):
    """Генерация ответа на отзыв через ruGPT-3"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    if not review.sentiment:
        raise HTTPException(status_code=400, detail="Сначала проанализируйте отзыв")
    
    # Получаем настройки пользователя
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == review.assigned_to or 1
    ).first()
    
    generator = get_generator(settings.rugpt_model_path)
    
    classes_list = []
    if review.classes:
        import json
        classes_list = json.loads(review.classes)
    
    response_text = generator.generate_response(
        review_text=review.review_text,
        rating=review.rating,
        sentiment=review.sentiment.value,
        classes=classes_list,
        settings=user_settings
    )
    
    # Сохранение ответа
    review.ai_response = response_text
    review.ai_response_generated_at = datetime.utcnow()
    review.status = "replied"
    
    db.commit()
    db.refresh(review)
    
    return {
        "review_id": review.id,
        "ai_response": response_text,
        "generated_at": review.ai_response_generated_at.isoformat()
    }


@router.post("/reviews/approve/{review_id}")
def approve_review(
    review_id: int,
    edited_response: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Утверждение ответа менеджером"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    if edited_response:
        review.manager_edited_response = edited_response
    else:
        review.manager_edited_response = review.ai_response
    
    review.status = "approved"
    db.commit()
    
    return {"review_id": review.id, "status": "approved"}


@router.post("/reviews/send/{review_id}")
def send_review(review_id: int, db: Session = Depends(get_db)):
    """Отправка ответа на платформу"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    if review.status != "approved":
        raise HTTPException(status_code=400, detail="Ответ должен быть утвержден")
    
    # Здесь будет логика отправки на платформу
    # Для примера просто помечаем как отправленный
    review.sent_at = datetime.utcnow()
    review.status = "sent"
    
    db.commit()
    
    return {"review_id": review.id, "sent_at": review.sent_at.isoformat()}


@router.post("/reviews/generate-synthetic")
def generate_synthetic_reviews(
    count: int = 3000,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Генерация синтетических отзывов для дообучения"""
    generator = get_synthetic_generator()
    
    def task():
        saved = generator.save_to_db(count)
        print(f"Saved {saved} synthetic reviews")
    
    if background_tasks:
        background_tasks.add_task(task)
        return {"message": f"Генерация {count} синтетических отзывов запущена в фоне"}
    else:
        saved = generator.save_to_db(count)
        return {"message": f"Сгенерировано и сохранено {saved} синтетических отзывов"}


@router.post("/parser/run")
async def run_parser(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Запуск парсера для сбора отзывов"""
    parser_service = get_parser_service()
    
    # Конфигурация источников (должна храниться в БД или настройках)
    sources_config = {
        "booking.com": {
            "hotel_ids": ["hotel_123", "hotel_456"],  # Пример ID
            "limit": 50
        },
        "yandex_maps": {
            "org_ids": ["123456789"],  # Пример ID организации
            "limit": 50
        }
    }
    
    async def task():
        count = await parser_service.parse_all_sources(sources_config)
        print(f"Parsed {count} reviews")
        
        # Автозапуск анализа для новых отзывов
        new_reviews = db.query(Review).filter(Review.status == "pending").all()
        analyzer = get_analyzer(settings.rubert_model_path)
        
        for review in new_reviews:
            try:
                analysis = analyzer.analyze_review(review.review_text)
                review.sentiment = SentimentType(analysis["sentiment"])
                review.sentiment_score = analysis["sentiment_score"]
                review.classes = analysis["classes_json"]
                review.status = "analyzed"
            except Exception as e:
                print(f"Error analyzing review {review.id}: {e}")
        
        db.commit()
    
    background_tasks.add_task(task)
    
    return {"message": "Парсинг запущен в фоновом режиме"}


@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Получение статистики по отзывам"""
    total = db.query(Review).count()
    pending = db.query(Review).filter(Review.status == "pending").count()
    analyzed = db.query(Review).filter(Review.status == "analyzed").count()
    replied = db.query(Review).filter(Review.status == "replied").count()
    sent = db.query(Review).filter(Review.status == "sent").count()
    
    positive = db.query(Review).filter(Review.sentiment == SentimentType.POSITIVE).count()
    neutral = db.query(Review).filter(Review.sentiment == SentimentType.NEUTRAL).count()
    negative = db.query(Review).filter(Review.sentiment == SentimentType.NEGATIVE).count()
    
    synthetic = db.query(Review).filter(Review.is_synthetic == True).count()
    
    return {
        "total": total,
        "by_status": {
            "pending": pending,
            "analyzed": analyzed,
            "replied": replied,
            "sent": sent
        },
        "by_sentiment": {
            "positive": positive,
            "neutral": neutral,
            "negative": negative
        },
        "synthetic_count": synthetic
    }
