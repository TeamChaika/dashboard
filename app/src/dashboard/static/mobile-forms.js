/**
 * Mobile Forms Enhancement
 * Улучшения форм для мобильных устройств
 */

class MobileForms {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.init();
    }
    
    init() {
        if (!this.isMobile) {
            console.log('📱 Desktop detected, mobile enhancements disabled');
            return;
        }
        
        console.log('📱 Mobile detected, enabling enhancements...');
        
        // 1. Sticky кнопка отправки
        this.createStickySubmit();
        
        // 2. FAB для добавления товаров
        this.createFAB();
        
        // 3. Свайп для удаления
        this.enableSwipeToDelete();
        
        // 4. Автофокус на следующее поле
        this.enableAutoFocus();
        
        // 5. Haptic feedback
        this.enableHapticFeedback();
        
        // 6. Улучшенная анимация добавления
        this.enhanceItemAddition();
        
        // 7. Keyboard avoiding
        this.enableKeyboardAvoiding();
        
        console.log('✅ Mobile enhancements enabled');
    }
    
    /**
     * 1. Создаём sticky кнопку отправки
     */
    createStickySubmit() {
        const form = document.querySelector('form[method="post"]');
        if (!form) return;
        
        const submitBtn = form.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        
        // Создаём sticky контейнер
        const stickyContainer = document.createElement('div');
        stickyContainer.className = 'mobile-sticky-actions';
        
        // Клонируем кнопку
        const stickyBtn = submitBtn.cloneNode(true);
        stickyBtn.classList.add('btn-ripple');
        
        stickyContainer.appendChild(stickyBtn);
        document.body.appendChild(stickyContainer);
        
        // Показываем при скролле вниз
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 200) {
                stickyContainer.classList.add('visible');
            } else {
                stickyContainer.classList.remove('visible');
            }
            
            lastScroll = currentScroll;
        });
        
        // Синхронизируем отправку
        stickyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            submitBtn.click();
        });
        
        console.log('✅ Sticky submit button created');
    }
    
    /**
     * 2. Создаём FAB (Floating Action Button)
     */
    createFAB() {
        const plusBtn = document.querySelector('.plus');
        if (!plusBtn) return;
        
        const fab = document.createElement('button');
        fab.className = 'fab-add-item';
        fab.innerHTML = '+';
        fab.type = 'button';
        fab.setAttribute('aria-label', 'Добавить товар');
        
        document.body.appendChild(fab);
        
        fab.addEventListener('click', () => {
            plusBtn.click();
            this.vibrate(50);
            
            // Прокручиваем к новому полю
            setTimeout(() => {
                const lastItem = document.querySelector('input[name="products_names[]"]:last-of-type');
                if (lastItem) {
                    lastItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    lastItem.focus();
                }
            }, 100);
        });
        
        console.log('✅ FAB created');
    }
    
    /**
     * 3. Свайп для удаления строк
     */
    enableSwipeToDelete() {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        let targetElement = null;
        
        document.addEventListener('touchstart', (e) => {
            const minusBtn = e.target.closest('.minus');
            if (!minusBtn) {
                const row = e.target.closest('tr');
                if (row && row.querySelector('.minus')) {
                    targetElement = row;
                    startX = e.touches[0].clientX;
                    isDragging = true;
                    targetElement.classList.add('swipeable-item');
                }
            }
        });
        
        document.addEventListener('touchmove', (e) => {
            if (!isDragging || !targetElement) return;
            
            currentX = e.touches[0].clientX;
            const diff = startX - currentX;
            
            if (diff > 0) { // Свайп влево
                targetElement.style.transform = `translateX(-${Math.min(diff, 100)}px)`;
                targetElement.classList.add('swiping');
            }
        });
        
        document.addEventListener('touchend', () => {
            if (!isDragging || !targetElement) return;
            
            const diff = startX - currentX;
            
            if (diff > 80) {
                // Удаляем
                targetElement.classList.add('deleting');
                this.vibrate(30);
                
                setTimeout(() => {
                    const minusBtn = targetElement.querySelector('.minus');
                    if (minusBtn) {
                        minusBtn.click();
                    }
                }, 300);
            } else {
                // Возвращаем на место
                targetElement.style.transform = '';
            }
            
            targetElement.classList.remove('swiping');
            isDragging = false;
            targetElement = null;
        });
        
        console.log('✅ Swipe to delete enabled');
    }
    
    /**
     * 4. Автофокус на следующее поле
     */
    enableAutoFocus() {
        document.addEventListener('input', (e) => {
            const input = e.target;
            
            // Если заполнили название товара, переходим к количеству
            if (input.name === 'products_names[]' && input.value) {
                const row = input.closest('tr');
                if (row) {
                    const amountInput = row.querySelector('input[name="products_counts[]"]');
                    if (amountInput && !amountInput.value) {
                        setTimeout(() => {
                            amountInput.focus();
                        }, 100);
                    }
                }
            }
        });
        
        console.log('✅ Auto focus enabled');
    }
    
    /**
     * 5. Haptic feedback (вибрация)
     */
    enableHapticFeedback() {
        // Для кнопок
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn, .fab-add-item, .minus')) {
                this.vibrate(30);
            }
        });
        
        // Для успешной отправки формы
        const form = document.querySelector('form[method="post"]');
        if (form) {
            form.addEventListener('submit', () => {
                this.vibrate([50, 50, 100]);
            });
        }
        
        console.log('✅ Haptic feedback enabled');
    }
    
    /**
     * 6. Улучшенная анимация добавления строк
     */
    enhanceItemAddition() {
        const plusBtn = document.querySelector('.plus');
        if (!plusBtn) return;
        
        const originalClick = plusBtn.onclick;
        plusBtn.onclick = function(e) {
            if (originalClick) {
                originalClick.call(this, e);
            }
            
            setTimeout(() => {
                const rows = document.querySelectorAll('tr:has(input[name="products_names[]"])');
                const lastRow = rows[rows.length - 1];
                if (lastRow) {
                    lastRow.classList.add('item-row-new');
                    setTimeout(() => {
                        lastRow.classList.remove('item-row-new');
                    }, 300);
                }
            }, 50);
        };
        
        console.log('✅ Enhanced item addition');
    }
    
    /**
     * 7. Keyboard avoiding (прокрутка при фокусе)
     */
    enableKeyboardAvoiding() {
        document.addEventListener('focus', (e) => {
            if (e.target.matches('.form-control, .form-select')) {
                setTimeout(() => {
                    e.target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 300); // Задержка для анимации клавиатуры
            }
        }, true);
        
        console.log('✅ Keyboard avoiding enabled');
    }
    
    /**
     * Вибрация (если поддерживается)
     */
    vibrate(pattern) {
        if ('vibrate' in navigator) {
            navigator.vibrate(pattern);
        }
    }
    
    /**
     * Ripple effect для кнопок
     */
    static addRipple(element) {
        element.classList.add('btn-ripple');
    }
}

// Глобальный экземпляр
window.mobileForms = null;

// Автоматическая инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileForms = new MobileForms();
    });
} else {
    window.mobileForms = new MobileForms();
}

// Переинициализация при изменении размера окна
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        const wasMobile = window.mobileForms && window.mobileForms.isMobile;
        const isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== isMobile) {
            window.location.reload();
        }
    }, 250);
});

console.log('✅ MobileForms загружен');

