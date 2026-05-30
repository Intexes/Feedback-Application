# Backend для системы Feedbacket

## Структура проекта

```
backend/
├── api/                    # FastAPI приложение
│   └── main.py            # Основной файл API
├── parsers/               # Парсеры отзывов
│   ├── review_collectors.py  # Парсеры платформ (Booking, Ostrovok, Manul, Google, Yandex)
│   └── synthetic_generator.py # Генератор синтетических отзывов
├── analysis/              # Анализ тональности
│   └── sentiment_analyzer.py # ruBERT анализатор
├── generation/            # Генерация ответов
│   └── response_generator.py # ruGPT-3 генератор
├── database/              # Работа с БД
│   └── db_manager.py      # SQLite менеджер
├── pipeline.py            # Основной пайплайн обработки
├── requirements.txt       # Зависимости
└── README.md             # Документация
```

## Установка

```bash
pip install -r requirements.txt
```

## Запуск API сервера

```bash
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Запуск полного пайплайна

```bash
python pipeline.py
```

## API Endpoints

### Статистика
- `GET /api/statistics` - Получить статистику по отзывам

### Отзывы
- `GET /api/reviews` - Получить отзывы с фильтрацией
  - Параметры: `sentiment`, `topic`, `source`, `status`, `limit`
- `GET /api/reviews/pending` - Получить отзывы без ответа
- `POST /api/reviews/{review_id}/response` - Сохранить ответ менеджера
- `POST /api/reviews/{review_id}/regenerate` - Перегенерировать ответ AI

### Настройки
- `GET /api/settings/{user_id}` - Получить настройки пользователя
- `POST /api/settings/{user_id}` - Сохранить настройки пользователя

### Отели
- `GET /api/hotels` - Список отелей
- `POST /api/hotels` - Добавить отель

### Пайплайн
- `POST /api/pipeline/run?hotel_id=xxx&synthetic_count=3000` - Запустить обработку
- `POST /api/parse?hotel_id=xxx` - Запустить парсинг

## Архитектура работы

1. **Парсинг**: Сбор отзывов с Booking, Ostrovok, Manul, Google Maps, Yandex Maps
2. **Генерация**: Создание 3000 синтетических отзывов для дообучения
3. **Анализ**: Обработка всех отзывов через ruBERT (тональность + темы)
4. **Генерация ответов**: Создание ответов через ruGPT-3 на основе контекста
5. **Сохранение**: Запись результатов в SQLite БД
6. **Интеграция**: Фронтенд получает данные через REST API

## Модели ML

- **ruBERT** (`blanchefort/rubert-base-cased-sentiment-rusentiment`) - Анализ тональности
- **ruGPT-3** (`sberbank-ai/rugpt3large_based_on_gpt2`) - Генерация ответов

## Требования

- Python 3.8+
- PyTorch
- Transformers
- FastAPI
- SQLite
