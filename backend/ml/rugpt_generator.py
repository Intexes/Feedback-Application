from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Optional, Dict
import re

from models import UserSettings


class RuGPT3Generator:
    """Генерация ответов на отзывы с помощью ruGPT-3"""
    
    def __init__(self, model_path: str = "sberbank-ai/rugpt3c_based_on_gpt2"):
        """
        Инициализация модели ruGPT-3 для генерации ответов
        
        Args:
            model_path: Путь к модели или название в HuggingFace
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Настройки по умолчанию
        self.max_lengths = {
            "short": 100,
            "medium": 200,
            "long": 400
        }
        
        # Тональности
        self.tone_prompts = {
            "business": "Официально-деловой стиль. Будьте вежливы и профессиональны.",
            "friendly": "Дружелюбный и теплый тон. Проявите эмпатию и заботу.",
            "reserved": "Сдержанный и нейтральный тон. Кратко и по делу."
        }
    
    def generate_response(
        self, 
        review_text: str, 
        rating: int,
        sentiment: str,
        classes: list,
        settings: Optional[UserSettings] = None,
        max_length: Optional[int] = None
    ) -> str:
        """
        Генерация ответа на отзыв
        
        Args:
            review_text: Текст отзыва
            rating: Оценка (1-5)
            sentiment: Тональность отзыва (positive/neutral/negative)
            classes: Классы отзыва
            settings: Настройки пользователя
            max_length: Максимальная длина ответа
            
        Returns:
            str: Сгенерированный ответ
        """
        # Определение параметров
        if settings:
            length_key = settings.response_length or "medium"
            tone_key = settings.tone_of_voice or "business"
        else:
            length_key = "medium"
            tone_key = "business"
        
        if max_length is None:
            max_length = self.max_lengths.get(length_key, 200)
        
        tone_instruction = self.tone_prompts.get(tone_key, self.tone_prompts["business"])
        
        # Формирование промпта
        prompt = self._build_prompt(
            review_text=review_text,
            rating=rating,
            sentiment=sentiment,
            classes=classes,
            tone_instruction=tone_instruction
        )
        
        # Токенизация
        inputs = self.tokenizer.encode(
            prompt, 
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).to(self.device)
        
        # Генерация
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_length,
                min_length=50,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Декодирование
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Очистка ответа
        response = self._clean_response(generated_text, prompt)
        
        return response
    
    def _build_prompt(
        self, 
        review_text: str, 
        rating: int,
        sentiment: str,
        classes: list,
        tone_instruction: str
    ) -> str:
        """Построение промпта для генерации"""
        
        # Определение типа ситуации
        if rating <= 2:
            situation = "негативный отзыв с низкой оценкой"
            action = "Извинитесь за неудобства, объясните меры по исправлению ситуации"
        elif rating == 3 or rating == 4:
            situation = "нейтральный отзыв со средней оценкой"
            action = "Поблагодарите за отзыв, отметьте положительные моменты, предложите улучшить сервис"
        else:
            situation = "положительный отзыв с высокой оценкой"
            action = "Поблагодарите гостя за высокую оценку и теплые слова"
        
        # Классы на русском
        class_names_ru = {
            "service": "сервис",
            "staff": "персонал",
            "cleanliness": "чистота",
            "room": "номер",
            "location": "расположение",
            "food": "питание",
            "price": "цена",
            "amenities": "удобства",
            "other": "общее"
        }
        
        topics_str = ", ".join([class_names_ru.get(c, c) for c in classes])
        
        prompt = f"""{tone_instruction}

Напиши ответ на отзыв гостя отеля.

Контекст:
- Это {situation}
- Оценка гостя: {rating}/5
- Темы отзыва: {topics_str}
- Текст отзыва: "{review_text}"

Требования к ответу:
- {action}
- Обратись к гостю по имени (если известно) или используйте "Уважаемый гость"
- Объяни ситуацию на данный момент
- Предложи связаться для дальнейшего обсуждения (если негатив)
- Подпишись как "Команда отеля"
- Длина ответа: до {100} символов

Ответ:"""
        
        return prompt
    
    def _clean_response(self, generated_text: str, prompt: str) -> str:
        """Очистка сгенерированного ответа"""
        # Удаление промпта из ответа
        if prompt in generated_text:
            response = generated_text.split(prompt, 1)[1]
        else:
            response = generated_text
        
        # Удаление лишних пробелов и переносов строк
        response = re.sub(r'\n\s*\n', '\n', response.strip())
        response = ' '.join(response.split())
        
        # Обрезка до разумной длины
        if len(response) > 500:
            response = response[:497] + "..."
        
        return response


# Singleton instance
_generator_instance = None


def get_generator(model_path: str = None) -> RuGPT3Generator:
    """Получить экземпляр генератора (singleton)"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = RuGPT3Generator(model_path or "sberbank-ai/rugpt3c_based_on_gpt2")
    return _generator_instance
