// Navbar JavaScript

// Toggle user dropdown menu
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

function openPostModal() {
    const modal = document.getElementById('postModal');
    if (modal) {
        modal.classList.add('show');
        const textarea = modal.querySelector('textarea');
        if (textarea) {
            setTimeout(() => textarea.focus(), 100);
        }
    }
}

function closePostModal() {
    const modal = document.getElementById('postModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Update notification badge
function updateNotificationBadge() {
    fetch('/notifications/unread-count/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationBadge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

// Update badge on page load and every 30 seconds
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationBadge();
    setInterval(updateNotificationBadge, 30000); // Update every 30 seconds
});

document.addEventListener('click', function(event) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && dropdown && !userMenu.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closePostModal();
    }
});
