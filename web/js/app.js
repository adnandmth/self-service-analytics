 // BI Self-Service Chatbot - Main Application
class BIChatbot {
    constructor() {
        this.apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        this.conversationId = null;
        this.queryHistory = [];
        
        this.initializeEventListeners();
        this.loadQueryHistory();
    }

    initializeEventListeners() {
        // Chat form submission
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.textContent.trim();
                this.executeQuickAction(action);
            });
        });

        // Modal controls
        document.getElementById('schemaBtn').addEventListener('click', () => this.showSchemaModal());
        document.getElementById('helpBtn').addEventListener('click', () => this.showHelpModal());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportResults());

        document.getElementById('closeSchemaModal').addEventListener('click', () => this.hideSchemaModal());
        document.getElementById('closeHelpModal').addEventListener('click', () => this.hideHelpModal());

        // Close modals on outside click
        document.getElementById('schemaModal').addEventListener('click', (e) => {
            if (e.target.id === 'schemaModal') this.hideSchemaModal();
        });
        document.getElementById('helpModal').addEventListener('click', (e) => {
            if (e.target.id === 'helpModal') this.hideHelpModal();
        });
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Clear input
        messageInput.value = '';

        // Add user message to chat
        this.addMessage(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await this.callAPI('/api/v1/chat/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            // Hide typing indicator
            this.hideTypingIndicator();

            if (response.success) {
                this.conversationId = response.conversation_id;
                this.addMessage(response.message, 'bot', response);
                this.addToQueryHistory(message, response);
            } else {
                this.addMessage('Sorry, I encountered an error processing your request.', 'bot');
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    addMessage(message, sender, data = null) {
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

    showTypingIndicator() {
        document.getElementById('typingIndicator').classList.add('show');
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').classList.remove('show');
    }

    async callAPI(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    async showSchemaModal() {
        try {
            const response = await this.callAPI('/api/v1/chat/schema');
            if (response.success) {
                this.displaySchema(response.schemas);
                document.getElementById('schemaModal').classList.remove('hidden');
            }
        } catch (error) {
            console.error('Failed to load schema:', error);
            alert('Failed to load schema information');
        }
    }

    hideSchemaModal() {
        document.getElementById('schemaModal').classList.add('hidden');
    }

    showHelpModal() {
        document.getElementById('helpModal').classList.remove('hidden');
    }

    hideHelpModal() {
        document.getElementById('helpModal').classList.add('hidden');
    }

    displaySchema(schemas) {
        const schemaContent = document.getElementById('schemaContent');
        let html = '';

        for (const [schemaName, schemaData] of Object.entries(schemas)) {
            html += `
                <div class="mb-6">
                    <h4 class="font-medium text-gray-900 mb-2">${schemaName} Schema</h4>
                    <p class="text-sm text-gray-600 mb-3">${schemaData.description}</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            `;

            for (const [tableName, tableData] of Object.entries(schemaData.tables)) {
                html += `
                    <div class="border rounded p-3">
                        <h5 class="font-medium text-sm mb-1">${tableName}</h5>
                        <p class="text-xs text-gray-600 mb-2">${tableData.description}</p>
                        <div class="text-xs text-gray-500">
                            <strong>Columns:</strong> ${Object.keys(tableData.columns).join(', ')}
                        </div>
                    </div>
                `;
            }

            html += '</div></div>';
        }

        schemaContent.innerHTML = html;
    }

    executeQuickAction(action) {
        const actionQueries = {
            'Top Projects': 'Show me the top 10 projects by leads',
            'User Leads': 'Show me user leads from the last 30 days',
            'Regional Data': 'Show me data by region for the last month',
            'Recent Activity': 'Show me recent activity from the last week'
        };

        const query = actionQueries[action];
        if (query) {
            document.getElementById('messageInput').value = query;
            this.sendMessage();
        }
    }

    addToQueryHistory(message, response) {
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
        localStorage.setItem('bi_chatbot_history', JSON.stringify(this.queryHistory));
    }

    loadQueryHistory() {
        const saved = localStorage.getItem('bi_chatbot_history');
        if (saved) {
            this.queryHistory = JSON.parse(saved);
            this.displayQueryHistory();
        }
    }

    displayQueryHistory() {
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
                document.getElementById('messageInput').value = item.message;
            });
            
            historyContainer.appendChild(historyItem);
        });
    }

    exportResults() {
        // Implementation for exporting results
        alert('Export functionality will be implemented soon');
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new BIChatbot();
});