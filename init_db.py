#!/usr/bin/env python3
"""
Скрипт для создания и инициализации базы данных
Запустите этот файл первым перед использованием парсера
"""

import sys
import os

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from backend.models import Base, engine, init_db

def main():
    print("🚀 Инициализация базы данных Feedbacket...")
    print(f"📍 Путь к БД: sqlite:///./data/feedbacket.db")
    
    # Создаём таблицы
    init_db()
    
    print("\n✅ База данных успешно создана!")
    print("\n📊 Созданные таблицы:")
    print("   • raw_reviews — сырые отзывы из парсера")
    print("   • synthetic_reviews — синтетические отзывы")
    print("   • sentiment_labels — метки тональности (ruBert)")
    print("   • generated_responses — сгенерированные ответы (ruGPT)")
    
    print("\n📝 Следующие шаги:")
    print("   1. Запустите парсер: python backend/parser/selenium_parser.py")
    print("   2. Сгенерируйте синтетические отзывы")
    print("   3. Запустите анализ тональности ruBert")
    print("   4. Сгенерируйте ответы через ruGPT")
    print("   5. Запустите бэкенд: uvicorn backend.main:app --reload")

if __name__ == "__main__":
    main()
