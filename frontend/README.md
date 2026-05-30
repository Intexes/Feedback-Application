# Фронтенд для системы Feedbacket

## Структура проекта

```
/workspace/
├── index.html              # Главная страница (Dashboard)
├── workspace.html          # Рабочая зона менеджера
├── account.html            # Страница аккаунта
├── settings.html           # Страница настроек
├── styles.css              # Основные стили
├── logic.js                # JavaScript логика
└── all_styles/             # Изображения и ресурсы
    ├── logo-*.png
    └── News_*.jpg
```

## Интеграция с бэкендом

Фронтенд подключается к API бэкенда по адресу `http://localhost:8000/api/`

### Основные endpoints:

1. **Статистика** - `GET /api/statistics`
2. **Отзывы** - `GET /api/reviews`, `GET /api/reviews/pending`
3. **Ответы** - `POST /api/reviews/{id}/response`
4. **Настройки** - `GET/POST /api/settings/{user_id}`
5. **Пайплайн** - `POST /api/pipeline/run`

## Запуск

Просто откройте `index.html` в браузере или используйте локальный сервер:

```bash
# Python HTTP сервер
python -m http.server 8080

# Или Node.js live-server
npx live-server
```

## Настройка API URL

В файле `logic.js` измените переменную `API_URL`:

```javascript
const API_URL = 'http://localhost:8000/api'; // Для локальной разработки
// const API_URL = 'https://api.feedbacket.com/api'; // Для продакшена
```
