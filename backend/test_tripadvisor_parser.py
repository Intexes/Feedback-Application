"""
Скрипт для тестирования парсера TripAdvisor
Запускайте локально после установки зависимостей

Установка:
    pip install -r requirements.txt
    playwright install chromium

Запуск:
    python test_tripadvisor_parser.py
"""

import asyncio
from parsers.review_parsers import TripAdvisorParser


async def test_tripadvisor():
    # URL страницы отзывов вашего отеля
    url = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"
    
    parser = TripAdvisorParser()
    
    print(f"🔍 Начинаем парсинг TripAdvisor...")
    print(f"📍 URL: {url}")
    print("-" * 80)
    
    reviews = await parser.parse_hotel_reviews(url, limit=10)
    
    print(f"\n✅ Найдено отзывов: {len(reviews)}")
    print("-" * 80)
    
    for i, review in enumerate(reviews, 1):
        print(f"\n📝 Отзыв #{i}:")
        print(f"   👤 Автор: {review['author_name']}")
        print(f"   ⭐ Рейтинг: {review['rating']}/5")
        print(f"   📅 Дата: {review['review_date'].strftime('%d.%m.%Y') if review['review_date'] else 'Н/Д'}")
        print(f"   💬 Текст: {review['review_text'][:150]}{'...' if len(review['review_text']) > 150 else ''}")
        print(f"   🔗 ID: {review['external_id']}")
    
    return reviews


if __name__ == "__main__":
    try:
        reviews = asyncio.run(test_tripadvisor())
        
        if reviews:
            print("\n" + "=" * 80)
            print("🎉 Парсинг завершен успешно!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("⚠️ Отзывы не найдены. Возможно, изменилась структура сайта.")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ Ошибка при парсинге: {e}")
        print("\n💡 Советы:")
        print("   1. Убедитесь, что установлен Chromium: playwright install chromium")
        print("   2. Проверьте интернет-соединение")
        print("   3. Попробуйте увеличить timeout в настройках парсера")
