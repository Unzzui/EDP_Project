/**
 * PAGORA LANDING PAGE - EXECUTIVE INTERACTIONS
 * Advanced JavaScript for Landing Page Enhancements
 * Following Executive Dashboard Design System Philosophy
 */

(function() {
  'use strict';

  // ==========================================================================
  // EXECUTIVE DASHBOARD UTILITIES
  // ==========================================================================

  const LANDING = {
    config: {
      animationDuration: 600,
      counterSpeed: 50,
      glitchInterval: 3000,
      metricsUpdateInterval: 5000
    },
    
    state: {
      isInitialized: false,
      currentTheme: 'dark',
      metrics: {
        systems: 847,
        uptime: 99.97,
        processing: 2847,
        efficiency: 94.3
      }
    }
  };

  // ==========================================================================
  // THEME MANAGEMENT
  // ==========================================================================

  function initializeTheme() {
    const savedTheme = localStorage.getItem('managerTheme') || 'dark';
    LANDING.state.currentTheme = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
  }

  window.toggleTheme = function() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('managerTheme', newTheme);
    LANDING.state.currentTheme = newTheme;
    
    // Trigger theme-specific animations
    triggerThemeTransition();
  };

  function triggerThemeTransition() {
    const body = document.body;
    body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    
    setTimeout(() => {
      body.style.transition = '';
    }, 300);
  }

  // ==========================================================================
  // REAL-TIME CLOCK
  // ==========================================================================

  function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('es-ES', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
      clockElement.textContent = timeString;
    }
  }

  // ==========================================================================
  // ANIMATED COUNTERS
  // ==========================================================================

  function animateCounter(element, start, end, duration = 2000) {
    if (!element) return;
    
    const startTime = performance.now();
    const isFloat = end % 1 !== 0;
    
    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * easeOutCubic;
      
      if (isFloat) {
        element.textContent = current.toFixed(1);
      } else {
        element.textContent = Math.floor(current).toLocaleString();
      }
      
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    }
    
    requestAnimationFrame(updateCounter);
  }

  // ==========================================================================
  // METRICS ANIMATION
  // ==========================================================================

  function initializeMetrics() {
    const metrics = [
      { id: 'systems-count', value: LANDING.state.metrics.systems },
      { id: 'uptime-value', value: LANDING.state.metrics.uptime },
      { id: 'processing-count', value: LANDING.state.metrics.processing },
      { id: 'efficiency-value', value: LANDING.state.metrics.efficiency }
    ];

    metrics.forEach(metric => {
      const element = document.getElementById(metric.id);
      if (element) {
        animateCounter(element, 0, metric.value, 2000);
      }
    });
  }

  // ==========================================================================
  // DYNAMIC METRICS UPDATES
  // ==========================================================================

  function updateMetrics() {
    // Simulate real-time data updates
    LANDING.state.metrics.systems += Math.floor(Math.random() * 3);
    LANDING.state.metrics.processing += Math.floor(Math.random() * 50) - 25;
    LANDING.state.metrics.efficiency = Math.min(99.9, LANDING.state.metrics.efficiency + (Math.random() - 0.5) * 0.5);
    
    // Update DOM elements
    const systemsEl = document.getElementById('systems-count');
    const processingEl = document.getElementById('processing-count');
    const efficiencyEl = document.getElementById('efficiency-value');
    
    if (systemsEl) systemsEl.textContent = LANDING.state.metrics.systems.toLocaleString();
    if (processingEl) processingEl.textContent = LANDING.state.metrics.processing.toLocaleString();
    if (efficiencyEl) efficiencyEl.textContent = LANDING.state.metrics.efficiency.toFixed(1);
  }

  // ==========================================================================
  // INTERSECTION OBSERVER FOR ANIMATIONS
  // ==========================================================================

  function initializeAnimations() {
    const animatedElements = document.querySelectorAll('.animate-in');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '50px'
    });

    animatedElements.forEach(element => {
      element.style.animationPlayState = 'paused';
      observer.observe(element);
    });
  }

  // ==========================================================================
  // EXECUTIVE GLITCH EFFECTS
  // ==========================================================================

  function createGlitchEffect() {
    const glitchElements = document.querySelectorAll('.terminal-text, .mono-font');
    
    glitchElements.forEach(element => {
      if (Math.random() < 0.1) { // 10% chance
        element.style.textShadow = '2px 0 #ff0066, -2px 0 #00ff88';
        element.style.transform = 'translateX(1px)';
        
        setTimeout(() => {
          element.style.textShadow = '';
          element.style.transform = '';
        }, 100);
      }
    });
  }

  // ==========================================================================
  // SMOOTH SCROLLING
  // ==========================================================================

  function initializeSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href');
        
        // Validate that targetId is a valid selector (not just "#")
        if (targetId && targetId !== '#' && targetId.length > 1) {
          const targetElement = document.querySelector(targetId);
          
          if (targetElement) {
            targetElement.scrollIntoView({
              behavior: 'smooth',
              block: 'start'
            });
          }
        }
      });
    });
  }

  // ==========================================================================
  // PARTICLE SYSTEM (OPTIONAL ENHANCEMENT)
  // ==========================================================================

  function createParticleSystem() {
    const canvas = document.createElement('canvas');
    canvas.id = 'particle-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '1';
    canvas.style.opacity = '0.3';
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const particles = [];
    
    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    
    function createParticle() {
      return {
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        life: Math.random() * 100
      };
    }
    
    function animateParticles() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Only show particles in dark theme
      if (LANDING.state.currentTheme === 'dark') {
        particles.forEach((particle, index) => {
          particle.x += particle.vx;
          particle.y += particle.vy;
          particle.life--;
          
          if (particle.life <= 0 || particle.x < 0 || particle.x > canvas.width || 
              particle.y < 0 || particle.y > canvas.height) {
            particles[index] = createParticle();
          }
          
          ctx.fillStyle = `rgba(0, 255, 136, ${particle.life / 100})`;
          ctx.fillRect(particle.x, particle.y, 1, 1);
        });
      }
      
      requestAnimationFrame(animateParticles);
    }
    
    // Initialize particles
    for (let i = 0; i < 50; i++) {
      particles.push(createParticle());
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animateParticles();
  }

  // ==========================================================================
  // MODAL DE SOLICITUD DE ACCESO
  // ==========================================================================

  // Modal state
  let isModalOpen = false;

  // Open access modal
  window.openAccessModal = function() {
    const modal = document.getElementById('accessModal');
    if (modal) {
      modal.style.display = 'flex';
      isModalOpen = true;
      
      // Focus on first input
      const firstInput = modal.querySelector('input');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    }
  };

  // Close access modal
  window.closeAccessModal = function() {
    const modal = document.getElementById('accessModal');
    if (modal) {
      modal.style.display = 'none';
      isModalOpen = false;
      
      // Restore body scroll
      document.body.style.overflow = '';
      
      // Reset form
      const form = document.getElementById('accessForm');
      if (form) {
        form.reset();
      }
    }
  };

  // Submit access request
  window.submitAccessRequest = function(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Add loading state
    form.classList.add('form-loading');
    submitBtn.textContent = 'Enviando...';
    
    // Prepare data
    const data = {
      nombre: formData.get('nombre'),
      email: formData.get('email'),
      empresa: formData.get('empresa'),
      cargo: formData.get('cargo'),
      telefono: formData.get('telefono'),
      motivo: formData.get('motivo'),
      tipo: 'access-request',
      timestamp: new Date().toISOString()
    };
    
    // Send request
    submitFormData(data, form, submitBtn, 'Enviar Solicitud', closeAccessModal);
  };

  // Submit contact form
  window.submitContactForm = function(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Add loading state
    form.classList.add('form-loading');
    submitBtn.textContent = 'Enviando...';
    submitBtn.disabled = true;
    
    // Prepare data
    const data = {
      nombre: formData.get('nombre'),
      email: formData.get('email'),
      empresa: formData.get('empresa'),
      telefono: formData.get('telefono'),
      mensaje: formData.get('mensaje'),
      tipo: 'contact-form',
      timestamp: new Date().toISOString()
    };
    
    // Send request
    submitFormData(data, form, submitBtn, 'ENVIAR SOLICITUD', function() {
      // Reset form on success
      form.reset();
    });
  };

  // Generic form submission function
  function submitFormData(data, form, submitBtn, defaultBtnText, onSuccess) {
    // Send request
    fetch('/api/contact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
      // Remove loading state
      form.classList.remove('form-loading');
      submitBtn.textContent = defaultBtnText;
      submitBtn.disabled = false;
      
      if (result.success) {
        // Show success message
        const successMessage = data.tipo === 'access-request' 
          ? 'Solicitud de acceso enviada exitosamente. Nos pondremos en contacto contigo pronto.'
          : 'Mensaje enviado exitosamente. Nos pondremos en contacto contigo pronto.';
        
        showNotification(successMessage, 'success');
        
        if (onSuccess) {
          onSuccess();
        }
      } else {
        // Show error message
        showNotification(result.message || 'Error al enviar la solicitud. Inténtalo de nuevo.', 'error');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      
      // Remove loading state
      form.classList.remove('form-loading');
      submitBtn.textContent = defaultBtnText;
      submitBtn.disabled = false;
      
      // Show error message
      showNotification('Error de conexión. Inténtalo de nuevo.', 'error');
    });
  }

  // Show notification
  function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.getElementById('notification');
    if (existingNotification) {
      existingNotification.remove();
    }
    
    const notificationHTML = `
      <div id="notification" class="notification ${type}" style="z-index: 999999;">
        <div class="notification-content">
          <span class="notification-message">${message}</span>
          <button class="notification-close" onclick="closeNotification()">&times;</button>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', notificationHTML);
    
    const notification = document.getElementById('notification');
    if (notification) {
      // Auto-hide after 5 seconds
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 5000);
    }
  }

  // Close notification
  window.closeNotification = function() {
    const notification = document.getElementById('notification');
    if (notification) {
      notification.remove();
    }
  };

  // Close modal when clicking outside
  document.addEventListener('click', function(event) {
    const modal = document.getElementById('accessModal');
    if (modal && event.target === modal) {
      closeAccessModal();
    }
  });

  // Close modal with Escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && isModalOpen) {
      closeAccessModal();
    }
  });

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================

  function initialize() {
    if (LANDING.state.isInitialized) return;
    
    // Core initialization
    initializeTheme();
    initializeSmoothScrolling();
    initializeAnimations();
    initializeMetrics();
    
    // Start intervals
    setInterval(updateClock, 1000);
    setInterval(updateMetrics, LANDING.config.metricsUpdateInterval);
    setInterval(createGlitchEffect, LANDING.config.glitchInterval);
    
    // Optional enhancements
    if (window.innerWidth > 768) {
      createParticleSystem();
    }
    
    LANDING.state.isInitialized = true;
    
    // Initial updates
    updateClock();
    
    console.log('🚀 PAGORA Sistema Empresarial Inicializado');
  }

  // ==========================================================================
  // EVENT LISTENERS
  // ==========================================================================

  document.addEventListener('DOMContentLoaded', initialize);
  
  // Handle visibility changes for performance
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Pause expensive operations when tab is not visible
    } else {
      // Resume operations when tab becomes visible
      updateClock();
    }
  });

  // Export for global access
  window.PAGORA_LANDING = LANDING;

})();
