class CampusChatbot {
    constructor() {
        this.apiBase = 'http://localhost:8000/api';
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkConnection();
    }
    
    initializeElements() {
        this.chatMessages = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.connectionStatus = document.getElementById('connection-status');
        this.languageIndicator = document.getElementById('language-indicator');
        this.adminPanel = document.getElementById('admin-panel');
        this.adminToggleBtn = document.getElementById('admin-toggle-btn');
        this.fileInput = document.getElementById('file-input');
        this.docTitle = document.getElementById('doc-title');
        this.uploadBtn = document.getElementById('upload-btn');
        this.initKbBtn = document.getElementById('init-kb-btn');
        this.clearLogsBtn = document.getElementById('clear-logs-btn');
        this.systemStatus = document.getElementById('system-status');
    }
    
    attachEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Admin panel
        this.adminToggleBtn.addEventListener('click', () => this.toggleAdminPanel());
        this.uploadBtn.addEventListener('click', () => this.uploadDocument());
        this.initKbBtn.addEventListener('click', () => this.initializeKnowledgeBase());
        this.clearLogsBtn.addEventListener('click', () => this.clearLogs());
        
        // Auto-resize input
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
        });
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBase}/health/`);
            const data = await response.json();
            
            this.isConnected = response.ok;
            this.updateConnectionStatus(data);
            
            if (this.isConnected) {
                this.connectionStatus.innerHTML = '🟢 Connected';
                this.connectionStatus.classList.add('connected');
                this.connectionStatus.classList.remove('disconnected');
            } else {
                throw new Error('Health check failed');
            }
            
        } catch (error) {
            console.error('Connection check failed:', error);
            this.isConnected = false;
            this.connectionStatus.innerHTML = '🔴 Disconnected';
            this.connectionStatus.classList.add('disconnected');
            this.connectionStatus.classList.remove('connected');
        }
    }
    
    updateConnectionStatus(healthData) {
        if (this.systemStatus) {
            this.systemStatus.innerHTML = `
                <strong>System Status:</strong><br>
                Ollama: ${healthData.ollama_connected ? '✅ Connected' : '❌ Disconnected'}<br>
                Model: ${healthData.model}<br>
                Documents: ${healthData.documents_count}<br>
                Chat Logs: ${healthData.chat_logs_count}
            `;
        }
    }
    
    async sendMessage() {
        const query = this.userInput.value.trim();
        if (!query || !this.isConnected) return;
        
        // Add user message to chat
        this.addMessage(query, 'user');
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        
        // Show loading state
        this.setLoading(true);
        
        try {
            const response = await fetch(`${this.apiBase}/ask/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add bot response to chat
            this.addMessage(data.response, 'bot', data.language, data.confidence);
            this.updateLanguageIndicator(data.language);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(
                'Sorry, I encountered an error while processing your request. Please try again.',
                'bot',
                'en',
                0
            );
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(content, sender, language = 'en', confidence = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        const textP = document.createElement('p');
        textP.textContent = content;
        messageContent.appendChild(textP);
        
        if (sender === 'bot' && confidence !== null) {
            const metaSpan = document.createElement('small');
            metaSpan.textContent = `Language: ${language.toUpperCase()} | Confidence: ${(confidence * 100).toFixed(1)}%`;
            messageContent.appendChild(metaSpan);
        }
        
        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    setLoading(isLoading) {
        const sendSpan = this.sendBtn.querySelector('span:first-child');
        const loadingSpan = this.sendBtn.querySelector('.loading');
        
        if (isLoading) {
            sendSpan.classList.add('hidden');
            loadingSpan.classList.remove('hidden');
            this.sendBtn.disabled = true;
        } else {
            sendSpan.classList.remove('hidden');
            loadingSpan.classList.add('hidden');
            this.sendBtn.disabled = false;
        }
    }
    
    updateLanguageIndicator(language) {
        const languageNames = {
            'en': 'English',
            'hi': 'Hindi', 
            'hinglish': 'Hinglish'
        };
        this.languageIndicator.textContent = languageNames[language] || language;
    }
    
    toggleAdminPanel() {
        this.adminPanel.classList.toggle('show');
        if (this.adminPanel.classList.contains('show')) {
            this.checkConnection(); // Update system status
        }
    }
    
    async uploadDocument() {
        const file = this.fileInput.files[0];
        const title = this.docTitle.value.trim();
        
        if (!file || !title) {
            alert('Please select a file and enter a title.');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', title);
        
        try {
            const response = await fetch(`${this.apiBase}/upload-docs/`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`Document uploaded successfully! Created ${data.chunks_created} chunks.`);
                this.fileInput.value = '';
                this.docTitle.value = '';
                this.checkConnection(); // Update status
            } else {
                alert(`Error: ${data.error || 'Upload failed'}`);
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            alert('Error uploading document. Please try again.');
        }
    }
    
    async initializeKnowledgeBase() {
        if (!confirm('This will process all documents in the documents directory. Continue?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/initialize-kb/`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(`Knowledge base initialized! ${data.documents_added} documents processed.`);
                this.checkConnection(); // Update status
            } else {
                alert(`Error: ${data.error || 'Initialization failed'}`);
            }
            
        } catch (error) {
            console.error('Initialization error:', error);
            alert('Error initializing knowledge base. Please try again.');
        }
    }
    
    async clearLogs() {
        if (!confirm('This will clear all chat logs. Continue?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/delete-logs/`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(data.message);
                this.checkConnection(); // Update status
            } else {
                alert('Error clearing logs.');
            }
            
        } catch (error) {
            console.error('Clear logs error:', error);
            alert('Error clearing logs. Please try again.');
        }
    }
}

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    new CampusChatbot();
});