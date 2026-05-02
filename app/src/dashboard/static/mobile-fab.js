/**
 * Mobile FAB (Floating Action Button) JavaScript
 * Оптимизировано для 95% мобильного трафика
 * Material Design 3 compliant
 */

class MobileFAB {
  constructor() {
    this.fab = null;
    this.menu = null;
    this.overlay = null;
    this.isOpen = false;
    this.init();
  }
  
  init() {
    // Ждем загрузки DOM
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupFAB());
    } else {
      this.setupFAB();
    }
  }
  
  setupFAB() {
    this.fab = document.querySelector('.mobile-fab');
    this.menu = document.querySelector('.mobile-fab-menu');
    this.overlay = document.querySelector('.mobile-fab-overlay');
    
    if (!this.fab) return;
    
    // Слушатели событий
    this.fab.addEventListener('click', (e) => this.toggleMenu(e));
    
    // Клик по overlay закрывает меню
    if (this.overlay) {
      this.overlay.addEventListener('click', () => this.closeMenu());
    }
    
    // Клик вне меню закрывает его
    document.addEventListener('click', (e) => {
      if (this.isOpen && !e.target.closest('.mobile-fab-menu') && !e.target.closest('.mobile-fab')) {
        this.closeMenu();
      }
    });
    
    // ESC закрывает меню
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.closeMenu();
      }
    });
    
    // Swipe gesture для мобильных
    this.setupSwipeGesture();
  }
  
  toggleMenu(e) {
    e.stopPropagation();
    
    if (this.isOpen) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }
  
  openMenu() {
    if (!this.menu || !this.overlay) return;
    
    this.isOpen = true;
    this.menu.classList.add('show');
    this.overlay.classList.add('show');
    
    // Добавляем анимацию поворота к иконке
    const icon = this.fab.querySelector('i');
    if (icon) {
      this.fab.classList.add('rotating');
      setTimeout(() => this.fab.classList.remove('rotating'), 300);
    }
    
    // Haptic feedback для мобильных
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
  }
  
  closeMenu() {
    if (!this.menu || !this.overlay) return;
    
    this.isOpen = false;
    this.menu.classList.remove('show');
    this.overlay.classList.remove('show');
    
    // Убираем анимацию поворота
    const icon = this.fab.querySelector('i');
    if (icon) {
      this.fab.classList.add('rotating');
      setTimeout(() => this.fab.classList.remove('rotating'), 300);
    }
  }
  
  setupSwipeGesture() {
    let startY = 0;
    let currentY = 0;
    let isSwiping = false;
    
    if (this.overlay) {
      this.overlay.addEventListener('touchstart', (e) => {
        startY = e.touches[0].clientY;
        isSwiping = true;
      });
      
      this.overlay.addEventListener('touchmove', (e) => {
        if (!isSwiping) return;
        currentY = e.touches[0].clientY;
        
        if (currentY - startY > 50) {
          this.closeMenu();
          isSwiping = false;
        }
      });
      
      this.overlay.addEventListener('touchend', () => {
        isSwiping = false;
      });
    }
  }
  
  // Добавляем новый элемент в меню
  addMenuItem(icon, label, href, onClick) {
    if (!this.menu) return;
    
    const item = document.createElement('a');
    item.className = 'mobile-fab-menu-item';
    item.href = href || '#';
    item.innerHTML = `
      <i class='${icon}'></i>
      <span>${label}</span>
    `;
    
    if (onClick) {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        onClick();
      });
    }
    
    this.menu.appendChild(item);
  }
  
  // Обновить иконку FAB
  updateIcon(icon) {
    if (!this.fab) return;
    
    const iconElement = this.fab.querySelector('i');
    if (iconElement) {
      iconElement.className = icon;
    }
  }
  
  // Обновить текст FAB (для extended FAB)
  updateLabel(label) {
    if (!this.fab) return;
    
    let labelElement = this.fab.querySelector('.fab-label');
    if (!labelElement) {
      labelElement = document.createElement('span');
      labelElement.className = 'fab-label';
      this.fab.appendChild(labelElement);
      this.fab.classList.add('extended');
    }
    
    labelElement.textContent = label;
  }
  
  // Показать FAB
  show() {
    if (this.fab) {
      this.fab.style.display = 'flex';
    }
  }
  
  // Скрыть FAB
  hide() {
    if (this.fab) {
      this.fab.style.display = 'none';
    }
  }
  
  // Обновить позицию FAB
  setPosition(bottom = '80px', right = '20px') {
    if (this.fab) {
      this.fab.style.bottom = bottom;
      this.fab.style.right = right;
    }
  }
}

// Инициализация
let mobileFAB = null;

function initMobileFAB() {
  if (window.innerWidth <= 768) {
    mobileFAB = new MobileFAB();
  }
}

// Инициализация при загрузке
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMobileFAB);
} else {
  initMobileFAB();
}

// Переинициализация при изменении размера окна
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (window.innerWidth <= 768 && !mobileFAB) {
      initMobileFAB();
    } else if (window.innerWidth > 768 && mobileFAB) {
      mobileFAB.closeMenu();
      mobileFAB = null;
    }
  }, 250);
});

// Экспортируем для использования в других скриптах
window.MobileFAB = MobileFAB;
window.mobileFAB = mobileFAB;
