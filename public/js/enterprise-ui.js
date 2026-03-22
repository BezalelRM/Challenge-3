/**
 * Enterprise UI Framework
 * Advanced animations, transitions, and dynamic updates for corporate applications
 */

class EnterpriseUI {
  constructor() {
    this.currentPage = '';
    this.transitionDuration = 600;
    this.isTransitioning = false;
    this.observers = new Map();
    this.init();
  }

  init() {
    this.setupPageTransitions();
    this.setupSidebarAnimations();
    this.setupIntersectionObservers();
    this.setupDynamicUpdates();
    this.setupKeyboardNavigation();
    
    // Always use light theme
    document.documentElement.setAttribute('data-theme', 'light');
  }

  // ====== PAGE TRANSITION SYSTEM ======
  setupPageTransitions() {
    // Intercept navigation clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (link && this.isInternalLink(link.href)) {
        e.preventDefault();
        this.navigateToPage(link.href);
      }
    });

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.page) {
        this.loadPage(e.state.page, false);
      }
    });

    // Set initial page state
    this.currentPage = window.location.pathname;
    history.replaceState({ page: this.currentPage }, '', this.currentPage);
  }

  isInternalLink(href) {
    try {
      const url = new URL(href, window.location.origin);
      return url.origin === window.location.origin && 
             url.pathname.endsWith('.html');
    } catch {
      return false;
    }
  }

  async navigateToPage(href) {
    if (this.isTransitioning) return;
    
    const url = new URL(href, window.location.origin);
    const targetPage = url.pathname;
    
    if (targetPage === this.currentPage) return;

    this.isTransitioning = true;
    
    // Add exit animation
    document.body.classList.add('page-transitioning');
    const main = document.querySelector('.main');
    if (main) {
      main.classList.add('page-exit');
    }

    // Wait for exit animation
    await this.delay(400);

    // Load new page
    try {
      const response = await fetch(href);
      const html = await response.text();
      const parser = new DOMParser();
      const newDoc = parser.parseFromString(html, 'text/html');
      
      // Update page content
      this.updatePageContent(newDoc);
      
      // Update URL and history
      history.pushState({ page: targetPage }, '', href);
      this.currentPage = targetPage;
      
      // Add enter animation
      if (main) {
        main.classList.remove('page-exit');
        main.classList.add('page-enter');
      }
      
      // Initialize new page
      this.initializePage();
      
    } catch (error) {
      console.error('Navigation failed:', error);
      window.location.href = href; // Fallback to normal navigation
    }

    await this.delay(200);
    document.body.classList.remove('page-transitioning');
    this.isTransitioning = false;
  }

  updatePageContent(newDoc) {
    // Update title
    document.title = newDoc.title;
    
    // Update main content
    const currentMain = document.querySelector('.main');
    const newMain = newDoc.querySelector('.main');
    if (currentMain && newMain) {
      currentMain.innerHTML = newMain.innerHTML;
    }
    
    // Update active navigation
    this.updateActiveNavigation();
  }

  updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar a');
    
    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === currentPath.split('/').pop()) {
        link.classList.add('active');
      }
    });
  }

  initializePage() {
    // Reinitialize page-specific functionality
    this.setupStaggeredAnimations();
    this.setupDynamicContent();
    this.setupInteractiveElements();
    
    // Trigger page-specific initialization
    const event = new CustomEvent('pageInitialized', {
      detail: { page: this.currentPage }
    });
    document.dispatchEvent(event);
  }

  // ====== SIDEBAR ANIMATIONS ======
  setupSidebarAnimations() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    
    if (mobileToggle) {
      mobileToggle.addEventListener('click', () => {
        this.toggleSidebar();
      });
    }
    
    if (overlay) {
      overlay.addEventListener('click', () => {
        this.closeSidebar();
      });
    }

    // Enhanced sidebar link animations
    const sidebarLinks = document.querySelectorAll('.sidebar a');
    sidebarLinks.forEach((link, index) => {
      link.style.animationDelay = `${index * 0.1}s`;
      link.addEventListener('mouseenter', () => {
        this.animateSidebarLink(link, 'enter');
      });
      link.addEventListener('mouseleave', () => {
        this.animateSidebarLink(link, 'leave');
      });
    });
  }

  toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar && overlay) {
      const isOpen = sidebar.classList.contains('open');
      
      if (isOpen) {
        this.closeSidebar();
      } else {
        this.openSidebar();
      }
    }
  }

  openSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar && overlay) {
      sidebar.classList.add('open');
      overlay.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  }

  closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar && overlay) {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
      document.body.style.overflow = '';
    }
  }

  animateSidebarLink(link, state) {
    const icon = link.querySelector('::before');
    if (state === 'enter') {
      link.style.transform = 'translateX(8px) scale(1.02)';
    } else {
      link.style.transform = '';
    }
  }

  // ====== INTERSECTION OBSERVERS ======
  setupIntersectionObservers() {
    // Animate elements as they come into view
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe cards and content sections
    const observeElements = () => {
      const elements = document.querySelectorAll('.card, .content-section, .stat-card');
      elements.forEach(el => {
        if (!el.classList.contains('animate-fade-in')) {
          observer.observe(el);
        }
      });
    };

    observeElements();
    this.observers.set('fadeIn', observer);
  }

  // ====== DYNAMIC UPDATES ======
  setupDynamicUpdates() {
    // Auto-refresh leaderboard when returning to page
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && window.location.pathname.includes('leaderboard')) {
        this.refreshLeaderboard();
      }
    });

    // Refresh data when navigating back to pages
    window.addEventListener('focus', () => {
      this.refreshCurrentPageData();
    });
  }

  async refreshLeaderboard() {
    const leaderboardContent = document.getElementById('leaderboard-content');
    if (!leaderboardContent) return;

    // Show loading state
    leaderboardContent.innerHTML = `
      <div class="content-loading">
        <div class="loading-spinner-large"></div>
        <div class="loading-text">Refreshing leaderboard...</div>
      </div>
    `;

    try {
      // Simulate API call delay for smooth UX
      await this.delay(800);
      
      // Trigger leaderboard reload if function exists
      if (typeof loadLeaderboard === 'function') {
        await loadLeaderboard();
      }
    } catch (error) {
      console.error('Failed to refresh leaderboard:', error);
      this.showErrorState(leaderboardContent, 'Failed to load leaderboard data');
    }
  }

  refreshCurrentPageData() {
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('dashboard')) {
      if (typeof loadProgress === 'function') {
        loadProgress();
      }
    } else if (currentPath.includes('leaderboard')) {
      this.refreshLeaderboard();
    }
  }

  // ====== STAGGERED ANIMATIONS ======
  setupStaggeredAnimations() {
    const staggerContainers = document.querySelectorAll('.stagger-children');
    
    staggerContainers.forEach(container => {
      const children = container.children;
      Array.from(children).forEach((child, index) => {
        child.style.animationDelay = `${index * 0.1}s`;
        child.classList.add('animate-fade-in');
      });
    });
  }

  // ====== INTERACTIVE ELEMENTS ======
  setupInteractiveElements() {
    // Enhanced button interactions
    const buttons = document.querySelectorAll('button, .btn');
    buttons.forEach(button => {
      button.addEventListener('click', (e) => {
        this.createButtonRipple(e);
      });
    });

    // Enhanced card interactions
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-8px) scale(1.02)';
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  }

  createButtonRipple(event) {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      left: ${x}px;
      top: ${y}px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      transform: scale(0);
      animation: rippleExpand 0.6s ease-out;
      pointer-events: none;
    `;
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  // ====== KEYBOARD NAVIGATION ======
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Escape key closes sidebar
      if (e.key === 'Escape') {
        this.closeSidebar();
      }
      
      // Alt + number keys for quick navigation
      if (e.altKey && e.key >= '1' && e.key <= '9') {
        e.preventDefault();
        const navLinks = document.querySelectorAll('.sidebar a:not(.logout-btn)');
        const index = parseInt(e.key) - 1;
        if (navLinks[index]) {
          navLinks[index].click();
        }
      }
    });
  }

  // ====== UTILITY METHODS ======
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  showErrorState(container, message) {
    container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <div class="error-title">Something went wrong</div>
        <div class="error-message">${message}</div>
      </div>
    `;
  }

  showEmptyState(container, title, message) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-title">${title}</div>
        <div class="empty-message">${message}</div>
      </div>
    `;
  }

  // ====== NOTIFICATION SYSTEM ======
  showNotification(message, type = 'info', duration = 4000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const colors = {
      success: 'bg-success-bg text-success-color border-success-border',
      error: 'bg-error-bg text-error-color border-error-border',
      warning: 'bg-warning-bg text-warning-color border-warning-border',
      info: 'bg-info-bg text-info-color border-info-border'
    };
    
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;
    
    notification.style.cssText = `
      position: fixed;
      top: 24px;
      right: 24px;
      z-index: 1000;
      padding: 16px 20px;
      border-radius: 12px;
      box-shadow: var(--shadow-lg);
      backdrop-filter: blur(10px);
      border: 1px solid;
      transform: translateX(100%);
      transition: transform 0.3s var(--ease-out-cubic);
      max-width: 400px;
    `;
    
    notification.className += ` ${colors[type]}`;
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, duration);
  }

  // ====== NUMBER ANIMATION ======
  animateNumber(elementId, targetValue, suffix = '', duration = 1000) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const startValue = 0;
    const startTime = performance.now();

    const updateNumber = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutCubic);
      
      element.textContent = currentValue.toLocaleString() + suffix;
      
      if (progress < 1) {
        requestAnimationFrame(updateNumber);
      }
    };
    
    requestAnimationFrame(updateNumber);
  }

  // ====== TYPEWRITER EFFECT ======
  typewriterEffect(elementId, text, speed = 30) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = '';
    let i = 0;

    const typeChar = () => {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
        setTimeout(typeChar, speed);
      }
    };

    typeChar();
  }
}

// Initialize Enterprise UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.enterpriseUI = new EnterpriseUI();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EnterpriseUI;
}