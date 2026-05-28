from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import get_db, RawReview, SyntheticReview, SentimentLabel, GeneratedResponse

app = FastAPI(title="Feedbacket API", description="API для системы управления отзывами отелей")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic модели для API
class ReviewBase(BaseModel):
    id: int
    source: str
    author_name: str
    review_text: str
    rating: Optional[int] = None
    
    class Config:
        from_attributes = True


class ReviewWithSentiment(ReviewBase):
    sentiment: Optional[str] = None
    confidence_score: Optional[float] = None
    response_text: Optional[str] = None


class StatsResponse(BaseModel):
    total_reviews: int
    positive: int
    neutral: int
    negative: int
    average_rating: float


# Эндпоинты
@app.get("/")
def read_root():
    return {"message": "Feedbacket API работает! Используйте /docs для документации"}


@app.get("/api/reviews/raw", response_model=List[ReviewWithSentiment])
def get_raw_reviews(limit: int = 50, db: Session = Depends(get_db)):
    """Получить сырые отзывы с метками и ответами"""
    reviews = db.query(RawReview).limit(limit).all()
    
    result = []
    for review in reviews:
        sentiment = db.query(SentimentLabel).filter(
            SentimentLabel.review_id == review.id,
            SentimentLabel.review_type == 'raw'
        ).first()
        
        response = db.query(GeneratedResponse).filter(
            GeneratedResponse.review_id == review.id,
            GeneratedResponse.review_type == 'raw'
        ).first()
        
        review_data = ReviewWithSentiment(
            id=review.id,
            source=review.source,
            author_name=review.author_name,
            review_text=review.review_text,
            rating=review.rating,
            sentiment=sentiment.sentiment if sentiment else None,
            confidence_score=sentiment.confidence_score if sentiment else None,
            response_text=response.response_text if response else None
        )
        result.append(review_data)
    
    return result


@app.get("/api/reviews/synthetic", response_model=List[ReviewBase])
def get_synthetic_reviews(limit: int = 50, db: Session = Depends(get_db)):
    """Получить синтетические отзывы"""
    reviews = db.query(SyntheticReview).limit(limit).all()
    return reviews


@app.get("/api/stats", response_model=StatsResponse)
def get_statistics(db: Session = Depends(get_db)):
    """Получить статистику по отзывам"""
    total = db.query(RawReview).count()
    
    positive = db.query(SentimentLabel).filter(
        SentimentLabel.sentiment == 'positive',
        SentimentLabel.review_type == 'raw'
    ).count()
    
    neutral = db.query(SentimentLabel).filter(
        SentimentLabel.sentiment == 'neutral',
        SentimentLabel.review_type == 'raw'
    ).count()
    
    negative = db.query(SentimentLabel).filter(
        SentimentLabel.sentiment == 'negative',
        SentimentLabel.review_type == 'raw'
    ).count()
    
    # Средняя оценка
    from sqlalchemy import func
    avg_rating = db.query(func.avg(RawReview.rating)).scalar() or 0
    
    return StatsResponse(
        total_reviews=total,
        positive=positive,
        neutral=neutral,
        negative=negative,
        average_rating=round(avg_rating, 2)
    )


@app.get("/api/review/{review_id}/response")
def get_response_for_review(review_id: int, db: Session = Depends(get_db)):
    """Получить сгенерированный ответ для конкретного отзыва"""
    response = db.query(GeneratedResponse).filter(
        GeneratedResponse.review_id == review_id,
        GeneratedResponse.review_type == 'raw'
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Ответ не найден")
    
    return {
        "review_id": review_id,
        "response_text": response.response_text,
        "sentiment": response.sentiment_context
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
