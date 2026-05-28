import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Добавляем корень проекта в путь, чтобы работали импорты
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.models import SessionLocal, engine, Base, RawReview

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

class TripAdvisorParser:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.reviews = []

    def setup_driver(self):
        """Настройка драйвера Chrome"""
        chrome_options = Options()
        # Не закрываем браузер сразу при ошибке, чтобы можно было посмотреть
        chrome_options.add_experimental_option("detach", True) 
        
        # Устанавливаем реалистичный User-Agent
        ua = UserAgent()
        chrome_options.add_argument(f"user-agent={ua.random}")
        
        # Убираем флаги автоматизации (немного снижает шанс детекта)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Скрипт для скрытия факта автоматизации
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def wait_for_captcha_and_load(self, timeout=90):
        """
        Ждет указанное время, чтобы пользователь мог решить капчу.
        """
        print(f"\n⏳ БРАУЗЕР ОТКРЫТ! У вас есть {timeout} секунд.")
        print("👉 РЕШИТЕ КАПЧУ ВРУЧНУЮ В ОТКРЫВШЕМСЯ ОКНЕ.")
        print("👉 Если страница не загрузилась сама после капчи — обновите её (F5).")
        print(f"⏳ Парсинг начнется автоматически через {timeout} секунд...\n")
        
        # Просто ждем нужное время
        time.sleep(timeout)
        
        print("⏰ Время вышло! Начинаем попытку сбора данных...")

    def parse_reviews(self, max_reviews=20):
        self.setup_driver()
        
        try:
            print(f"Открываем страницу: {self.url}")
            self.driver.get(self.url)
            
            # ЭТАП РУЧНОГО ПРОХОЖДЕНИЯ КАПЧИ
            self.wait_for_captcha_and_load(timeout=90)
            
            # После ожидания пытаемся найти отзывы
            wait = WebDriverWait(self.driver, 10)
            
            # Ищем контейнеры с отзывами (селекторы могут меняться, используем общие классы)
            # Обычно отзывы лежат в div с data-attr="review-list" или похожим
            # Пробуем найти по классу review selectors
            
            # Скроллим немного вниз, чтобы подгрузить контент
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Попытка найти блоки отзывов (селекторы актуальны на 2024 год, но могут измениться)
            # Ищем элементы, содержащие текст отзыва
            review_elements = soup.select('div[data-test-target="review-list"] div[data-test-target="review-card"]')
            
            if not review_elements:
                # Альтернативный селектор, если первый не сработал
                review_elements = soup.select('li[class*="review-item"]')
            
            if not review_elements:
                # Еще одна попытка по общему признаку
                review_elements = soup.find_all('div', class_=lambda x: x and 'review-' in x.lower())

            print(f"Найдено элементов, похожих на отзывы: {len(review_elements)}")

            count = 0
            for el in review_elements:
                if count >= max_reviews:
                    break
                
                try:
                    # Извлекаем текст отзыва
                    text_tag = el.find('span', {'data-test-target': 'review-text'}) or el.find('div', class_='review-body')
                    if not text_tag:
                        continue
                    
                    content = text_tag.get_text(strip=True)
                    
                    # Извлекаем заголовок (если есть)
                    title_tag = el.find('span', {'data-test-target': 'review-title'}) or el.find('div', class_='title')
                    title = title_tag.get_text(strip=True) if title_tag else "Без заголовка"
                    
                    # Извлекаем оценку
                    rating_tag = el.find('span', {'data-test-target': 'review-rating'}) or el.find('div', class_='rating')
                    rating = rating_tag['aria-label'] if rating_tag and 'aria-label' in rating_tag.attrs else "Нет оценки"
                    
                    # Извлекаем дату
                    date_tag = el.find('span', {'data-test-target': 'review-date'})
                    date_str = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime("%Y-%m-%d")

                    full_text = f"{title}. {content}"

                    # Сохраняем в БД
                    new_review = RawReview(
                        content=full_text,
                        source="TripAdvisor",
                        rating=rating,
                        raw_date=date_str,
                        collected_at=datetime.now()
                    )
                    
                    db = SessionLocal()
                    db.add(new_review)
                    db.commit()
                    db.close()
                    
                    print(f"✓ Сохранен отзыв #{count+1}: {content[:50]}...")
                    count += 1
                    
                except Exception as e:
                    print(f"Ошибка при разборе одного отзыва: {e}")
                    continue

            if count == 0:
                print("\n❌ Отзывы не найдены даже после ожидания.")
                print("Проверьте, правильно ли вы решили капчу и загрузилась ли страница с отзывами.")
            else:
                print(f"\n✅ Успешно собрано {count} отзывов!")

        except Exception as e:
            print(f"Критическая ошибка: {e}")
        finally:
            # Не закрываем браузер сразу, если была ошибка, чтобы пользователь увидел результат
            # Но в штатном режиме лучше закрыть, если все прошло успешно. 
            # Оставим открытым на всякий случай, так как detach=True
            print("\nБраузер оставлен открытым для проверки. Закройте его вручную.")
            # self.driver.quit() # Закомментировано, чтобы окно не закрылось сразу

if __name__ == "__main__":
    URL = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"
    
    print("🚀 Запуск парсера TripAdvisor для City Park Hotel Sochi...")
    print("⚠️ ВНИМАНИЕ: Сейчас откроется браузер. Вам нужно будет решить капчу!")
    
    parser = TripAdvisorParser(URL)
    # Берем пока 5 отзывов для теста
    parser.parse_reviews(max_reviews=5)