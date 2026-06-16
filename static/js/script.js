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

    // 4. File Upload Drag & Drop / Selection UI on Home Page
    const fileInput = document.getElementById("dataset-file");
    const fileText  = document.getElementById("selected-file");
    const form      = document.getElementById("upload-form");
    const toast     = document.getElementById("no-file-toast");
    const dropZone  = document.querySelector('.upload-card');

    if (fileInput && fileText && form) {
        let toastTimer = null;

        // Handle file selection via click
        fileInput.addEventListener("change", function () {
            if (this.files && this.files.length > 0) {
                fileText.textContent = "✅ " + this.files[0].name;
                fileText.style.color = "#16a34a"; // green color to indicate success
                if (toast) toast.style.display = "none";
            } else {
                fileText.textContent = "Choose CSV or Excel File";
                fileText.style.color = "#2563eb";
            }
        });

        if (dropZone) {
            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            document.body.addEventListener('dragenter', preventDefaults, false);
            document.body.addEventListener('dragover', preventDefaults, false);
            document.body.addEventListener('dragleave', preventDefaults, false);
            document.body.addEventListener('drop', preventDefaults, false);

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            // Highlight drop zone when item is dragged over it
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });

            function highlight(e) {
                dropZone.style.background = '#eef4ff';
                dropZone.style.borderColor = '#1d4ed8';
                dropZone.style.transform = 'translateY(-3px)';
            }

            function unhighlight(e) {
                dropZone.style.background = '#f8fbff';
                dropZone.style.borderColor = '#2563eb';
                dropZone.style.transform = 'translateY(0)';
            }

            // Handle dropped files
            dropZone.addEventListener('drop', handleDrop, false);

            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    fileInput.files = files; // Assign files to the input element
                    
                    // Trigger the change event manually to update the UI
                    const event = new Event('change');
                    fileInput.dispatchEvent(event);
                }
            }
        }

        form.addEventListener("submit", function (e) {
            if (!fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();

                if (toast) {
                    // Show toast
                    toast.style.display = "flex";
                    toast.style.animation = "none";
                    // Trigger reflow to restart animation
                    void toast.offsetWidth;
                    toast.style.animation = "slideIn 0.3s ease";

                    // Auto-hide after 4 seconds
                    clearTimeout(toastTimer);
                    toastTimer = setTimeout(() => {
                        toast.style.display = "none";
                    }, 4000);

                    // Scroll toast into view smoothly
                    toast.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            }
        });
    }
});

