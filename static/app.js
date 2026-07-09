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

    // Show typing indicator while waiting for first token
    const typingId = showTypingIndicator();
    setLoading(true);

    try {
        await streamChat(message, typingId);
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToUI('assistant', `❌ Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

/**
 * Stream a chat response using Server-Sent Events.
 * Tokens are displayed incrementally as they arrive from the LLM,
 * which dramatically improves perceived response time.
 */
async function streamChat(message, typingId) {
    const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(error.detail || 'Error en la petición');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let assistantDiv = null;
    let contentDiv = null;
    let fullText = '';
    let sources = [];

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // Decode the chunk and process each SSE event
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;

                let event;
                try {
                    event = JSON.parse(line.slice(6));
                } catch {
                    continue; // skip malformed lines
                }

                switch (event.type) {
                    case 'sources':
                        sources = event.data || [];
                        break;

                    case 'token':
                        // Remove typing indicator on first token
                        if (!assistantDiv) {
                            removeTypingIndicator(typingId);
                            ({ assistantDiv, contentDiv } = createAssistantMessage());
                        }
                        fullText += event.data;
                        // Render formatted content
                        contentDiv.innerHTML = `<p>${formatMessage(fullText)}</p>`;
                        // Scroll to bottom
                        const messagesDiv = document.getElementById('messages');
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        break;

                    case 'done':
                        // Ensure the message is finalized
                        if (!assistantDiv) {
                            removeTypingIndicator(typingId);
                            ({ assistantDiv, contentDiv } = createAssistantMessage());
                            contentDiv.innerHTML = `<p>${formatMessage(fullText)}</p>`;
                        }
                        // Add sources if available
                        if (sources.length > 0) {
                            const sourcesDiv = document.createElement('div');
                            sourcesDiv.className = 'message-sources';
                            sourcesDiv.textContent = `📎 Fuentes: ${sources.join(', ')}`;
                            contentDiv.appendChild(sourcesDiv);
                        }
                        break;

                    case 'error':
                        if (!assistantDiv) {
                            removeTypingIndicator(typingId);
                        }
                        addMessageToUI('assistant', `❌ Error: ${event.data}`);
                        break;
                }
            }
        }
    } catch (error) {
        if (!assistantDiv) {
            removeTypingIndicator(typingId);
        }
        throw error;
    }
}

/**
 * Create an empty assistant message bubble in the DOM.
 * Returns references to the outer div and the content div so
 * the caller can update the content incrementally.
 */
function createAssistantMessage() {
    const messagesDiv = document.getElementById('messages');
    const assistantDiv = document.createElement('div');
    assistantDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    assistantDiv.appendChild(avatar);
    assistantDiv.appendChild(contentDiv);
    messagesDiv.appendChild(assistantDiv);

    return { assistantDiv, contentDiv };
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
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');

    // Convert URLs to clickable links (except mailto: and wa.me which are handled separately)
    formatted = formatted.replace(
        /(?!<a\s)(?:^|[^"=])\b(https?:\/\/(?!wa\.me)[^\s<]+)/g,
        (match, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
    );

    // Convert email addresses to clickable mailto: links
    formatted = formatted.replace(
        /\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b/g,
        (match, email) => `<a href="mailto:${email}" target="_blank" rel="noopener noreferrer">${email}</a>`
    );

    // Convert WhatsApp phone numbers to clickable wa.me links
    // Matches patterns like +5215534624630, +52 15534624630, +52 1 55 3462 4630, etc.
    formatted = formatted.replace(
        /\+52\s*1?\s*[\d\s]{10,}/g,
        (match) => {
            // Remove all spaces and the + sign to get the raw number
            const rawNumber = match.replace(/[\s+]/g, '');
            return `<a href="https://wa.me/${rawNumber}" target="_blank" rel="noopener noreferrer">${match}</a>`;
        }
    );

    return formatted;
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

// ─── Utility Functions ────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Initialize ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Show initial greeting from Lykos
    const greeting = "¡Hola! Soy parte del equipo de Lykos. ¿Buscas proteger tu empresa contra ciberataques o tienes alguna consulta técnica? Dime en qué te puedo ayudar.";
    addMessageToUI('assistant', greeting);

    // Focus on input
    document.getElementById('messageInput').focus();
});
