from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import random
from datetime import datetime
import sys
import os

# Добавляем родительскую директорию в путь для импорта models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import RawReview, SessionLocal


class TripAdvisorParser:
    """Парсер отзывов с TripAdvisor"""
    
    def __init__(self):
        self.base_url = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"
        self.driver = None
        
    def setup_driver(self):
        """Настройка WebDriver с обходом базовой защиты"""
        ua = UserAgent()
        chrome_options = Options()
        chrome_options.add_argument(f"--user-agent={ua.random}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Скрипт для скрытия автоматизации
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def scroll_page(self):
        """Прокрутка страницы для подгрузки отзывов"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
    def parse_reviews(self, max_reviews=50):
        """Парсинг отзывов"""
        if not self.driver:
            self.setup_driver()
            
        reviews = []
        
        try:
            self.driver.get(self.base_url)
            time.sleep(random.uniform(3, 5))
            
            # Прокручиваем страницу для загрузки отзывов
            self.scroll_page()
            time.sleep(2)
            
            while len(reviews) < max_reviews:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Ищем контейнеры с отзывами (селекторы могут меняться)
                review_containers = soup.find_all('div', {'data-test-target': 'review-list'})
                if not review_containers:
                    review_containers = soup.find_all('div', class_='review-container')
                
                for container in review_containers:
                    if len(reviews) >= max_reviews:
                        break
                        
                    try:
                        # Извлечение текста отзыва
                        text_elem = container.find('span', class_='partial_entry') or \
                                   container.find('div', class_='review-text') or \
                                   container.find('p')
                        review_text = text_elem.get_text(strip=True) if text_elem else ""
                        
                        # Извлечение автора
                        author_elem = container.find('a', class_='username') or \
                                     container.find('div', class_='user-info')
                        author = author_elem.get_text(strip=True) if author_elem else "Аноним"
                        
                        # Извлечение оценки
                        rating_elem = container.find('span', class_='ui_bubble_rating') or \
                                     container.find('div', class_='rating')
                        rating = None
                        if rating_elem:
                            rating_class = rating_elem.get('class', [])
                            for cls in rating_class:
                                if 'bubble_' in cls:
                                    try:
                                        rating = int(cls.split('_')[1])
                                    except:
                                        pass
                        
                        # Извлечение даты
                        date_elem = container.find('span', class_='publish_date') or \
                                   container.find('div', class_='review-date')
                        review_date = None
                        if date_elem:
                            date_str = date_elem.get_text(strip=True).replace('от ', '')
                            try:
                                review_date = datetime.strptime(date_str, '%d %B %Y')
                            except:
                                review_date = datetime.now()
                        
                        if review_text and len(review_text) > 20:
                            reviews.append({
                                'source': 'tripadvisor',
                                'hotel_id': 'd304815',
                                'author_name': author,
                                'review_text': review_text,
                                'rating': rating,
                                'review_date': review_date.date() if review_date else None
                            })
                    except Exception as e:
                        print(f"Ошибка при обработке отзыва: {e}")
                        continue
                
                # Переход на следующую страницу
                if len(reviews) < max_reviews:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Следующая страница"]')
                        if next_button:
                            next_button.click()
                            time.sleep(random.uniform(3, 5))
                            self.scroll_page()
                        else:
                            break
                    except:
                        break
                        
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
        return reviews
    
    def save_to_db(self, reviews):
        """Сохранение отзывов в БД"""
        db = SessionLocal()
        try:
            for review_data in reviews:
                review = RawReview(**review_data)
                db.add(review)
            db.commit()
            print(f"✅ Сохранено {len(reviews)} отзывов в БД")
        except Exception as e:
            db.rollback()
            print(f"❌ Ошибка сохранения: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    parser = TripAdvisorParser()
    print("🔍 Начинаем парсинг TripAdvisor для City Park Hotel Sochi...")
    reviews = parser.parse_reviews(max_reviews=20)
    print(f"📊 Найдено отзывов: {len(reviews)}")
    
    if reviews:
        parser.save_to_db(reviews)
        print("✅ Парсинг завершен!")
    else:
        print("⚠️ Отзывы не найдены")
