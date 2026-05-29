from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import SessionLocal, SentimentLabel, RawReview, GeneratedResponse

class ResponseGenerator:
    def __init__(self, model_name="cointegrated/rubert-tiny2"):
        """
        Инициализация легкой модели для генерации ответов
        Используем rubert-tiny2 из-за ограничений по памяти
        """
        print(f"🔄 Загрузка модели {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()
        print("✅ Модель загружена!")

    def generate_response(self, review_text, sentiment, max_length=150):
        """Генерация ответа на отзыв"""
        
        # Формируем промпт в зависимости от тональности
        if sentiment == 'positive':
            prompt = f"Отзыв клиента: {review_text}\n\nНапишите вежливый благодарственный ответ от имени отеля:"
        elif sentiment == 'negative':
            prompt = f"Отзыв клиента: {review_text}\n\nНапишите вежливый ответ с извинениями и предложением решения от имени отеля:"
        else:  # neutral
            prompt = f"Отзыв клиента: {review_text}\n\nНапишите нейтральный вежливый ответ от имени отеля:"
        
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=300)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length + len(inputs['input_ids'][0]),
                min_length=50,
                num_beams=5,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Извлекаем только ответ (после промпта)
        response = generated_text.replace(prompt, "").strip()
        
        # Убираем возможные артефакты
        if "\n\n" in response:
            response = response.split("\n\n")[0]
        
        return response[:500]  # Ограничиваем длину

    def generate_for_all_reviews(self, batch_size=5):
        """Генерация ответов для всех отзывов без ответов"""
        db = SessionLocal()
        try:
            # Получаем все отзывы с метками, но без ответов
            # Упрощенная версия - работаем только с raw_reviews
            raw_reviews_with_labels = db.query(RawReview).join(
                SentimentLabel, RawReview.id == SentimentLabel.review_id
            ).filter(
                ~RawReview.id.in_(
                    db.query(GeneratedResponse.review_id)
                )
            ).all()
            
            total = len(raw_reviews_with_labels)
            print(f"\n📊 Найдено {total} отзывов для генерации ответов")
            
            processed = 0
            
            # Обрабатываем сырые отзывы
            for review in raw_reviews_with_labels:
                label = db.query(SentimentLabel).filter(
                    SentimentLabel.review_id == review.id
                ).first()
                
                response_text = self.generate_response(review.content, label.sentiment)
                
                response = GeneratedResponse(
                    review_id=review.id,
                    response_text=response_text,
                    created_at=datetime.now()
                )
                
                db.add(response)
                processed += 1
                
                if processed % batch_size == 0:
                    db.commit()
                    print(f"✓ Сгенерировано {processed}/{total} ответов")
            
            db.commit()
            print(f"\n✅ Генерация завершена! Создано {processed} ответов")
            
        finally:
            db.close()


if __name__ == "__main__":
    generator = ResponseGenerator()
    generator.generate_for_all_reviews()
    print("\n🎉 Все ответы сгенерированы!")
