import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Определяем путь к БД
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'feedbacket.db')

# Создаем папку data, если нет
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RawReview(Base):
    __tablename__ = 'raw_reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)       # Текст отзыва
    source = Column(String, default="Unknown")   # Источник (TripAdvisor, Synthetic, Google)
    rating = Column(String, nullable=True)       # Оценка (например, "5/5" или "10")
    raw_date = Column(String, nullable=True)     # Дата из текста
    collected_at = Column(DateTime, nullable=True) # Дата сбора

# Таблица для результатов анализа тональности (будет заполняться позже)
class SentimentLabel(Base):
    __tablename__ = 'sentiment_labels'
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False) # ID отзыва из raw_reviews
    sentiment = Column(String, nullable=False)  # positive, negative, neutral
    confidence = Column(Float, nullable=True)   # Уверенность модели
    created_at = Column(DateTime, nullable=True)

# Таблица для сгенерированных ответов
class GeneratedResponse(Base):
    __tablename__ = 'generated_responses'
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)