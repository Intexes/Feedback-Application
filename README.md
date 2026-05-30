# Feedbacket - Система анализа отзывов и генерации ответов на основе ИИ

## Описание

Feedbacket — это полноценная система для сбора, анализа отзывов о отелях с различных платформ (Booking, Ostrovok, Manul, Google Maps, Яндекс.Карты) и автоматической генерации ответов с использованием российских языковых моделей ruBERT и ruGPT-3.

## Структура проекта

```
/workspace/
├── README.md               # Общая документация
├── index.html              # Главная страница (Dashboard)
├── workspace.html          # Рабочая зона менеджера
├── account.html            # Страница аккаунта
├── settings.html           # Страница настроек
├── styles.css              # Основные стили CSS
├── logic.js                # JavaScript логика фронтенда
├── img/                    # Изображения и ресурсы
│   ├── logo-*.png
│   └── News_*.jpg
├── backend/                # Бэкенд часть
│   ├── api/                # FastAPI приложение
│   │   └── main.py         # Основной API файл
│   ├── parsers/            # Парсеры отзывов
│   │   ├── review_collectors.py  # Парсеры платформ
│   │   └── synthetic_generator.py # Генератор синтетических отзывов
│   ├── analysis/           # Анализ тональности
│   │   └── sentiment_analyzer.py # ruBERT анализатор
│   ├── generation/         # Генерация ответов
│   │   └── response_generator.py # ruGPT-3 генератор
│   ├── database/           # Работа с БД
│   │   └── db_manager.py   # SQLite менеджер
│   ├── pipeline.py         # Основной пайплайн обработки
│   ├── requirements.txt    # Python зависимости
│   └── README.md           # Документация бэкенда
└── frontend/               # Фронтенд документация
    └── README.md
```

## Архитектура работы

### Полный цикл обработки отзывов:

1. **Парсинг** → Сбор отзывов с платформ:
   - Booking.com
   - Ostrovok.ru
   - Manul.ru
   - Google Maps
   - Яндекс.Карты

2. **Генерация синтетических данных** → Создание ~3000 дополнительных отзывов для дообучения модели

3. **Анализ тональности (ruBERT)** → Классификация каждого отзыва:
   - Тональность: positive/negative/neutral
   - Тема: номер/завтрак/персонал/локация/чистота/цена/wi-fi
   - Уверенность модели

4. **Генерация ответов (ruGPT-3)** → Создание персонализированных ответов на основе:
   - Текста отзыва
   - Определенной тональности
   - Темы отзыва
   - Рейтинга

5. **Сохранение в БД** → Запись всех данных в SQLite базу

6. **Интеграция с фронтендом** → REST API для отображения данных в интерфейсе менеджера

## Быстрый старт

### 1. Установка зависимостей бэкенда

```bash
cd backend
pip install -r requirements.txt
```

### 2. Запуск API сервера

```bash
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступно по адресу: http://localhost:8000
Документация Swagger: http://localhost:8000/docs

### 3. Запуск полного пайплайна обработки

```bash
cd backend
python pipeline.py
```

### 4. Запуск фронтенда

```bash
# Вариант 1: Python HTTP сервер
python -m http.server 8080

# Вариант 2: Просто открыть файл в браузере
# Откройте index.html в любом современном браузере
```

Фронтенд: http://localhost:8080

## API Endpoints

### Статистика
- `GET /api/statistics` - Получить общую статистику

### Отзывы
- `GET /api/reviews` - Список отзывов с фильтрацией
- `GET /api/reviews/pending` - Отзывы без ответа
- `POST /api/reviews/{id}/response` - Сохранить ответ
- `POST /api/reviews/{id}/regenerate` - Перегенерировать ответ AI

### Настройки
- `GET /api/settings/{user_id}` - Настройки пользователя
- `POST /api/settings/{user_id}` - Сохранить настройки

### Пайплайн
- `POST /api/pipeline/run?hotel_id=xxx` - Запустить обработку
- `POST /api/parse?hotel_id=xxx` - Запустить парсинг

## Технологии

### Бэкенд
- **FastAPI** - Веб-фреймворк
- **SQLite** - База данных
- **PyTorch + Transformers** - ML модели
- **ruBERT** - Анализ тональности
- **ruGPT-3** - Генерация текста

### Фронтенд
- **HTML5/CSS3** - Верстка
- **Vanilla JavaScript** - Логика
- **Fetch API** - Работа с бэкендом

## Модели машинного обучения

- **ruBERT** (`blanchefort/rubert-base-cased-sentiment-rusentiment`) - Модель для анализа тональности русскоязычных текстов
- **ruGPT-3** (`sberbank-ai/rugpt3large_based_on_gpt2`) - Модель для генерации ответов на русском языке

## Лицензия

НИТУ МИСИС © 2026
