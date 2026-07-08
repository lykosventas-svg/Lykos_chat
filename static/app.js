/**
 * RAG Chatbot - Frontend Application
 * ChromaDB + Huawei Cloud MaaS
 */

// ─── State ────────────────────────────────────────────────────────
let isLoading = false;

// ─── API Helpers ──────────────────────────────────────────────────
async function api(endpoint, options = {}) {
    const url = `/api${endpoint}`;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options
    };
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }
    const response = await fetch(url, config);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(error.detail || 'Error en la petición');
    }
    return response.json();
}

// ─── Chat Functions ───────────────────────────────────────────────
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || isLoading) return;

    // Add user message to UI
    addMessageToUI('user', message);
    input.value = '';
    autoResize(input);

    // Show typing indicator
    const typingId = showTypingIndicator();
    setLoading(true);

    try {
        const data = await api('/chat', {
            method: 'POST',
            body: { message }
        });

        removeTypingIndicator(typingId);
        addMessageToUI('assistant', data.response, data.sources);
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToUI('assistant', `❌ Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function addMessageToUI(role, content, sources = []) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Parse markdown-like formatting
    const formattedContent = formatMessage(content);
    contentDiv.innerHTML = `<p>${formattedContent}</p>`;

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.textContent = `📎 Fuentes: ${sources.join(', ')}`;
        contentDiv.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);

    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function formatMessage(text) {
    // Simple formatting: bold, code, line breaks
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function showTypingIndicator() {
    const messagesDiv = document.getElementById('messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(contentDiv);
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function setLoading(state) {
    isLoading = state;
    const btn = document.getElementById('btnSend');
    btn.disabled = state;
}

// ─── Config Modal Functions ───────────────────────────────────────
function openConfigModal() {
    const modal = document.getElementById('configModal');
    modal.style.display = 'flex';

    // Load current config
    loadConfig();
}

function closeConfigModal() {
    const modal = document.getElementById('configModal');
    modal.style.display = 'none';
    const status = document.getElementById('configStatus');
    status.style.display = 'none';
}

async function loadConfig() {
    try {
        const data = await api('/config');
        document.getElementById('maasUrl').value = data.url || '';
        document.getElementById('maasModel').value = data.model || '';
        // Show masked API key if configured
        if (data.api_key && data.api_key !== '' && data.api_key !== '...') {
            document.getElementById('maasApiKey').value = data.api_key;
        } else {
            document.getElementById('maasApiKey').value = '';
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function saveConfig() {
    const url = document.getElementById('maasUrl').value.trim();
    const apiKey = document.getElementById('maasApiKey').value.trim();
    const model = document.getElementById('maasModel').value.trim();

    if (!url || !apiKey || !model) {
        showConfigStatus('error', 'Todos los campos son requeridos.');
        return;
    }

    try {
        await api('/config', {
            method: 'POST',
            body: { url, api_key: apiKey, model }
        });
        showConfigStatus('success', '✅ Configuración guardada exitosamente.');
        // Keep the API key value in the field (don't clear it)
    } catch (error) {
        showConfigStatus('error', `❌ Error al guardar: ${error.message}`);
    }
}

async function testConnection() {
    const url = document.getElementById('maasUrl').value.trim();
    const apiKey = document.getElementById('maasApiKey').value.trim();
    const model = document.getElementById('maasModel').value.trim();

    if (!url || !apiKey || !model) {
        showConfigStatus('error', 'Configure todos los campos antes de probar.');
        return;
    }

    // Save first, then test
    try {
        await api('/config', {
            method: 'POST',
            body: { url, api_key: apiKey, model }
        });

        showConfigStatus('success', '⏳ Probando conexión...');

        const result = await api('/config/test', { method: 'POST' });

        if (result.success) {
            showConfigStatus('success', `✅ ${result.message}`);
        } else {
            showConfigStatus('error', `❌ ${result.message}`);
        }
    } catch (error) {
        showConfigStatus('error', `❌ Error: ${error.message}`);
    }
}

function showConfigStatus(type, message) {
    const status = document.getElementById('configStatus');
    status.className = `config-status ${type}`;
    status.textContent = message;
    status.style.display = 'block';
}

// ─── Utility Functions ────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Initialize ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Focus on input
    document.getElementById('messageInput').focus();

    // Load config status
    api('/config').then(data => {
        if (!data.is_configured) {
            const btn = document.getElementById('btnConfig');
            btn.style.background = 'var(--primary-light)';
            btn.title = '⚠️ MaaS no configurado - Haga clic para configurar';
        }
    }).catch(() => {});
});
