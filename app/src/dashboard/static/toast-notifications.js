/**
 * Toast Notifications System
 * Легкая система уведомлений для пользовательского feedback
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Создаём контейнер для toast'ов
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    /**
     * Показать уведомление
     * @param {string} type - 'success', 'error', 'warning', 'info'
     * @param {string} message - Текст сообщения
     * @param {number} duration - Длительность показа (мс)
     */
    show(type, message, duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = this.getIcon(type);
        
        toast.innerHTML = `
            <div class="toast-content">
                <i class="bx ${icon} toast-icon"></i>
                <span class="toast-message">${this.escapeHtml(message)}</span>
            </div>
            <button class="toast-close" aria-label="Закрыть">
                <i class="bx bx-x"></i>
            </button>
        `;
        
        this.container.appendChild(toast);
        
        // Анимация появления
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Обработчик закрытия
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.hide(toast));
        
        // Автоматическое скрытие
        if (duration > 0) {
            setTimeout(() => this.hide(toast), duration);
        }
        
        return toast;
    }

    hide(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    getIcon(type) {
        const icons = {
            'success': 'bx-check-circle',
            'error': 'bx-error-circle',
            'warning': 'bx-error',
            'info': 'bx-info-circle'
        };
        return icons[type] || icons['info'];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Удобные методы
    success(message, duration) {
        return this.show('success', message, duration);
    }

    error(message, duration) {
        return this.show('error', message, duration);
    }

    warning(message, duration) {
        return this.show('warning', message, duration);
    }

    info(message, duration) {
        return this.show('info', message, duration);
    }
}

// Глобальный экземпляр
window.toastManager = new ToastManager();

// Удобные глобальные функции
window.showToast = function(type, message, duration) {
    return window.toastManager.show(type, message, duration);
};

window.showSuccess = function(message, duration) {
    return window.toastManager.success(message, duration);
};

window.showError = function(message, duration) {
    return window.toastManager.error(message, duration);
};

window.showWarning = function(message, duration) {
    return window.toastManager.warning(message, duration);
};

window.showInfo = function(message, duration) {
    return window.toastManager.info(message, duration);
};

console.log('✅ Toast Notifications System загружен');

