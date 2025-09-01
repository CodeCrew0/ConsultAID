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
                display: flex;
                flex-direction: column;
            }
            #faq-bot-container .message { max-width: 85%; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
            #faq-bot-container .user-message { background-color: #007bff; color: white; align-self: flex-end; }
            #faq-bot-container .bot-message { background-color: #e9e9eb; color: #333; align-self: flex-start; white-space: pre-wrap; }
            #faq-bot-container #form-container {
                display: flex;
                padding: 10px;
                border-top: 1px solid #eee;
                background: #fff;
                align-items: flex-end;
            }
            
            #faq-bot-container #query-input {
                flex: 1;
                border: 1px solid #ccc;
                border-radius: 20px;
                padding: 10px;
                font-size: 1em;
                font-family: inherit;
                line-height: 1.4;
                margin-right: 10px;
                resize: none;
                overflow-y: hidden;
                max-height: 100px;
                min-height: 40px;
                width: 20vw;
            }

            #faq-bot-container #query-input:disabled { background-color: #f5f5f5; cursor: not-allowed; }
            #faq-bot-container #submit-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #007bff; padding: 5px; min-width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; }
            #faq-bot-container #submit-btn:disabled { color: #aaa; cursor: not-allowed; }
        </style>
        
        <div class="chat-widget">
            <div class="header">FAQ Assistant</div>
            <div id="chat-container"></div>
            <form id="chat-form">
                <div id="form-container">
                    <textarea id="query-input" placeholder="Please wait..." required disabled rows="1"></textarea>
                    <button id="submit-btn" type="submit" aria-label="Send" disabled>➡️</button>
                </div>
            </form>
        </div>

        <button id="faq-bot-toggle-button" aria-label="Toggle Chat">
            <span class="icon-open">?</span>
            <span class="icon-close" style="display:none;">✕</span>
        </button>
    </div>
    `;

    // Prevent multiple initializations by checking if UI already exists
    if (document.getElementById('faq-bot-container')) {
        console.log('FAQ Bot UI already exists, skipping initialization...');
        return;
    }

    // Step 2: Inject the UI.
    document.body.insertAdjacentHTML('beforeend', chatbotUiHtml);

    // Step 3: Run the script.
    function initializeChatbot() {
        const API_BASE_URL = 'https://77b493b6d5b1.ngrok-free.app'; //'http://127.0.0.1:5001';
        
        const container = document.getElementById('faq-bot-container');
        const toggleButton = document.getElementById('faq-bot-toggle-button');
        const chatForm = document.getElementById('chat-form');
        const queryInput = document.getElementById('query-input');
        const submitBtn = document.getElementById('submit-btn');
        const chatContainer = document.getElementById('chat-container');
        const iconOpen = toggleButton.querySelector('.icon-open');
        const iconClose = toggleButton.querySelector('.icon-close');
        
        // Generate or retrieve session ID with proper persistence
        let session_id;
        try {
            session_id = localStorage.getItem('faq_bot_session_id');
            if (!session_id) {
                session_id = 'sess_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
                localStorage.setItem('faq_bot_session_id', session_id);
            }
        } catch (e) {
            // Fallback if localStorage is not available
            session_id = 'sess_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
        }
        
        // let session_id;
        let welcomeMessage = `Hello! How can I help you?
You can try asking one of these suggestions:
- What is the main topic?
- Can you summarize the key points?`;

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `${sender}-message`);
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            // Scroll to bottom
            requestAnimationFrame(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            
            // Save chat state
            try {
                sessionStorage.setItem('faq_bot_chat_html', chatContainer.innerHTML);
            } catch (e) {
                console.log('Could not save chat state');
            }
        }

        async function submitQuery(query) {
            if (!query || query.trim() === '') return;
            
            const trimmedQuery = query.trim();
            
            // Disable form during request
            disableForm();
            
            addMessage(trimmedQuery, 'user');
            
            // Show loading message
            const loadingMessage = document.createElement('div');
            loadingMessage.classList.add('message', 'bot-message');
            loadingMessage.textContent = "Thinking...";
            loadingMessage.id = 'loading-message-' + Date.now(); // Unique ID
            chatContainer.appendChild(loadingMessage);
            
            // Scroll to bottom
            requestAnimationFrame(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });

            try {
                const response = await fetch(`${API_BASE_URL}/api/ask`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ 
                        query: trimmedQuery, 
                        session_id: session_id 
                    })
                });

                // Remove loading message
                if (chatContainer.contains(loadingMessage)) {
                    chatContainer.removeChild(loadingMessage);
                }

                if (!response.ok) {
                    let errorMessage = `Server error (${response.status})`;
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.error || errorMessage;
                        console.error('Server error details:', errorData);
                    } catch (e) {
                        console.error('Could not parse error response:', e);
                        errorMessage += ' - Could not parse server response';
                    }
                    throw new Error(errorMessage);
                }

                const data = await response.json();
                addMessage(data.response || 'No response received', 'bot');
                
            } catch (error) {
                console.error('Error details:', error);
                
                // Remove loading message if it still exists
                if (chatContainer.contains(loadingMessage)) {
                    chatContainer.removeChild(loadingMessage);
                }
                
                let errorMsg = `Sorry, an error occurred: ${error.message}`;
                if (error.message.includes('Failed to fetch')) {
                    errorMsg = 'Connection error: Cannot reach the server. Please check if the server is running on port 5001.';
                }
                
                addMessage(errorMsg, 'bot');
            } finally {
                // Re-enable form
                enableForm();
            }
        }
        
        function enableForm() {
            queryInput.disabled = false;
            submitBtn.disabled = false;
            queryInput.placeholder = "Ask a question...";
        }

        function disableForm() {
            queryInput.disabled = true;
            submitBtn.disabled = true;
            queryInput.placeholder = "Please wait...";
        }

        async function initializeSession() {
            // Check if session is already initialized
            try {
                const isInitialized = sessionStorage.getItem('faq_bot_initialized');
                if (isInitialized === 'true') {
                    console.log('Session already initialized, restoring state...');
                    restoreSession();
                    return;
                }
            } catch (e) {
                console.log('SessionStorage not available, proceeding with initialization');
            }

            try {
                addMessage("Establishing connection...", 'bot');
                disableForm();
                
                const response = await fetch(`${API_BASE_URL}/api/init`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ session_id: session_id })
                });
                
                if (!response.ok) {
                    throw new Error(`Initialization failed: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Use welcome message from server (potentially translated)
                if (data.welcome_message) {
                    welcomeMessage = data.welcome_message;
                }
                
                // Mark as initialized
                try {
                    sessionStorage.setItem('faq_bot_initialized', 'true');
                } catch (e) {
                    console.log('Could not set sessionStorage');
                }
                
                // Clear the container and show welcome message
                chatContainer.innerHTML = '';
                addMessage(welcomeMessage, 'bot');
                enableForm();
                
            } catch (error) {
                console.error("Initialization error:", error);
                chatContainer.innerHTML = '';
                addMessage("Connection failed. Please refresh the page to try again.", 'bot');
                disableForm();
            }
        }

        function restoreSession() {
            try {
                const savedHtml = sessionStorage.getItem('faq_bot_chat_html');
                const isOpen = sessionStorage.getItem('faq_bot_is_open') === 'true';
                
                if (savedHtml) {
                    chatContainer.innerHTML = savedHtml;
                    requestAnimationFrame(() => {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    });
                } else {
                    // If no saved chat, show welcome message
                    addMessage(welcomeMessage, 'bot');
                }
                
                if (isOpen) {
                    container.classList.add('open');
                    iconOpen.style.display = 'none';
                    iconClose.style.display = 'block';
                }
                
                enableForm();
            } catch (e) {
                console.log('Could not restore session, showing welcome message');
                addMessage(welcomeMessage, 'bot');
                enableForm();
            }
        }

        // Toggle button event listener
        toggleButton.addEventListener('click', function() {
            container.classList.toggle('open');
            const isOpen = container.classList.contains('open');
            iconOpen.style.display = isOpen ? 'none' : 'block';
            iconClose.style.display = isOpen ? 'block' : 'none';
            
            // Save open state
            try {
                sessionStorage.setItem('faq_bot_is_open', isOpen.toString());
            } catch (e) {
                console.log('Could not save open state');
            }
        });

        // Submit button click handler - ADD THIS
        submitBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const query = queryInput.value.trim();
            if (query && !queryInput.disabled) {
                submitQuery(query);
                queryInput.value = '';
                queryInput.style.height = 'auto';
            }
            return false;
        });

        // Form submit event listener - COMPLETELY REWRITTEN
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const query = queryInput.value.trim();
            if (query && !queryInput.disabled) {
                submitQuery(query);
                queryInput.value = '';
                queryInput.style.height = 'auto';
            }
            return false;
        });
        
        // Auto-grow textarea functionality
        queryInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        // Handle Enter key - COMPLETELY REWRITTEN
        queryInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                
                // Directly call the submit logic instead of dispatching events
                const query = queryInput.value.trim();
                if (query && !queryInput.disabled) {
                    submitQuery(query);
                    queryInput.value = '';
                    queryInput.style.height = 'auto';
                }
                return false;
            }
        });

        // Initialize the session
        initializeSession();
    }

    // Prevent multiple initializations by checking if already initialized
    if (window.faqBotInitialized) {
        console.log('FAQ Bot already initialized, skipping...');
        return;
    }
    window.faqBotInitialized = true;

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeChatbot);
    } else {
        initializeChatbot();
    }
})();