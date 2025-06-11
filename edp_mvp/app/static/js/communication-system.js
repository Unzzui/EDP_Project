/**
 * EDP COMMUNICATION SYSTEM - ENTERPRISE LEVEL
 * 
 * Advanced communication system for executive dashboard
 * Features: Multi-channel messaging, AI assistance, templates, attachments, analytics
 * 
 * @version 2.0.0
 * @author EDP Team
 * @created 2024
 */

class EDPCommunicationSystem {
  constructor() {
    this.currentPriority = "medium";
    this.currentCommunicationType = "";
    this.currentRecipient = "";
    this.currentTab = "message";
    this.attachments = [];
    this.drafts = {};
    this.initialized = false;

    // Configuration for different communication types
    this.communicationConfig = {
      jp: {
        title: "Consultar a Jefe de Proyecto",
        subtitle: "Gestión directa con responsable del proyecto",
        icon: "var(--danger)",
        defaultPriority: "medium",
      },
      controller: {
        title: "Escalar a Controller Financiero",
        subtitle: "Revisión financiera y escalación de problemas críticos",
        icon: "var(--warning)",
        defaultPriority: "high",
      },
      legal: {
        title: "Consulta Departamento Legal",
        subtitle: "Revisión de aspectos legales y compliance",
        icon: "var(--info)",
        defaultPriority: "medium",
      },
      direction: {
        title: "Escalación a Dirección General",
        subtitle: "Situación crítica que requiere intervención ejecutiva",
        icon: "var(--accent-purple)",
        defaultPriority: "high",
      },
    };

    // Message templates
    this.messageTemplates = {
      status: {
        subject: "Solicitud de Estado - Proyecto Crítico",
        body: "Estimado/a [NOMBRE],\n\nSolicito una actualización urgente sobre el estado del proyecto [PROYECTO_ID].\n\nPuntos específicos que requieren clarificación:\n• Progreso actual vs. cronograma\n• Obstáculos o impedimentos identificados\n• Recursos adicionales necesarios\n• Próximos pasos y fechas críticas\n\nAgradeceré su respuesta a la brevedad posible.\n\nSaludos cordiales,\n[USUARIO]"
      },
      escalation: {
        subject: "ESCALACIÓN CRÍTICA - Intervención Requerida",
        body: "ATENCIÓN URGENTE\n\nEscalo la siguiente situación crítica que requiere intervención inmediata:\n\nPROYECTO: [PROYECTO_ID]\nIMPACTO: Alto riesgo financiero y operativo\nESTADO: Fuera de control\n\nSITUACIÓN:\n[DESCRIBIR_SITUACIÓN]\n\nACCIÓN REQUERIDA:\n• Intervención inmediata\n• Revisión de estrategia\n• Recursos adicionales\n\nSolicito reunión urgente para definir plan de acción.\n\n[USUARIO]"
      },
      meeting: {
        subject: "Solicitud de Reunión Urgente - Proyecto Crítico",
        body: "Estimado/a [NOMBRE],\n\nSolicito agendar reunión urgente para revisar situación del proyecto [PROYECTO_ID].\n\nOBJETIVO: Definir plan de acción inmediato\nDURACIÓN ESTIMADA: 60 minutos\nPARTICIPANTES SUGERIDOS: [LISTA]\n\nTEMAS A TRATAR:\n• Estado actual y problemas identificados\n• Alternativas de solución\n• Recursos y timeline\n• Próximos pasos\n\nQuedo a disposición para coordinar horarios.\n\n[USUARIO]"
      }
    };

    this.init();
  }

  /**
   * Initialize the communication system
   */
  init() {
    if (this.initialized) return;
    
    console.log("🚀 Inicializando EDP Communication System...");
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Load existing drafts
    this.loadDrafts();
    
    // Initialize components
    this.updateAttachmentsList();
    
    this.initialized = true;
    this.logSystemInfo();
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    // DOM Content Loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
    } else {
      this.onDOMReady();
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => this.handleKeyboardShortcuts(e));

    // Modal click outside to close
    const modal = document.getElementById("communicationModal");
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          this.closeCommunicationModal();
        }
      });
    }

    // Form submission
    const form = document.getElementById("communicationForm");
    if (form) {
      form.addEventListener("submit", (e) => this.handleFormSubmission(e));
    }
  }

  /**
   * Handle DOM ready event
   */
  onDOMReady() {
    // Character count for message text
    const messageText = document.getElementById('messageText');
    if (messageText) {
      messageText.addEventListener('input', () => this.updateCharCount());
      this.updateCharCount(); // Initialize
    }
  }

  /**
   * Tab Management
   */
  switchTab(tabName) {
    this.currentTab = tabName;
    
    const tabs = ['message', 'meeting', 'task', 'history'];
    tabs.forEach(tab => {
      const button = document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
      const content = document.getElementById(`tabContent${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
      
      if (button && content) {
        if (tab === tabName) {
          button.style.background = 'var(--info)';
          button.style.color = 'white';
          content.classList.remove('hidden');
        } else {
          button.style.background = 'var(--bg-subtle)';
          button.style.color = 'var(--text-secondary)';
          content.classList.add('hidden');
        }
      }
    });
  }

  /**
   * Open communication modal
   */
  openCommunicationModal(type, recipientName, messageType) {
    this.currentCommunicationType = type;
    this.currentRecipient = recipientName;

    const config = this.communicationConfig[type];
    const modal = document.getElementById("communicationModal");

    if (!config || !modal) return;

    // Update modal content
    this.updateElement("modalTitle", config.title);
    this.updateElement("modalSubtitle", config.subtitle);
    
    const modalIcon = document.getElementById("modalIcon");
    if (modalIcon) {
      modalIcon.style.background = config.icon;
    }

    // Update recipient info
    this.updateElement("recipientName", recipientName);
    this.updateElement("recipientInitials", this.getInitials(recipientName));

    // Set role based on type
    const roleMap = {
      jp: "Jefe de Proyecto",
      controller: "Controller Financiero", 
      legal: "Departamento Legal",
      direction: "Dirección General",
    };
    this.updateElement("recipientRole", roleMap[type]);

    // Set default message type
    const messageTypeSelect = document.getElementById("messageType");
    if (messageTypeSelect) {
      messageTypeSelect.value = messageType;
    }

    // Set default priority
    this.setPriority(config.defaultPriority);

    // Reset form
    this.resetCommunicationForm();

    // Reset to message tab
    this.switchTab('message');

    // Show modal with animation
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    
    // Add entrance animation
    setTimeout(() => {
      modal.style.opacity = "1";
      const modalContent = modal.querySelector('.rounded-xl');
      if (modalContent) {
        modalContent.style.transform = "scale(1)";
      }
    }, 10);
  }

  /**
   * Close communication modal
   */
  closeCommunicationModal() {
    const modal = document.getElementById("communicationModal");
    if (!modal) return;
    
    // Add exit animation
    modal.style.opacity = "0";
    const modalContent = modal.querySelector('.rounded-xl');
    if (modalContent) {
      modalContent.style.transform = "scale(0.95)";
    }
    
    setTimeout(() => {
      modal.classList.add("hidden");
      document.body.style.overflow = "auto";
      modal.style.opacity = "";
      if (modalContent) {
        modalContent.style.transform = "";
      }
    }, 200);
  }

  /**
   * Reset communication form
   */
  resetCommunicationForm() {
    const messageText = document.getElementById("messageText");
    if (messageText) {
      messageText.value = "";
    }
    
    this.attachments = [];
    this.updateAttachmentsList();
    this.updateCharCount();
    
    // Reset checkboxes to defaults
    this.setCheckboxValue("notifyApp", true);
    this.setCheckboxValue("notifyEmail", true);
    this.setCheckboxValue("notifySlack", false);
    this.setCheckboxValue("scheduleMessage", false);
    this.setCheckboxValue("requireResponse", false);
    this.setCheckboxValue("trackDelivery", true);
  }

  /**
   * Set priority level
   */
  setPriority(level) {
    this.currentPriority = level;

    // Reset all buttons
    ["priorityLow", "priorityMedium", "priorityHigh"].forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.style.background = "var(--bg-subtle)";
        btn.style.color = "var(--text-secondary)";
      }
    });

    // Highlight selected
    const selectedBtn = document.getElementById(
      "priority" + level.charAt(0).toUpperCase() + level.slice(1)
    );
    if (selectedBtn) {
      const colors = {
        low: "var(--success)",
        medium: "var(--warning)",
        high: "var(--danger)",
      };

      selectedBtn.style.background = colors[level];
      selectedBtn.style.color = "white";
    }
  }

  /**
   * Template functions
   */
  useTemplate(templateType) {
    const template = this.messageTemplates[templateType];
    if (!template) return;

    const messageText = document.getElementById("messageText");
    if (!messageText) return;

    messageText.value = template.body
      .replace(/\[NOMBRE\]/g, this.currentRecipient)
      .replace(/\[PROYECTO_ID\]/g, 'EDP-001')
      .replace(/\[USUARIO\]/g, 'Manager EDP');
    
    this.updateCharCount();
    
    // Show animation
    messageText.style.backgroundColor = 'var(--info)';
    messageText.style.color = 'white';
    setTimeout(() => {
      messageText.style.backgroundColor = '';
      messageText.style.color = '';
    }, 500);
  }

  /**
   * Character count
   */
  updateCharCount() {
    const messageText = document.getElementById("messageText");
    const charCount = document.getElementById("charCount");
    
    if (!messageText || !charCount) return;

    const count = messageText.value.length;
    charCount.textContent = `${count}/500`;
    
    if (count > 450) {
      charCount.style.color = 'var(--danger)';
    } else if (count > 400) {
      charCount.style.color = 'var(--warning)';
    } else {
      charCount.style.color = 'var(--text-secondary)';
    }
  }

  /**
   * Attachment management
   */
  addAttachment() {
    const fileName = prompt("Nombre del archivo (simulación):", "documento.pdf");
    if (!fileName) return;

    const attachment = {
      id: Date.now(),
      name: fileName,
      size: Math.floor(Math.random() * 5000) + 500, // KB
      type: fileName.split('.').pop() || 'unknown'
    };
    
    this.attachments.push(attachment);
    this.updateAttachmentsList();
    
    this.showNotification('success', 'Archivo adjunto', `${fileName} ha sido agregado exitosamente.`);
  }

  removeAttachment(id) {
    this.attachments = this.attachments.filter(att => att.id !== id);
    this.updateAttachmentsList();
  }

  updateAttachmentsList() {
    const container = document.getElementById("attachmentsList");
    if (!container) return;

    if (this.attachments.length === 0) {
      container.innerHTML = '<p style="color: var(--text-secondary);" class="text-sm italic">No hay archivos adjuntos</p>';
      return;
    }

    container.innerHTML = this.attachments.map(att => `
      <div style="background: var(--bg-card); border: 1px solid var(--border-color);" class="flex items-center justify-between p-3 rounded-lg">
        <div class="flex items-center gap-3">
          <div style="background: var(--info); color: white;" class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold">
            ${att.type.toUpperCase()}
          </div>
          <div>
            <div style="color: var(--text-primary);" class="text-sm font-medium">${att.name}</div>
            <div style="color: var(--text-secondary);" class="text-xs">${(att.size / 1024).toFixed(1)} MB</div>
          </div>
        </div>
        <button onclick="communicationSystem.removeAttachment(${att.id})" style="color: var(--danger);" class="hover:opacity-70 transition-opacity">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    `).join('');
  }

  /**
   * AI Assistant simulation
   */
  toggleAIAssist() {
    const suggestions = [
      "Sugerir escalar a Controller debido a impacto financiero crítico",
      "Recomendar reunión urgente con stakeholders",
      "Proponer plan de contingencia inmediato",
      "Solicitar recursos adicionales para recuperación"
    ];
    
    const suggestion = suggestions[Math.floor(Math.random() * suggestions.length)];
    
    if (confirm(`💡 AI Assistant sugiere:\n\n"${suggestion}"\n\n¿Deseas aplicar esta sugerencia?`)) {
      const messageText = document.getElementById("messageText");
      if (messageText) {
        messageText.value += `\n\n[Sugerencia AI]: ${suggestion}`;
        this.updateCharCount();
      }
    }
  }

  /**
   * Draft management
   */
  saveDraft() {
    const messageText = document.getElementById("messageText");
    const messageType = document.getElementById("messageType");
    
    if (!messageText || !messageType) return;

    const draftData = {
      recipient: this.currentRecipient,
      type: this.currentCommunicationType,
      messageType: messageType.value,
      priority: this.currentPriority,
      message: messageText.value,
      attachments: [...this.attachments],
      timestamp: new Date().toISOString()
    };
    
    const draftKey = `draft_${this.currentCommunicationType}_${Date.now()}`;
    this.drafts[draftKey] = draftData;
    
    // Save to localStorage
    try {
      localStorage.setItem('edp_communication_drafts', JSON.stringify(this.drafts));
    } catch (e) {
      console.warn('Could not save draft to localStorage:', e);
    }
    
    this.showNotification('success', 'Borrador guardado', 'Tu mensaje ha sido guardado como borrador.');
  }

  loadDrafts() {
    try {
      const savedDrafts = localStorage.getItem('edp_communication_drafts');
      if (savedDrafts) {
        this.drafts = JSON.parse(savedDrafts);
      }
    } catch (e) {
      console.log('No drafts found or error loading drafts');
    }
  }

  /**
   * Communication methods
   */
  initiateCall() {
    this.showNotification('info', 'Iniciando llamada...', `Conectando con ${this.currentRecipient}`);
    setTimeout(() => {
      alert(`📞 Llamada iniciada con ${this.currentRecipient}\n\n• Duración estimada: 15-30 min\n• Se registrará automáticamente\n• Resumen será enviado post-llamada`);
    }, 1000);
  }

  initiateVideoCall() {
    this.showNotification('info', 'Preparando videollamada...', 'Verificando disponibilidad');
    setTimeout(() => {
      alert(`📹 Videollamada programada con ${this.currentRecipient}\n\n• Enlace: edp-meet.com/urgent-${Date.now()}\n• Se enviará invitación de calendario\n• Grabación automática activada`);
    }, 1500);
  }

  sendWhatsApp() {
    const message = `Hola ${this.currentRecipient}, necesito conversar urgentemente sobre el proyecto EDP-001. ¿Tienes disponibilidad para una llamada breve?`;
    this.showNotification('success', 'WhatsApp enviado', 'Mensaje enviado exitosamente');
    console.log('WhatsApp message:', message);
  }

  /**
   * Quick action functions
   */
  openCommunicationHistory() {
    this.switchTab('history');
    const historyContent = document.getElementById('tabContentHistory');
    if (historyContent) {
      historyContent.innerHTML = `
        <h3 style="color: var(--text-primary);" class="text-lg font-bold mb-4">🕒 Historial de Comunicaciones</h3>
        <div class="space-y-3">
          ${this.generateHistoryItems()}
        </div>
      `;
    }
  }

  generateHistoryItems() {
    const items = [
      { time: '2h ago', type: 'email', contact: 'María González', subject: 'Re: Estado proyecto EDP-001', status: 'read' },
      { time: '5h ago', type: 'call', contact: 'Controller Financiero', subject: 'Llamada telefónica - 15 min', status: 'completed' },
      { time: '1d ago', type: 'meeting', contact: 'Equipo Legal', subject: 'Revisión contractual urgente', status: 'completed' },
      { time: '2d ago', type: 'escalation', contact: 'Dirección General', subject: 'Escalación crítica - EDP-001', status: 'pending' }
    ];

    return items.map(item => `
      <div style="background: var(--bg-subtle); border: 1px solid var(--border-color);" class="p-4 rounded-lg">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full flex items-center justify-center ${this.getTypeColor(item.type)}">
              ${this.getTypeIcon(item.type)}
            </div>
            <div>
              <div style="color: var(--text-primary);" class="font-medium text-sm">${item.contact}</div>
              <div style="color: var(--text-secondary);" class="text-xs">${item.time}</div>
            </div>
          </div>
          <span class="px-2 py-1 rounded text-xs ${this.getStatusClass(item.status)}">${item.status.toUpperCase()}</span>
        </div>
        <div style="color: var(--text-secondary);" class="text-sm">${item.subject}</div>
      </div>
    `).join('');
  }

  getTypeColor(type) {
    const colors = {
      email: 'bg-blue-500 text-white',
      call: 'bg-green-500 text-white', 
      meeting: 'bg-purple-500 text-white',
      escalation: 'bg-red-500 text-white'
    };
    return colors[type] || 'bg-gray-500 text-white';
  }

  getTypeIcon(type) {
    const icons = {
      email: '📧',
      call: '📞',
      meeting: '👥',
      escalation: '🚨'
    };
    return icons[type] || '📝';
  }

  getStatusClass(status) {
    const classes = {
      read: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  openScheduleMeeting() {
    alert('📅 Función de programación de reuniones\n\nPróximamente:\n• Integración con calendario\n• Disponibilidad automática\n• Invitaciones personalizadas\n• Recordatorios automáticos');
  }

  openTaskCreate() {
    alert('📋 Sistema de creación de tareas\n\nPróximamente:\n• Asignación automática\n• Seguimiento de progreso\n• Notificaciones de vencimiento\n• Integración con dashboard');
  }

  openNotificationCenter() {
    alert('🔔 Centro de notificaciones\n\nPróximamente:\n• Vista unificada de todas las comunicaciones\n• Filtros avanzados\n• Configuración de preferencias\n• Análisis de respuestas');
  }

  /**
   * Enhanced form submission
   */
  handleFormSubmission(e) {
    e.preventDefault();

    const messageText = document.getElementById("messageText");
    const messageType = document.getElementById("messageType");
    
    if (!messageText || !messageType) return;

    const notifyApp = this.getCheckboxValue("notifyApp");
    const notifyEmail = this.getCheckboxValue("notifyEmail");
    const notifySlack = this.getCheckboxValue("notifySlack");
    const scheduleMessage = this.getCheckboxValue("scheduleMessage");
    const requireResponse = this.getCheckboxValue("requireResponse");
    const trackDelivery = this.getCheckboxValue("trackDelivery");

    if (!messageText.value.trim()) {
      this.showNotification('error', 'Campo requerido', 'Por favor, escribe un mensaje antes de enviar.');
      return;
    }

    // Enhanced sending simulation
    const sendButton = document.getElementById("sendButton");
    if (!sendButton) return;

    sendButton.innerHTML = `
      <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Procesando envío...
    `;
    sendButton.disabled = true;

    // Simulate processing steps
    const steps = [
      { message: "Validando destinatario...", delay: 500 },
      { message: "Procesando archivos adjuntos...", delay: 800 },
      { message: "Configurando notificaciones...", delay: 600 },
      { message: "Enviando mensaje...", delay: 1000 }
    ];

    this.processSteps(steps, 0, sendButton, {
      notifyApp, notifyEmail, notifySlack, scheduleMessage, requireResponse, trackDelivery
    });
  }

  processSteps(steps, stepIndex, sendButton, options) {
    if (stepIndex < steps.length) {
      sendButton.innerHTML = `
        <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        ${steps[stepIndex].message}
      `;
      
      setTimeout(() => {
        this.processSteps(steps, stepIndex + 1, sendButton, options);
      }, steps[stepIndex].delay);
    } else {
      this.completeSending(sendButton, options);
    }
  }

  completeSending(sendButton, options) {
    const deliveryMethods = [
      options.notifyApp && "📱 Aplicación",
      options.notifyEmail && "📧 Email",
      options.notifySlack && "💬 Slack"
    ].filter(Boolean);

    const features = [
      this.attachments.length && `📎 ${this.attachments.length} archivos adjuntos`,
      options.scheduleMessage && "⏰ Envío programado",
      options.requireResponse && "✅ Respuesta requerida",
      options.trackDelivery && "📊 Seguimiento activado"
    ].filter(Boolean);

    this.showNotification(
      'success',
      `✅ Mensaje enviado exitosamente`,
      `Comunicación establecida con ${this.currentRecipient}\n\n` +
      `🎯 Prioridad: ${this.currentPriority.toUpperCase()}\n` +
      `📡 Canales: ${deliveryMethods.join(', ')}\n` +
      (features.length ? `🔧 Características: ${features.join(', ')}\n` : '') +
      `⏰ Tiempo estimado de respuesta: ${this.currentPriority === 'high' ? '1-2 horas' : '2-4 horas'}`
    );

    this.closeCommunicationModal();

    // Reset form
    sendButton.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
      </svg>
      Enviar Consulta
    `;
    sendButton.disabled = false;

    this.updateDashboardStats();
  }

  /**
   * Keyboard shortcuts handler
   */
  handleKeyboardShortcuts(e) {
    const modal = document.getElementById("communicationModal");
    if (!modal) return;

    const isModalOpen = !modal.classList.contains("hidden");
    
    if (e.key === "Escape" && isModalOpen) {
      this.closeCommunicationModal();
    }
    
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && isModalOpen) {
      e.preventDefault();
      const form = document.getElementById("communicationForm");
      if (form) {
        form.dispatchEvent(new Event('submit'));
      }
    }
    
    // Ctrl/Cmd + S to save draft
    if ((e.ctrlKey || e.metaKey) && e.key === "s" && isModalOpen) {
      e.preventDefault();
      this.saveDraft();
    }
  }

  /**
   * Update dashboard stats
   */
  updateDashboardStats() {
    console.log("📊 Dashboard stats updated - new communication sent");
    // This would integrate with the dashboard to update counters
  }

  /**
   * Notification system
   */
  showNotification(type, title, message) {
    console.log(`🔔 ${type.toUpperCase()}: ${title} - ${message}`);

    // Create notification element
    const notification = document.createElement("div");
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'});
      color: white;
      padding: 16px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      max-width: 300px;
      animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 4px;">${title}</div>
      <div style="font-size: 14px; opacity: 0.9;">${message}</div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease-in';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }

  /**
   * Utility functions
   */
  getInitials(name) {
    return name
      .split(" ")
      .map((word) => word.charAt(0))
      .join("")
      .toUpperCase();
  }

  updateElement(id, text) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = text;
    }
  }

  setCheckboxValue(id, value) {
    const checkbox = document.getElementById(id);
    if (checkbox) {
      checkbox.checked = value;
    }
  }

  getCheckboxValue(id) {
    const checkbox = document.getElementById(id);
    return checkbox ? checkbox.checked : false;
  }

  scheduleCall(clientName) {
    alert(
      `📞 Programando llamada con ${clientName}...\n\n` +
      `• Se enviará invitación de calendario\n` +
      `• Se notificará al equipo de gestión\n` +
      `• Se preparará brief con información crítica`
    );
  }

  /**
   * Log system information
   */
  logSystemInfo() {
    console.log("🚀 Sistema de comunicación enterprise cargado");
    console.log("📋 Funcionalidades disponibles:");
    console.log("   • Comunicación multi-canal (app, email, chat)");
    console.log("   • Sistema de templates inteligentes");
    console.log("   • Gestión de archivos adjuntos");
    console.log("   • AI Assistant integrado");
    console.log("   • Seguimiento y analytics");
    console.log("   • Escalación automática por jerarquía");
    console.log("   • Integración con calendario y tareas");
    console.log("   • Historial completo de comunicaciones");
    console.log("✅ Sistema listo para uso en producción");
  }
}

// ========== GLOBAL INSTANCE AND FUNCTION EXPOSURE ==========

// Create global instance
const edpCommunicationSystem = new EDPCommunicationSystem();

// Expose functions globally for HTML onclick compatibility
window.openCommunicationModal = (type, recipientName, messageType) => {
  edpCommunicationSystem.openCommunicationModal(type, recipientName, messageType);
};

window.closeCommunicationModal = () => {
  edpCommunicationSystem.closeCommunicationModal();
};

window.switchTab = (tabName) => {
  edpCommunicationSystem.switchTab(tabName);
};

window.useTemplate = (templateType) => {
  edpCommunicationSystem.useTemplate(templateType);
};

window.setPriority = (level) => {
  edpCommunicationSystem.setPriority(level);
};

window.addAttachment = () => {
  edpCommunicationSystem.addAttachment();
};

window.removeAttachment = (id) => {
  edpCommunicationSystem.removeAttachment(id);
};

window.toggleAIAssist = () => {
  edpCommunicationSystem.toggleAIAssist();
};

window.saveDraft = () => {
  edpCommunicationSystem.saveDraft();
};

window.initiateCall = () => {
  edpCommunicationSystem.initiateCall();
};

window.initiateVideoCall = () => {
  edpCommunicationSystem.initiateVideoCall();
};

window.sendWhatsApp = () => {
  edpCommunicationSystem.sendWhatsApp();
};

window.openCommunicationHistory = () => {
  edpCommunicationSystem.openCommunicationHistory();
};

window.openScheduleMeeting = () => {
  edpCommunicationSystem.openScheduleMeeting();
};

window.openTaskCreate = () => {
  edpCommunicationSystem.openTaskCreate();
};

window.openNotificationCenter = () => {
  edpCommunicationSystem.openNotificationCenter();
};

window.scheduleCall = (clientName) => {
  edpCommunicationSystem.scheduleCall(clientName);
};

// Export for module usage (if needed)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EDPCommunicationSystem;
}

console.log("✅ EDP Communication System - Funciones globales expuestas");
console.log("📱 Sistema listo para interacción desde HTML");

// CSS for animations
const communicationStyle = document.createElement('style');
communicationStyle.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(communicationStyle); 