/**
 * Modal Viewer - Модальные окна для просмотра документов
 * Загружает и отображает накладные и списания без перехода на другую страницу
 */

class ModalViewer {
    constructor() {
        this.overlay = null;
        this.modal = null;
        this.currentDocType = null;
        this.currentDocId = null;
        this.init();
    }
    
    init() {
        this.createModal();
        this.attachEventListeners();
        console.log('✅ ModalViewer инициализирован');
    }
    
    /**
     * Создаёт HTML структуру модального окна
     */
    createModal() {
        // Overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';
        this.overlay.addEventListener('click', () => this.close());
        
        // Modal
        this.modal = document.createElement('div');
        this.modal.className = 'modal-viewer';
        this.modal.innerHTML = `
            <div class="modal-viewer-header">
                <h3 class="modal-viewer-title">
                    <i class='bx bxs-file-doc'></i>
                    <span class="modal-title-text">Документ</span>
                </h3>
                <div class="modal-viewer-actions">
                    <button class="modal-action-btn" data-action="edit" title="Редактировать" style="display: none;">
                        <i class='bx bx-edit'></i>
                    </button>
                    <button class="modal-action-btn" data-action="confirm" title="Подтвердить" style="display: none;">
                        <i class='bx bx-check'></i>
                    </button>
                    <button class="modal-action-btn" data-action="deny" title="Отклонить" style="display: none;">
                        <i class='bx bx-x'></i>
                    </button>
                    <button class="modal-action-btn" data-action="cancel" title="Отменить" style="display: none;">
                        <i class='bx bx-x'></i>
                    </button>
                    <button class="modal-action-btn" data-action="copy" title="Копировать" style="display: none;">
                        <i class='bx bx-repeat'></i>
                    </button>
                    <button class="modal-viewer-close">
                        <i class='bx bx-x'></i>
                    </button>
                </div>
            </div>
            <div class="modal-viewer-body">
                <div class="modal-loading">
                    <div class="modal-loading-spinner"></div>
                    <div class="modal-loading-text">Загрузка...</div>
                </div>
            </div>
        `;
        
        // Предотвращаем закрытие при клике на modal
        this.modal.addEventListener('click', (e) => e.stopPropagation());
        
        // Кнопка закрытия
        this.modal.querySelector('.modal-viewer-close').addEventListener('click', () => this.close());
        
        // Append to body
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.modal);
    }
    
    /**
     * Прикрепляет обработчики событий к кнопкам "Просмотр" в списках
     */
    attachEventListeners() {
        // Делегирование событий для динамических элементов
        document.addEventListener('click', (e) => {
            const viewBtn = e.target.closest('[data-modal-view]');
            if (viewBtn) {
                e.preventDefault();
                const docType = viewBtn.dataset.modalView; // 'waybill' или 'writeoff'
                const docId = viewBtn.dataset.modalId;
                this.open(docType, docId);
            }
        });
        
        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.close();
            }
        });
        
        // Действия (подтвердить, отклонить и т.д.)
        this.modal.querySelectorAll('.modal-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.performAction(action);
            });
        });
    }
    
    /**
     * Открывает модальное окно и загружает данные
     * @param {string} docType - 'waybill' или 'writeoff'
     * @param {number} docId - ID документа
     */
    async open(docType, docId) {
        this.currentDocType = docType;
        this.currentDocId = docId;
        
        // Показываем loading
        this.modal.classList.add('loading');
        this.overlay.classList.add('active');
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Загружаем данные
        try {
            const data = await this.fetchDocument(docType, docId);
            this.renderDocument(data);
        } catch (error) {
            console.error('Ошибка загрузки документа:', error);
            showError('Не удалось загрузить документ');
            this.close();
        }
    }
    
    /**
     * Закрывает модальное окно
     */
    close() {
        this.overlay.classList.remove('active');
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        
        setTimeout(() => {
            this.modal.classList.remove('loading');
            this.currentDocType = null;
            this.currentDocId = null;
        }, 400);
    }
    
    /**
     * Загружает данные документа с сервера
     * @param {string} docType - 'waybill' или 'writeoff'
     * @param {number} docId - ID документа
     * @returns {Promise<Object>} - Данные документа
     */
    async fetchDocument(docType, docId) {
        const endpoint = `/${docType}s/${docId}/api/`;
        
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Отображает данные документа в модальном окне
     * @param {Object} data - Данные документа
     */
    renderDocument(data) {
        const body = this.modal.querySelector('.modal-viewer-body');
        const titleText = this.modal.querySelector('.modal-title-text');
        
        // Убираем loading
        this.modal.classList.remove('loading');
        
        // Заголовок
        titleText.textContent = this.currentDocType === 'waybill' 
            ? `Накладная #${data.id}` 
            : `Списание #${data.id}`;
        
        // Рендерим контент
        if (this.currentDocType === 'waybill') {
            body.innerHTML = this.renderWaybill(data);
        } else {
            body.innerHTML = this.renderWriteoff(data);
        }
        
        // Показываем/скрываем кнопки действий
        this.updateActionButtons(data);
    }
    
    /**
     * Рендерит HTML для накладной
     * @param {Object} data - Данные накладной
     * @returns {string} HTML
     */
    renderWaybill(data) {
        const statusClass = this.getStatusClass(data.status);
        const statusText = this.getStatusText(data.status);
        
        let html = `
            <div class="document-info">
                <div class="document-field">
                    <div class="document-field-label">Номер документа</div>
                    <div class="document-field-value">#${data.id}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Склад</div>
                    <div class="document-field-value">${data.store}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Контрагент</div>
                    <div class="document-field-value">${data.counteragent}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Создана пользователем</div>
                    <div class="document-field-value">${data.created_by}</div>
                </div>
        `;
        
        if (data.processed_by) {
            const processedLabel = data.status === 'Sent' 
                ? 'Подтверждена пользователем' 
                : data.status === 'Denied' 
                    ? 'Отклонена пользователем' 
                    : 'Отменена пользователем';
            
            html += `
                <div class="document-field">
                    <div class="document-field-label">${processedLabel}</div>
                    <div class="document-field-value">${data.processed_by}</div>
                </div>
            `;
        }
        
        if (data.comment) {
            html += `
                <div class="document-field">
                    <div class="document-field-label">Комментарий</div>
                    <div class="document-field-value">${data.comment}</div>
                </div>
            `;
        }
        
        html += `
                <div class="document-field">
                    <div class="document-field-label">Статус</div>
                    <div class="document-field-value status ${statusClass}">${statusText}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Дата и время</div>
                    <div class="document-field-value">${data.created_at}</div>
                </div>
            </div>
            
            <div class="document-items">
                <h4 class="document-items-title">
                    <i class='bx bx-package'></i>
                    Товары
                </h4>
                <table class="document-items-table">
                    <thead>
                        <tr>
                            <th>Наименование</th>
                            <th style="width: 150px;">Количество</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(item => `
                            <tr>
                                <td data-label="Наименование">${item.name}</td>
                                <td data-label="Количество">${item.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Рендерит HTML для списания
     * @param {Object} data - Данные списания
     * @returns {string} HTML
     */
    renderWriteoff(data) {
        const statusClass = this.getStatusClass(data.status);
        const statusText = this.getStatusText(data.status);
        
        let html = `
            <div class="document-info">
                <div class="document-field">
                    <div class="document-field-label">Номер документа</div>
                    <div class="document-field-value">#${data.id}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Склад</div>
                    <div class="document-field-value">${data.store}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Создано пользователем</div>
                    <div class="document-field-value">${data.created_by}</div>
                </div>
        `;
        
        if (data.processed_by) {
            const processedLabel = data.status === 'Sent' 
                ? 'Подтверждено пользователем' 
                : 'Отклонено пользователем';
            
            html += `
                <div class="document-field">
                    <div class="document-field-label">${processedLabel}</div>
                    <div class="document-field-value">${data.processed_by}</div>
                </div>
            `;
        }
        
        if (data.comment) {
            html += `
                <div class="document-field">
                    <div class="document-field-label">Комментарий</div>
                    <div class="document-field-value">${data.comment}</div>
                </div>
            `;
        }
        
        html += `
                <div class="document-field">
                    <div class="document-field-label">Статус</div>
                    <div class="document-field-value status ${statusClass}">${statusText}</div>
                </div>
                <div class="document-field">
                    <div class="document-field-label">Дата и время</div>
                    <div class="document-field-value">${data.created_at}</div>
                </div>
            </div>
            
            <div class="document-items">
                <h4 class="document-items-title">
                    <i class='bx bx-package'></i>
                    Товары
                </h4>
                <table class="document-items-table">
                    <thead>
                        <tr>
                            <th>Наименование</th>
                            <th style="width: 150px;">Количество</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.items.map(item => `
                            <tr>
                                <td data-label="Наименование">${item.name}</td>
                                <td data-label="Количество">${item.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Обновляет видимость кнопок действий в зависимости от прав и статуса
     * @param {Object} data - Данные документа
     */
    updateActionButtons(data) {
        // Скрываем все кнопки
        this.modal.querySelectorAll('.modal-action-btn').forEach(btn => {
            btn.style.display = 'none';
        });
        
        // Показываем нужные кнопки (логику взять из item.html)
        // Для упрощения пока оставляем только кнопки, которые есть в permissions
        // Полную логику можно добавить позже
        
        if (data.actions) {
            data.actions.forEach(action => {
                const btn = this.modal.querySelector(`[data-action="${action}"]`);
                if (btn) {
                    btn.style.display = 'flex';
                }
            });
        }
    }
    
    /**
     * Выполняет действие над документом
     * @param {string} action - Действие (confirm, deny, cancel, copy, edit)
     */
    async performAction(action) {
        if (action === 'edit') {
            // Переход на страницу редактирования
            window.location.href = `/${this.currentDocType}s/${this.currentDocId}/edit`;
            return;
        }
        
        if (!confirm(`Вы уверены что хотите выполнить это действие?`)) {
            return;
        }
        
        try {
            // Получаем CSRF токен из основной страницы
            let csrfToken = '';
            
            // Ищем токен в форме на странице
            const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                csrfToken = csrfInput.value;
            } else {
                // Ищем в мета-тегах
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                if (csrfMeta) {
                    csrfToken = csrfMeta.getAttribute('content');
                } else {
                    // Получаем из cookies
                    const cookies = document.cookie.split(';');
                    for (let cookie of cookies) {
                        const [name, value] = cookie.trim().split('=');
                        if (name === 'csrftoken') {
                            csrfToken = value;
                            break;
                        }
                    }
                }
            }
            
            console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
            
            const response = await fetch(`/${this.currentDocType}s/${this.currentDocId}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `csrfmiddlewaretoken=${csrfToken}`
            });
            
            if (response.ok) {
                showSuccess('Действие выполнено успешно');
                this.close();
                // Обновляем список
                setTimeout(() => window.location.reload(), 500);
            } else {
                throw new Error('Ошибка выполнения действия');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showError('Не удалось выполнить действие');
        }
    }
    
    /**
     * Возвращает CSS класс для статуса
     * @param {string} status - Статус
     * @returns {string} CSS класс
     */
    getStatusClass(status) {
        const map = {
            'Created': 'created',
            'Sent': 'sent',
            'Denied': 'denied',
            'Cancelled': 'cancelled'
        };
        return map[status] || 'created';
    }
    
    /**
     * Возвращает текст статуса
     * @param {string} status - Статус
     * @returns {string} Текст
     */
    getStatusText(status) {
        const map = {
            'Created': 'В обработке',
            'Sent': 'Создана',
            'Denied': 'Отклонена',
            'Cancelled': 'Отменена'
        };
        return map[status] || status;
    }
}

// Глобальный экземпляр
window.modalViewer = null;

// Автоматическая инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.modalViewer = new ModalViewer();
    });
} else {
    window.modalViewer = new ModalViewer();
}

console.log('✅ ModalViewer загружен');

