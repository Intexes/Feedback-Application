import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Определяем абсолютный путь к базе данных
# База будет лежать в папке data рядом с этим файлом (внутри backend) или в корне проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)  # Создаем папку data, если её нет
DB_PATH = os.path.join(DATA_DIR, "feedbacket.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Нужно для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модель сырого отзыва (из парсера)
class RawReview(Base):
    __tablename__ = "raw_reviews"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # 'tripadvisor', 'google', 'yandex'
    hotel_id = Column(String(100))
    author_name = Column(String(255))
    review_text = Column(Text, nullable=False)
    rating = Column(Integer)
    review_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    sentiment = relationship("SentimentLabel", back_populates="review", uselist=False)
    response = relationship("GeneratedResponse", back_populates="review", uselist=False)


# Модель синтетического отзыва
class SyntheticReview(Base):
    __tablename__ = "synthetic_reviews"

    id = Column(Integer, primary_key=True, index=True)
    base_review_id = Column(Integer, ForeignKey("raw_reviews.id"))
    review_text = Column(Text, nullable=False)
    rating = Column(Integer)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    sentiment = relationship("SentimentLabel", back_populates="synthetic_review", uselist=False)
    response = relationship("GeneratedResponse", back_populates="synthetic_review", uselist=False)


# Модель метки тональности (результат ruBert)
class SentimentLabel(Base):
    __tablename__ = "sentiment_labels"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False)
    review_type = Column(String(20), nullable=False)  # 'raw' или 'synthetic'
    sentiment = Column(String(20), nullable=False)  # 'positive', 'negative', 'neutral'
    confidence_score = Column(Float)
    model_version = Column(String(50))
    processed_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    review = relationship("RawReview", back_populates="sentiment")
    synthetic_review = relationship("SyntheticReview", back_populates="sentiment")


# Модель сгенерированного ответа (результат ruGPT)
class GeneratedResponse(Base):
    __tablename__ = "generated_responses"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False)
    review_type = Column(String(20), nullable=False)
    response_text = Column(Text, nullable=False)
    sentiment_context = Column(String(20))
    model_version = Column(String(50))
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    review = relationship("RawReview", back_populates="response")
    synthetic_review = relationship("SyntheticReview", back_populates="response")


# Функция для создания таблиц
def init_db():
    Base.metadata.create_all(bind=engine)


# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
