document.addEventListener('DOMContentLoaded', () => {
    // --- Системные элементы интерфейса ---
    const menuBtn = document.getElementById('menuBtn');
    const closeSidebar = document.getElementById('closeSidebar');
    const sidebarMenu = document.getElementById('sidebarMenu');

    const searchBtn = document.getElementById('searchBtn');
    const searchContainer = document.getElementById('searchContainer');
    const searchInput = document.getElementById('searchInput');

    const themeBtn = document.getElementById('ThemBtn');
    const themeIcon = document.getElementById('themeIcon');
    const langBtn = document.getElementById('LangBtn');
    const logoImg = document.getElementById('logoImg');

    // --- Сворачивание очереди на рабочей странице ---
    const collapsePanelBtn = document.getElementById('collapsePanelBtn');
    const reviewsPanel = document.getElementById('reviewsPanel');

    const editBtn = document.querySelector('.action-btn.secondary');
    const aiTextArea = document.getElementById('aiResponseText');

    const notepad = document.querySelector('.notepad-input');
    const saveBtn = document.querySelector('.save-notes-btn');

    if (collapsePanelBtn && reviewsPanel) {
    collapsePanelBtn.addEventListener('click', () => {
        reviewsPanel.classList.toggle('collapsed');
        
        // Меняем стрелочку в зависимости от состояния
        if (reviewsPanel.classList.contains('collapsed')) {
            collapsePanelBtn.textContent = '»'; // Развернуть
        } else {
            collapsePanelBtn.textContent = '«'; // Свернуть
        }
    });
}

    // --- Инициализация состояний из localStorage ---
    let currentTheme = localStorage.getItem('app-theme') || 'dark';
    let currentLang = localStorage.getItem('app-lang') || 'ru';

    // Функция применения темы и обновления SVG-иконки (Солнце / Луна)
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('app-theme', theme);
        
        if (logoImg) {
            logoImg.src = (theme === 'light') ? 'all_img/logo-black.png' : 'all_img/logo-white.png';
        }

        if (themeIcon) {
            if (theme === 'light') {
                themeIcon.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:100%; height:100%; color:#0f172a;">
                        <circle cx="12" cy="12" r="5"></circle>
                        <line x1="12" y1="1" x2="12" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="23"></line>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                        <line x1="1" y1="12" x2="3" y2="12"></line>
                        <line x1="21" y1="12" x2="23" y2="12"></line>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                    </svg>
                `;
            } else {
                themeIcon.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:100%; height:100%; color:#ffffff;">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                `;
            }
        }
    }

    // Применение языка и локализация активных элементов селекторов
    function applyLanguage(lang) {
        localStorage.setItem('app-lang', lang);
        if (langBtn) {
            const langText = langBtn.querySelector('.lang-text');
            if (langText) langText.textContent = lang.toUpperCase();
        }

        document.querySelectorAll('[data-ru]').forEach(el => {
            if (lang === 'ru') {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    if (el.hasAttribute('data-ru-placeholder')) {
                        el.setAttribute('placeholder', el.getAttribute('data-ru-placeholder'));
                    }
                } else {
                    if (!el.classList.contains('dropdown-option')) {
                        el.textContent = el.getAttribute('data-ru');
                    }
                }
            }
        });

        document.querySelectorAll('[data-en]').forEach(el => {
            if (lang === 'en') {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    if (el.hasAttribute('data-en-placeholder')) {
                        el.setAttribute('placeholder', el.getAttribute('data-en-placeholder'));
                    }
                } else {
                    if (!el.classList.contains('dropdown-option')) {
                        el.textContent = el.getAttribute('data-en');
                    }
                }
            }
        });

        // Синхронизируем отображаемый текст в селекторах под текущий язык
        selectPairs.forEach(pair => {
            const dropdownEl = document.getElementById(pair.dropdown);
            const valueEl = document.getElementById(pair.value); // Может быть null для aiModel
            if (dropdownEl && valueEl) {
                const activeOption = dropdownEl.querySelector('.dropdown-option.active');
                if (activeOption) {
                    valueEl.textContent = activeOption.getAttribute(`data-${lang}`) || activeOption.textContent;
                }
            }
        });
    }

    // Первичный вызов конфигурации
    applyTheme(currentTheme);

    // Управление сайдбаром
    function toggleSidebar() {
        if (sidebarMenu) {
            sidebarMenu.classList.toggle('active');
            document.body.classList.toggle('sidebar-open');
        }
    }

    if (menuBtn) menuBtn.addEventListener('click', toggleSidebar);
    if (closeSidebar) closeSidebar.addEventListener('click', toggleSidebar);

    // Поиск анимированный
    if (searchBtn && searchContainer) {
        searchBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            searchContainer.classList.toggle('active');
            if (searchContainer.classList.contains('active') && searchInput) {
                searchInput.focus();
            }
        });
    }

    // Переключатели в шапке
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            currentTheme = (currentTheme === 'dark') ? 'light' : 'dark';
            applyTheme(currentTheme);
        });
    }

    if (langBtn) {
        langBtn.addEventListener('click', () => {
            currentLang = (currentLang === 'ru') ? 'en' : 'ru';
            applyLanguage(currentLang);
        });
    }

    // --- Кастомные выпадающие списки (Настройки) ---
    const selectPairs = [
        { trigger: 'modeTrigger', dropdown: 'modeDropdown', value: 'modeValue' },
        { trigger: 'lengthTrigger', dropdown: 'lengthDropdown', value: 'lengthValue' },
        { trigger: 'aiModelTrigger', dropdown: 'aiModelDropdown', value: 'aiModelValue' }, // Добавили гипотетический value или обработаем ниже безопаснее
        { trigger: 'toneTrigger', dropdown: 'toneDropdown', value: 'toneValue' },
        { trigger: 'parseTrigger', dropdown: 'parseDropdown', value: 'parseValue' }
    ];

    selectPairs.forEach(pair => {
        const triggerEl = document.getElementById(pair.trigger);
        const dropdownEl = document.getElementById(pair.dropdown);
        const valueEl = document.getElementById(pair.value);

        // Безопасная проверка: вешаем события, только если триггер и дропдаун существуют на странице
        if (triggerEl && dropdownEl) {
            triggerEl.addEventListener('click', (e) => {
                e.stopPropagation();
                // Закрываем другие открытые списки
                selectPairs.forEach(p => {
                    if (p.trigger !== pair.trigger) {
                        const d = document.getElementById(p.dropdown);
                        const t = document.getElementById(p.trigger);
                        if (d) d.classList.remove('active');
                        if (t) t.classList.remove('open');
                    }
                });
                dropdownEl.classList.toggle('active');
                triggerEl.classList.toggle('open');
            });

            dropdownEl.querySelectorAll('.dropdown-option').forEach(option => {
                option.addEventListener('click', (e) => {
                    e.stopPropagation();
                    dropdownEl.querySelectorAll('.dropdown-option').forEach(opt => opt.classList.remove('active'));
                    option.classList.add('active');
                    
                    // Обновляем текст, только если текстовый элемент существует
                    if (valueEl) {
                        const lang = localStorage.getItem('app-lang') || 'ru';
                        valueEl.textContent = option.getAttribute(`data-${lang}`) || option.textContent;
                    }
                    
                    dropdownEl.classList.remove('active');
                    triggerEl.classList.remove('open');
                });
            });
        }
    });

    // Поздняя инициализация языка (после регистрации структуры selectPairs)
    applyLanguage(currentLang);

    // Глобальный клик: закрытие окон поиска, сайдбара и селекторов при клике в пустую область
    document.addEventListener('click', (e) => {
        // Безопасная проверка сайдбара
        if (sidebarMenu && sidebarMenu.classList.contains('active')) {
            const isClickInsideSidebar = sidebarMenu.contains(e.target);
            const isClickOnMenuBtn = menuBtn && menuBtn.contains(e.target);
            
            if (!isClickInsideSidebar && !isClickOnMenuBtn) {
                toggleSidebar();
            }
        }
        
        // Безопасная проверка контейнера поиска
        if (searchContainer && searchContainer.classList.contains('active')) {
            const isClickInsideSearch = searchContainer.contains(e.target);
            const isClickOnSearchBtn = searchBtn && searchBtn.contains(e.target);
            
            if (!isClickInsideSearch && !isClickOnSearchBtn) {
                searchContainer.classList.remove('active');
            }
        }
        
        // Безопасная проверка кастомных селекторов
        selectPairs.forEach(pair => {
            const dropdown = document.getElementById(pair.dropdown);
            const trigger = document.getElementById(pair.trigger);
            if (dropdown && dropdown.classList.contains('active')) {
                if (!dropdown.contains(e.target) && (!trigger || !trigger.contains(e.target))) {
                    dropdown.classList.remove('active');
                    if (trigger) trigger.classList.remove('open');
                }
            }
        });
    });

    // --- Автоматический слайдер новостей ---
    const slides = document.querySelectorAll('.slide');
    const progressBar = document.querySelector('.timer-progress');

    if (slides.length > 0 && progressBar) {
        let slideIndex = 0;
        let slideInterval;

        function updateSlide(index) {
            slides.forEach(s => s.classList.remove('active'));
            progressBar.style.transition = 'none';
            progressBar.style.width = '0%';
            
            setTimeout(() => {
                if (slides[index]) slides[index].classList.add('active');
                progressBar.style.transition = 'width 6000ms linear';
                progressBar.style.width = '100%';
            }, 50);

            slideIndex = index;
        }

        function moveNext() {
            let next = (slideIndex + 1) % slides.length;
            updateSlide(next);
        }

        function startTimer() {
            clearInterval(slideInterval);
            slideInterval = setInterval(moveNext, 6000);
        }

        const nextBtn = document.getElementById('nextSlide');
        const prevBtn = document.getElementById('prevSlide');

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                moveNext();
                startTimer();
            });
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                let prev = (slideIndex - 1 + slides.length) % slides.length;
                updateSlide(prev);
                startTimer();
            });
        }

        updateSlide(0);
        startTimer();
    }

    if (editBtn) {
    editBtn.addEventListener('click', () => {
        if (aiTextArea && aiTextArea.hasAttribute('readonly')) {
            aiTextArea.removeAttribute('readonly');
            aiTextArea.focus();
        }
    });
    }

    // Загружаем заметку при старте страницы
        if (notepad) {
            notepad.value = localStorage.getItem('manager_notes') || '';
        }

    // Сохраняем по клику
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
            localStorage.setItem('manager_notes', notepad.value);
            alert('Заметки успешно сохранены локально!');
            });
}
});