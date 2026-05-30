"""
Тестовый скрипт для проверки парсера TripAdvisor
Запуск: python test_tripadvisor_parser.py
"""

import asyncio
import sys
import os

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.review_parsers import TripAdvisorParser
from database.models import PlatformSource

async def test_tripadvisor():
    # URL отеля из задачи
    url = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"
    
    # Прокси (опционально) - замените на свой при необходимости
    # proxy = "http://user:pass@ip:port"
    proxy = None
    
    parser = TripAdvisorParser()
    
    print("=" * 60)
    print("🧪 ТЕСТ ПАРСЕРА TRIPADVISOR")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Прокси: {'✅ ' + proxy if proxy else '❌ Не используется'}")
    print("=" * 60)
    
    try:
        reviews = await parser.parse_hotel_reviews(
            url=url,
            limit=10,  # Количество отзывов для теста
            proxy=proxy
        )
        
        print("\n" + "=" * 60)
        print(f"✅ РЕЗУЛЬТАТ: Найдено {len(reviews)} отзывов")
        print("=" * 60)
        
        if reviews:
            print("\n📋 Пример первого отзыва:")
            first_review = reviews[0]
            print(f"   Автор: {first_review['author_name']}")
            print(f"   Рейтинг: {first_review['rating']}/5")
            print(f"   Текст: {first_review['review_text'][:100]}...")
            print(f"   Дата: {first_review['review_date']}")
            print(f"   Платформа: {first_review['platform']}")
            
            print("\n📊 Распределение оценок:")
            ratings_count = {}
            for r in reviews:
                rating = r['rating']
                ratings_count[rating] = ratings_count.get(rating, 0) + 1
            
            for rating in sorted(ratings_count.keys(), reverse=True):
                count = ratings_count[rating]
                bar = "█" * count
                print(f"   {rating}⭐: {bar} ({count})")
        
        return len(reviews) > 0
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tripadvisor())
    sys.exit(0 if success else 1)
