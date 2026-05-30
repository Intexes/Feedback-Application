import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
import json

from models import Review, PlatformSource, SessionLocal


class BaseParser:
    """Базовый класс для парсеров с использованием Playwright"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def init_browser(self, proxy: Optional[str] = None):
        """
        Инициализация браузера с поддержкой прокси
        
        Args:
            proxy: Строка прокси в формате 'http://user:pass@ip:port' или 'ip:port'
        """
        if self.browser is None:
            playwright = await async_playwright().start()
            
            # Настройки браузера
            browser_args = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            }
            
            # Добавляем прокси, если указан
            if proxy:
                browser_args['proxy'] = {'server': proxy}
            
            self.browser = await playwright.chromium.launch(**browser_args)
            
            # Эмуляция устройства (User-Agent)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="ru-RU",
                timezone_id="Europe/Moscow",
                viewport={"width": 1920, "height": 1080}
            )
            
            self.page = await self.context.new_page()
            
            # Скрипт для скрытия признаков бота
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                navigator.plugins.length = 3;
                navigator.languages = ['ru-RU', 'ru'];
            """)
    
    async def close_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    async def accept_cookies(self):
        """Принятие куки, если всплывет баннер"""
        try:
            # Попытка принять куки для различных сайтов
            cookie_selectors = [
                'button[id="onetrust-accept-btn-handler"]',
                'button[class*="accept-all"]',
                'button[class*="cookie-accept"]',
                '[aria-label="Accept all cookies"]',
                'button[id="accept-cookies"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    print("✅ Куки приняты")
                    return
                except:
                    continue
        except Exception as e:
            pass  # Баннера нет или не удалось нажать


class TripAdvisorParser(BaseParser):
    """Парсер для TripAdvisor"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.tripadvisor.ru"
        # Селекторы для TripAdvisor (обновленные)
        self.selectors = {
            'review_card': '[data-test-target="review-list"] li, div[data-reviewid]',
            'title': 'h3[data-test-target="review-title"] span, h3 a, a[class*="title"]',
            'text': 'div[data-test-target="review-text"] span, div[data-test-target="review-text"] p, span[class*="text"]',
            'rating': 'span[data-test-target="review-rating"] span, svg[aria-label*="из 5"], [class*="bubble"]',
            'date': 'span[data-test-target="review-date"], time[class*="date"]',
            'author': 'a[data-test-target="review-author-link"] span, span[data-test-target="review-author"], a[class*="username"]'
        }
    
    async def parse_hotel_reviews(
        self, 
        url: str,
        limit: int = 50,
        proxy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов отеля с TripAdvisor
        
        Args:
            url: Полный URL страницы отзывов
            limit: Максимальное количество отзывов
            proxy: Строка прокси в формате 'http://user:pass@ip:port'
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser(proxy=proxy)
        reviews = []
        
        try:
            print(f"🚀 Начинаем парсинг TripAdvisor: {url}")
            if proxy:
                print(f"🔒 Используем прокси: {proxy}")
            
            # Переход на страницу
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Принять куки
            await self.accept_cookies()
            
            # Прокрутка для загрузки всех отзывов
            for i in range(5):
                await self.page.evaluate(f"window.scrollBy(0, {1000 * (i+1)})")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами
            review_blocks = soup.select(self.selectors['review_card'])[:limit]
            
            print(f"📄 Найдено {len(review_blocks)} карточек отзывов")
            
            for i, block in enumerate(review_blocks):
                try:
                    # Извлечение данных
                    author_elem = block.select_one(self.selectors['author'])
                    rating_elem = block.select_one(self.selectors['rating'])
                    title_elem = block.select_one(self.selectors['title'])
                    text_elem = block.select_one(self.selectors['text'])
                    date_elem = block.select_one(self.selectors['date'])
                    
                    if not text_elem and not title_elem:
                        continue
                    
                    review_text = ""
                    if title_elem:
                        review_text += title_elem.get_text(strip=True) + ". "
                    if text_elem:
                        review_text += text_elem.get_text(strip=True)
                    
                    # Извлечение рейтинга
                    rating = self._extract_rating(rating_elem) if rating_elem else 3
                    
                    review_data = {
                        "platform": PlatformSource.TRIPADVISOR,
                        "external_id": block.get('data-reviewid', f'ta_{i}'),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": rating,
                        "review_text": review_text.strip(),
                        "review_date": self._parse_date(date_elem.get_text()) if date_elem else datetime.now(),
                        "is_synthetic": False,
                        "url": url
                    }
                    reviews.append(review_data)
                    print(f"   ✅ Найден отзыв #{len(reviews)}: {rating}/5")
                    
                except Exception as e:
                    print(f"   ⚠️ Ошибка при парсинге карточки {i}: {e}")
                    continue
                        
        except Exception as e:
            print(f"❌ Критическая ошибка парсинга TripAdvisor: {e}")
        finally:
            await self.close_browser()
        
        print(f"🎉 Парсинг TripAdvisor завершен. Найдено отзывов: {len(reviews)}")
        return reviews
    
    def _extract_rating(self, rating_elem) -> int:
        """Извлечение рейтинга из классов элемента или aria-label"""
        try:
            # Попытка получить из aria-label (для SVG)
            aria_label = rating_elem.get('aria-label', '')
            if aria_label:
                match = re.search(r'(\d+)', aria_label)
                if match:
                    return int(match.group(1))
            
            # Попытка получить из класса (например, "40_bubble")
            class_attr = rating_elem.get('class', [])
            for cls in class_attr:
                match = re.search(r'(\d+)_bubble', cls)
                if match:
                    return int(match.group(1))
            
            return 3
        except:
            return 3
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            else:
                return now
        except:
            return datetime.now()


class GoogleMapsParser(BaseParser):
    """Парсер для Google Maps"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.google.com/maps"
    
    async def parse_place_reviews(
        self, 
        url: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов места с Google Maps
        
        Args:
            url: Полный URL страницы места (например, https://www.google.com/maps/place/City+Park+Hotel+Sochi/...)
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser()
        reviews = []
        
        try:
            # Переход на страницу
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки отзывов
            await asyncio.sleep(3)
            
            # Прокрутка для загрузки всех отзывов
            for i in range(10):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами - обновленные селекторы для Google Maps
            review_blocks = soup.select('div[data-review-id], div[jscontroller*="review"]')[:limit]
            
            for block in review_blocks:
                try:
                    # Извлечение данных
                    author_elem = block.select_one('div[class*="author"], span[class*="author"]')
                    rating_elem = block.select_one('[role="img"][aria-label*="rating"], [class*="star-rating"]')
                    text_elem = block.select_one('span[class*="text"], div[class*="review-text"], span[jscontent*="text"]')
                    date_elem = block.select_one('span[class*="date"], time[class*="date"], span[jscontent*="date"]')
                    
                    if not text_elem:
                        continue
                    
                    review_data = {
                        "platform": PlatformSource.GOOGLE_MAPS,
                        "external_id": block.get('data-review-id', ''),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": self._extract_rating(rating_elem) if rating_elem else 3,
                        "review_text": text_elem.get_text(strip=True),
                        "review_date": self._parse_date(date_elem.get_text()) if date_elem else datetime.now(),
                        "is_synthetic": False
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing review block: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error parsing Google Maps: {e}")
        finally:
            await self.close_browser()
        
        return reviews
    
    def _extract_rating(self, rating_elem) -> int:
        """Извлечение рейтинга из aria-label"""
        try:
            aria_label = rating_elem.get('aria-label', '')
            match = re.search(r'(\d+\.?\d*)', aria_label)
            if match:
                rating = float(match.group(1))
                return round(rating)
            return 3
        except:
            return 3
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            elif "год" in date_str:
                years = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=years*365)
            else:
                return now
        except:
            return datetime.now()
    
    async def parse_with_api(
        self,
        place_id: str,
        api_key: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг через официальное Google Places API
        
        Args:
            place_id: ID места
            api_key: API ключ Google
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        reviews = []
        
        try:
            # Получение деталей места с отзывами
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,rating,reviews",
                "key": api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(details_url, params=params) as response:
                    if response.status != 200:
                        return reviews
                    
                    data = await response.json()
                    
                    if data.get("status") != "OK":
                        return reviews
                    
                    place_data = data.get("result", {})
                    raw_reviews = place_data.get("reviews", [])[:limit]
                    
                    for review in raw_reviews:
                        review_data = {
                            "platform": PlatformSource.GOOGLE_MAPS,
                            "external_id": review.get("review_id", ""),
                            "author_name": review.get("author_name", "Аноним"),
                            "rating": review.get("rating", 3),
                            "review_text": review.get("text", ""),
                            "review_date": datetime.fromtimestamp(review.get("time", 0)) if review.get("time") else datetime.now(),
                            "is_synthetic": False
                        }
                        reviews.append(review_data)
                        
        except Exception as e:
            print(f"Error parsing Google Maps API: {e}")
        
        return reviews


class YandexMapsParser(BaseParser):
    """Парсер для Яндекс.Карт"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://yandex.ru/maps"
    
    async def parse_organization_reviews(
        self, 
        url: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов организации с Яндекс.Карт
        
        Args:
            url: Полный URL страницы отзывов (например, https://yandex.ru/maps/org/city_park_hotel/124982210500/reviews/)
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser()
        reviews = []
        
        try:
            # Переход на страницу
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки отзывов
            await asyncio.sleep(3)
            
            # Прокрутка для загрузки всех отзывов
            for i in range(10):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами - обновленные селекторы для Яндекс.Карт
            review_blocks = soup.select('div[class*="review"], div[data-review-id], div[jsname*="review"]')[:limit]
            
            for block in review_blocks:
                try:
                    # Извлечение данных
                    author_elem = block.select_one('[class*="author"], span[class*="name"]')
                    rating_elem = block.select_one('[class*="rating"], [class*="stars"]')
                    text_elem = block.select_one('[class*="text"], p[class*="content"], div[class*="review-text"]')
                    date_elem = block.select_one('[class*="date"], time[class*="date"], span[class*="time"]')
                    
                    if not text_elem:
                        continue
                    
                    review_data = {
                        "platform": PlatformSource.YANDEX_MAPS,
                        "external_id": block.get('data-review-id', ''),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": self._extract_rating(rating_elem) if rating_elem else 3,
                        "review_text": text_elem.get_text(strip=True),
                        "review_date": self._parse_date(date_elem.get_text()) if date_elem else datetime.now(),
                        "is_synthetic": False
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing review block: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error parsing Yandex Maps: {e}")
        finally:
            await self.close_browser()
        
        return reviews
    
    def _extract_rating(self, rating_elem) -> int:
        """Извлечение рейтинга"""
        try:
            text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d+)', text)
            return int(match.group(1)) if match else 3
        except:
            return 3
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            else:
                return now
        except:
            return datetime.now()


class BookingParser(BaseParser):
    """Парсер для Booking.com"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.booking.com/hotel/ru"
    
    async def parse_hotel_reviews(
        self, 
        url: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов отеля с Booking.com
        
        Args:
            url: Полный URL страницы отзывов отеля на booking.com
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser()
        reviews = []
        
        try:
            # Переход на страницу
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки отзывов
            await asyncio.sleep(3)
            
            # Прокрутка для загрузки всех отзывов
            for i in range(10):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами - обновленные селекторы для Booking.com
            review_blocks = soup.select('div[data-testid="review-card"], div[class*="review"]')[:limit]
            
            for block in review_blocks:
                try:
                    # Извлечение данных
                    author_elem = block.select_one('h4, [class*="author"]')
                    rating_elem = block.select_one('[data-testid="review-score"], [class*="score"]')
                    text_elem = block.select_one('[data-testid="review-body"], [class*="review-text"]')
                    date_elem = block.select_one('time, [class*="date"]')
                    
                    if not text_elem:
                        continue
                    
                    review_data = {
                        "platform": PlatformSource.BOOKING,
                        "external_id": block.get('data-review-id', ''),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": int(float(rating_elem.get_text(strip=True))) if rating_elem else 3,
                        "review_text": text_elem.get_text(strip=True),
                        "review_date": datetime.now() if not date_elem else self._parse_date(date_elem.get_text()),
                        "is_synthetic": False
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing review block: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error parsing Booking.com: {e}")
        finally:
            await self.close_browser()
        
        return reviews
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            else:
                return now
        except:
            return datetime.now()


class OstrovokParser(BaseParser):
    """Парсер для Ostrovok.ru"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://ostrovok.ru"
    
    async def parse_hotel_reviews(
        self, 
        url: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов отеля с Ostrovok.ru
        
        Args:
            url: Полный URL страницы отзывов отеля на ostrovok.ru
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser()
        reviews = []
        
        try:
            # Переход на страницу
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки отзывов
            await asyncio.sleep(3)
            
            # Прокрутка для загрузки всех отзывов
            for i in range(10):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами
            review_blocks = soup.select('div[class*="review"], div[data-review-id]')[:limit]
            
            for block in review_blocks:
                try:
                    author_elem = block.select_one('[class*="author"], [class*="name"]')
                    rating_elem = block.select_one('[class*="rating"], [class*="score"]')
                    text_elem = block.select_one('[class*="text"], [class*="content"]')
                    date_elem = block.select_one('[class*="date"], time')
                    
                    if not text_elem:
                        continue
                    
                    review_data = {
                        "platform": PlatformSource.OSTROVOK,
                        "external_id": block.get('data-review-id', ''),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": self._extract_rating(rating_elem) if rating_elem else 3,
                        "review_text": text_elem.get_text(strip=True),
                        "review_date": self._parse_date(date_elem.get_text()) if date_elem else datetime.now(),
                        "is_synthetic": False
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing review block: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error parsing Ostrovok: {e}")
        finally:
            await self.close_browser()
        
        return reviews
    
    def _extract_rating(self, rating_elem) -> int:
        try:
            text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d+)', text)
            return int(match.group(1)) if match else 3
        except:
            return 3
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            else:
                return now
        except:
            return datetime.now()


class ManulParser(BaseParser):
    """Парсер для Manul (заглушка, так как специфика парсера неизвестна)"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://manul.ru"
    
    async def parse_reviews(
        self, 
        url: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Парсинг отзывов с Manul
        
        Args:
            url: Полный URL страницы отзывов
            limit: Максимальное количество отзывов
            
        Returns:
            List[Dict]: Список отзывов
        """
        await self.init_browser()
        reviews = []
        
        try:
            # Переход на страницу
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Ждем загрузки
            await asyncio.sleep(3)
            
            # Прокрутка
            for i in range(5):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # Получение HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Поиск блоков с отзывами (общие селекторы)
            review_blocks = soup.select('div[class*="review"], article[class*="review"]')[:limit]
            
            for block in review_blocks:
                try:
                    author_elem = block.select_one('[class*="author"], [class*="name"]')
                    rating_elem = block.select_one('[class*="rating"], [class*="stars"]')
                    text_elem = block.select_one('[class*="text"], p[class*="content"]')
                    date_elem = block.select_one('[class*="date"], time')
                    
                    if not text_elem:
                        continue
                    
                    review_data = {
                        "platform": PlatformSource.MANUL,
                        "external_id": block.get('data-id', ''),
                        "author_name": author_elem.get_text(strip=True) if author_elem else "Аноним",
                        "rating": self._extract_rating(rating_elem) if rating_elem else 3,
                        "review_text": text_elem.get_text(strip=True),
                        "review_date": self._parse_date(date_elem.get_text()) if date_elem else datetime.now(),
                        "is_synthetic": False
                    }
                    reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing review block: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error parsing Manul: {e}")
        finally:
            await self.close_browser()
        
        return reviews
    
    def _extract_rating(self, rating_elem) -> int:
        try:
            text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d+)', text)
            return int(match.group(1)) if match else 3
        except:
            return 3
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            now = datetime.now()
            if "день" in date_str or "дня" in date_str:
                days = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            elif "недел" in date_str:
                weeks = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(weeks=weeks)
            elif "месяц" in date_str:
                months = int(re.search(r'(\d+)', date_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=months*30)
            else:
                return now
        except:
            return datetime.now()


class ReviewParserService:
    """Сервис для управления парсерами"""
    
    def __init__(self):
        self.parsers = {
            PlatformSource.TRIPADVISOR: TripAdvisorParser(),
            PlatformSource.GOOGLE_MAPS: GoogleMapsParser(),
            PlatformSource.YANDEX_MAPS: YandexMapsParser(),
            PlatformSource.BOOKING: BookingParser(),
            PlatformSource.OSTROVOK: OstrovokParser(),
            PlatformSource.MANUL: ManulParser(),
        }
    
    async def parse_all_sources(
        self,
        sources_config: Dict[str, Dict],
        save_to_db: bool = True
    ) -> int:
        """
        Парсинг всех настроенных источников
        
        Args:
            sources_config: Конфигурация источников
                {
                    "tripadvisor": {"urls": ["https://www.tripadvisor.ru/..."], "limit": 50},
                    "google_maps": {"urls": ["https://www.google.com/maps/..."], "limit": 50},
                    "yandex_maps": {"urls": ["https://yandex.ru/maps/..."], "limit": 50},
                    "booking.com": {"urls": ["https://www.booking.com/..."], "limit": 50},
                    "ostrovok": {"urls": ["https://ostrovok.ru/..."], "limit": 50},
                    "manul": {"urls": ["https://manul.ru/..."], "limit": 50}
                }
            save_to_db: Сохранять ли в БД
            
        Returns:
            int: Количество спарсенных отзывов
        """
        all_reviews = []
        
        # Парсинг TripAdvisor
        if "tripadvisor" in sources_config:
            config = sources_config["tripadvisor"]
            parser = self.parsers[PlatformSource.TRIPADVISOR]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_hotel_reviews(
                    url, 
                    config.get("limit", 50)
                )
                all_reviews.extend(reviews)
        
        # Парсинг Google Maps
        if "google_maps" in sources_config:
            config = sources_config["google_maps"]
            parser = self.parsers[PlatformSource.GOOGLE_MAPS]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_place_reviews(url, config.get("limit", 50))
                all_reviews.extend(reviews)
        
        # Парсинг Яндекс.Карт
        if "yandex_maps" in sources_config:
            config = sources_config["yandex_maps"]
            parser = self.parsers[PlatformSource.YANDEX_MAPS]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_organization_reviews(
                    url,
                    config.get("limit", 50)
                )
                all_reviews.extend(reviews)
        
        # Парсинг Booking.com
        if "booking.com" in sources_config:
            config = sources_config["booking.com"]
            parser = self.parsers[PlatformSource.BOOKING]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_hotel_reviews(
                    url, 
                    config.get("limit", 50)
                )
                all_reviews.extend(reviews)
        
        # Парсинг Ostrovok
        if "ostrovok" in sources_config:
            config = sources_config["ostrovok"]
            parser = self.parsers[PlatformSource.OSTROVOK]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_hotel_reviews(
                    url, 
                    config.get("limit", 50)
                )
                all_reviews.extend(reviews)
        
        # Парсинг Manul
        if "manul" in sources_config:
            config = sources_config["manul"]
            parser = self.parsers[PlatformSource.MANUL]
            
            for url in config.get("urls", []):
                reviews = await parser.parse_reviews(
                    url, 
                    config.get("limit", 50)
                )
                all_reviews.extend(reviews)
        
        # Сохранение в БД
        if save_to_db and all_reviews:
            self._save_reviews_to_db(all_reviews)
        
        return len(all_reviews)
    
    def _save_reviews_to_db(self, reviews: List[Dict]):
        """Сохранение отзывов в БД"""
        db = SessionLocal()
        try:
            for review_data in reviews:
                # Проверка на дубликаты
                existing = db.query(Review).filter(
                    Review.platform == review_data["platform"],
                    Review.external_id == review_data.get("external_id")
                ).first()
                
                if existing:
                    continue
                
                review = Review(
                    platform=review_data["platform"],
                    external_id=review_data.get("external_id"),
                    author_name=review_data.get("author_name"),
                    rating=review_data["rating"],
                    review_text=review_data["review_text"],
                    review_date=review_data.get("review_date"),
                    status="pending",
                    is_synthetic=False
                )
                db.add(review)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


# Singleton
_parser_service_instance = None


def get_parser_service() -> ReviewParserService:
    """Получить экземпляр сервиса парсинга"""
    global _parser_service_instance
    if _parser_service_instance is None:
        _parser_service_instance = ReviewParserService()
    return _parser_service_instance
