/**
 * Form Autosave System
 * Автоматическое сохранение форм в LocalStorage
 */

class FormAutosave {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        if (!this.form) {
            console.warn('Form not found:', formSelector);
            return;
        }
        
        this.options = {
            storageKey: options.storageKey || 'form_draft',
            saveDelay: options.saveDelay || 2000, // 2 секунды после изменения
            autoSaveInterval: options.autoSaveInterval || 30000, // 30 секунд
            showIndicator: options.showIndicator !== false,
            excludeFields: options.excludeFields || [],
            onSave: options.onSave || null,
            onRestore: options.onRestore || null
        };
        
        this.saveTimeout = null;
        this.autoSaveTimer = null;
        this.lastSaveTime = null;
        
        this.init();
    }
    
    init() {
        // Создаём индикатор сохранения
        if (this.options.showIndicator) {
            this.createIndicator();
        }
        
        // Пытаемся восстановить черновик
        this.restoreDraft();
        
        // Слушаем изменения
        this.attachListeners();
        
        // Автосохранение по таймеру
        this.startAutoSave();
        
        // Очистка при успешной отправке
        this.attachSubmitHandler();
        
        console.log('✅ FormAutosave инициализирован:', this.options.storageKey);
    }
    
    createIndicator() {
        this.indicator = document.createElement('div');
        this.indicator.className = 'autosave-indicator';
        this.indicator.innerHTML = '<i class="bx bx-check-circle"></i> <span>Сохранено</span>';
        this.indicator.style.display = 'none';
        
        // На мобильных добавляем в body для избежания конфликтов
        const isMobile = window.innerWidth <= 768;
        
        if (isMobile) {
            // На мобильных - в body (fixed positioning) с inline стилями
            document.body.appendChild(this.indicator);
            
            // Принудительные inline стили для мобильных
            if (window.innerWidth <= 576) {
                this.indicator.style.width = '48px';
                this.indicator.style.height = '48px';
                this.indicator.style.minWidth = '48px';
                this.indicator.style.maxWidth = '48px';
                this.indicator.style.borderRadius = '50%';
                this.indicator.style.padding = '12px';
                this.indicator.style.left = 'auto';
                this.indicator.style.right = '20px';
                this.indicator.style.bottom = '80px';
                this.indicator.style.top = 'auto';
            } else {
                this.indicator.style.width = 'fit-content';
                this.indicator.style.maxWidth = '200px';
                this.indicator.style.left = 'auto';
                this.indicator.style.right = '16px';
                this.indicator.style.top = '16px';
            }
        } else {
            // На desktop - рядом с кнопкой отправки
            const submitBtn = this.form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.parentNode.insertBefore(this.indicator, submitBtn);
            } else {
                this.form.appendChild(this.indicator);
            }
        }
    }
    
    attachListeners() {
        // Слушаем все изменения в форме
        this.form.addEventListener('input', (e) => {
            this.scheduleAutosave();
        });
        
        this.form.addEventListener('change', (e) => {
            this.scheduleAutosave();
        });
        
        // Динамически добавляемые поля
        const observer = new MutationObserver(() => {
            this.scheduleAutosave();
        });
        
        observer.observe(this.form, {
            childList: true,
            subtree: true
        });
    }
    
    attachSubmitHandler() {
        this.form.addEventListener('submit', (e) => {
            // Очищаем черновик при успешной отправке
            this.clearDraft();
        });
    }
    
    scheduleAutosave() {
        // Отменяем предыдущий таймер
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        // Сохраняем через delay
        this.saveTimeout = setTimeout(() => {
            this.saveDraft();
        }, this.options.saveDelay);
    }
    
    startAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            this.saveDraft();
        }, this.options.autoSaveInterval);
    }
    
    saveDraft() {
        const data = this.collectFormData();
        
        if (!data || Object.keys(data).length === 0) {
            return;
        }
        
        const draft = {
            data: data,
            timestamp: Date.now(),
            url: window.location.pathname
        };
        
        try {
            localStorage.setItem(this.options.storageKey, JSON.stringify(draft));
            this.lastSaveTime = Date.now();
            this.showSaveIndicator();
            
            if (this.options.onSave) {
                this.options.onSave(draft);
            }
            
            console.log('💾 Черновик сохранён:', this.options.storageKey);
        } catch (e) {
            console.error('Ошибка сохранения черновика:', e);
        }
    }
    
    collectFormData() {
        const data = {};
        
        // Обычные поля
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Пропускаем исключённые поля
            if (this.options.excludeFields.includes(input.name)) {
                return;
            }
            
            // Пропускаем пустые поля без name
            if (!input.name) {
                return;
            }
            
            // Для массивов (products_names[], products_counts[])
            if (input.name.includes('[]')) {
                if (!data[input.name]) {
                    data[input.name] = [];
                }
                data[input.name].push(input.value);
            } else {
                data[input.name] = input.value;
            }
        });
        
        return data;
    }
    
    restoreDraft() {
        try {
            const stored = localStorage.getItem(this.options.storageKey);
            if (!stored) {
                return;
            }
            
            const draft = JSON.parse(stored);
            
            // Проверяем что черновик для этой страницы
            if (draft.url !== window.location.pathname) {
                return;
            }
            
            // Проверяем возраст черновика (не старше 7 дней)
            const age = Date.now() - draft.timestamp;
            const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 дней
            
            if (age > maxAge) {
                this.clearDraft();
                return;
            }
            
            // Проверяем что есть хотя бы один товар
            const hasProducts = this.hasValidProducts(draft.data);
            if (!hasProducts) {
                console.log('🗑️ Черновик пустой (нет товаров), очищаем');
                this.clearDraft();
                return;
            }
            
            // Спрашиваем пользователя
            const ageFormatted = this.formatAge(age);
            const productsCount = this.countProducts(draft.data);
            const confirmed = confirm(
                `Найден несохранённый черновик (${ageFormatted} назад).\n` +
                `Товаров: ${productsCount}\n\n` +
                `Восстановить?`
            );
            
            if (confirmed) {
                this.fillForm(draft.data);
                showInfo('Черновик восстановлен');
                
                if (this.options.onRestore) {
                    this.options.onRestore(draft);
                }
                
                console.log('📋 Черновик восстановлен');
            } else {
                this.clearDraft();
            }
        } catch (e) {
            console.error('Ошибка восстановления черновика:', e);
        }
    }
    
    /**
     * Проверяет есть ли в черновике хотя бы один товар
     */
    hasValidProducts(data) {
        const productNames = data['products_names[]'];
        
        if (!productNames || !Array.isArray(productNames)) {
            return false;
        }
        
        // Проверяем что есть хотя бы одно непустое название
        return productNames.some(name => name && name.trim().length > 0);
    }
    
    /**
     * Считает количество товаров с заполненными названиями
     */
    countProducts(data) {
        const productNames = data['products_names[]'];
        
        if (!productNames || !Array.isArray(productNames)) {
            return 0;
        }
        
        return productNames.filter(name => name && name.trim().length > 0).length;
    }
    
    fillForm(data) {
        // Заполняем обычные поля
        for (const [name, value] of Object.entries(data)) {
            if (name.includes('[]')) {
                // Для массивов
                const inputs = this.form.querySelectorAll(`[name="${name}"]`);
                
                // Если полей меньше чем значений - добавляем
                if (inputs.length < value.length) {
                    const diff = value.length - inputs.length;
                    for (let i = 0; i < diff; i++) {
                        // Триггерим кнопку "Добавить позицию"
                        const addBtn = this.form.querySelector('.plus');
                        if (addBtn) {
                            addBtn.click();
                        }
                    }
                }
                
                // Заполняем значения
                setTimeout(() => {
                    const updatedInputs = this.form.querySelectorAll(`[name="${name}"]`);
                    updatedInputs.forEach((input, index) => {
                        if (value[index]) {
                            input.value = value[index];
                        }
                    });
                }, 100);
            } else {
                // Для обычных полей
                const input = this.form.querySelector(`[name="${name}"]`);
                if (input) {
                    input.value = value;
                }
            }
        }
    }
    
    clearDraft() {
        localStorage.removeItem(this.options.storageKey);
        console.log('🗑️ Черновик удалён:', this.options.storageKey);
    }
    
    showSaveIndicator() {
        if (!this.indicator) return;
        
        this.indicator.style.display = 'flex';
        this.indicator.classList.add('show');
        
        setTimeout(() => {
            this.indicator.classList.remove('show');
            setTimeout(() => {
                this.indicator.style.display = 'none';
            }, 300);
        }, 2000);
    }
    
    formatAge(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days} дн.`;
        if (hours > 0) return `${hours} ч.`;
        if (minutes > 0) return `${minutes} мин.`;
        return `${seconds} сек.`;
    }
    
    destroy() {
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
    }
}

// Глобальный экземпляр
window.FormAutosave = FormAutosave;

console.log('✅ FormAutosave загружен');

