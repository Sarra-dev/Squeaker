document.addEventListener('click', function(event) {
    if (!event.target.closest('.share-wrapper')) {
        document.querySelectorAll('.share-popup').forEach(menu => {
            menu.style.display = 'none';
        });
    }
});

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

function copyLink(event, url) {
    event.preventDefault();
    event.stopPropagation();
    
    navigator.clipboard.writeText(url).then(function() {
        const option = event.currentTarget;
        const originalHTML = option.innerHTML;
        option.innerHTML = '<i class="fas fa-check"></i> Copied!';
        option.style.color = 'var(--primary-color)';
        
        setTimeout(() => {
            option.innerHTML = originalHTML;
            option.style.color = '';
            option.closest('.share-popup').style.display = 'none';
        }, 1500);
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
        alert('Failed to copy link');
    });
}