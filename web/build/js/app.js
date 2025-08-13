// BI Self-Service Chatbot - Main Application
class BIChatbot {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.conversationId = null;
        this.queryHistory = [];

        console.log("[BIChatbot] Initialized with API URL:", this.apiUrl);

        this.initializeEventListeners();
        this.loadQueryHistory();
    }

    initializeEventListeners() {
        console.log("[BIChatbot] Setting up event listeners...");

        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log("[Event] Chat form submitted");
            this.sendMessage();
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log("[Event] Enter pressed in message input");
                this.sendMessage();
            }
        });

        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.textContent.trim();
                console.log("[Event] Quick action clicked:", action);
                this.executeQuickAction(action);
            });
        });

        // Modal controls
        document.getElementById('schemaBtn').addEventListener('click', () => {
            console.log("[Event] Schema modal opened");
            this.showSchemaModal();
        });
        document.getElementById('helpBtn').addEventListener('click', () => {
            console.log("[Event] Help modal opened");
            this.showHelpModal();
        });
        document.getElementById('exportBtn').addEventListener('click', () => {
            console.log("[Event] Export results clicked");
            this.exportResults();
        });

        document.getElementById('closeSchemaModal').addEventListener('click', () => {
            console.log("[Event] Schema modal closed");
            this.hideSchemaModal();
        });
        document.getElementById('closeHelpModal').addEventListener('click', () => {
            console.log("[Event] Help modal closed");
            this.hideHelpModal();
        });
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        console.log("[sendMessage] User message:", message);

        if (!message) {
            console.warn("[sendMessage] Empty message, skipping send");
            return;
        }

        messageInput.value = '';
        this.addMessage(message, 'user');

        try {
            console.log("[sendMessage] Sending API request...");
            const response = await this.callAPI('/api/v1/chat/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            console.log("[sendMessage] API response received:", response);

            if (!response.error) {
                this.conversationId = response.conversation_id;
                console.log("[sendMessage] Updated conversationId:", this.conversationId);
                this.addMessage(response.message, 'bot', response);
                this.addToQueryHistory(message, response);
            } else {
                console.error("[sendMessage] API returned error:", response);
                this.addMessage('Sorry, I encountered an error processing your request.', 'bot');
            }

        } catch (error) {
            console.error("[sendMessage] Request failed:", error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    async callAPI(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        console.log("[callAPI] Fetching:", url, "with options:", options);

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            console.log("[callAPI] HTTP status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("[callAPI] Response JSON:", data);
            return data;

        } catch (error) {
            console.error("[callAPI] Failed:", error);
            throw error;
        }
    }

    addMessage(message, sender, data = null) {
        console.log(`[addMessage] Adding ${sender} message:`, message, data ? "(with data)" : "");
        // unchanged DOM rendering logic...
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble mb-4 ${sender === 'user' ? 'ml-auto bg-blue-600 text-white' : 'bg-gray-100'}`;
        
        const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        const iconColor = sender === 'user' ? 'text-white' : 'text-blue-600';
        
        messageDiv.innerHTML = `
            <div class="flex items-start">
                <i class="${icon} ${iconColor} mt-1 mr-3"></i>
                <div class="flex-1">
                    <p class="text-sm">${message}</p>
                    ${data && data.sql_query ? `
                        <details class="mt-2">
                            <summary class="text-xs text-gray-500 cursor-pointer">View SQL Query</summary>
                            <pre class="text-xs bg-gray-800 text-green-400 p-2 rounded mt-1 overflow-x-auto">${data.sql_query}</pre>
                        </details>
                    ` : ''}
                    ${data && data.results && data.results.data && data.results.data.length > 0 ? `
                        <div class="mt-3">
                            <div class="table-container">
                                <table class="result-table w-full border-collapse border border-gray-300">
                                    <thead>
                                        <tr>
                                            ${data.results.columns.map(col => `<th class="border border-gray-300 px-2 py-1 text-left bg-gray-100">${col}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.results.data.slice(0, 10).map(row => `
                                            <tr>
                                                ${data.results.columns.map(col => `<td class="border border-gray-300 px-2 py-1">${row[col] || ''}</td>`).join('')}
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                            ${data.results.data.length > 10 ? `
                                <p class="text-xs text-gray-500 mt-1">Showing first 10 of ${data.results.data.length} results</p>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    executeQuickAction(action) {
        console.log("[executeQuickAction] Action triggered:", action);
        const actionQueries = {
            'Top Projects': 'Show me the top 10 projects by leads',
            'User Leads': 'Show me user leads from the last 30 days',
            'Regional Data': 'Show me data by region for the last month',
            'Recent Activity': 'Show me recent activity from the last week'
        };

        const query = actionQueries[action];
        if (query) {
            console.log("[executeQuickAction] Mapped query:", query);
            document.getElementById('messageInput').value = query;
            this.sendMessage();
        } else {
            console.warn("[executeQuickAction] No query found for action:", action);
        }
    }

    addToQueryHistory(message, response) {
        console.log("[addToQueryHistory] Storing message in history:", message, response);
        const historyItem = {
            message: message,
            timestamp: new Date().toLocaleString(),
            sql: response.sql_query,
            results: response.results
        };

        this.queryHistory.unshift(historyItem);
        if (this.queryHistory.length > 10) {
            this.queryHistory = this.queryHistory.slice(0, 10);
        }

        this.saveQueryHistory();
        this.displayQueryHistory();
    }

    saveQueryHistory() {
        console.log("[saveQueryHistory] Saving to localStorage", this.queryHistory);
        localStorage.setItem('bi_chatbot_history', JSON.stringify(this.queryHistory));
    }

    loadQueryHistory() {
        console.log("[loadQueryHistory] Loading from localStorage...");
        const saved = localStorage.getItem('bi_chatbot_history');
        if (saved) {
            this.queryHistory = JSON.parse(saved);
            console.log("[loadQueryHistory] Loaded history:", this.queryHistory);
            this.displayQueryHistory();
        } else {
            console.log("[loadQueryHistory] No saved history found");
        }
    }

    displayQueryHistory() {
        console.log("[displayQueryHistory] Rendering query history...");
        const historyContainer = document.getElementById('queryHistory');
        historyContainer.innerHTML = '';

        this.queryHistory.forEach((item, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'p-2 border rounded hover:bg-gray-50 cursor-pointer';
            historyItem.innerHTML = `
                <div class="text-xs text-gray-500">${item.timestamp}</div>
                <div class="text-sm truncate">${item.message}</div>
            `;
            
            historyItem.addEventListener('click', () => {
                console.log("[HistoryClick] Selected query:", item);
                document.getElementById('messageInput').value = item.message;
            });
            
            historyContainer.appendChild(historyItem);
        });
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log("[DOM] Document ready, initializing BIChatbot");
    new BIChatbot();
});