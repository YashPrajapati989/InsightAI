document.addEventListener('DOMContentLoaded', () => {
    const btnCopy = document.getElementById('btn-copy');
    const btnPrint = document.getElementById('btn-print');

    if (btnCopy) {
        btnCopy.addEventListener('click', () => {
            const reportContainer = document.getElementById('story-report');
            if (!reportContainer) return;
            
            const reportText = reportContainer.innerText;
            // Clean up button text from the copy
            const cleanText = reportText
                .replace("📝 Copy Story", "")
                .replace("📄 Download Story Report", "")
                .replace("⬅ Back to Dashboard Recommendations", "")
                .trim();
            
            // Fallback for older browsers or if clipboard API fails (e.g. non-HTTPS localhost without clipboard perms)
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(cleanText).then(() => {
                    alert("Story Report copied to clipboard!");
                }).catch(err => {
                    console.error("Could not copy text using Clipboard API: ", err);
                    fallbackCopyTextToClipboard(cleanText);
                });
            } else {
                fallbackCopyTextToClipboard(cleanText);
            }
        });
    }

    if (btnPrint) {
        btnPrint.addEventListener('click', () => {
            window.print();
        });
    }

    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        
        // Avoid scrolling to bottom
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            if (successful) {
                alert("Story Report copied to clipboard!");
            } else {
                alert("Failed to copy. Please select the text manually.");
            }
        } catch (err) {
            console.error('Fallback: Oops, unable to copy', err);
            alert("Failed to copy. Please select the text manually.");
        }

        document.body.removeChild(textArea);
    }
});
