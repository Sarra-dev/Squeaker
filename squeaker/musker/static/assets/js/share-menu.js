// Close share menu when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.share-wrapper')) {
        document.querySelectorAll('.share-popup').forEach(menu => {
            menu.style.display = 'none';
        });
    }
});

// Toggle share menu visibility
function toggleShareMenu(event, meepId) {
    event.preventDefault();
    event.stopPropagation();
    
    const menu = document.getElementById('share-menu-' + meepId);
    
    document.querySelectorAll('.share-popup').forEach(m => {
        if (m.id !== 'share-menu-' + meepId) {
            m.style.display = 'none';
        }
    });
    
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

// Handle share option clicks
document.addEventListener('click', function(event) {
    const option = event.target.closest('.share-option');
    if (!option) return;
    
    const menu = option.closest('.share-popup');
    const meepUrl = menu.dataset.meepUrl;
    const meepId = menu.dataset.meepId;
    const action = option.dataset.action;
    
    // Prevent default and stop propagation for all options
    event.preventDefault();
    event.stopPropagation();
    
    switch (action) {
        case 'copy':
            copyLink(option, meepUrl);
            break;
            
        case 'repost':
            repostMeep(option, meepId);
            break;
            
        case 'whatsapp':
            shareOnWhatsApp(meepUrl);
            break;
            
        case 'facebook':
            shareOnFacebook(meepUrl);
            break;
    }
    
    // Close the menu after action
    menu.style.display = 'none';
});

// Copy link to clipboard
function copyLink(option, url) {
    navigator.clipboard.writeText(url).then(function() {
        const originalHTML = option.innerHTML;
        const checkIcon = option.querySelector('i').cloneNode(true);
        option.innerHTML = '';
        option.appendChild(checkIcon);
        option.innerHTML += ' Copied!';
        option.style.color = 'var(--primary-color)';
        
        setTimeout(() => {
            option.innerHTML = originalHTML;
            option.style.color = '';
        }, 1500);
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
        showToast('Failed to copy link', 'error');
    });
}

// Share on WhatsApp
function shareOnWhatsApp(url) {
    const text = `Check this out: ${url}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(whatsappUrl, '_blank');
}

// Share on Facebook
function shareOnFacebook(url) {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(facebookUrl, 'facebook-share-dialog', 'width=800,height=600');
}

// Repost meep
function repostMeep(option, meepId) {
    // Show loading state
    const originalHTML = option.innerHTML;
    option.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reposting...';
    
    // Here you would make an AJAX call to your Django backend
    // to handle the repost functionality
    fetch(`/meep/${meepId}/repost/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Successfully reposted!', 'success');
            // Optionally update the UI to show the repost
        } else {
            throw new Error(data.error || 'Failed to repost');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to repost', 'error');
    })
    .finally(() => {
        option.innerHTML = originalHTML;
    });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show toast notification
function showToast(message, type = 'info') {
    // You can implement a toast notification system here
    // For now, we'll use a simple alert
    alert(`${type.toUpperCase()}: ${message}`);
}