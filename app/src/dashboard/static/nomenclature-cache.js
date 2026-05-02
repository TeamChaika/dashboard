/**
 * Nomenclature Cache Manager
 * 
 * Управляет кэшированием номенклатуры в LocalStorage для ускорения загрузки страниц.
 * 
 * Основные возможности:
 * - Загрузка номенклатуры с сервера через API
 * - Кэширование в LocalStorage на 24 часа
 * - Автоматическое обновление при истечении срока
 * - Принудительное обновление
 * 
 * @example
 * const cache = new NomenclatureCache();
 * const products = await cache.get();
 * console.log(`Загружено ${products.length} товаров`);
 */

class NomenclatureCache {
    constructor() {
        this.storageKey = 'iiko_nomenclature';
        this.versionKey = 'iiko_nomenclature_version';
        this.version = '1.0'; // Увеличивайте при изменении структуры данных
        this.cacheTime = 24 * 60 * 60 * 1000; // 24 часа в миллисекундах
        this.apiUrl = '/api/nomenclature';
    }

    /**
     * Получить номенклатуру (из кэша или с сервера)
     * @returns {Promise<Array<string>>} Массив названий товаров
     */
    async get() {
        // Проверяем версию кэша
        const cachedVersion = localStorage.getItem(this.versionKey);
        if (cachedVersion !== this.version) {
            console.log('🔄 Версия кэша устарела, очищаем...');
            this.clear();
        }

        // Пытаемся получить из кэша
        const cached = localStorage.getItem(this.storageKey);
        if (cached) {
            try {
                const data = JSON.parse(cached);
                const age = Date.now() - data.timestamp;
                
                // Проверяем свежесть данных
                if (age < this.cacheTime) {
                    console.log(`📦 Номенклатура из кэша (${this._formatAge(age)} назад)`);
                    return data.products;
                } else {
                    console.log('⏰ Кэш устарел, обновляем...');
                }
            } catch (e) {
                console.error('❌ Ошибка чтения кэша:', e);
                this.clear();
            }
        }

        // Загружаем с сервера
        return await this.refresh();
    }

    /**
     * Принудительно обновить номенклатуру с сервера
     * @returns {Promise<Array<string>>} Массив названий товаров
     */
    async refresh() {
        try {
            console.log('🌐 Загрузка номенклатуры с сервера...');
            const startTime = Date.now();
            
            const response = await fetch(this.apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                credentials: 'same-origin' // Включаем cookies для аутентификации
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            const loadTime = Date.now() - startTime;

            // Сохраняем в LocalStorage
            localStorage.setItem(this.storageKey, JSON.stringify({
                products: result.products,
                timestamp: Date.now(),
                count: result.count
            }));

            // Сохраняем версию
            localStorage.setItem(this.versionKey, this.version);

            console.log(`✅ Загружено ${result.count} товаров за ${loadTime}ms`);
            return result.products;

        } catch (error) {
            console.error('❌ Ошибка загрузки номенклатуры:', error);
            
            // Пытаемся использовать устаревший кэш как fallback
            const cached = localStorage.getItem(this.storageKey);
            if (cached) {
                console.warn('⚠️ Используем устаревший кэш из-за ошибки загрузки');
                const data = JSON.parse(cached);
                return data.products;
            }

            throw error;
        }
    }

    /**
     * Очистить кэш
     */
    clear() {
        localStorage.removeItem(this.storageKey);
        localStorage.removeItem(this.versionKey);
        console.log('🗑️ Кэш очищен');
    }

    /**
     * Получить информацию о кэше
     * @returns {Object} Информация о кэше
     */
    getInfo() {
        const cached = localStorage.getItem(this.storageKey);
        if (!cached) {
            return { exists: false };
        }

        try {
            const data = JSON.parse(cached);
            const age = Date.now() - data.timestamp;
            
            return {
                exists: true,
                count: data.count,
                timestamp: data.timestamp,
                age: age,
                ageFormatted: this._formatAge(age),
                isExpired: age >= this.cacheTime,
                size: new Blob([cached]).size
            };
        } catch (e) {
            return { exists: false, error: e.message };
        }
    }

    /**
     * Форматировать возраст кэша для вывода
     * @private
     */
    _formatAge(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}ч ${minutes % 60}мин`;
        } else if (minutes > 0) {
            return `${minutes}мин`;
        } else {
            return `${seconds}сек`;
        }
    }
}


/**
 * Recent Products Manager
 * 
 * Управляет списком недавно использованных товаров.
 * Используется для быстрого доступа к часто используемым товарам.
 */
class RecentProducts {
    constructor() {
        this.storageKey = 'iiko_recent_products';
        this.maxItems = 20;
    }

    /**
     * Добавить товар в список недавних
     * @param {string} productName Название товара
     */
    add(productName) {
        if (!productName) return;

        let recent = this.get();
        
        // Убираем если уже есть (чтобы переместить в начало)
        recent = recent.filter(name => name !== productName);
        
        // Добавляем в начало
        recent.unshift(productName);
        
        // Ограничиваем количество
        recent = recent.slice(0, this.maxItems);
        
        localStorage.setItem(this.storageKey, JSON.stringify(recent));
    }

    /**
     * Получить список недавних товаров
     * @returns {Array<string>} Массив названий товаров
     */
    get() {
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : [];
    }

    /**
     * Очистить список недавних товаров
     */
    clear() {
        localStorage.removeItem(this.storageKey);
    }
}


/**
 * Nomenclature Helper
 * 
 * Вспомогательные функции для работы с номенклатурой в формах.
 */
class NomenclatureHelper {
    constructor(cache, recentProducts) {
        this.cache = cache;
        this.recentProducts = recentProducts;
    }

    /**
     * Инициализировать datalist элементы на странице
     * @param {string} datalistId ID элемента datalist (по умолчанию 'nomenclature')
     */
    async initializeDatalist(datalistId = 'nomenclature') {
        const $datalist = $(`#${datalistId}`);
        if ($datalist.length === 0) {
            console.warn(`⚠️ Datalist #${datalistId} не найден`);
            return;
        }

        try {
            // Загружаем номенклатуру
            const products = await this.cache.get();
            
            // Очищаем существующие опции
            $datalist.empty();
            
            // Добавляем опции
            products.forEach(product => {
                $datalist.append(`<option value="${this._escapeHtml(product)}">`);
            });
            
            console.log(`✅ Datalist #${datalistId} инициализирован (${products.length} товаров)`);
            
            // Добавляем обработчик для отслеживания выбранных товаров
            this._attachRecentTracker(datalistId);
            
            return products;
        } catch (error) {
            console.error('❌ Ошибка инициализации datalist:', error);
            throw error;
        }
    }

    /**
     * Подключить отслеживание недавно выбранных товаров
     * @private
     */
    _attachRecentTracker(datalistId) {
        const self = this;
        $(`input[list="${datalistId}"]`).on('change', function() {
            const value = $(this).val();
            if (value) {
                self.recentProducts.add(value);
            }
        });
    }

    /**
     * Экранировать HTML
     * @private
     */
    _escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}


// Глобальные экземпляры для использования в шаблонах
window.nomenclatureCache = new NomenclatureCache();
window.recentProducts = new RecentProducts();
window.nomenclatureHelper = new NomenclatureHelper(
    window.nomenclatureCache,
    window.recentProducts
);

// Вспомогательная функция для быстрой инициализации
window.initNomenclature = async function(datalistId = 'nomenclature') {
    return await window.nomenclatureHelper.initializeDatalist(datalistId);
};

// Debug функции (доступны в консоли браузера)
window.debugNomenclature = {
    info: () => window.nomenclatureCache.getInfo(),
    refresh: () => window.nomenclatureCache.refresh(),
    clear: () => window.nomenclatureCache.clear(),
    recent: () => window.recentProducts.get(),
    clearRecent: () => window.recentProducts.clear()
};

console.log('✅ Nomenclature Cache загружен. Доступно: window.nomenclatureCache, window.initNomenclature()');
console.log('🔍 Debug: window.debugNomenclature');

