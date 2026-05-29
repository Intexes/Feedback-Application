import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sys
import os

# Добавляем путь к backend в sys.path для импорта моделей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models import SessionLocal, RawReview

def parse_tripadvisor(url, max_reviews=50, headless=True):
    """
    Парсинг отзывов с TripAdvisor
    
    Args:
        url: URL страницы отеля/ресторана
        max_reviews: Максимальное количество отзывов для сбора
        headless: Запуск браузера в фоновом режиме
    
    Returns:
        List словарей с данными отзывов
    """
    
    # Настройка Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--lang=ru")
    
    # Инициализация драйвера
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    reviews_data = []
    
    try:
        print(f"Открываем страницу: {url}")
        driver.get(url)
        time.sleep(5)  # Ждем загрузки страницы
        
        wait = WebDriverWait(driver, 10)
        
        # Прокрутка страницы для загрузки динамического контента
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 5
        
        while scroll_attempts < max_scroll_attempts:
            # Прокрутка вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Проверка новых элементов
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height
            
            # Попытка найти кнопку "Еще" для загрузки следующих отзывов
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, "button[data-test-target='load-more-reviews']")
                if load_more_button.is_displayed():
                    driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(2)
            except:
                pass  # Кнопка не найдена или не видна
        
        # Получаем HTML после прокрутки
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Более универсальные селекторы для отзывов TripAdvisor
        # Пробуем разные варианты селекторов
        review_selectors = [
            'div[data-review-id]',  # Основной контейнер отзыва
            'div.review-container',
            'div.qQjHh',  # Класс контейнера отзыва
            'div[data-test-target="review-list"] > div'
        ]
        
        review_elements = []
        for selector in review_selectors:
            elements = soup.select(selector)
            if elements:
                review_elements = elements
                print(f"Найдено отзывов по селектору '{selector}': {len(elements)}")
                break
        
        if not review_elements:
            # Если стандартные селекторы не сработали, пробуем найти по структуре
            print("Стандартные селекторы не сработали, пробуем альтернативный поиск...")
            # Ищем все div с классами, содержащими 'review'
            all_divs = soup.find_all('div', class_=lambda x: x and 'review' in x.lower())
            review_elements = all_divs[:max_reviews] if all_divs else []
            print(f"Найдено альтернативных элементов: {len(review_elements)}")
        
        # Обработка найденных отзывов
        for i, review_elem in enumerate(review_elements[:max_reviews]):
            try:
                # Извлечение текста отзыва - пробуем разные селекторы
                text_elem = review_elem.find('p', {'data-test-target': 'review-text'})
                if not text_elem:
                    text_elem = review_elem.find('span', class_='partial_entry')
                if not text_elem:
                    text_elem = review_elem.find('div', class_='tIeMl')
                
                review_text = text_elem.get_text(strip=True) if text_elem else ""
                
                if not review_text:
                    continue
                
                # Извлечение заголовка
                title_elem = review_elem.find('a', {'data-test-target': 'review-title'})
                if not title_elem:
                    title_elem = review_elem.find('span', class_='cPQsE')
                if not title_elem:
                    title_elem = review_elem.find('div', class_='titVW')
                
                title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
                
                # Извлечение рейтинга
                rating_elem = review_elem.find('span', class_='ui_bubble_rating')
                if not rating_elem:
                    rating_elem = review_elem.find('div', class_='dZusA')
                
                rating = None
                if rating_elem:
                    rating_class = rating_elem.get('class', [])
                    for cls in rating_class:
                        if 'bubble_' in cls:
                            try:
                                rating = int(cls.split('_')[1])
                                break
                            except:
                                pass
                
                # Извлечение даты
                date_elem = review_elem.find('span', {'data-test-target': 'review-date'})
                if not date_elem:
                    date_elem = review_elem.find('span', class_='jpRIL')
                
                date_text = date_elem.get_text(strip=True) if date_elem else None
                
                # Извлечение имени автора
                author_elem = review_elem.find('a', {'data-test-target': 'review-author-username'})
                if not author_elem:
                    author_elem = review_elem.find('span', class_='zPdrD')
                
                author = author_elem.get_text(strip=True) if author_elem else "Аноним"
                
                if review_text:
                    reviews_data.append({
                        'text': review_text,
                        'title': title,
                        'rating': rating,
                        'date': date_text,
                        'author': author,
                        'source': 'tripadvisor',
                        'url': url
                    })
                    print(f"[{len(reviews_data)}] Найдено: {title[:50]}... (Рейтинг: {rating})")
                
            except Exception as e:
                print(f"Ошибка при обработке отзыва {i}: {e}")
                continue
        
        print(f"\nВсего собрано отзывов: {len(reviews_data)}")
        
    except Exception as e:
        print(f"Критическая ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
    
    return reviews_data


def save_to_database(reviews_data):
    """Сохранение отзывов в базу данных"""
    session = SessionLocal()
    saved_count = 0
    duplicate_count = 0
    
    try:
        for review_data in reviews_data:
            # Проверка на дубликаты по тексту
            existing = session.query(RawReview).filter(
                RawReview.text == review_data['text'],
                RawReview.source == review_data['source']
            ).first()
            
            if existing:
                duplicate_count += 1
                print(f"Дубликат пропускается: {review_data['title'][:30]}...")
                continue
            
            # Создание нового отзыва
            raw_review = RawReview(
                text=review_data['text'],
                title=review_data.get('title', ''),
                rating=review_data.get('rating'),
                review_date=review_data.get('date'),
                author=review_data.get('author', 'Аноним'),
                source=review_data.get('source', 'unknown'),
                url=review_data.get('url', '')
            )
            
            session.add(raw_review)
            saved_count += 1
            print(f"✓ Сохранено: {review_data['title'][:30]}...")
        
        session.commit()
        print(f"\n=== Итоги сохранения ===")
        print(f"Сохранено: {saved_count}")
        print(f"Пропущено дубликатов: {duplicate_count}")
        
    except Exception as e:
        session.rollback()
        print(f"Ошибка при сохранении в БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    # URL для парсинга (отель из примера)
    TARGET_URL = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html#REVIEWS"
    
    print("=== Парсер TripAdvisor ===")
    print(f"Целевой URL: {TARGET_URL}")
    print("Запуск парсера...")
    
    # Сбор отзывов
    reviews = parse_tripadvisor(TARGET_URL, max_reviews=50, headless=True)
    
    if reviews:
        print("\nСохранение в базу данных...")
        save_to_database(reviews)
        print("\nПарсинг завершен!")
    else:
        print("\nОтзывы не найдены. Возможно, изменилась структура сайта или сработала защита от ботов.")
        print("Попробуйте:")
        print("1. Установить headless=False для отладки")
        print("2. Использовать прокси")
        print("3. Обновить селекторы")
