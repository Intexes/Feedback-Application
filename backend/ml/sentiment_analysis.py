from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from torch.nn.functional import softmax
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import SessionLocal, SentimentLabel, RawReview, SyntheticReview

class SentimentAnalyzer:
    def __init__(self, model_name="blanchefort/rubert-base-cased-sentiment-rusentiplex"):
        """
        Инициализация модели ruBert для анализа тональности
        Модель: blanchefort/rubert-base-cased-sentiment-rusentiplex
        Классы: negative, neutral, positive
        """
        print(f"🔄 Загрузка модели {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
        print("✅ Модель загружена!")

    def predict_sentiment(self, text, max_length=512):
        """Предсказание тональности для одного отзыва"""
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=max_length,
            padding=True
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = softmax(outputs.logits, dim=1)[0]
            predicted_class = torch.argmax(probabilities).item()
            
        return {
            'sentiment': self.label_map[predicted_class],
            'confidence_score': probabilities[predicted_class].item(),
            'all_probabilities': {
                'negative': probabilities[0].item(),
                'neutral': probabilities[1].item(),
                'positive': probabilities[2].item()
            }
        }

    def analyze_raw_reviews(self, batch_size=10):
        """Анализ всех сырых отзывов в БД"""
        db = SessionLocal()
        try:
            reviews = db.query(RawReview).filter(
                ~RawReview.id.in_(
                    db.query(SentimentLabel.review_id).filter(
                        SentimentLabel.review_type == 'raw'
                    )
                )
            ).all()
            
            print(f"\n📊 Найдено {len(reviews)} отзывов для анализа")
            
            processed = 0
            for i, review in enumerate(reviews):
                result = self.predict_sentiment(review.review_text)
                
                label = SentimentLabel(
                    review_id=review.id,
                    review_type='raw',
                    sentiment=result['sentiment'],
                    confidence_score=result['confidence_score'],
                    model_version="blanchefort/rubert-base-cased-sentiment-rusentiplex"
                )
                
                db.add(label)
                processed += 1
                
                if processed % batch_size == 0:
                    db.commit()
                    print(f"✓ Обработано {processed}/{len(reviews)} отзывов")
            
            db.commit()
            print(f"\n✅ Анализ завершён! Обработано {processed} отзывов")
            
        finally:
            db.close()

    def analyze_synthetic_reviews(self, batch_size=10):
        """Анализ синтетических отзывов"""
        db = SessionLocal()
        try:
            reviews = db.query(SyntheticReview).filter(
                ~SyntheticReview.id.in_(
                    db.query(SentimentLabel.review_id).filter(
                        SentimentLabel.review_type == 'synthetic'
                    )
                )
            ).all()
            
            print(f"\n📊 Найдено {len(reviews)} синтетических отзывов для анализа")
            
            processed = 0
            for review in reviews:
                result = self.predict_sentiment(review.review_text)
                
                label = SentimentLabel(
                    review_id=review.id,
                    review_type='synthetic',
                    sentiment=result['sentiment'],
                    confidence_score=result['confidence_score'],
                    model_version="blanchefort/rubert-base-cased-sentiment-rusentiplex"
                )
                
                db.add(label)
                processed += 1
            
            db.commit()
            print(f"\n✅ Анализ синтетических отзывов завершён! Обработано {processed}")
            
        finally:
            db.close()


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    print("\n🔍 Анализ сырых отзывов...")
    analyzer.analyze_raw_reviews()
    
    print("\n🔍 Анализ синтетических отзывов...")
    analyzer.analyze_synthetic_reviews()
    
    print("\n🎉 Все отзывы проанализированы!")
