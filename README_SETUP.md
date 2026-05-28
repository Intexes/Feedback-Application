# Инструкция по запуску Feedbacket

## 📋 Структура проекта

```
/workspace
├── backend/
│   ├── models.py              # Модели базы данных (SQLAlchemy)
│   ├── main.py                # FastAPI приложение
│   ├── parser/
│   │   └── selenium_parser.py # Парсер отзывов (Selenium + BeautifulSoup)
│   ├── ml/
│   │   ├── sentiment_analysis.py    # Анализ тональности (ruBert)
│   │   └── response_generation.py   # Генерация ответов (ruGPT)
│   └── requirements.txt       # Зависимости Python
├── data/
│   └── feedbacket.db          # SQLite база данных (создаётся автоматически)
├── init_db.py                 # Скрипт инициализации БД
└── frontend/                  # Ваш существующий HTML/CSS/JS интерфейс
```

## 🚀 Быстрый старт

### Шаг 1: Установка зависимостей

```bash
cd /workspace
pip install -r backend/requirements.txt
```

### Шаг 2: Инициализация базы данных

```bash
python init_db.py
```

Это создаст файл `data/feedbacket.db` со всеми таблицами:
- `raw_reviews` — сырые отзывы из парсера
- `synthetic_reviews` — синтетические отзывы
- `sentiment_labels` — метки тональности от ruBert
- `generated_responses` — ответы от ruGPT

### Шаг 3: Запуск парсера

Отредактируйте URLs в `backend/parser/selenium_parser.py`:

```python
tripadvisor_url = "https://www.tripadvisor.ru/Hotel_Review-..."
google_url = "https://www.google.com/maps/place/..."
yandex_url = "https://yandex.ru/maps/-/..."
```

Запустите парсер:

```bash
python backend/parser/selenium_parser.py
```

### Шаг 4: Генерация синтетических отзывов (опционально)

Создайте скрипт `backend/ml/synthetic_data.py` для аугментации данных.

### Шаг 5: Анализ тональности (ruBert)

```bash
python backend/ml/sentiment_analysis.py
```

Модель автоматически загрузится и проанализирует все отзывы.

### Шаг 6: Генерация ответов (ruGPT)

```bash
python backend/ml/response_generation.py
```

Модель сгенерирует ответы для всех отзывов на основе их тональности.

### Шаг 7: Запуск бэкенда

```bash
cd /workspace
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: http://localhost:8000

Документация Swagger: http://localhost:8000/docs

## 🔌 Интеграция с фронтендом

Пример запроса к API из вашего JavaScript:

```javascript
// Получить отзывы
fetch('http://localhost:8000/api/reviews/raw?limit=50')
  .then(response => response.json())
  .then(data => {
    console.log('Отзывы:', data);
    // Отобразите данные в вашем интерфейсе
  });

// Получить статистику
fetch('http://localhost:8000/api/stats')
  .then(response => response.json())
  .then(stats => {
    console.log('Статистика:', stats);
  });

// Получить ответ для конкретного отзыва
fetch('http://localhost:8000/api/review/1/response')
  .then(response => response.json())
  .then(data => {
    console.log('Ответ:', data.response_text);
  });
```

## 📊 Схема работы

```
┌─────────────────┐
│   Парсинг       │ Selenium + BeautifulSoup
│   (TripAdvisor, │
│   Google,       │
│   Яндекс)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  raw_reviews    │ SQLite БД
│  (сырые отзывы) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ruBert         │ Анализ тональности
│  (sentiment)    │ positive/negative/neutral
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ruGPT          │ Генерация ответов
│  (response)     │ Текст ответа менеджеру
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │ REST API для фронтенда
│  Backend        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │ Ваш HTML/CSS/JS интерфейс
│  (Manager UI)   │
└─────────────────┘
```

## ⚠️ Важные замечания

1. **Парсинг**: Сайты могут менять структуру HTML. Возможно потребуется обновить селекторы в `selenium_parser.py`.

2. **ML модели**: Первое запустите скачает модели (~2-4 GB). Убедитесь в наличии интернета.

3. **Ресурсы**: Для работы с ruGPT требуется минимум 8GB RAM. Рекомендуется использовать GPU.

4. **Безопасность**: В продакшене измените CORS настройки в `main.py` и добавьте аутентификацию.

## 🛠 Troubleshooting

**Ошибка: Chrome WebDriver не найден**
```bash
pip install webdriver-manager
```

**Ошибка: Недостаточно памяти для ML моделей**
```bash
# Используйте CPU режим с ограничением памяти
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

**Ошибка: Миграции БД**
```bash
# Удалите старый файл БД и создайте заново
rm data/feedbacket.db
python init_db.py
```
