document.addEventListener('DOMContentLoaded', () => {
    // We need to get fileId and csrfToken from the DOM instead of Jinja templating
    // since this is an external JS file. We can store them as data attributes on the body or read from existing elements.
    
    // fileId can be extracted from the URL if needed, or we can add a meta tag for it.
    // Let's add a meta tag in chat.html or just read it from the URL.
    // The URL is like /chat/<file_id>
    const pathParts = window.location.pathname.split('/');
    const fileId = pathParts[pathParts.length - 1];
    
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
    
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const suggestions = document.querySelectorAll('.suggestion-btn');
    
    // AI Memory Context
    let chatHistory = [];
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addMessage(text, sender, components = {}) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        let html = `<div class="bubble">`;
        html += text;
        
        // Add Chart if present
        if (components.chart) {
            html += `<br><img src="${components.chart}" class="chart-img" alt="Data Chart" />`;
        }
        
        // Add Table if present
        if (components.table) {
            html += components.table;
        }
        
        html += `</div>`;
        
        // Add Explanation if AI and present
        if (sender === 'ai' && components.explanation) {
            html += `<div class="explanation-card">🔍 <strong>Performed:</strong> ${components.explanation}</div>`;
        }
        
        msgDiv.innerHTML = html;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function addTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message ai typing-indicator';
        msgDiv.id = 'typing-indicator';
        msgDiv.innerHTML = `
            <div class="bubble typing">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
    
    async function sendMessage(question) {
        if (!question.trim()) return;
        
        // 1. Add User Message
        addMessage(question, 'user');
        chatInput.value = '';
        sendBtn.disabled = true;
        chatInput.disabled = true;
        
        // 2. Show Typing
        addTypingIndicator();
        
        // 3. API Call
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    file_id: fileId,
                    question: question,
                    history: chatHistory
                })
            });
            
            const data = await response.json();
            removeTypingIndicator();
            
            if (response.ok) {
                // 4. Update Memory
                if (data.parsed_intent) {
                    chatHistory.push({
                        question: question,
                        parsed_intent: data.parsed_intent
                    });
                    // Keep memory small
                    if (chatHistory.length > 5) chatHistory.shift();
                }
                
                // 5. Render AI Response
                addMessage(data.answer, 'ai', {
                    chart: data.chart,
                    table: data.table,
                    explanation: data.explanation
                });
            } else {
                addMessage("❌ Error: " + (data.error || "Failed to process question."), 'ai');
            }
        } catch (err) {
            removeTypingIndicator();
            addMessage("❌ Network Error: Could not reach the AI Engine.", 'ai');
            console.error(err);
        } finally {
            sendBtn.disabled = false;
            chatInput.disabled = false;
            chatInput.focus();
        }
    }
    
    // Events
    if (sendBtn) {
        sendBtn.addEventListener('click', () => sendMessage(chatInput.value));
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage(chatInput.value);
        });
    }
    
    suggestions.forEach(btn => {
        btn.addEventListener('click', () => {
            sendMessage(btn.textContent);
        });
    });
    
    if (chatInput) {
        chatInput.focus();
    }
});
