document.addEventListener('DOMContentLoaded', function() {
    const slideshowContainer = document.getElementById('theme-slideshow-container');
    if (!slideshowContainer) return;
    
    const totalThemes = parseInt(slideshowContainer.getAttribute('data-total-themes') || '0', 10);
    if (totalThemes <= 1) return;
    
    let currentThemeIndex = 0;
    
    const nextButtons = document.querySelectorAll('.btn-next-theme');
    nextButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Hide current slide
            const currentSlide = document.getElementById('theme-slide-' + currentThemeIndex);
            if (currentSlide) {
                currentSlide.style.display = 'none';
            }
            
            // Increment and wrap around
            currentThemeIndex = (currentThemeIndex + 1) % totalThemes;
            
            // Show next slide with a slight fade effect
            const nextSlide = document.getElementById('theme-slide-' + currentThemeIndex);
            if (nextSlide) {
                nextSlide.style.opacity = '0';
                nextSlide.style.display = 'block';
                
                // Trigger reflow and fade in
                void nextSlide.offsetWidth;
                nextSlide.style.transition = 'opacity 0.3s ease';
                nextSlide.style.opacity = '1';
            }
        });
    });
});
