// chatbot.js

(function() {
    // --- CONFIGURATION ---
    const API_BASE_URL = 'http://127.0.0.1:5001';

    // Get references to the UI elements
    const container = document.getElementById('faq-bot-container');
    const toggleButton = document.getElementById('faq-bot-toggle-button');
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const chatContainer = document.getElementById('chat-container');
    const iconOpen = toggleButton.querySelector('.icon-open');
    const iconClose = toggleButton.querySelector('.icon-close');
    
    // --- STATE MANAGEMENT ---
    let session_id = getOrCreateSessionId();
    let isInitialized = false;
    let messageQueue = [];

    // Load 'marked' library for Markdown rendering
    if (typeof marked === 'undefined') {
        let script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        document.head.appendChild(script);
    }
    
    const welcomeMessage = `
        Hello! How can I help you today? You can ask me anything or start with one of these common questions:
        <ul class="faq-list">
            <li>What is the main topic of the document?</li>
            <li>Can you summarize the key points?</li>
            <li>Who is the intended audience?</li>
        </ul>
    `;
    
    // --- CORE FUNCTIONS ---
    
    function getOrCreateSessionId() {
        let storedId = localStorage.getItem('faq_bot_session_id');
        if (!storedId) {
            storedId = 'sess_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('faq_bot_session_id', storedId);
        }
        return storedId;
    }
    
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        if (sender === 'bot') {
            messageDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(text) : text;
        } else {
            messageDiv.textContent = text;
        }
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        sessionStorage.setItem('faq_bot_chat_html', chatContainer.innerHTML);
    }
    
    async function submitQuery(query) {
        if (!query) return;

        // NEW: If not initialized, queue the message and do nothing else.
        if (!isInitialized) {
            addMessage(query, 'user');
            messageQueue.push(query);
            return;
        }

        addMessage(query, 'user');
        try {
            const response = await fetch(`${API_BASE_URL}/api/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, session_id: session_id })
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            addMessage(data.response, 'bot');
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, an error occurred. The API might be offline.', 'bot');
        }
    }
    
    async function initializeSession() {
        try {
            // Show your quirky loading message immediately.
            addMessage("Establishing connection to the unknown...", 'bot');

            // Call the new initialization endpoint.
            const response = await fetch(`${API_BASE_URL}/api/init`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: session_id })
            });

            if (!response.ok) throw new Error('Initialization failed on the server.');

            // --- Initialization Successful ---
            isInitialized = true;
            sessionStorage.setItem('faq_bot_initialized', 'true');
            
            // Clear the loading message and show the real welcome message.
            chatContainer.innerHTML = '';
            addMessage(welcomeMessage, 'bot');
            
            // Process any messages that the user typed while we were loading.
            if (messageQueue.length > 0) {
                for (const query of messageQueue) {
                    await submitQuery(query);
                }
                messageQueue = []; // Clear the queue
            }
        } catch (error) {
            console.error("Initialization error:", error);
            chatContainer.innerHTML = '';
            addMessage("Connection failed. Please refresh the page to try again.", 'bot');
        }
    }
    
    function restoreSession() {
        const savedHtml = sessionStorage.getItem('faq_bot_chat_html');
        const isOpen = sessionStorage.getItem('faq_bot_is_open') === 'true';

        if (savedHtml) {
            chatContainer.innerHTML = savedHtml;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            // This should not happen if initialized, but it's a good fallback.
            addMessage(welcomeMessage, 'bot');
        }

        if (isOpen) {
            container.classList.add('open');
            iconOpen.style.display = 'none';
            iconClose.style.display = 'block';
        }
    }

    // --- EVENT LISTENERS ---
    
    toggleButton.addEventListener('click', () => {
        container.classList.toggle('open');
        const isOpen = container.classList.contains('open');
        iconOpen.style.display = isOpen ? 'none' : 'block';
        iconClose.style.display = isOpen ? 'block' : 'none';
        sessionStorage.setItem('faq_bot_is_open', isOpen);
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        submitQuery(query);
        queryInput.value = '';
    });

    chatContainer.addEventListener('click', (e) => {
        if (e.target && e.target.nodeName === 'LI') {
            const question = e.target.textContent;
            submitQuery(question);
        }
    });

    // --- INITIALIZATION LOGIC ---
    
    // Check if this tab has already been initialized to support cross-page persistence.
    if (sessionStorage.getItem('faq_bot_initialized') === 'true') {
        isInitialized = true;
        restoreSession();
    } else {
        // If it's a new tab, start the initialization process.
        initializeSession();
    }
})();