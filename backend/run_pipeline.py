"""
Скрипт для запуска парсинга отзывов с указанных источников
City Park Hotel Sochi
"""
import asyncio
import sys
sys.path.insert(0, '/workspace/backend')

from parsers.review_parsers import ReviewParserService
from ml.synthetic_generator import SyntheticReviewsGenerator
from ml.rubert_analyzer import RuBertAnalyzer
from ml.rugpt_generator import ResponseGenerator
from database.db_manager import DatabaseManager


# URL для парсинга (указанные пользователем)
SOURCES_CONFIG = {
    "tripadvisor": {
        "urls": [
            "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"
        ],
        "limit": 50
    },
    "google_maps": {
        "urls": [
            "https://www.google.com/maps/place/City+Park+Hotel+Sochi/@43.5763511,39.7267893,18.13z/data=!3m1!5s0x40f5c981054aade7:0xd56d39fb21e36bea!4m11!3m10!1s0x40f5c98119c0a57d:0xcde63de0ff0f8ab3!5m2!4m1!1i2!8m2!3d43.5762002!4d39.7260598!9m1!1b1!16s%2Fg%2F122_4qdc?entry=ttu&g_ep=EgoyMDI2MDUyNy4wIKXMDSoASAFQAw%3D%3D"
        ],
        "limit": 50
    },
    "yandex_maps": {
        "urls": [
            "https://yandex.ru/maps/org/city_park_hotel/124982210500/reviews/?indoorLevel=1&ll=39.726044%2C43.576193&z=17"
        ],
        "limit": 50
    },
    # Можно добавить другие источники при необходимости
    # "booking.com": {
    #     "urls": ["https://www.booking.com/hotel/ru/..."],
    #     "limit": 50
    # },
    # "ostrovok": {
    #     "urls": ["https://ostrovok.ru/hotel/..."],
    #     "limit": 50
    # }
}


async def run_full_pipeline():
    """Запуск полного пайплайна обработки отзывов"""
    
    print("=" * 60)
    print("ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА ОБРАБОТКИ ОТЗЫВОВ")
    print("=" * 60)
    
    # 1. Парсинг отзывов с указанных источников
    print("\n[1/5] Парсинг отзывов с TripAdvisor, Google Maps, Яндекс.Карт...")
    parser_service = ReviewParserService()
    parsed_count = await parser_service.parse_all_sources(SOURCES_CONFIG, save_to_db=True)
    print(f"✓ Спарсено {parsed_count} отзывов")
    
    # 2. Генерация синтетических отзывов для дообучения
    print("\n[2/5] Генерация 3000 синтетических отзывов...")
    synthetic_generator = SyntheticReviewsGenerator()
    synthetic_reviews = synthetic_generator.generate_batch(3000)
    
    # Сохранение синтетических отзывов в БД
    db = DatabaseManager()
    saved_synthetic = db.save_synthetic_reviews(synthetic_reviews)
    print(f"✓ Сгенерировано и сохранено {saved_synthetic} синтетических отзывов")
    
    # 3. Анализ тональности через ruBERT
    print("\n[3/5] Анализ тональности через ruBERT...")
    analyzer = RuBertAnalyzer()
    
    # Получаем все отзывы из БД
    all_reviews = db.get_all_reviews(limit=None)
    analyzed_count = 0
    
    for review in all_reviews:
        if not review.sentiment:  # Если ещё не анализирован
            result = analyzer.analyze_sentiment(review.review_text)
            db.update_review_sentiment(
                review.id, 
                sentiment=result['sentiment'],
                confidence=result['confidence'],
                topics=result.get('topics', [])
            )
            analyzed_count += 1
    
    print(f"✓ Проанализировано {analyzed_count} отзывов")
    
    # 4. Генерация ответов через ruGPT-3
    print("\n[4/5] Генерация ответов через ruGPT-3...")
    response_gen = ResponseGenerator()
    
    # Получаем отзывы без ответов
    reviews_without_response = db.get_reviews_without_response()
    generated_count = 0
    
    for review in reviews_without_response:
        # Генерация ответа с погружением в контекст
        response = response_gen.generate_response(
            review_text=review.review_text,
            sentiment=review.sentiment,
            rating=review.rating,
            platform=review.platform.value,
            topics=review.topics or []
        )
        
        if response:
            db.save_response(review.id, response)
            generated_count += 1
    
    print(f"✓ Сгенерировано {generated_count} ответов")
    
    # 5. Итоговая статистика
    print("\n[5/5] Итоговая статистика:")
    stats = db.get_statistics()
    print(f"  - Всего отзывов: {stats['total_reviews']}")
    print(f"  - Позитивных: {stats['positive_reviews']}")
    print(f"  - Негативных: {stats['negative_reviews']}")
    print(f"  - Нейтральных: {stats['neutral_reviews']}")
    print(f"  - С ответами: {stats['reviews_with_response']}")
    print(f"  - Без ответов: {stats['reviews_without_response']}")
    
    print("\n" + "=" * 60)
    print("ПАЙПЛАЙН ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 60)
    print("\nТеперь отзывы с метками доступны в системе менеджера.")
    print("Менеджер может просматривать отзывы и использовать сгенерированные ответы.")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
