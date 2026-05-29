import os
import sys
from datetime import datetime

# Добавляем корень проекта в путь
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.models import SessionLocal, RawReview, SentimentLabel, Base, engine
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

# Создаем таблицы, если их нет (на случай если sentiment_labels еще нет)
Base.metadata.create_all(bind=engine)

# --- Конфигурация модели ---
# Используем легкую модель для тональности (около 50MB)
MODEL_NAME = "cointegrated/rubert-tiny-sentiment-balanced"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Загрузка модели {MODEL_NAME} на устройстве: {device}...")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()
    print("✅ Модель успешно загружена!")
except Exception as e:
    print(f"❌ Ошибка загрузки модели: {e}")
    print("Убедитесь, что есть интернет для первой загрузки модели.")
    sys.exit(1)

# Маппинг лейблов для rubert-tiny-sentiment-balanced
# Классы: negative (0), neutral (1), positive (2)
label_map = {0: "negative", 1: "neutral", 2: "positive"}

def predict_sentiment(text):
    """Возвращает метку и уверенность."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        confidence, predicted_class = torch.max(probabilities, dim=1)
        
        pred_label_id = predicted_class.item()
        conf_score = confidence.item()
        
        # Для этой модели маппинг может отличаться, проверим по логике:
        # Обычно в таких моделях порядок классов совпадает с индексом.
        # Если модель blanchefort/rubert-base-cased-sentiment, то классы: ['NEG', 'NEU', 'POS']
        # Индексы: 0, 1, 2.
        
        sentiment_text = label_map.get(pred_label_id, "unknown")
        return sentiment_text, conf_score

def analyze_reviews():
    db = SessionLocal()
    
    # Получаем все отзывы, для которых еще нет анализа
    # Мы будем искать отзывы, у которых нет записи в SentimentLabel с этим review_id
    all_reviews = db.query(RawReview).all()
    
    print(f"\n📊 Найдено отзывов для анализа: {len(all_reviews)}")
    
    processed_count = 0
    
    for review in all_reviews:
        # Проверяем, есть ли уже метка
        existing_label = db.query(SentimentLabel).filter_by(review_id=review.id).first()
        if existing_label:
            continue # Пропускаем, если уже проанализировано
            
        print(f"⏳ Анализ отзыва #{review.id}: {review.content[:50]}...")
        
        try:
            sentiment, confidence = predict_sentiment(review.content)
            
            new_label = SentimentLabel(
                review_id=review.id,
                sentiment=sentiment,
                confidence=confidence,
                created_at=datetime.now()
            )
            
            db.add(new_label)
            processed_count += 1
            
            if processed_count % 5 == 0:
                db.commit() # Периодически сохраняем, чтобы не потерять прогресс
                print(f"✓ Сохранено {processed_count} результатов...")
                
        except Exception as e:
            print(f"⚠️ Ошибка при анализе отзыва {review.id}: {e}")
            continue
            
    db.commit()
    db.close()
    
    print(f"\n✅ Готово! Проанализировано {processed_count} отзывов.")
    print("Данные сохранены в таблицу sentiment_labels.")

if __name__ == "__main__":
    analyze_reviews()