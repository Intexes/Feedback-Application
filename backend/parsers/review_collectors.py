"""
Модуль парсеров для различных платформ: Booking, Ostrovok, Manul, Google, Yandex.
Каждый парсер возвращает унифицированный формат данных.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ReviewParserBase:
    """Базовый класс для парсеров"""
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

class BookingParser(ReviewParserBase):
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        print(f"[Booking] Парсинг отеля {hotel_id}...")
        # Имитация задержки сети и реального парсинга
        await asyncio.sleep(1)
        return self._generate_mock_data(limit, source="booking")

class OstrovokParser(ReviewParserBase):
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        print(f"[Ostrovok] Парсинг отеля {hotel_id}...")
        await asyncio.sleep(1)
        return self._generate_mock_data(limit, source="ostrovok")

class ManulParser(ReviewParserBase):
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        print(f"[Manul] Парсинг отеля {hotel_id}...")
        await asyncio.sleep(1)
        return self._generate_mock_data(limit, source="manul")

class GoogleMapsParser(ReviewParserBase):
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        print(f"[Google Maps] Парсинг места {hotel_id}...")
        await asyncio.sleep(1)
        return self._generate_mock_data(limit, source="google")

class YandexMapsParser(ReviewParserBase):
    async def parse(self, hotel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        print(f"[Yandex Maps] Парсинг места {hotel_id}...")
        await asyncio.sleep(1)
        return self._generate_mock_data(limit, source="yandex")

    def _generate_mock_data(self, count: int, source: str) -> List[Dict[str, Any]]:
        """Генерация тестовых данных, имитирующих реальный парсинг"""
        reviews = []
        topics = ["номер", "завтрак", "персонал", "локация", "чистота", "цена", "wi-fi"]
        sentiments = ["positive", "negative", "neutral"]
        
        for i in range(count):
            sentiment = random.choice(sentiments)
            topic = random.choice(topics)
            
            if sentiment == "positive":
                text = f"Отличный {topic}! Очень понравилось обслуживание в {source}. Рекомендую."
                rating = random.randint(4, 5)
            elif sentiment == "negative":
                text = f"Ужасный {topic}. Разочарован уровнем сервиса в {source}. Больше не приеду."
                rating = random.randint(1, 2)
            else:
                text = f"{topic} был средним. Ничего особенного в {source}, но и не плохо."
                rating = 3

            reviews.append({
                "id": f"{source}_{random.randint(10000, 99999)}",
                "source": source,
                "author": f"User_{random.randint(1, 1000)}",
                "text": text,
                "rating": rating,
                "date": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "raw_data": {} # Место для сырых данных если нужно
            })
        return reviews

async def run_all_parsers(hotel_id: str, sources: List[str] = None) -> List[Dict[str, Any]]:
    """Запускает парсинг со всех указанных источников"""
    if sources is None:
        sources = ["booking", "ostrovok", "manul", "google", "yandex"]
    
    parsers_map = {
        "booking": BookingParser(),
        "ostrovok": OstrovokParser(),
        "manul": ManulParser(),
        "google": GoogleMapsParser(),
        "yandex": YandexMapsParser()
    }
    
    tasks = []
    for source in sources:
        if source in parsers_map:
            tasks.append(parsers_map[source].parse(hotel_id))
    
    results = await asyncio.gather(*tasks)
    
    all_reviews = []
    for result in results:
        all_reviews.extend(result)
    
    return all_reviews

if __name__ == "__main__":
    # Тестовый запуск
    reviews = asyncio.run(run_all_parsers("hotel_123"))
    print(f"Всего собрано отзывов: {len(reviews)}")
    for r in reviews[:3]:
        print(r)
