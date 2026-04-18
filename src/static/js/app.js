const taskMessages = {};
const eventSource = new EventSource('/events');
eventSource.addEventListener('task_start', (e) => {
    const data = JSON.parse(e.data);
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant task-message';
    msgDiv.id = `task-${data.task_id}`;
    msgDiv.innerHTML = `<div>${escapeHtml(data.message)}</div><div class="task-status">${t('task.executing')}</div><button class="stop-task-btn" data-task-id="${data.task_id}">${t('task.stop')}</button>`;
    window.chatMessages.appendChild(msgDiv);
    window.chatMessages.scrollTop = window.chatMessages.scrollHeight;
    taskMessages[data.task_id] = msgDiv;
    msgDiv.querySelector('.stop-task-btn').onclick = () => stopTask(data.task_id);
});
eventSource.addEventListener('task_chunk', (e) => {
    const data = JSON.parse(e.data);
    const msgDiv = taskMessages[data.task_id];
    if (msgDiv) {
        let resultDiv = msgDiv.querySelector('.task-result');
        if (!resultDiv) { resultDiv = document.createElement('div'); resultDiv.className = 'task-result'; msgDiv.appendChild(resultDiv); }
        resultDiv.textContent += data.chunk;
        window.chatMessages.scrollTop = window.chatMessages.scrollHeight;
    }
});
eventSource.addEventListener('task_done', (e) => {
    const data = JSON.parse(e.data);
    const msgDiv = taskMessages[data.task_id];
    if (msgDiv) { msgDiv.innerHTML = `<div>${t('task.completed')}</div><div class="task-result">${escapeHtml(data.result || t('task.no_content'))}</div>`; delete taskMessages[data.task_id]; }
});
eventSource.addEventListener('task_error', (e) => {
    const data = JSON.parse(e.data);
    const msgDiv = taskMessages[data.task_id];
    if (msgDiv) { msgDiv.innerHTML = `<div>${t('task.failed')}</div><div class="task-result">${t('chat.error', { message: escapeHtml(data.error) })}</div>`; delete taskMessages[data.task_id]; }
});
eventSource.addEventListener('task_cancel', (e) => {
    const data = JSON.parse(e.data);
    const msgDiv = taskMessages[data.task_id];
    if (msgDiv) { msgDiv.innerHTML = `<div>${t('task.cancelled')}</div>`; delete taskMessages[data.task_id]; }
});
async function stopTask(taskId) {
    try {
        const resp = await fetchWithAuth(`/cancel_task/${taskId}`, { method: 'POST' });
        const result = await resp.json();
        if (result.status !== 'cancelling') alert(t('task.stop_failed', { message: result.error || t('task.unknown_error') }));
    } catch(err) { alert(t('task.stop_failed', { message: err.message })); }
}

async function checkSessionAndClear() {
    try {
        const resp = await fetch('/session');
        const data = await resp.json();
        const storedId = localStorage.getItem('startup_id');
        if (storedId !== data.startup_id) {
            localStorage.removeItem('chatMessages');
            window.chatMessages.innerHTML = '';
            localStorage.setItem('startup_id', data.startup_id);
        }
    } catch(e) { console.error(e); }
}

async function loadMessagesFromServer() {
    try {
        const resp = await fetchWithAuth('/api/messages');
        const data = await resp.json();
        if (data.messages && data.messages.length > 0) {
            window.chatMessages.innerHTML = '';
            let mergedMessages = [];
            let lastAssistantMsg = null;
            data.messages.forEach(msg => {
                if (msg.role === 'assistant') {
                    if (!lastAssistantMsg) {
                        lastAssistantMsg = { role: 'assistant', chunks: [] };
                    }
                    if (msg.content) {
                        lastAssistantMsg.chunks.push({ type: 'text', content: msg.content });
                    }
                    if (msg.tool_calls) {
                        lastAssistantMsg.chunks.push({ type: 'tool_calls', calls: msg.tool_calls });
                    }
                } else if (msg.role === 'tool' && lastAssistantMsg) {
                    for (let i = lastAssistantMsg.chunks.length - 1; i >= 0; i--) {
                        if (lastAssistantMsg.chunks[i].type === 'tool_calls') {
                            const chunk = lastAssistantMsg.chunks[i];
                            const call = chunk.calls.find(c => c.id === msg.tool_call_id);
                            if (call) {
                                call.result = msg.content;
                            }
                            break;
                        }
                    }
                } else {
                    if (lastAssistantMsg) {
                        mergedMessages.push(lastAssistantMsg);
                        lastAssistantMsg = null;
                    }
                    mergedMessages.push(msg);
                }
            });
            if (lastAssistantMsg) {
                mergedMessages.push(lastAssistantMsg);
            }
            mergedMessages.forEach(msg => {
                if (msg.role === 'user') {
                    addMessage('user', msg.content);
                } else if (msg.role === 'assistant') {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message assistant';
                    msg.chunks.forEach(chunk => {
                        if (chunk.type === 'text') {
                            const contentContainer = document.createElement('div');
                            contentContainer.className = 'assistant-content';
                            if (chunk.content) {
                                try {
                                    contentContainer.innerHTML = marked.parse(chunk.content);
                                    wrapTables(contentContainer);
                                } catch(e) {
                                    contentContainer.textContent = chunk.content;
                                }
                            }
                            msgDiv.appendChild(contentContainer);
                        } else if (chunk.type === 'tool_calls') {
                            chunk.calls.forEach(tc => {
                                const callId = tc.id;
                                let toolName = tc.function.name;
                                let params = {};
                                try { params = JSON.parse(tc.function.arguments); } catch(e) {}
                                let actualName = toolName;
                                let actualParams = params;
                                if (toolName === 'tools' && params.tool_name) {
                                    actualName = params.tool_name;
                                    if (params.arguments) actualParams = params.arguments;
                                }
                                const resultContent = tc.result;
                                addToolCallBlockStructured(msgDiv, callId, actualName, actualParams, resultContent || t('tool.no_result'));
                            });
                        }
                    });
                    if (window.renderMathInElement) {
                        window.renderMathInElement(msgDiv, {
                            delimiters: [{left: '$$', right: '$$', display: true},{left: '$', right: '$', display: false}]
                        });
                    }
                    window.chatMessages.appendChild(msgDiv);
                }
            });
            saveMessagesToLocalStorage();
            return true;
        }
        return false;
    } catch(e) {
        console.error('Failed to load messages from server', e);
        return false;
    }
}

(async function init() {
    await loadI18n();
    applyTranslations();
    document.title = t('app.title');
    setSendButtonToSend();
    const tempToken = localStorage.getItem('FranxAgent_temp_token');
    if (tempToken) { setAuthToken(tempToken); localStorage.removeItem('FranxAgent_temp_token'); }
    const authenticated = await checkAuth();
    if (!authenticated) return;
    await checkSessionAndClear();
    const loadedFromServer = await loadMessagesFromServer();
    if (!loadedFromServer) {
        loadMessagesFromLocalStorage();
    }
    loadConfig();
    loadTasks();
})();