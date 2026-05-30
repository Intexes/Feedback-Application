from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class SentimentType(enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ReviewClass(enum.Enum):
    SERVICE = "service"
    CLEANLINESS = "cleanliness"
    LOCATION = "location"
    FOOD = "food"
    PRICE = "price"
    STAFF = "staff"
    ROOM = "room"
    AMENITIES = "amenities"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reviews = relationship("Review", back_populates="assigned_to")
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    operation_mode = Column(String(50), default="manual")  # manual, autopilot
    response_length = Column(String(50), default="medium")  # short, medium, long
    tone_of_voice = Column(String(50), default="business")  # business, friendly, reserved
    parse_interval = Column(String(50), default="30m")  # 30m, 2h, 24h
    alert_email = Column(String(255))
    alert_telegram_id = Column(String(255))
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="settings")


class PlatformSource(enum.Enum):
    BOOKING = "booking.com"
    YANDEX_MAPS = "yandex_maps"
    GOOGLE_MAPS = "google_maps"
    TRIPADVISOR = "tripadvisor"
    OSTROVOK = "ostrovok"
    MANUL = "manul"
    MANUAL = "manual"


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source info
    platform = Column(SQLEnum(PlatformSource), nullable=False)
    external_id = Column(String(255), index=True)  # ID на внешней платформе
    
    # Review content
    author_name = Column(String(255))
    rating = Column(Integer, nullable=False)  # 1-5
    review_text = Column(Text, nullable=False)
    review_date = Column(DateTime)
    
    # ML Analysis
    sentiment = Column(SQLEnum(SentimentType))
    sentiment_score = Column(Float)  # 0.0 - 1.0
    classes = Column(String(500))  # JSON string of ReviewClass values
    is_synthetic = Column(Boolean, default=False)
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, analyzed, replied, approved, sent
    assigned_to = Column(Integer, ForeignKey("users.id"))
    
    # AI Response
    ai_response = Column(Text)
    ai_response_generated_at = Column(DateTime)
    manager_edited_response = Column(Text)
    sent_at = Column(DateTime)
    
    # Timestamps
    parsed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assigned_user = relationship("User", back_populates="reviews")


class SyntheticDataConfig(Base):
    __tablename__ = "synthetic_data_config"
    
    id = Column(Integer, primary_key=True, index=True)
    class_type = Column(String(100), nullable=False, unique=True)
    sentiment = Column(String(50), nullable=False)
    template_count = Column(Integer, default=0)
    last_generated_at = Column(DateTime)


engine = create_engine("postgresql://postgres:postgres@localhost:5432/feedbacket_db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
