// chatbot.js

(function() {
    // Step 1: Define the complete HTML and CSS.
    const chatbotUiHtml = `
    <div id="faq-bot-container">
        <style>
            #faq-bot-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
            #faq-bot-container * { box-sizing: border-box; }
            #faq-bot-toggle-button { background-color: #007bff; color: white; width: 60px; height: 60px; border-radius: 50%; border: none; font-size: 24px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.2s ease; display: flex; justify-content: center; align-items: center; }
            #faq-bot-container .chat-widget {
                width: 400px;
                max-height: 70vh;
                background: white;
                border-radius: 15px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.2);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                position: absolute;
                bottom: 80px;
                right: 0;
                opacity: 0;
                transform: translateY(20px);
                pointer-events: none;
                transition: opacity 0.3s ease, transform 0.3s ease;
                position: relative; 
            }
            #faq-bot-container.open .chat-widget { opacity: 1; transform: translateY(0); pointer-events: auto; }
            #faq-bot-container .header {
                background: #007bff;
                color: white;
                padding: 15px;
                text-align: center;
                font-weight: bold;
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                z-index: 1;
            }
            #faq-bot-container #chat-container {
                flex: 1;
                padding: 70px 20px 20px 20px;
                overflow-y: auto;
                background-color: #f7f8fc;
            }
            #faq-bot-container .message { max-width: 85%; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
            #faq-bot-container .user-message { background-color: #007bff; color: white; align-self: flex-end; }
            #faq-bot-container .bot-message { background-color: #e9e9eb; color: #333; align-self: flex-start; white-space: pre-wrap; }
            #faq-bot-container #form-container {
                display: flex;
                padding: 10px;
                border-top: 1px solid #eee;
                background: #fff;
                align-items: center;
            }
            
            /* --- CSS FIX IS HERE --- */
            #faq-bot-container #query-input {
                flex: 1;
                border: 1px solid #ccc;
                border-radius: 20px;
                padding: 10px;
                font-size: 1em;
                font-family: inherit; /* Ensures textarea uses the same font */
                line-height: 1.4;
                margin-right: 10px;
                resize: none; /* Hides the manual resize handle */
                overflow-y: hidden; /* Prevents scrollbar from flashing */
                max-height: 100px; /* Limits the max growth height */
                width: 20vw;
            }

            #faq-bot-container #query-input:disabled { background-color: #f5f5f5; cursor: not-allowed; }
            #faq-bot-container #submit-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #007bff; align-self: flex-end; padding-bottom: 5px; } /* Aligns button to bottom */
            #faq-bot-container #submit-btn:disabled { color: #aaa; cursor: not-allowed; }
        </style>
        
        <div class="chat-widget">
            <div class="header">FAQ Assistant</div>
            <div id="chat-container"></div>
            <form id="chat-form" style="display: flex; width: 100%;">
                <div id="form-container">
                    <textarea id="query-input" placeholder="Please wait..." required disabled rows="1"></textarea>
                    <button id="submit-btn" type="submit" aria-label="Send" disabled>➡️</button>
                </div>
            </form>
        </div>

        <button id="faq-bot-toggle-button" aria-label="Toggle Chat">
            <span class="icon-open">?</span>
            <span class="icon-close" style="display:none;">X</span>
        </button>
    </div>
    `;

    // Step 2: Inject the UI.
    document.body.insertAdjacentHTML('beforeend', chatbotUiHtml);

    // Step 3: Run the script.
    function initializeChatbot() {
        const API_BASE_URL = 'http://127.0.0.1:5001';
        
        const container = document.getElementById('faq-bot-container');
        const toggleButton = document.getElementById('faq-bot-toggle-button');
        const chatForm = document.getElementById('chat-form');
        const queryInput = document.getElementById('query-input'); // This now refers to the <textarea>
        const submitBtn = document.getElementById('submit-btn');
        const chatContainer = document.getElementById('chat-container');
        const iconOpen = toggleButton.querySelector('.icon-open');
        const iconClose = toggleButton.querySelector('.icon-close');
        
        let session_id = localStorage.getItem('faq_bot_session_id') || 'sess_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('faq_bot_session_id', session_id);
        
        const welcomeMessage = `Hello! How can I help you?
You can try asking one of these suggestions:
- What is the main topic?
- Can you summarize the key points?`;

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `${sender}-message`);
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 0);
            sessionStorage.setItem('faq_bot_chat_html', chatContainer.innerHTML);
        }

        async function submitQuery(query) {
            if (!query) return;
            addMessage(query, 'user');
            const loadingMessage = document.createElement('div');
            loadingMessage.classList.add('message', 'bot-message');
            loadingMessage.textContent = "Thinking...";
            chatContainer.appendChild(loadingMessage);
            setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 0);

            try {
                const response = await fetch(`${API_BASE_URL}/api/ask`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, session_id: session_id })
                });
                chatContainer.removeChild(loadingMessage);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'API request failed');
                }
                const data = await response.json();
                addMessage(data.response, 'bot');
            } catch (error) {
                console.error('Error:', error);
                if(chatContainer.contains(loadingMessage)) {
                    chatContainer.removeChild(loadingMessage);
                }
                addMessage(`Sorry, an error occurred: ${error.message}`, 'bot');
            }
        }
        
        function enableForm() {
            queryInput.disabled = false;
            submitBtn.disabled = false;
            queryInput.placeholder = "Ask a question...";
        }

        async function initializeSession() {
            try {
                addMessage("Establishing connection to the unknown...", 'bot');
                const response = await fetch(`${API_BASE_URL}/api/init`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: session_id })
                });
                if (!response.ok) throw new Error('Initialization failed on the server.');
                sessionStorage.setItem('faq_bot_initialized', 'true');
                chatContainer.innerHTML = '';
                addMessage(welcomeMessage, 'bot');
				enableForm();
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
                setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 0);
            }
            if (isOpen) {
                container.classList.add('open');
                iconOpen.style.display = 'none';
                iconClose.style.display = 'block';
            }
            enableForm();
        }

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
            if (query) {
                submitQuery(query);
                queryInput.value = '';
                queryInput.style.height = 'auto'; // Reset height after sending
            }
        });
        
        // --- JAVASCRIPT FIX IS HERE ---
        // This makes the textarea auto-grow.
        queryInput.addEventListener('input', () => {
            queryInput.style.height = 'auto';
            queryInput.style.height = `${queryInput.scrollHeight}px`;
        });
        
        // Prevents Enter from submitting the form, allowing for new lines.
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        });


        if (sessionStorage.getItem('faq_bot_initialized') === 'true') {
            restoreSession();
        } else {
            initializeSession();
        }
    }

    initializeChatbot();
})();