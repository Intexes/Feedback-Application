from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import SessionLocal, SentimentLabel, RawReview, SyntheticReview, GeneratedResponse

class ResponseGenerator:
    def __init__(self, model_name="ai-forever/rugpt3large_based_on_gpt2"):
        """
        Инициализация модели ruGPT для генерации ответов
        Модель: ai-forever/rugpt3large_based_on_gpt2
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
            raw_reviews_with_labels = db.query(RawReview).join(SentimentLabel).filter(
                SentimentLabel.review_type == 'raw',
                ~RawReview.id.in_(
                    db.query(GeneratedResponse.review_id).filter(
                        GeneratedResponse.review_type == 'raw'
                    )
                )
            ).all()
            
            synthetic_reviews_with_labels = db.query(SyntheticReview).join(SentimentLabel).filter(
                SentimentLabel.review_type == 'synthetic',
                ~SyntheticReview.id.in_(
                    db.query(GeneratedResponse.review_id).filter(
                        GeneratedResponse.review_type == 'synthetic'
                    )
                )
            ).all()
            
            total = len(raw_reviews_with_labels) + len(synthetic_reviews_with_labels)
            print(f"\n📊 Найдено {total} отзывов для генерации ответов")
            
            processed = 0
            
            # Обрабатываем сырые отзывы
            for review in raw_reviews_with_labels:
                label = db.query(SentimentLabel).filter(
                    SentimentLabel.review_id == review.id,
                    SentimentLabel.review_type == 'raw'
                ).first()
                
                response_text = self.generate_response(review.review_text, label.sentiment)
                
                response = GeneratedResponse(
                    review_id=review.id,
                    review_type='raw',
                    response_text=response_text,
                    sentiment_context=label.sentiment,
                    model_version="ai-forever/rugpt3large_based_on_gpt2"
                )
                
                db.add(response)
                processed += 1
                
                if processed % batch_size == 0:
                    db.commit()
                    print(f"✓ Сгенерировано {processed}/{total} ответов")
            
            # Обрабатываем синтетические отзывы
            for review in synthetic_reviews_with_labels:
                label = db.query(SentimentLabel).filter(
                    SentimentLabel.review_id == review.id,
                    SentimentLabel.review_type == 'synthetic'
                ).first()
                
                response_text = self.generate_response(review.review_text, label.sentiment)
                
                response = GeneratedResponse(
                    review_id=review.id,
                    review_type='synthetic',
                    response_text=response_text,
                    sentiment_context=label.sentiment,
                    model_version="ai-forever/rugpt3large_based_on_gpt2"
                )
                
                db.add(response)
                processed += 1
            
            db.commit()
            print(f"\n✅ Генерация завершена! Создано {processed} ответов")
            
        finally:
            db.close()


if __name__ == "__main__":
    generator = ResponseGenerator()
    generator.generate_for_all_reviews()
    print("\n🎉 Все ответы сгенерированы!")
