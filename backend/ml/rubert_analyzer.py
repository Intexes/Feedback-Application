from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from typing import List, Tuple, Dict
import json

from models import SentimentType, ReviewClass


class RuBERTAnalyzer:
    """Анализ тональности и классификация отзывов с помощью ruBERT"""
    
    def __init__(self, model_path: str = "cointegrated/rubert-base-cased-nli-threeway"):
        """
        Инициализация модели ruBERT для анализа тональности
        
        Args:
            model_path: Путь к модели или название в HuggingFace
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Маппинг лейблов для тональности (зависит от модели)
        self.sentiment_labels = ["negative", "neutral", "positive"]
        
        # Классы для классификации тем отзыва
        self.class_topics = [
            "сервис", "чистота", "расположение", "еда", 
            "цена", "персонал", "номер", "удобства"
        ]
        self.class_map = {
            "сервис": ReviewClass.SERVICE,
            "персонал": ReviewClass.STAFF,
            "чистота": ReviewClass.CLEANLINESS,
            "номер": ReviewClass.ROOM,
            "расположение": ReviewClass.LOCATION,
            "еда": ReviewClass.FOOD,
            "цена": ReviewClass.PRICE,
            "удобства": ReviewClass.AMENITIES,
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[SentimentType, float]:
        """
        Анализ тональности текста
        
        Args:
            text: Текст отзыва
            
        Returns:
            Tuple[SentimentType, float]: Тональность и уверенность (0-1)
        """
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = F.softmax(outputs.logits, dim=-1)[0]
            
        confidence, predicted_class = torch.max(probabilities, 0)
        
        sentiment = SentimentType(self.sentiment_labels[predicted_class.item()])
        confidence_score = confidence.item()
        
        return sentiment, confidence_score
    
    def classify_topics(self, text: str, threshold: float = 0.6) -> List[ReviewClass]:
        """
        Классификация тем отзыва (мультилейбл)
        
        Args:
            text: Текст отзыва
            threshold: Порог уверенности для назначения класса
            
        Returns:
            List[ReviewClass]: Список классов, которые относятся к отзыву
        """
        # Упрощенная реализация через ключевые слова
        # В продакшене можно использовать отдельную модель для мультилейбл классификации
        text_lower = text.lower()
        
        detected_classes = []
        keyword_mapping = {
            ReviewClass.SERVICE: ["сервис", "обслуживание", "ресепшн", "заселение", "выселение"],
            ReviewClass.STAFF: ["персонал", "менеджер", "сотрудник", "администратор", "горничная"],
            ReviewClass.CLEANLINESS: ["чистот", "грязн", "уборк", "пыль", "пятн"],
            ReviewClass.ROOM: ["номер", "комната", "кровать", "душ", "туалет", "балкон"],
            ReviewClass.LOCATION: ["расположен", "центр", "метро", "транспорт", "район", "адрес"],
            ReviewClass.FOOD: ["завтрак", "еда", "кухня", "ресторан", "питание", "вкусн"],
            ReviewClass.PRICE: ["цена", "стоимость", "дорого", "дешево", "оплата", "деньги"],
            ReviewClass.AMENITIES: ["wi-fi", "интернет", "парковк", "бассейн", "спортзал", "кондиционер"],
        }
        
        for review_class, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_classes.append(review_class)
                    break
        
        return detected_classes if detected_classes else [ReviewClass.OTHER]
    
    def analyze_review(self, text: str) -> Dict:
        """
        Полный анализ отзыва
        
        Args:
            text: Текст отзыва
            
        Returns:
            Dict: Результаты анализа (тональность, уверенность, классы)
        """
        sentiment, confidence = self.analyze_sentiment(text)
        classes = self.classify_topics(text)
        
        return {
            "sentiment": sentiment.value,
            "sentiment_score": round(confidence, 4),
            "classes": [c.value for c in classes],
            "classes_json": json.dumps([c.value for c in classes])
        }


# Singleton instance
_analyzer_instance = None


def get_analyzer(model_path: str = None) -> RuBERTAnalyzer:
    """Получить экземпляр анализатора (singleton)"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = RuBERTAnalyzer(model_path or "cointegrated/rubert-base-cased-nli-threeway")
    return _analyzer_instance
