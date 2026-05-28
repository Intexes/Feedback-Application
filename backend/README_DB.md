# Database Configuration for Feedbacket

## SQLite (Рекомендуется для локальной разработки)

Для локальной БД будем использовать **SQLite** — это легковесная файловая база данных, которая:
- Не требует установки сервера
- Хранится в одном файле (`feedbacket.db`)
- Идеальна для прототипирования и небольших проектов
- Легко мигрирует на PostgreSQL в продакшене

### Схема базы данных

```sql
-- Таблица сырых отзывов (из парсера)
CREATE TABLE raw_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(50) NOT NULL,  -- 'tripadvisor', 'google', 'yandex'
    hotel_id VARCHAR(100),
    author_name VARCHAR(255),
    review_text TEXT NOT NULL,
    rating INTEGER,
    review_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица синтетических отзывов
CREATE TABLE synthetic_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_review_id INTEGER,  -- ссылка на исходный отзыв
    review_text TEXT NOT NULL,
    rating INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_review_id) REFERENCES raw_reviews(id)
);

-- Таблица с метками тональности (результат ruBert)
CREATE TABLE sentiment_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    review_type VARCHAR(20) NOT NULL,  -- 'raw' или 'synthetic'
    sentiment VARCHAR(20) NOT NULL,  -- 'positive', 'negative', 'neutral'
    confidence_score FLOAT,
    model_version VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сгенерированных ответов (результат ruGPT)
CREATE TABLE generated_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    review_type VARCHAR(20) NOT NULL,
    response_text TEXT NOT NULL,
    sentiment_context VARCHAR(20),
    model_version VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Структура проекта

```
/workspace
├── backend/
│   ├── database.py          # Подключение к БД, модели SQLAlchemy
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── selenium_parser.py  # Парсер на Selenium
│   │   └── beautifulsoup_parser.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── sentiment_analysis.py  # ruBert
│   │   ├── response_generation.py  # ruGPT
│   │   └── synthetic_data.py  # Генерация синтетических отзывов
│   ├── models.py            # SQLAlchemy модели
│   ├── main.py              # FastAPI приложение
│   └── requirements.txt
├── data/
│   └── feedbacket.db        # Файл SQLite базы данных
└── frontend/                # Ваш существующий HTML/CSS/JS
```

Создать файлы структуры?
