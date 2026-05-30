"""
Менеджер базы данных для хранения отзывов и ответов.
Использует SQLite для локального хранения.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "reviews.db"):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица отзывов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                author TEXT,
                text TEXT NOT NULL,
                rating INTEGER,
                date TEXT,
                sentiment TEXT,
                sentiment_confidence REAL,
                topic TEXT,
                is_synthetic BOOLEAN DEFAULT FALSE,
                generated_response TEXT,
                manager_response TEXT,
                manager_id TEXT,
                response_status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица настроек пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                dark_mode BOOLEAN DEFAULT FALSE,
                font_size INTEGER DEFAULT 14,
                language TEXT DEFAULT 'ru',
                notifications_enabled BOOLEAN DEFAULT TRUE,
                email_notifications BOOLEAN DEFAULT FALSE,
                auto_generate_responses BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица отелей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                sources_config TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индексы для ускорения поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON reviews(sentiment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic ON reviews(topic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON reviews(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON reviews(response_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON reviews(date)")
        
        conn.commit()
        conn.close()
        print(f"База данных инициализирована: {self.db_path}")
    
    def save_reviews(self, reviews: List[Dict[str, Any]]):
        """Сохраняет список отзывов в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for review in reviews:
            cursor.execute("""
                INSERT OR REPLACE INTO reviews 
                (id, source, author, text, rating, date, sentiment, sentiment_confidence, 
                 topic, is_synthetic, generated_response, response_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review.get("id"),
                review.get("source"),
                review.get("author"),
                review.get("text"),
                review.get("rating"),
                review.get("date"),
                review.get("sentiment"),
                review.get("sentiment_confidence"),
                review.get("topic"),
                review.get("is_synthetic", False),
                review.get("generated_response"),
                "answered" if review.get("generated_response") else "pending",
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Сохранено {len(reviews)} отзывов в БД")
    
    def get_reviews_without_response(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает отзывы без ответа менеджера"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reviews 
            WHERE is_synthetic = FALSE 
            AND (manager_response IS NULL OR response_status = 'pending')
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_review_response(self, review_id: str, response_text: str, manager_id: str = "system"):
        """Обновляет ответ менеджера для отзыва"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reviews 
            SET manager_response = ?, 
                manager_id = ?, 
                response_status = 'answered',
                updated_at = ?
            WHERE id = ?
        """, (response_text, manager_id, datetime.now().isoformat(), review_id))
        
        conn.commit()
        conn.close()
        print(f"Ответ сохранен для отзыва {review_id}")
    
    def get_all_reviews(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Получает все отзывы с фильтрацией"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM reviews WHERE is_synthetic = FALSE"
        params = []
        
        if filters:
            if filters.get("sentiment"):
                query += " AND sentiment = ?"
                params.append(filters["sentiment"])
            if filters.get("topic"):
                query += " AND topic = ?"
                params.append(filters["topic"])
            if filters.get("source"):
                query += " AND source = ?"
                params.append(filters["source"])
            if filters.get("status"):
                query += " AND response_status = ?"
                params.append(filters["status"])
        
        query += " ORDER BY date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику по отзывам"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Общее количество реальных отзывов
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE is_synthetic = FALSE")
        stats["total_real_reviews"] = cursor.fetchone()[0]
        
        # Количество синтетических отзывов
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE is_synthetic = TRUE")
        stats["total_synthetic_reviews"] = cursor.fetchone()[0]
        
        # По тональности
        cursor.execute("""
            SELECT sentiment, COUNT(*) 
            FROM reviews 
            WHERE is_synthetic = FALSE 
            GROUP BY sentiment
        """)
        stats["by_sentiment"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # По темам
        cursor.execute("""
            SELECT topic, COUNT(*) 
            FROM reviews 
            WHERE is_synthetic = FALSE 
            GROUP BY topic
        """)
        stats["by_topic"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # По источникам
        cursor.execute("""
            SELECT source, COUNT(*) 
            FROM reviews 
            WHERE is_synthetic = FALSE 
            GROUP BY source
        """)
        stats["by_source"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Статус ответов
        cursor.execute("""
            SELECT response_status, COUNT(*) 
            FROM reviews 
            WHERE is_synthetic = FALSE 
            GROUP BY response_status
        """)
        stats["by_response_status"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Средний рейтинг
        cursor.execute("""
            SELECT AVG(rating) 
            FROM reviews 
            WHERE is_synthetic = FALSE AND rating IS NOT NULL
        """)
        stats["average_rating"] = round(cursor.fetchone()[0] or 0, 2)
        
        conn.close()
        
        return stats
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает настройки пользователя"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def save_user_settings(self, user_id: str, settings: Dict[str, Any]):
        """Сохраняет настройки пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings 
            (user_id, dark_mode, font_size, language, notifications_enabled, 
             email_notifications, auto_generate_responses, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            settings.get("dark_mode", False),
            settings.get("font_size", 14),
            settings.get("language", "ru"),
            settings.get("notifications_enabled", True),
            settings.get("email_notifications", False),
            settings.get("auto_generate_responses", True),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def add_hotel(self, hotel_id: str, name: str, address: str = "", sources_config: List[str] = None):
        """Добавляет отель в базу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO hotels (id, name, address, sources_config, active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            hotel_id,
            name,
            address,
            json.dumps(sources_config or ["booking", "ostrovok", "manul", "google", "yandex"]),
            True
        ))
        
        conn.commit()
        conn.close()
    
    def get_hotels(self) -> List[Dict[str, Any]]:
        """Получает список всех отелей"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM hotels")
        rows = cursor.fetchall()
        conn.close()
        
        hotels = []
        for row in rows:
            hotel = dict(row)
            hotel["sources_config"] = json.loads(hotel["sources_config"]) if hotel["sources_config"] else []
            hotels.append(hotel)
        
        return hotels


if __name__ == "__main__":
    # Тестирование БД
    db = DatabaseManager("test_reviews.db")
    
    # Тестовые данные
    test_reviews = [
        {"id": "test_1", "source": "booking", "text": "Отличный отель!", "rating": 5, "sentiment": "positive", "topic": "общее"},
        {"id": "test_2", "source": "yandex", "text": "Ужасный сервис.", "rating": 1, "sentiment": "negative", "topic": "персонал"}
    ]
    
    db.save_reviews(test_reviews)
    
    stats = db.get_statistics()
    print("\nСтатистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
