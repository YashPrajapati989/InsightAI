document.addEventListener('DOMContentLoaded', () => {
    // 1. Inject the loader HTML into the body if it doesn't exist
    if (!document.getElementById('global-loader')) {
        const loaderHTML = `
            <div id="global-loader">
                <div class="spinner"></div>
                <div class="loader-text" id="loader-message">Processing your request...</div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loaderHTML);
    }

    const loader = document.getElementById('global-loader');
    const loaderMessage = document.getElementById('loader-message');

    function showLoader(message) {
        if (message) {
            loaderMessage.textContent = message;
        }
        loader.classList.add('active');
    }

    // 2. Hook into all forms. Show loader on submit unless it has a 'no-loader' class
    const forms = document.querySelectorAll('form:not(.no-loader)');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (e.defaultPrevented) return;
            
            // Give specific messages based on the form action
            const action = form.getAttribute('action') || '';
            if (action.includes('/upload')) {
                showLoader('Uploading and analyzing dataset...');
            } else if (action.includes('/clean')) {
                showLoader('Applying AI Data Cleaning...');
            } else {
                showLoader('Processing...');
            }
        });
    });

    // 3. Hook into specific links that trigger heavy processing
    // Dashboard Recommendations
    const recLinks = document.querySelectorAll('a[href*="/recommendations/"]');
    recLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Ignore if it opens in a new tab
            if (link.target === '_blank') return;
            showLoader('Generating Dashboard Recommendations...');
        });
    });

    // Storytelling
    const storyLinks = document.querySelectorAll('a[href*="/storytelling/"]');
    storyLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Ignore if it opens in a new tab
            if (link.target === '_blank') return;
            showLoader('Generating AI Business Story...');
        });
    });
});
