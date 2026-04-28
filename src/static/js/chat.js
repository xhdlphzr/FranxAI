const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
window.chatMessages = chatMessages;

let currentAbortController = null;
let isGenerating = false;
let currentUserMessage = '';
let currentPartialText = '';
let currentAssistantMsgDiv = null;
let currentKnowledgeItems = [];
let currentKnowledgeBlock = null;

function escapeHtml(str) {
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function sanitizeForMarkdown(str) {
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#39;');
}

function wrapTables(container) {
    container.querySelectorAll('table').forEach(table => {
        if (table.parentElement.classList.contains('table-scroll-wrapper')) return;
        const wrapper = document.createElement('div');
        wrapper.className = 'table-scroll-wrapper';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

function renderStreamingMarkdown(msgDiv, rawText) {
    msgDiv._rawText = rawText;
    let contentContainer = msgDiv.querySelector('.assistant-content:last-of-type');
    if (!contentContainer) {
        contentContainer = document.createElement('div');
        contentContainer.className = 'assistant-content';
        msgDiv.appendChild(contentContainer);
    }
    try {
        const html = marked.parse(rawText);
        contentContainer.innerHTML = html;
    } catch(e) {
        contentContainer.textContent = rawText;
    }
    wrapTables(contentContainer);
    const existingDot = contentContainer.querySelector('.typing-dot');
    if (existingDot) existingDot.remove();
    const dot = document.createElement('span');
    dot.className = 'typing-dot';
    const lastChild = contentContainer.lastElementChild;
    if (lastChild) {
        lastChild.appendChild(dot);
    } else {
        contentContainer.appendChild(dot);
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateKnowledgeBlock(msgDiv, knowledgeItems) {
    msgDiv._knowledgeItems = knowledgeItems;
    if (!knowledgeItems.length) {
        if (currentKnowledgeBlock) currentKnowledgeBlock.remove();
        currentKnowledgeBlock = null;
        return;
    }
    // If currentKnowledgeBlock belongs to a different message, reset it
    if (currentKnowledgeBlock && currentKnowledgeBlock.parentElement !== msgDiv) {
        currentKnowledgeBlock = null;
    }
    if (!currentKnowledgeBlock) {
        currentKnowledgeBlock = document.createElement('div');
        currentKnowledgeBlock.className = 'assistant-block knowledge-block';
        const header = document.createElement('div');
        header.className = 'block-header';
        const icon = document.createElement('span');
        icon.className = 'toggle-icon';
        icon.textContent = '▶';
        header.appendChild(icon);
        header.appendChild(document.createTextNode(t('knowledge.title') + ' (' + knowledgeItems.length + ')'));
        const contentDiv = document.createElement('div');
        contentDiv.className = 'block-content';
        const inner = document.createElement('div');
        inner.style.display = 'flex';
        inner.style.flexDirection = 'column';
        inner.style.gap = '0.75rem';
        contentDiv.appendChild(inner);
        currentKnowledgeBlock.appendChild(header);
        currentKnowledgeBlock.appendChild(contentDiv);
        header.addEventListener('click', () => {
            const isOpen = contentDiv.classList.contains('show');
            if (isOpen) {
                contentDiv.classList.remove('show');
                icon.textContent = '▶';
            } else {
                contentDiv.classList.add('show');
                icon.textContent = '▼';
            }
        });
        msgDiv.insertBefore(currentKnowledgeBlock, msgDiv.firstChild);
    }
    const inner = currentKnowledgeBlock.querySelector('.block-content > div');
    inner.innerHTML = '';
    knowledgeItems.forEach((text) => {
        let summary = '';
        const titleMatch = text.match(/^###\s+(.+)$/m);
        if (titleMatch) summary = titleMatch[1];
        else summary = text.substring(0, 50) + (text.length > 50 ? '…' : '');
        const itemDiv = document.createElement('div');
        itemDiv.className = 'knowledge-item';
        const sumDiv = document.createElement('div');
        sumDiv.className = 'knowledge-summary';
        sumDiv.innerHTML = `📄 ${escapeHtml(summary)} <span style="font-size:0.7rem;">▼</span>`;
        const fullDiv = document.createElement('div');
        fullDiv.className = 'knowledge-full';
        try {
            const html = marked.parse(text);
            fullDiv.innerHTML = html;
            wrapTables(fullDiv);
            if (window.renderMathInElement) {
                window.renderMathInElement(fullDiv, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ]
                });
            }
        } catch(e) {
            fullDiv.textContent = text;
        }
        sumDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            fullDiv.classList.toggle('show');
            const iconSpan = sumDiv.querySelector('span');
            if (fullDiv.classList.contains('show')) {
                iconSpan.textContent = '▼';
            } else {
                iconSpan.textContent = '▶';
            }
        });
        itemDiv.appendChild(sumDiv);
        itemDiv.appendChild(fullDiv);
        inner.appendChild(itemDiv);
    });
    const header = currentKnowledgeBlock.querySelector('.block-header');
    header.lastChild.textContent = t('knowledge.title') + ' (' + knowledgeItems.length + ')';
}

function addToolCallBlockStructured(msgDiv, callId, toolName, argumentsObj, resultText) {
    let params = argumentsObj;
    if (params && typeof params === 'object') {
        if ('arguments' in params && params.arguments && typeof params.arguments === 'object') {
            params = params.arguments;
        }
    }
    if (!params || typeof params !== 'object') params = {};
    if (typeof toolName !== 'string') {
        toolName = String(toolName);
    }
    const blockDiv = document.createElement('div');
    blockDiv.className = 'assistant-block tool-call-block';
    blockDiv.dataset.callId = callId;
    const header = document.createElement('div');
    header.className = 'block-header';
    header.dataset.toolName = toolName;
    const icon = document.createElement('span');
    icon.className = 'toggle-icon';
    icon.textContent = '▶';
    header.appendChild(icon);
    header.appendChild(document.createTextNode(t('tool.using', { name: toolName })));
    const paramsDiv = document.createElement('div');
    paramsDiv.className = 'tool-params';
    if (Object.keys(params).length > 0) {
        for (const [key, value] of Object.entries(params)) {
            const paramLine = document.createElement('div');
            paramLine.className = 'tool-param';
            let valStr = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
            paramLine.textContent = `${key}: ${valStr}`;
            paramsDiv.appendChild(paramLine);
        }
    } else {
        const fallback = document.createElement('div');
        fallback.className = 'tool-param';
        fallback.textContent = t('tool.no_params');
        paramsDiv.appendChild(fallback);
    }
    const resultLabel = document.createElement('div');
    resultLabel.className = 'tool-param';
    resultLabel.style.fontWeight = 'bold';
    resultLabel.style.marginTop = '0.5rem';
    resultLabel.textContent = t('tool.result');
    paramsDiv.appendChild(resultLabel);
    const resultContent = document.createElement('div');
    resultContent.className = 'tool-param';
    resultContent.style.padding = '0.25rem 0';
    if (resultText && resultText !== 'null' && resultText !== '') {
        resultContent.textContent = resultText;
        header.lastChild.textContent = t('tool.used', { name: toolName });
    } else {
        resultContent.textContent = t('tool.executing');
        resultContent.classList.add('tool-result-pending');
    }
    paramsDiv.appendChild(resultContent);
    blockDiv.appendChild(header);
    blockDiv.appendChild(paramsDiv);
    header.addEventListener('click', () => {
        const isOpen = paramsDiv.classList.contains('show');
        if (isOpen) {
            paramsDiv.classList.remove('show');
            icon.textContent = '▶';
        } else {
            paramsDiv.classList.add('show');
            icon.textContent = '▼';
        }
    });
    msgDiv.appendChild(blockDiv);
    return blockDiv;
}

function updateToolCallResult(msgDiv, callId, resultText) {
    const blockDiv = msgDiv.querySelector(`.tool-call-block[data-call-id="${callId}"]`);
    if (!blockDiv) return;
    const header = blockDiv.querySelector('.block-header');
    if (header) {
        const toolName = header.dataset.toolName;
        header.lastChild.textContent = t('tool.used', { name: toolName });
    }
    const pendingResult = blockDiv.querySelector('.tool-result-pending');
    if (pendingResult) {
        pendingResult.textContent = resultText;
        pendingResult.classList.remove('tool-result-pending');
    } else {
        const resultContent = blockDiv.querySelectorAll('.tool-param')[1];
        if (resultContent) resultContent.textContent = resultText;
    }
}

function addConfirmationBlock(msgDiv, confirmId, toolName, argumentsObj) {
    let params = argumentsObj;
    if (params && typeof params === 'object') {
        if ('arguments' in params && params.arguments && typeof params.arguments === 'object') {
            params = params.arguments;
        }
        if ('tool_name' in params && 'arguments' in params) {
            params = params.arguments;
        }
    }
    if (!params || typeof params !== 'object') params = {};
    const blockDiv = document.createElement('div');
    blockDiv.className = 'confirm-block';
    blockDiv.dataset.confirmId = confirmId;
    const header = document.createElement('div');
    header.className = 'confirm-header';
    header.textContent = t('tool.confirm', { name: toolName });
    blockDiv.appendChild(header);
    const paramsDiv = document.createElement('div');
    paramsDiv.className = 'confirm-params';
    let displayParams = '';
    if (toolName === 'write') {
        const path = params.path || '';
        const mode = params.mode || 'overwrite';
        const content = params.content || '';
        const startLine = params.start_line || 0;
        const endLine = params.end_line || 0;
        displayParams = t('tool.confirm_write_template', {path, mode, content, startLine, endLine});
    } else if (toolName === 'command') {
        const command = params.command || '';
        displayParams = t('tool.confirm_command_template', { command });
    } else {
        displayParams = JSON.stringify(params, null, 2);
    }
    try {
        paramsDiv.innerHTML = marked.parse(displayParams);
    } catch(e) {
        paramsDiv.textContent = displayParams;
    }
    blockDiv.appendChild(paramsDiv);
    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'confirm-buttons';
    const approveBtn = document.createElement('button');
    approveBtn.className = 'confirm-approve';
    approveBtn.textContent = t('tool.approve');
    const rejectBtn = document.createElement('button');
    rejectBtn.className = 'confirm-reject';
    rejectBtn.textContent = t('tool.reject');
    buttonsDiv.appendChild(approveBtn);
    buttonsDiv.appendChild(rejectBtn);
    blockDiv.appendChild(buttonsDiv);
    approveBtn.addEventListener('click', async () => {
        try {
            await fetchWithAuth('/api/confirm_tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirm_id: confirmId, approved: true })
            });
            blockDiv.remove();
        } catch(err) {
            console.error('Failed to send approval', err);
        }
    });
    rejectBtn.addEventListener('click', async () => {
        try {
            await fetchWithAuth('/api/confirm_tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirm_id: confirmId, approved: false })
            });
            blockDiv.innerHTML = `<div class="confirm-header">${t('tool.rejected')}</div>`;
        } catch(err) {
            console.error('Failed to send rejection', err);
        }
    });
    msgDiv.appendChild(blockDiv);
    blockDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return blockDiv;
}

function saveMessagesToLocalStorage() {
    const messages = [];
    document.querySelectorAll('.message').forEach(msgDiv => {
        const role = msgDiv.classList.contains('user') ? 'user' : 'assistant';
        if (!msgDiv.classList.contains('temp')) {
            const msg = { role };
            if (role === 'assistant') {
                if (msgDiv._rawText) {
                    msg.content = msgDiv._rawText;
                } else if (msgDiv._textNode) {
                    msg.content = msgDiv._textNode.textContent;
                } else {
                    msg.content = msgDiv.textContent;
                }
                if (msgDiv._knowledgeItems && msgDiv._knowledgeItems.length > 0) {
                    msg.knowledge = msgDiv._knowledgeItems;
                }
            } else {
                msg.content = msgDiv.textContent;
            }
            messages.push(msg);
        }
    });
    localStorage.setItem('chatMessages', JSON.stringify(messages));
}

function loadMessagesFromLocalStorage() {
    const stored = localStorage.getItem('chatMessages');
    if (stored) {
        const messages = JSON.parse(stored);
        messages.forEach(msg => {
            const msgDiv = addMessage(msg.role, msg.content, false, '', true);
            if (msg.role === 'assistant' && msg.knowledge && msg.knowledge.length > 0) {
                msgDiv._knowledgeItems = msg.knowledge;
                updateKnowledgeBlock(msgDiv, msg.knowledge);
            }
        });
    }
}

function addMessage(role, content, temporary = false, extraClass = '', parseMarkdown = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role} ${extraClass}`;
    if (temporary) msgDiv.classList.add('temp');
    if (role === 'assistant' && temporary) {
        msgDiv._rawText = '';
        const contentContainer = document.createElement('div');
        contentContainer.className = 'assistant-content';
        msgDiv.appendChild(contentContainer);
        renderStreamingMarkdown(msgDiv, content);
    } else if (parseMarkdown && !temporary) {
        if (role === 'user') {
            const safeContent = sanitizeForMarkdown(content);
            const html = marked.parse(safeContent);
            msgDiv.innerHTML = html;
        } else {
            const html = marked.parse(content);
            msgDiv.innerHTML = html;
        }
        wrapTables(msgDiv);
        if (window.renderMathInElement) {
            window.renderMathInElement(msgDiv, { delimiters: [{left: '$$', right: '$$', display: true},{left: '$', right: '$', display: false}] });
        }
    } else {
        msgDiv.textContent = content;
    }
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    if (!temporary) saveMessagesToLocalStorage();
    return msgDiv;
}

function updateMessage(msgDiv, content) {
    msgDiv._rawText = content;
    const contentContainer = msgDiv.querySelector('.assistant-content');
    if (contentContainer) {
        try {
            const html = marked.parse(content);
            contentContainer.innerHTML = html;
            wrapTables(contentContainer);
            let dot = contentContainer.querySelector('.typing-dot');
            if (!dot) {
                dot = document.createElement('span');
                dot.className = 'typing-dot';
            } else {
                dot.remove();
            }
            const lastChild = contentContainer.lastElementChild;
            if (lastChild) lastChild.appendChild(dot);
            else contentContainer.appendChild(dot);
        } catch(e) {
            contentContainer.textContent = content;
        }
    } else {
        msgDiv.textContent = content;
    }
    msgDiv.classList.remove('temp');
    chatMessages.scrollTop = chatMessages.scrollHeight;
    saveMessagesToLocalStorage();
}

function removeTypingDot(msgDiv) {
    const lastContainer = msgDiv.querySelector('.assistant-content:last-of-type');
    if (lastContainer) {
        const dot = lastContainer.querySelector('.typing-dot');
        if (dot) dot.remove();
    }
}

function setSendButtonToStop() {
    sendBtn.textContent = t('chat.stop');
    sendBtn.removeEventListener('click', sendMessage);
    sendBtn.addEventListener('click', stopGeneration);
}

function setSendButtonToSend() {
    sendBtn.textContent = t('chat.send');
    sendBtn.removeEventListener('click', stopGeneration);
    sendBtn.addEventListener('click', sendMessage);
}

function stopGeneration() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    setSendButtonToSend();
    isGenerating = false;
    if (currentPartialText && currentUserMessage) {
        fetchWithAuth('/api/save_partial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_message: currentUserMessage,
                partial_response: currentPartialText
            })
        }).catch(e => console.error('Failed to save partial response', e));
        if (currentAssistantMsgDiv) {
            const stopText = currentPartialText + '\n\n' + t('chat.stopped');
            currentAssistantMsgDiv._rawText = stopText;
            const contentContainer = currentAssistantMsgDiv.querySelector('.assistant-content');
            if (contentContainer) {
                try {
                    contentContainer.innerHTML = marked.parse(stopText);
                    wrapTables(contentContainer);
                } catch(e) {
                    contentContainer.textContent = stopText;
                }
            }
            removeTypingDot(currentAssistantMsgDiv);
            currentAssistantMsgDiv.classList.remove('temp');
            saveMessagesToLocalStorage();
        } else {
            addMessage('assistant', currentPartialText + '\n\n' + t('chat.stopped'));
        }
    } else {
        addMessage('assistant', t('chat.stopped'));
    }
    currentUserMessage = '';
    currentPartialText = '';
    currentAssistantMsgDiv = null;
    currentKnowledgeItems = [];
    currentKnowledgeBlock = null;
}

async function sendMessage() {
    currentKnowledgeItems = [];
    if (currentKnowledgeBlock) {
        currentKnowledgeBlock.remove();
        currentKnowledgeBlock = null;
    }
    const message = messageInput.value.trim();
    if (!message || isGenerating) return;
    isGenerating = true;
    messageInput.value = '';
    currentUserMessage = message;
    currentPartialText = '';
    currentAbortController = new AbortController();
    const signal = currentAbortController.signal;
    setSendButtonToStop();
    addMessage('user', message, false, '', true);
    const assistantMsgDiv = addMessage('assistant', t('chat.thinking'), true, '', false);
    currentAssistantMsgDiv = assistantMsgDiv;
    let fullText = '';
    let receivedHtml = false;
    try {
        const resp = await fetchWithAuth('/chat', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }), signal
        });
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.type === 'content') {
                            fullText += data.text;
                            currentPartialText = fullText;
                            renderStreamingMarkdown(assistantMsgDiv, fullText);
                            assistantMsgDiv.classList.remove('temp');
                        } else if (data.type === 'tool_call') {
                            removeTypingDot(assistantMsgDiv);
                            addToolCallBlockStructured(assistantMsgDiv, data.call_id, data.tool_name, data.arguments, data.result);
                            const newContainer = document.createElement('div');
                            newContainer.className = 'assistant-content';
                            assistantMsgDiv.appendChild(newContainer);
                            fullText = '';
                        } else if (data.type === 'tool_result') {
                            updateToolCallResult(assistantMsgDiv, data.call_id, data.result);
                        } else if (data.type === 'html') {
                            receivedHtml = true;
                            removeTypingDot(assistantMsgDiv);
                            assistantMsgDiv.classList.remove('temp');
                            if (window.renderMathInElement) {
                                window.renderMathInElement(assistantMsgDiv, {
                                    delimiters: [
                                        {left: '$$', right: '$$', display: true},
                                        {left: '$', right: '$', display: false}
                                    ]
                                });
                            }
                            saveMessagesToLocalStorage();
                        } else if (data.type === 'knowledge') {
                            currentKnowledgeItems.push(data.text);
                            updateKnowledgeBlock(assistantMsgDiv, currentKnowledgeItems);
                        } else if (data.type === 'confirmation_required') {
                            addConfirmationBlock(assistantMsgDiv, data.confirm_id, data.tool_name, data.arguments);
                        } else if (data.type === 'error') {
                            updateMessage(assistantMsgDiv, t('chat.error', { message: data.text }));
                            removeTypingDot(assistantMsgDiv);
                        }
                    } catch(e) { console.error(e); }
                }
            }
        }
        if (assistantMsgDiv.querySelector('.typing-dot')) {
            removeTypingDot(assistantMsgDiv);
            saveMessagesToLocalStorage();
        }
    } catch(err) {
        if (err.name !== 'AbortError') {
            updateMessage(assistantMsgDiv, t('chat.network_error', { message: err.message }));
            removeTypingDot(assistantMsgDiv);
        }
    } finally {
        setSendButtonToSend();
        isGenerating = false;
        currentAbortController = null;
        currentUserMessage = '';
        currentPartialText = '';
        currentAssistantMsgDiv = null;
        currentKnowledgeItems = [];
        currentKnowledgeBlock = null;
    }
}

messageInput.addEventListener('keydown', (e) => { if (e.ctrlKey && e.key === 'Enter') sendMessage(); });