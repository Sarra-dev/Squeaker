// UI interactions shared across pages

// Animate action buttons
(function() {
  const buttons = document.querySelectorAll('.action-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      this.style.transform = 'scale(1.1)';
      setTimeout(() => {
        this.style.transform = 'scale(1)';
      }, 200);
    });
  });
})();

// Animate tweet cards
(function() {
  const cards = document.querySelectorAll('.tweet-card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateX(2px)';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateX(0)';
    });
  });
})();
