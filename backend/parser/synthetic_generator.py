import os
import sys
import random
from datetime import datetime, timedelta

# Добавляем корень проекта в путь, чтобы работали импорты
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.models import SessionLocal, Base, engine, RawReview

# Создаем таблицы, если их нет (на случай если БД еще не создана)
Base.metadata.create_all(bind=engine)

# --- Шаблоны для генерации отзывов ---

HOTEL_NAME = "City Park Hotel Sochi"

POSITIVE_TITLES = [
    "Прекрасный отдых!", "Отличный отель в Сочи", "Рекомендую всем!", 
    "Замечательный сервис", "Лучший отель на побережье", "Уютно и чисто",
    "Понравилось всё!", "Идеально для семьи", "Вернемся еще раз", "Выше всяких похвал"
]

NEGATIVE_TITLES = [
    "Разочарование", "Не стоит своих денег", "Грязь и шум", 
    "Ужасный сервис", "Больше ни ногой", "Испорченный отпуск",
    "Много недостатков", "Ожидали лучшего", "Жалоба руководству", "Не рекомендую"
]

NEUTRAL_TITLES = [
    "Нормально, но есть нюансы", "Средний уровень", "Как обычно", 
    "Есть плюсы и минусы", "Неплохо, но можно лучше", "Типичный отель",
    "На троечку", "Без восторга", "Сойдет для ночевки", "Обычный сервис"
]

# Конструкторы фраз
POSITIVE_PHRASES = [
    "Персонал очень вежливый и отзывчивый.", "Номера чистые и уютные.", 
    "Завтраки просто великолепные, большой выбор.", "Вид из окна на море потрясающий.",
    "Расположение отличное, до пляжа 5 минут.", "Бассейн чистый, вода теплая.",
    "Кондиционер работал бесшумно.", "Кровати очень удобные, выспались отлично.",
    "Анимация для детей супер, ребенок в восторге.", "Тихо и спокойно, никто не мешал."
]

NEGATIVE_PHRASES = [
    "В номере было грязно, видно давно не убирали.", "Персонал хамил на ресепшене.",
    "Завтраки однообразные и невкусные.", "Шум с улицы не давал спать ночью.",
    "В душе слабый напор воды.", "Кондиционер не охлаждал воздух.",
    "До пляжа идти очень далеко, как обманули в описании.", "Мебель старая и потертая.",
    "Платный Wi-Fi еле работал.", "Постельное белье было несвежим."
]

NEUTRAL_PHRASES = [
    "Номер обычный, ничего особенного.", "Завтрак стандартный, голодным не останешься.",
    "Расположение удобное, но рядом стройка.", "Сервис средний, иногда приходилось ждать.",
    "Цена соответствует качеству.", "В номере было немного душно.",
    "Уборка проводилась, но не тщательно.", "Интернет работал с перебоями.",
    "Персонал вежливый, но медлительный.", "В целом неплохо для короткой поездки."
]

def generate_review():
    """Генерирует один случайный отзыв."""
    # Определяем тональность с весами (40% позитив, 30% негатив, 30% нейтраль)
    sentiment = random.choices(['positive', 'negative', 'neutral'], weights=[0.4, 0.3, 0.3])[0]
    
    if sentiment == 'positive':
        title = random.choice(POSITIVE_TITLES)
        phrases = POSITIVE_PHRASES
    elif sentiment == 'negative':
        title = random.choice(NEGATIVE_TITLES)
        phrases = NEGATIVE_PHRASES
    else:
        title = random.choice(NEUTRAL_TITLES)
        phrases = NEUTRAL_PHRASES
    
    # Выбираем 2-4 случайные фразы и объединяем их
    selected_phrases = random.sample(phrases, k=random.randint(2, 4))
    content = " ".join(selected_phrases)
    
    full_text = f"{title} {content}"
    
    # Генерируем случайную дату за последние 6 месяцев
    start_date = datetime.now() - timedelta(days=180)
    random_date = start_date + timedelta(days=random.randint(0, 180))
    
    # Имитируем оценку (1-5)
    if sentiment == 'positive':
        rating_val = random.choice([4, 5, 5, 5])
    elif sentiment == 'negative':
        rating_val = random.choice([1, 2, 2, 3])
    else:
        rating_val = random.choice([3, 4])
        
    return full_text, f"{rating_val}/5", random_date.strftime("%Y-%m-%d")

def generate_and_save(count=50):
    print(f"🚀 Начинаем генерацию {count} синтетических отзывов для {HOTEL_NAME}...")
    
    db = SessionLocal()
    created_count = 0
    
    try:
        for i in range(count):
            text, rating, date_str = generate_review()
            
            new_review = RawReview(
                content=text,
                source="Synthetic",
                rating=rating,
                raw_date=date_str,
                collected_at=datetime.now()
            )
            
            db.add(new_review)
            created_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"✓ Сгенерировано {i+1} отзывов...")
        
        db.commit()
        print(f"\n✅ Успешно! {created_count} синтетических отзывов сохранено в базу данных.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при сохранении: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    # Генерируем 50 отзывов для старта
    generate_and_save(count=50)