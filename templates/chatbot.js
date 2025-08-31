// chatbot.js

(function() {
    // Step 1: Define the complete HTML and CSS for the chatbot UI as a string.
    const chatbotUiHtml = `
    <div id="faq-bot-container">
        <style>
            #faq-bot-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
            #faq-bot-container * { box-sizing: border-box; }
            #faq-bot-toggle-button { background-color: #007bff; color: white; width: 60px; height: 60px; border-radius: 50%; border: none; font-size: 24px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.2s ease, background-color 0.2s ease; display: flex; justify-content: center; align-items: center; }
            #faq-bot-toggle-button:hover { transform: scale(1.1); background-color: #0056b3; }
            #faq-bot-container .chat-widget { width: 370px; max-height: 70vh; background: white; border-radius: 15px; box-shadow: 0 5px 25px rgba(0,0,0,0.2); overflow: hidden; display: flex; flex-direction: column; position: absolute; bottom: 80px; right: 0; opacity: 0; transform: translateY(20px); pointer-events: none; transition: opacity 0.3s ease, transform 0.3s ease; }
            #faq-bot-container.open .chat-widget { opacity: 1; transform: translateY(0); pointer-events: auto; }
            #faq-bot-container.open #faq-bot-toggle-button { transform: rotate(180deg); }
            #faq-bot-container .header { background: #007bff; color: white; padding: 15px; text-align: center; font-weight: bold; }
            #faq-bot-container #chat-container { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; background-color: #f7f8fc; }
            #faq-bot-container .message { max-width: 85%; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
            #faq-bot-container .user-message { background-color: #007bff; color: white; align-self: flex-end; }
            #faq-bot-container .bot-message { background-color: #e9e9eb; color: #333; align-self: flex-start; }
            #faq-bot-container .bot-message ul, #faq-bot-container .bot-message ol { padding-left: 20px; margin: 5px 0; }
            #faq-bot-container .bot-message .faq-list { list-style: none; padding: 0; cursor: pointer; }
            #faq-bot-container .bot-message .faq-list li { background-color: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-top: 5px; transition: background-color 0.2s; }
            #faq-bot-container .bot-message .faq-list li:hover { background-color: #f1f1f1; }
            #faq-bot-container #form-container { display: flex; padding: 10px; border-top: 1px solid #eee; background: #fff; }
            #faq-bot-container #query-input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; margin-right: 10px; font-size: 1em; }
            #faq-bot-container #query-input:focus { outline: none; border-color: #007bff; }
            #faq-bot-container #submit-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #007bff; }
        </style>
        
        <div class="chat-widget">
            <div class="header">FAQ Assistant</div>
            <div id="chat-container"></div>
            <form id="chat-form" style="display: flex; width: 100%;">
                <div id="form-container">
                    <input type="text" id="query-input" placeholder="Ask a question..." autocomplete="off" required>
                    <button id="submit-btn" type="submit" aria-label="Send">➡️</button>
                </div>
            </form>
        </div>

        <button id="faq-bot-toggle-button" aria-label="Toggle Chat">
            <span class="icon-open">?</span>
            <span class="icon-close" style="display:none;">X</span>
        </button>
    </div>
    `;

    // Step 2: Inject the UI into the host page's body.
    document.body.insertAdjacentHTML('beforeend', chatbotUiHtml);

    // Step 3: Define the main chatbot logic in a function.
    // This function will only be called AFTER the 'marked' library is loaded.
    function initializeChatbot() {
        const API_BASE_URL = 'http://127.0.0.1:5001';
        
        const container = document.getElementById('faq-bot-container');
        const toggleButton = document.getElementById('faq-bot-toggle-button');
        const chatForm = document.getElementById('chat-form');
        const queryInput = document.getElementById('query-input');
        const chatContainer = document.getElementById('chat-container');
        const iconOpen = toggleButton.querySelector('.icon-open');
        const iconClose = toggleButton.querySelector('.icon-close');
        
        let session_id = getOrCreateSessionId();
        let isInitialized = false;
        let messageQueue = [];

        const welcomeMessage = `
            Hello! How can I help you today? You can ask me anything or start with one of these common questions:
            <ul class="faq-list">
                <li>What is the main topic of the document?</li>
                <li>Can you summarize the key points?</li>
                <li>Who is the intended audience?</li>
            </ul>
        `;

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
            // Now that 'marked' is guaranteed to be loaded, we can use it directly.
            if (sender === 'bot') {
                messageDiv.innerHTML = marked.parse(text);
            } else {
                messageDiv.textContent = text;
            }
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            sessionStorage.setItem('faq_bot_chat_html', chatContainer.innerHTML);
        }

        async function submitQuery(query) {
            if (!query) return;
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
                addMessage("Establishing connection to the unknown...", 'bot');
                const response = await fetch(`${API_BASE_URL}/api/init`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: session_id })
                });
                if (!response.ok) throw new Error('Initialization failed on the server.');
                isInitialized = true;
                sessionStorage.setItem('faq_bot_initialized', 'true');
                chatContainer.innerHTML = '';
                addMessage(welcomeMessage, 'bot');
                if (messageQueue.length > 0) {
                    for (const query of messageQueue) {
                        await submitQuery(query);
                    }
                    messageQueue = [];
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
                addMessage(welcomeMessage, 'bot');
            }
            if (isOpen) {
                container.classList.add('open');
                iconOpen.style.display = 'none';
                iconClose.style.display = 'block';
            }
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
            submitQuery(query);
            queryInput.value = '';
        });
        chatContainer.addEventListener('click', (e) => {
            if (e.target && e.target.nodeName === 'LI') {
                const question = e.target.textContent;
                submitQuery(question);
            }
        });

        if (sessionStorage.getItem('faq_bot_initialized') === 'true') {
            isInitialized = true;
            restoreSession();
        } else {
            initializeSession();
        }
    }

    // Step 4: Load the 'marked.js' library and run the chatbot logic only after it's loaded.
    if (typeof marked === 'undefined') {
        let script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.onload = initializeChatbot; // Run the main logic after the script has loaded.
        document.head.appendChild(script);
    } else {
        initializeChatbot(); // If it's already on the page for some reason, run immediately.
    }

})();