// SocketIO connection
const socket = io();

// Notification variables
let unreadCount = 0;
let notifications = [];

// Connect to WebSocket
socket.on('connect', function() {
    console.log('Connected to notification server');
});

// Handle new notification
socket.on('new_notification', function(notification) {
    // Add to notifications array
    notifications.unshift(notification);
    
    // Update unread count
    unreadCount++;
    updateNotificationBadge();
    
    // Show browser notification if permitted
    if (Notification.permission === 'granted') {
        new Notification(notification.title, {
            body: notification.message,
            icon: '/static/img/icon.png'
        });
    }
    
    // Show toast notification
    showToast(notification);
});

// Update unread count
socket.on('unread_count', function(data) {
    unreadCount = data.count;
    updateNotificationBadge();
});

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Update notification badge
function updateNotificationBadge() {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Show toast notification
function showToast(notification) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        background: #1f1f1f;
        border-left: 4px solid #e50914;
        border-radius: 4px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        color: #fff;
        min-width: 300px;
        animation: slideIn 0.3s ease;
    `;
    
    toast.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <strong style="color: #e50914;">${notification.title}</strong>
                <div style="font-size: 14px; color: #b3b3b3; margin-top: 5px;">${notification.message}</div>
                <small style="color: #6c757d;">${notification.time_ago}</small>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: #fff; cursor: pointer;">×</button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Mark notification as read
function markAsRead(notificationId) {
    socket.emit('mark_read', { notification_id: notificationId });
}

// Mark all as read
function markAllAsRead() {
    socket.emit('mark_all_read');
}

// Load notifications
function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            notifications = data.notifications;
            unreadCount = data.unread_count;
            updateNotificationBadge();
            renderNotifications();
        });
}

// Render notifications dropdown
function renderNotifications() {
    const dropdown = document.getElementById('notificationsDropdown');
    if (!dropdown) return;
    
    let html = '';
    notifications.slice(0, 10).forEach(notification => {
        html += `
            <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                 onclick="markAsRead(${notification.id})"
                 style="padding: 10px; border-bottom: 1px solid #333; cursor: pointer;">
                <div style="display: flex; gap: 10px;">
                    <i class="bi ${getNotificationIcon(notification.type)}" style="color: #e50914;"></i>
                    <div>
                        <strong>${notification.title}</strong>
                        <div style="font-size: 12px; color: #b3b3b3;">${notification.message}</div>
                        <small style="color: #6c757d;">${notification.time_ago}</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    dropdown.innerHTML = html || '<div style="padding: 20px; text-align: center;">No notifications</div>';
}

// Get icon for notification type
function getNotificationIcon(type) {
    const icons = {
        'task_assigned': 'bi-check-circle',
        'project_update': 'bi-building',
        'milestone_due': 'bi-calendar',
        'comment': 'bi-chat',
        'submittal': 'bi-file-text'
    };
    return icons[type] || 'bi-bell';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    requestNotificationPermission();
    loadNotifications();
    
    // Add notification bell to navbar
    const navRight = document.querySelector('.nav-right');
    if (navRight) {
        const notificationBell = document.createElement('div');
        notificationBell.className = 'nav-icon position-relative';
        notificationBell.innerHTML = `
            <i class="bi bi-bell"></i>
            <span id="notificationBadge" class="notification-badge" style="display: none;">0</span>
        `;
        notificationBell.onclick = function() {
            // Toggle notifications dropdown
            let dropdown = document.getElementById('notificationsDropdown');
            if (!dropdown) {
                dropdown = document.createElement('div');
                dropdown.id = 'notificationsDropdown';
                dropdown.style.cssText = `
                    position: absolute;
                    top: 100%;
                    right: 0;
                    background: #1f1f1f;
                    border: 1px solid #333;
                    border-radius: 4px;
                    width: 350px;
                    max-height: 400px;
                    overflow-y: auto;
                    margin-top: 10px;
                    z-index: 1000;
                `;
                this.appendChild(dropdown);
                renderNotifications();
            }
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        };
        
        navRight.insertBefore(notificationBell, navRight.firstChild);
    }
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
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
    
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #e50914;
        color: #fff;
        font-size: 10px;
        min-width: 16px;
        height: 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 4px;
    }
    
    .notification-item.unread {
        background: rgba(229, 9, 20, 0.1);
    }
    
    .notification-item:hover {
        background: #333;
    }
`;
document.head.appendChild(style);