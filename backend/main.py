from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models import Base, engine
from config import settings
from api.reviews import router as reviews_router
from api.settings import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения"""
    # Создание таблиц в БД
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    yield
    
    # Очистка при завершении
    print("Application shutdown")


app = FastAPI(
    title="Feedbacket API",
    description="API для системы анализа отзывов и генерации ответов",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "*"  # Для разработки
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(reviews_router)
app.include_router(settings_router)


@app.get("/")
def root():
    """Корневой эндпоинт"""
    return {
        "message": "Feedbacket API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
