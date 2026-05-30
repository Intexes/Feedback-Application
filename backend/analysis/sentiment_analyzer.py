"""
Модуль анализа тональности на основе ruBERT.
Классифицирует отзывы по тональности и темам.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any, Tuple
import numpy as np

class RuBertSentimentAnalyzer:
    """Анализатор тональности на базе ruBERT"""
    
    def __init__(self, model_name: str = "blanchefort/rubert-base-cased-sentiment-rusentiment"):
        """
        Инициализация модели ruBERT для анализа тональности.
        :param model_name: Название модели HuggingFace
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Загрузка модели {model_name} на {self.device}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            self.label_map = {0: "negative", 1: "neutral", 2: "positive"}
            print("Модель успешно загружена!")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            print("Используется режим эмуляции (mock mode)")
            self.model = None
            self.tokenizer = None
            self.label_map = {0: "negative", 1: "neutral", 2: "positive"}

    def predict_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Предсказывает тональность текста.
        :param text: Текст отзыва
        :return: (тональность, уверенность)
        """
        if self.model is None or self.tokenizer is None:
            return self._mock_predict(text)
        
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted = torch.max(probabilities, 1)
            
            sentiment = self.label_map[predicted.item()]
            conf_score = confidence.item()
            
        return sentiment, conf_score

    def _mock_predict(self, text: str) -> Tuple[str, float]:
        """Эмуляция предсказания для тестирования без модели"""
        text_lower = text.lower()
        
        positive_words = ["отличный", "прекрасный", "хороший", "рекомендую", "доволен", "замечательно", "восхитительно"]
        negative_words = ["ужасный", "плохой", "разочарован", "катастрофа", "грязь", "хамство", "не рекомендую"]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive", 0.8
        elif neg_count > pos_count:
            return "negative", 0.8
        else:
            return "neutral", 0.6

    def analyze_batch(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Анализирует.batch отзывов.
        :param reviews: Список отзывов
        :return: Отзывы с добавленными метками тональности
        """
        print(f"Анализ {len(reviews)} отзывов...")
        
        for i, review in enumerate(reviews):
            if i % 500 == 0 and i > 0:
                print(f"Обработано {i}/{len(reviews)} отзывов")
                
            sentiment, confidence = self.predict_sentiment(review["text"])
            review["sentiment"] = sentiment
            review["sentiment_confidence"] = confidence
            
            # Определение темы (упрощенно по ключевым словам)
            review["topic"] = self._detect_topic(review["text"])
        
        print("Анализ завершен!")
        return reviews

    def _detect_topic(self, text: str) -> str:
        """Определяет тему отзыва"""
        text_lower = text.lower()
        
        topics_keywords = {
            "номер": ["номер", "комната", "кровать", "душ", "ванна", "окно", "кондиционер"],
            "завтрак": ["завтрак", "еда", "кухня", "ресторан", "шведский стол", "кофе"],
            "персонал": ["персонал", "администратор", "горничная", "сотрудник", "обслуживание", "ресепшн"],
            "локация": ["локация", "расположение", "центр", "метро", "транспорт", "район"],
            "чистота": ["чистота", "грязь", "уборка", "пыль", "порядок"],
            "цена": ["цена", "стоимость", "деньги", "оплата", "дорого", "дешево"],
            "wi-fi": ["wi-fi", "интернет", "wifi", "сеть", "подключение"]
        }
        
        topic_scores = {}
        for topic, keywords in topics_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            topic_scores[topic] = score
        
        if max(topic_scores.values()) == 0:
            return "общее"
        
        return max(topic_scores, key=topic_scores.get)

if __name__ == "__main__":
    # Тестирование
    analyzer = RuBertSentimentAnalyzer()
    
    test_reviews = [
        {"text": "Отличный номер, очень чисто и персонал вежливый!", "id": "1"},
        {"text": "Ужасное обслуживание, грязь в ванной, больше не приеду.", "id": "2"},
        {"text": "Нормальный отель, ничего особенного, но и не плохо.", "id": "3"}
    ]
    
    results = analyzer.analyze_batch(test_reviews)
    for r in results:
        print(f"Текст: {r['text']}")
        print(f"Тональность: {r.get('sentiment')}, Тема: {r.get('topic')}")
        print("---")
