/**
 * Control Panel Main JavaScript
 * Handles the main functionality for the control panel interface
 */

// Global variables
window.controlPanelState = {
    isInitialized: false,
    currentFilter: 'all',
    dragEnabled: true,
    socketConnected: false
};

/**
 * Initialize the control panel
 */
function initControlPanel() {
    if (window.controlPanelState.isInitialized) {
        console.log('Control panel already initialized');
        return;
    }

    console.log('Initializing control panel...');
    
    try {
        // Initialize drag and drop
        initDragAndDrop();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize filters
        initFilters();
        
        // Connect to socket
        initSocketConnection();
        
        window.controlPanelState.isInitialized = true;
        console.log('Control panel initialized successfully');
        
    } catch (error) {
        console.error('Error initializing control panel:', error);
    }
}

/**
 * Initialize drag and drop functionality
 */
function initDragAndDrop() {
    console.log('Initializing drag and drop...');
    
    // Find all kanban columns
    const columns = document.querySelectorAll('.kanban-column-content');
    
    columns.forEach(column => {
        if (window.Sortable) {
            new Sortable(column, {
                group: 'kanban',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onEnd: handleCardMove,
                onStart: function(evt) {
                    evt.item.classList.add('dragging');
                },
                onMove: function(evt) {
                    return window.controlPanelState.dragEnabled;
                }
            });
        }
    });
}

/**
 * Handle card movement between columns
 */
function handleCardMove(evt) {
    evt.item.classList.remove('dragging');
    
    const cardId = evt.item.dataset.edpId;
    const newStatus = evt.to.closest('.kanban-column').dataset.status;
    const oldStatus = evt.from.closest('.kanban-column').dataset.status;
    
    if (newStatus === oldStatus) {
        return; // No change
    }
    
    console.log(`Moving card ${cardId} from ${oldStatus} to ${newStatus}`);
    
    // Send update to server
    updateCardStatus(cardId, newStatus, oldStatus);
}

/**
 * Update card status on server
 */
async function updateCardStatus(edpId, newStatus, oldStatus) {
    try {
        const response = await fetch('/control/update_estado', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                edp_id: edpId,
                nuevo_estado: newStatus,
                estado_anterior: oldStatus
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Status updated successfully');
            showNotification('Estado actualizado correctamente', 'success');
        } else {
            console.error('Error updating status:', result.message);
            showNotification('Error al actualizar estado: ' + result.message, 'error');
            // Revert the move
            revertCardMove(edpId, oldStatus);
        }
        
    } catch (error) {
        console.error('Network error updating status:', error);
        showNotification('Error de conexión', 'error');
        revertCardMove(edpId, oldStatus);
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', handleFilterChange);
    });
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshControlPanel);
    }
}

/**
 * Initialize socket connection
 */
function initSocketConnection() {
    if (typeof io !== 'undefined') {
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Socket connected');
            window.controlPanelState.socketConnected = true;
        });
        
        socket.on('edp_status_updated', (data) => {
            handleRemoteStatusUpdate(data);
        });
        
        socket.on('disconnect', () => {
            console.log('Socket disconnected');
            window.controlPanelState.socketConnected = false;
        });
    }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', initControlPanel);

// Export for external use
window.controlPanel = {
    init: initControlPanel,
    updateStatus: updateCardStatus,
    showNotification: showNotification
};
