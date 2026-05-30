from typing import List, Dict, Any
import random
from datetime import datetime, timedelta
import json

from models import Review, PlatformSource, SentimentType, ReviewClass, SessionLocal


class SyntheticDataGenerator:
    """Генерация синтетических отзывов для дообучения модели"""
    
    def __init__(self):
        # Шаблоны для различных классов и тональностей
        self.templates = {
            # Негативные отзывы
            (SentimentType.NEGATIVE.value, "service"): [
                "Ужасный сервис на ресепшене. Заселение задержали на {hours} часа, менеджер даже не извинился.",
                "Обслуживание на нулевом уровне. Персонал игнорирует запросы гостей.",
                "Сервис просто отвратительный. Никто не реагирует на жалобы.",
                "Разочарован обслуживанием. Ожидал гораздо лучшего отношения.",
            ],
            (SentimentType.NEGATIVE.value, "cleanliness"): [
                "В номере было грязно. На полу волосы, в ванной плесень.",
                "Уборка оставляет желать лучшего. Пыль на мебели, пятна на ковре.",
                "Чистота номера не соответствует заявленному уровню отеля.",
                "Грязные полотенца, застиранное постельное белье. Очень неприятно.",
            ],
            (SentimentType.NEGATIVE.value, "room"): [
                "Номер маленький и темный. Кондиционер не работает.",
                "Кровать неудобная, подушки старые. Не смог нормально выспаться.",
                "В номере сломана мебель, сантехника течет.",
                "Окна не открываются, в душно. Номер требует ремонта.",
            ],
            (SentimentType.NEGATIVE.value, "food"): [
                "Завтрак ужасный. Еда холодная, выбор минимальный.",
                "Ресторан не соответствует уровню отеля. Блюда невкусные.",
                "Питание однообразное, продукты несвежие.",
                "Заказ принесли через час, еда остыла.",
            ],
            (SentimentType.NEGATIVE.value, "staff"): [
                "Персонал грубый и необученный. Менеджер хамит гостям.",
                "Администратор на ресепшене вела себя непрофессионально.",
                "Горничная ворчала когда попросил дополнительные полотенца.",
                "Сотрудники не знают английский язык, общение затруднено.",
            ],
            
            # Нейтральные отзывы
            (SentimentType.NEUTRAL.value, "location"): [
                "Расположение удобное, но шумно из-за дороги рядом.",
                "Отель в центре, но метро далеко. Приходится ходить пешком.",
                "Район спокойный, но мало ресторанов поблизости.",
                "Транспортная доступность средняя, такси ждать долго.",
            ],
            (SentimentType.NEUTRAL.value, "price"): [
                "Цена соответствует качеству. Не дешево, но и не дорого.",
                "Соотношение цена-качество среднее. Есть варианты лучше.",
                "За эти деньги ожидал большего, но в целом нормально.",
                "Цены адекватные для этого района.",
            ],
            (SentimentType.NEUTRAL.value, "amenities"): [
                "Wi-Fi работает нестабильно. Бассейн маленький.",
                "Спортзал есть, но оборудование старое.",
                "Парковка платная, что неудобно. Кондиционер в лобби не охлаждает.",
                "Удобства стандартные, ничего особенного.",
            ],
            
            # Положительные отзывы
            (SentimentType.POSITIVE.value, "service"): [
                "Превосходный сервис! Персонал очень внимательный и дружелюбный.",
                "Обслуживание на высшем уровне. Все запросы выполняли мгновенно.",
                "Сервис потрясающий. Чувствуешь себя как дома.",
                "Лучшее обслуживание среди всех отелей где был!",
            ],
            (SentimentType.POSITIVE.value, "cleanliness"): [
                "Идеальная чистота в номере. Убирались каждый день качественно.",
                "Номер сияет чистотой. Видно что следят за порядком.",
                "Ванная комната безупречно чистая. Полотенца свежие.",
                "Чистота на пятерку! Даже мелочи учтены.",
            ],
            (SentimentType.POSITIVE.value, "room"): [
                "Номер просторный и светлый. Вид из окна потрясающий!",
                "Кровать очень удобная, спал как младенец. Номер современный.",
                "Ремонт свежий, мебель новая. В номере есть все необходимое.",
                "Балкон с видом на море - это нечто! Номер превзошел ожидания.",
            ],
            (SentimentType.POSITIVE.value, "food"): [
                "Завтраки великолепные! Огромный выбор блюд, все вкусное.",
                "Ресторан отличный. Шеф-повар молодец, блюда как в мишленовском ресторане.",
                "Питание разнообразное и качественное. Фрукты свежие.",
                "Завтрак включен и это большой плюс. Еда вкусная и сытная.",
            ],
            (SentimentType.POSITIVE.value, "staff"): [
                "Персонал замечательный! Все улыбаются и помогают.",
                "Администратор Мария очень помогла с экскурсиями. Спасибо!",
                "Горничные молодцы, всегда приветливые. Оставляют приятные мелочи.",
                "Команда отеля профессиональная. Чувствуется любовь к работе.",
            ],
            (SentimentType.POSITIVE.value, "location"): [
                "Расположение идеальное! Метро рядом, магазины в шаговой доступности.",
                "Центр города в 5 минутах ходьбы. Очень удобно.",
                "Тихий район но при этом все рядом. Отличное место.",
                "До пляжа 2 минуты. Локация просто супер!",
            ],
        }
        
        self.names = [
            "Алексей", "Мария", "Дмитрий", "Елена", "Сергей", 
            "Ольга", "Андрей", "Наталья", "Игорь", "Екатерина",
            "Павел", "Анна", "Максим", "Юлия", "Александр"
        ]
        
        self.platforms = list(PlatformSource)
    
    def generate_synthetic_review(
        self, 
        sentiment: str = None, 
        class_type: str = None
    ) -> Dict[str, Any]:
        """
        Генерация одного синтетического отзыва
        
        Args:
            sentiment: Тональность (positive/negative/neutral)
            class_type: Класс отзыва
            
        Returns:
            Dict: Данные отзыва
        """
        # Если параметры не указаны, выбираем случайно
        if not sentiment or not class_type:
            keys = list(self.templates.keys())
            sentiment, class_type = random.choice(keys)
        
        key = (sentiment, class_type)
        
        # Получаем шаблоны
        templates = self.templates.get(key, self.templates[(SentimentType.NEGATIVE.value, "service")])
        review_text = random.choice(templates)
        
        # Заполняем переменные в шаблоне
        review_text = review_text.format(
            hours=random.randint(1, 3),
            days=random.randint(1, 5)
        )
        
        # Генерируем оценку на основе тональности
        if sentiment == SentimentType.POSITIVE.value:
            rating = random.choice([4, 5, 5, 5])
        elif sentiment == SentimentType.NEGATIVE.value:
            rating = random.choice([1, 1, 2, 2])
        else:
            rating = random.choice([2, 3, 3, 4])
        
        # Имя автора
        author_name = f"{random.choice(self.names)} {chr(random.randint(65, 90))}."
        
        # Платформа
        platform = random.choice([p for p in self.platforms if p != PlatformSource.MANUAL])
        
        # Дата (случайная в последние 30 дней)
        review_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        
        return {
            "platform": platform,
            "author_name": author_name,
            "rating": rating,
            "review_text": review_text,
            "review_date": review_date,
            "sentiment": sentiment,
            "classes": [class_type],
            "is_synthetic": True
        }
    
    def generate_batch(
        self, 
        count: int = 3000,
        distribution: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерация пакета синтетических отзывов
        
        Args:
            count: Количество отзывов
            distribution: Распределение по тональностям
                          {"positive": 0.6, "neutral": 0.2, "negative": 0.2}
            
        Returns:
            List[Dict]: Список отзывов
        """
        if distribution is None:
            distribution = {
                "positive": 0.6,
                "neutral": 0.15,
                "negative": 0.25
            }
        
        reviews = []
        
        # Классы для каждой тональности
        class_distribution = {
            "positive": ["service", "cleanliness", "room", "food", "staff", "location"],
            "neutral": ["location", "price", "amenities"],
            "negative": ["service", "cleanliness", "room", "food", "staff"]
        }
        
        for sentiment, prob in distribution.items():
            sentiment_count = int(count * prob)
            classes = class_distribution.get(sentiment, ["service"])
            
            for _ in range(sentiment_count):
                class_type = random.choice(classes)
                review_data = self.generate_synthetic_review(sentiment, class_type)
                reviews.append(review_data)
        
        # Перемешиваем
        random.shuffle(reviews)
        
        return reviews
    
    def save_to_db(self, count: int = 3000) -> int:
        """
        Генерация и сохранение синтетических отзывов в БД
        
        Args:
            count: Количество отзывов для генерации
            
        Returns:
            int: Количество сохраненных отзывов
        """
        db = SessionLocal()
        try:
            reviews_data = self.generate_batch(count)
            
            saved_count = 0
            for data in reviews_data:
                review = Review(
                    platform=data["platform"],
                    external_id=f"synth_{random.randint(100000, 999999)}",
                    author_name=data["author_name"],
                    rating=data["rating"],
                    review_text=data["review_text"],
                    review_date=data["review_date"],
                    sentiment=SentimentType(data["sentiment"]),
                    sentiment_score=random.uniform(0.7, 0.99),
                    classes=json.dumps(data["classes"]),
                    is_synthetic=True,
                    status="analyzed"
                )
                db.add(review)
                saved_count += 1
            
            db.commit()
            return saved_count
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


# Singleton
_generator_instance = None


def get_synthetic_generator() -> SyntheticDataGenerator:
    """Получить экземпляр генератора (singleton)"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = SyntheticDataGenerator()
    return _generator_instance
