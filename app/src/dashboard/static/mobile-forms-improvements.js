/**
 * Mobile Forms UI/UX Improvements
 * Дополнительная функциональность для улучшения UX
 */

class MobileFormsImprovements {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        if (!this.isMobile) {
            console.log('📱 Desktop detected, mobile improvements skipped');
            return;
        }
        
        this.init();
    }
    
    init() {
        console.log('✨ Initializing mobile form improvements...');
        
        // 1. Счётчик товаров
        this.createProductsCounter();
        
        // 2. Прогресс бар заполнения
        this.createProgressBar();
        
        // 3. Нумерация карточек товаров
        this.numberProductCards();
        
        // 4. Пустое состояние
        this.checkEmptyState();
        
        // 5. Анимация удаления
        this.enhanceDeleteAnimation();
        
        // 6. Autocomplete hints
        this.addAutocompleteHints();
        
        // 7. Haptic feedback (iOS)
        this.enableHapticFeedback();
        
        // 8. Наблюдатель за изменениями
        this.watchFormChanges();
        
        console.log('✅ Mobile improvements enabled');
    }
    
    /**
     * 1. Создаём счётчик товаров
     */
    createProductsCounter() {
        const counter = document.createElement('div');
        counter.className = 'products-counter';
        counter.innerHTML = '<span class="count">0</span>';
        document.body.appendChild(counter);
        
        this.counter = counter;
        this.updateProductsCount();
        
        console.log('✅ Products counter created');
    }
    
    /**
     * 2. Создаём прогресс бар
     */
    createProgressBar() {
        const progress = document.createElement('div');
        progress.className = 'form-progress';
        progress.innerHTML = '<div class="form-progress-bar" style="width: 0%"></div>';
        document.body.appendChild(progress);
        
        this.progressBar = progress.querySelector('.form-progress-bar');
        this.updateProgress();
        
        console.log('✅ Progress bar created');
    }
    
    /**
     * 3. Нумерация карточек
     */
    numberProductCards() {
        const cards = document.querySelectorAll('.input-group');
        cards.forEach((card, index) => {
            card.setAttribute('data-index', `#${index + 1}`);
        });
    }
    
    /**
     * 4. Проверка пустого состояния
     */
    checkEmptyState() {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;
        
        const products = form.querySelectorAll('input[name="products_names[]"]');
        
        if (products.length === 0) {
            this.showEmptyState();
        }
    }
    
    showEmptyState() {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;
        
        // Ищем где вставить
        const table = form.querySelector('table');
        if (!table) return;
        
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-products-state';
        emptyState.innerHTML = '<p>Нажмите на <strong>+</strong> чтобы добавить товар</p>';
        
        table.parentNode.insertBefore(emptyState, table.nextSibling);
        this.emptyState = emptyState;
    }
    
    hideEmptyState() {
        if (this.emptyState) {
            this.emptyState.remove();
            this.emptyState = null;
        }
    }
    
    /**
     * 5. Анимация удаления
     */
    enhanceDeleteAnimation() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.minus')) {
                const card = e.target.closest('.input-group');
                if (card) {
                    card.classList.add('removing');
                    this.vibrate(50);
                    
                    setTimeout(() => {
                        this.updateProductsCount();
                        this.numberProductCards();
                        this.updateProgress();
                        this.checkEmptyState();
                    }, 300);
                }
            }
        });
    }
    
    /**
     * 6. Подсказки для autocomplete
     */
    addAutocompleteHints() {
        const inputs = document.querySelectorAll('input[list="nomenclature"]');
        inputs.forEach(input => {
            const hint = document.createElement('div');
            hint.className = 'autocomplete-hint';
            hint.textContent = 'Начните вводить название';
            input.parentNode.appendChild(hint);
        });
    }
    
    /**
     * 7. Haptic feedback
     */
    enableHapticFeedback() {
        // Для кнопок
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn, .minus, .plus')) {
                this.vibrate(30);
            }
        });
        
        // Для фокуса на поле
        document.addEventListener('focus', (e) => {
            if (e.target.matches('.form-control')) {
                this.vibrate(10);
            }
        }, true);
    }
    
    /**
     * 8. Наблюдатель за изменениями
     */
    watchFormChanges() {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;
        
        // Наблюдаем за добавлением/удалением полей
        const observer = new MutationObserver(() => {
            this.updateProductsCount();
            this.numberProductCards();
            this.updateProgress();
            this.checkEmptyState();
            this.addAutocompleteHints();
        });
        
        observer.observe(form, {
            childList: true,
            subtree: true
        });
        
        // Наблюдаем за заполнением полей
        form.addEventListener('input', () => {
            this.updateProgress();
        });
    }
    
    /**
     * Обновление счётчика товаров
     */
    updateProductsCount() {
        const products = document.querySelectorAll('input[name="products_names[]"]');
        const count = products.length;
        
        if (this.counter) {
            const countEl = this.counter.querySelector('.count');
            countEl.textContent = count;
            
            // Анимация
            this.counter.style.transform = 'scale(1.2)';
            setTimeout(() => {
                this.counter.style.transform = 'scale(1)';
            }, 200);
        }
        
        // Скрываем/показываем пустое состояние
        if (count === 0) {
            this.showEmptyState();
        } else {
            this.hideEmptyState();
        }
    }
    
    /**
     * Обновление прогресс бара
     */
    updateProgress() {
        const form = document.querySelector('form[method="post"]');
        if (!form || !this.progressBar) return;
        
        const requiredFields = [
            'user_store_name',
            'counteragent_store_name',
            'products_names[]'
        ];
        
        let filledCount = 0;
        let totalCount = requiredFields.length;
        
        // Склад
        const store = form.querySelector('input[name="user_store_name"]');
        if (store && store.value.trim()) filledCount++;
        
        // Контрагент
        const counteragent = form.querySelector('input[name="counteragent_store_name"]');
        if (counteragent && counteragent.value.trim()) filledCount++;
        
        // Товары (хотя бы один)
        const products = form.querySelectorAll('input[name="products_names[]"]');
        const hasProduct = Array.from(products).some(p => p.value.trim());
        if (hasProduct) filledCount++;
        
        const progress = (filledCount / totalCount) * 100;
        this.progressBar.style.width = `${progress}%`;
    }
    
    /**
     * Вибрация
     */
    vibrate(duration) {
        if ('vibrate' in navigator) {
            navigator.vibrate(duration);
        }
    }
}

// Глобальный экземпляр
window.mobileFormsImprovements = null;

// Автоматическая инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileFormsImprovements = new MobileFormsImprovements();
    });
} else {
    window.mobileFormsImprovements = new MobileFormsImprovements();
}

console.log('✅ MobileFormsImprovements loaded');

