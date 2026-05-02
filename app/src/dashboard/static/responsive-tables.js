/**
 * Responsive Tables Helper
 * Автоматически добавляет data-label атрибуты для адаптивных таблиц
 */

class ResponsiveTables {
    constructor() {
        this.init();
    }
    
    init() {
        // Добавляем класс responsive-table ко всем таблицам
        document.querySelectorAll('.table').forEach(table => {
            if (!table.classList.contains('responsive-table')) {
                table.classList.add('responsive-table');
            }
        });
        
        // Добавляем data-label атрибуты
        this.addDataLabels();
        
        // Следим за динамически добавленными таблицами
        this.watchForNewTables();
        
        console.log('✅ ResponsiveTables инициализирован');
    }
    
    addDataLabels() {
        document.querySelectorAll('.responsive-table').forEach(table => {
            const headers = [];
            
            // Собираем заголовки
            table.querySelectorAll('thead th').forEach(th => {
                headers.push(th.textContent.trim());
            });
            
            // Добавляем data-label к каждой ячейке
            table.querySelectorAll('tbody tr').forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    if (headers[index] && !cell.hasAttribute('data-label')) {
                        cell.setAttribute('data-label', headers[index]);
                    }
                });
            });
        });
    }
    
    watchForNewTables() {
        // Наблюдаем за изменениями в DOM
        const observer = new MutationObserver(mutations => {
            let needsUpdate = false;
            
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // Проверяем добавленные таблицы
                        if (node.tagName === 'TABLE' || node.querySelector('table')) {
                            needsUpdate = true;
                        }
                        
                        // Проверяем добавленные строки в таблицах
                        if (node.tagName === 'TR' || node.querySelector('tr')) {
                            needsUpdate = true;
                        }
                    }
                });
            });
            
            if (needsUpdate) {
                this.addDataLabels();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Ручное обновление data-labels для конкретной таблицы
     * @param {string} selector - Селектор таблицы
     */
    update(selector) {
        const table = document.querySelector(selector);
        if (!table) return;
        
        const headers = [];
        table.querySelectorAll('thead th').forEach(th => {
            headers.push(th.textContent.trim());
        });
        
        table.querySelectorAll('tbody tr').forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (headers[index]) {
                    cell.setAttribute('data-label', headers[index]);
                }
            });
        });
    }
}

// Глобальный экземпляр
window.responsiveTables = null;

// Автоматическая инициализация при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.responsiveTables = new ResponsiveTables();
    });
} else {
    window.responsiveTables = new ResponsiveTables();
}

// Удобная функция для ручного обновления
window.updateResponsiveTable = function(selector) {
    if (window.responsiveTables) {
        window.responsiveTables.update(selector);
    }
};

console.log('✅ ResponsiveTables загружен');

