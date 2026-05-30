import asyncio
from playwright.async_api import async_playwright

URL = "https://www.tripadvisor.ru/Hotel_Review-g298536-d304815-Reviews-City_Park_Hotel_Sochi-Sochi_Greater_Sochi_Krasnodar_Krai_Southern_District.html"

async def test_tripadvisor_parser():
    print(f"🚀 Запуск теста парсинга TripAdvisor: {URL}")
    
    async with async_playwright() as p:
        # Запускаем браузер (headless=False, чтобы видеть процесс, если нужно отладить визуально)
        # Для сервера лучше headless=True, но для первого теста можно оставить False или True по желанию
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            locale="ru-RU"
        )
        page = await context.new_page()
        
        try:
            print("⏳ Загрузка страницы...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # Даем время на подгрузку JS и контента
            print("⏳ Ожидание рендеринга контента...")
            await page.wait_for_timeout(5000) 
            
            # Пробуем найти контейнеры отзывов
            # Структура TripAdvisor часто меняется, попробуем несколько популярных селекторов
            review_selectors = [
                "[data-test-target='review-list']", # Новый контейнер списка
                ".review-list",                     # Старый класс
                "[data-review-id]",                 # Контейнеры с ID отзыва
                ".property-review-card"             # Карточки отзывов
            ]
            
            found_reviews = []
            
            for selector in review_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ Найдено элементов по селектору '{selector}': {len(elements)}")
                    found_reviews = elements
                    break
            
            if not found_reviews:
                print("❌ Не удалось найти отзывы по стандартным селекторам.")
                print("🔍 Попробуем найти любой текст, похожий на отзыв...")
                # Фоллбэк: ищем блоки с текстом
                all_texts = await page.query_selector_all(".t6C74dGK") # Пример класса текста (может меняться)
                if all_texts:
                     print(f"Найдено потенциальных текстовых блоков: {len(all_texts)}")
                     # Выведем первый попавшийся текст для анализа структуры
                     first_text = await all_texts[0].inner_text()
                     print(f"Пример текста: {first_text[:100]}...")
                else:
                    # Сохраним скриншот для отладки, если ничего не найдено
                    await page.screenshot(path="tripadvisor_debug.png")
                    print("📸 Сделан скриншот страницы: tripadvisor_debug.png")
                    print("Возможно, TripAdvisor заблокировал запрос или требует капчу.")
                    return

            # Парсим найденные элементы
            parsed_data = []
            for i, review_el in enumerate(found_reviews[:5]): # Берем первые 5 для теста
                try:
                    # Попытка извлечь данные (селекторы примерные, нужно уточнять по структуре)
                    # Текст отзыва
                    text_el = await review_el.query_selector(".t6C74dGK, .qQj1wR7V, .fMyOvFuw") 
                    text = await text_el.inner_text() if text_el else "Текст не найден"
                    
                    # Оценка (обычно в title или классе)
                    rating_el = await review_el.query_selector("[class*='bubble'], [class*='rating']")
                    rating = "N/A"
                    if rating_el:
                        rating_class = await rating_el.get_attribute("class")
                        rating_title = await rating_el.get_attribute("title")
                        rating = rating_title or rating_class
                    
                    # Автор
                    author_el = await review_el.query_selector(".bp1sYfPo, .hH56gO7m, .username")
                    author = await author_el.inner_text() if author_el else "Аноним"
                    
                    # Дата
                    date_el = await review_el.query_selector(".abXdfem, .cPQSb, .publish-date")
                    date = await date_el.inner_text() if date_el else "Дата не найдена"

                    parsed_data.append({
                        "index": i + 1,
                        "author": author.strip(),
                        "rating": rating,
                        "date": date.strip(),
                        "text": text.strip()[:150] + "..." if len(text) > 150 else text.strip()
                    })
                except Exception as e:
                    print(f"Ошибка при парсинге элемента {i}: {e}")

            print("\n" + "="*30)
            print("📊 РЕЗУЛЬТАТЫ ПАРСИНГА:")
            print("="*30)
            if parsed_data:
                for item in parsed_data:
                    print(f"\nОтзыв #{item['index']}")
                    print(f"Автор: {item['author']}")
                    print(f"Оценка: {item['rating']}")
                    print(f"Дата: {item['date']}")
                    print(f"Текст: {item['text']}")
            else:
                print("Данные не удалось распарсить, хотя элементы найдены.")
                
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
        finally:
            await browser.close()
            print("\n✅ Тест завершен.")

if __name__ == "__main__":
    asyncio.run(test_tripadvisor_parser())
