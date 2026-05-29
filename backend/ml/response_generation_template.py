import sys
import os
from datetime import datetime
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import SessionLocal, SentimentLabel, RawReview, GeneratedResponse

class TemplateResponseGenerator:
    """Генератор ответов на основе шаблонов (без ML)"""
    
    def __init__(self):
        self.positive_templates = [
            "Благодарим вас за тёплый отзыв! Мы очень рады, что вам понравилось у нас. Будем ждать вашего возвращения!",
            "Спасибо за высокую оценку! Команда нашего отеля старается сделать каждый визит незабываемым. До новых встреч!",
            "Мы искренне благодарны за ваши добрые слова! Ваше удовлетворение — наша главная награда. Ждём вас снова!",
            "Огромное спасибо за отзыв! Мы счастливы, что смогли превзойти ваши ожидания. Приезжайте ещё!",
            "Благодарим за доверие и прекрасный отзыв! Рады, что вы отлично провели время. Всегда вам рады!"
        ]
        
        self.negative_templates = [
            "Приносим свои искренние извинения за доставленные неудобства. Мы уже работаем над устранением указанных проблем. Надеемся на возможность исправить впечатление.",
            "Нам очень жаль, что ваш визит не оправдал ожиданий. Благодарим за обратную связь — она помогает нам становиться лучше. Примите наши извинения.",
            "Сожалеем о произошедшем инциденте. Ваша критика важна для нас. Мы проводим внутреннее расследование и примем меры. Просим прощения.",
            "Извините за негативный опыт. Мы серьёзно относимся к вашим замечаниям и обязательно улучшим сервис. Надеемся на второй шанс.",
            "Приносим глубочайшие извинения. Ситуация неприемлема, и мы уже принимаем меры. Благодарим за терпение и понимание."
        ]
        
        self.neutral_templates = [
            "Благодарим вас за отзыв и оценку нашей работы. Мы ценим ваше мнение и будем рады видеть вас снова!",
            "Спасибо, что поделились впечатлениями. Мы постоянно работаем над улучшением сервиса. Ждём вашего возвращения!",
            "Признательны за ваш отзыв. Команда отеля стремится к совершенству, и ваше мнение очень важно для нас.",
            "Благодарим за уделённое время и обратную связь. Рады, что вы выбрали наш отель. До новых встреч!",
            "Спасибо за ваш отзыв! Мы учтём все пожелания и продолжим развиваться. Всегда вам рады!"
        ]
    
    def generate_response(self, review_text, sentiment):
        """Выбор случайного шаблона в зависимости от тональности"""
        if sentiment == 'positive':
            return random.choice(self.positive_templates)
        elif sentiment == 'negative':
            return random.choice(self.negative_templates)
        else:  # neutral
            return random.choice(self.neutral_templates)
    
    def generate_for_all_reviews(self):
        """Генерация ответов для всех отзывов без ответов"""
        db = SessionLocal()
        try:
            # Получаем все отзывы с метками, но без ответов
            raw_reviews_with_labels = db.query(RawReview).join(
                SentimentLabel, RawReview.id == SentimentLabel.review_id
            ).filter(
                ~RawReview.id.in_(
                    db.query(GeneratedResponse.review_id)
                )
            ).all()
            
            total = len(raw_reviews_with_labels)
            print(f"\n📊 Найдено {total} отзывов для генерации ответов")
            
            if total == 0:
                print("✅ Все отзывы уже имеют ответы!")
                return
            
            processed = 0
            
            for review in raw_reviews_with_labels:
                label = db.query(SentimentLabel).filter(
                    SentimentLabel.review_id == review.id
                ).first()
                
                if not label:
                    print(f"⚠️ Пропущен отзыв ID={review.id} (нет метки тональности)")
                    continue
                
                response_text = self.generate_response(review.content, label.sentiment)
                
                response = GeneratedResponse(
                    review_id=review.id,
                    response_text=response_text,
                    created_at=datetime.now()
                )
                
                db.add(response)
                processed += 1
                
                if processed % 10 == 0:
                    db.commit()
                    print(f"✓ Сгенерировано {processed}/{total} ответов")
            
            db.commit()
            print(f"\n✅ Генерация завершена! Создано {processed} ответов")
            
        finally:
            db.close()


if __name__ == "__main__":
    print("🚀 Запуск генератора ответов на шаблонах...")
    generator = TemplateResponseGenerator()
    generator.generate_for_all_reviews()
    print("\n🎉 Все ответы сгенерированы!")
