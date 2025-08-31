// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking on a nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }
});

// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const searchIcon = document.querySelector('.search-icon');
    
    if (searchInput && searchIcon) {
        searchIcon.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) {
                // Simulate search functionality
                alert(`Searching for: ${query}`);
                // In a real implementation, this would redirect to search results
                // window.location.href = `search.html?q=${encodeURIComponent(query)}`;
            }
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    alert(`Searching for: ${query}`);
                }
            }
        });
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animation on scroll
function animateOnScroll() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.program-card, .news-card, .quick-link-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', animateOnScroll);

// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 100) {
        header.style.background = 'rgba(255, 255, 255, 0.95)';
        header.style.backdropFilter = 'blur(10px)';
    } else {
        header.style.background = '#fff';
        header.style.backdropFilter = 'none';
    }
});

// Button hover effects
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-2px)';
    });
    
    button.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});

// Form validation (for future forms)
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
            field.addEventListener('input', function() {
                this.classList.remove('error');
            });
        }
    });
    
    return isValid;
}

// News card interactions
document.querySelectorAll('.news-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-10px)';
        this.style.boxShadow = '0 15px 40px rgba(0, 0, 0, 0.15)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(-5px)';
        this.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.1)';
    });
});

// Loading animation for buttons
function addLoadingState(button, text = 'Loading...') {
    const originalText = button.textContent;
    button.textContent = text;
    button.disabled = true;
    button.style.opacity = '0.7';
    
    // Simulate loading (remove this in real implementation)
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
        button.style.opacity = '1';
    }, 2000);
}

// Add click handlers for action buttons
document.addEventListener('DOMContentLoaded', function() {
    const applyButton = document.querySelector('.hero-actions .btn-primary');
    const tourButton = document.querySelector('.hero-actions .btn-secondary');
    const portalButton = document.querySelector('.nav-actions .btn-primary');
    
    if (applyButton) {
        applyButton.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Redirecting to application portal...');
            // In real implementation: window.location.href = 'apply.html';
        });
    }
    
    if (tourButton) {
        tourButton.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Starting virtual campus tour...');
            // In real implementation: window.location.href = 'virtual-tour.html';
        });
    }
    
    if (portalButton) {
        portalButton.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Redirecting to student portal...');
            // In real implementation: window.location.href = 'https://portal.meridianuniversity.edu';
        });
    }
});

// Utility function for API calls (for future use)
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// News feed functionality (for future dynamic content)
function loadNews() {
    // This would typically fetch from an API
    // fetchData('/api/news')
    //     .then(news => displayNews(news))
    //     .catch(error => console.error('Failed to load news:', error));
}

// Event handlers for quick links
document.querySelectorAll('.quick-link-card').forEach(card => {
    card.addEventListener('click', function(e) {
        e.preventDefault();
        const title = this.querySelector('h3').textContent;
        alert(`Accessing ${title}...`);
        // In real implementation, redirect to appropriate page
    });
});

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Meridian University website loaded successfully!');
    
    // Add any initialization code here
    // Example: loadNews();
});