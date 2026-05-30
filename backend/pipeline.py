"""
Основной пайплайн обработки отзывов.
1. Парсинг отзывов с платформ (Booking, Ostrovok, Manul, Google, Yandex)
2. Генерация синтетических отзывов (3000 шт)
3. Объединение реальных и синтетических отзывов
4. Анализ тональности через ruBERT
5. Генерация ответов через ruGPT-3
6. Сохранение в БД
"""
import asyncio
from typing import List, Dict, Any
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers.review_collectors import run_all_parsers
from parsers.synthetic_generator import SyntheticReviewGenerator
from analysis.sentiment_analyzer import RuBertSentimentAnalyzer
from generation.response_generator import RuGPT3ResponseGenerator
from database.db_manager import DatabaseManager


class ReviewProcessingPipeline:
    """Основной пайплайн обработки отзывов"""
    
    def __init__(self, db_path: str = "reviews.db"):
        self.db = DatabaseManager(db_path)
        self.sentiment_analyzer = RuBertSentimentAnalyzer()
        self.response_generator = RuGPT3ResponseGenerator()
        self.synthetic_generator = SyntheticReviewGenerator()
        
    async def run_full_pipeline(self, hotel_id: str, synthetic_count: int = 3000):
        """
        Запускает полный цикл обработки отзывов.
        :param hotel_id: ID отеля для парсинга
        :param synthetic_count: Количество синтетических отзывов
        """
        print("=" * 60)
        print("ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА ОБРАБОТКИ ОТЗЫВОВ")
        print("=" * 60)
        
        # Шаг 1: Парсинг реальных отзывов
        print("\n[1/5] Парсинг отзывов с платформ...")
        real_reviews = await run_all_parsers(hotel_id)
        print(f"Собрано {len(real_reviews)} реальных отзывов")
        
        # Шаг 2: Генерация синтетических отзывов
        print("\n[2/5] Генерация синтетических отзывов...")
        synthetic_reviews = self.synthetic_generator.generate(synthetic_count)
        print(f"Сгенерировано {len(synthetic_reviews)} синтетических отзывов")
        
        # Шаг 3: Объединение отзывов
        print("\n[3/5] Объединение отзывов...")
        all_reviews = real_reviews + synthetic_reviews
        print(f"Всего отзывов для анализа: {len(all_reviews)}")
        
        # Шаг 4: Анализ тональности через ruBERT
        print("\n[4/5] Анализ тональности и тем через ruBERT...")
        analyzed_reviews = self.sentiment_analyzer.analyze_batch(all_reviews)
        
        # Шаг 5: Генерация ответов через ruGPT-3
        print("\n[5/5] Генерация ответов через ruGPT-3...")
        # Генерируем ответы только для реальных отзывов (не для синтетических)
        real_analyzed = [r for r in analyzed_reviews if not r.get("is_synthetic", False)]
        synthetic_analyzed = [r for r in analyzed_reviews if r.get("is_synthetic", False)]
        
        print(f"Генерация ответов для {len(real_analyzed)} реальных отзывов...")
        responded_reviews = self.response_generator.generate_batch(real_analyzed)
        
        # Объединяем обратно
        final_reviews = responded_reviews + synthetic_analyzed
        
        # Сохранение в БД
        print("\n[ФИНАЛ] Сохранение результатов в базу данных...")
        self.db.save_reviews(final_reviews)
        
        print("\n" + "=" * 60)
        print("ПАЙПЛАЙН ЗАВЕРШЕН УСПЕШНО!")
        print(f"Всего обработано: {len(final_reviews)} отзывов")
        print(f"Реальных с ответами: {len(responded_reviews)}")
        print(f"Синтетических (для обучения): {len(synthetic_analyzed)}")
        print("=" * 60)
        
        return final_reviews
    
    def get_pending_responses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает отзывы, требующие ответа менеджера"""
        return self.db.get_reviews_without_response(limit)
    
    def save_response(self, review_id: str, response_text: str, manager_id: str = "system"):
        """Сохраняет ответ менеджера"""
        self.db.update_review_response(review_id, response_text, manager_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику по отзывам"""
        return self.db.get_statistics()


async def main():
    """Точка входа для запуска пайплайна"""
    pipeline = ReviewProcessingPipeline()
    
    # Запуск полного пайплайна для тестового отеля
    await pipeline.run_full_pipeline(hotel_id="test_hotel_123", synthetic_count=3000)
    
    # Получение статистики
    stats = pipeline.get_statistics()
    print("\nСтатистика:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
