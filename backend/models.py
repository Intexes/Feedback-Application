import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Определение пути к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'feedbacket.db')

# Создаем папку data, если её нет
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RawReview(Base):
    __tablename__ = 'raw_reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    source = Column(String, default='Unknown') # TripAdvisor, Google, Synthetic, etc.
    rating = Column(String, nullable=True)     # Например, "5/5" или "10"
    raw_date = Column(String, nullable=True)   # Дата в оригинальном формате
    collected_at = Column(DateTime, nullable=False) # Дата сбора
    
    # Связь с метками тональности
    sentiment = relationship("SentimentLabel", back_populates="review", uselist=False, cascade="all, delete-orphan")

class SentimentLabel(Base):
    __tablename__ = 'sentiment_labels'
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey('raw_reviews.id'), unique=True, nullable=False)
    
    sentiment = Column(String, nullable=False) # positive, negative, neutral
    confidence = Column(Float, nullable=True)  # Уверенность модели от 0 до 1
    analyzed_at = Column(DateTime, nullable=False) # Дата анализа
    
    # Обратная связь
    review = relationship("RawReview", back_populates="sentiment")

class GeneratedResponse(Base):
    __tablename__ = 'generated_responses'
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey('raw_reviews.id'), nullable=False)
    response_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False)
    
    review = relationship("RawReview")

# Функция для создания таблиц
def init_db():
    Base.metadata.create_all(bind=engine)