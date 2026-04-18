const configForm = document.getElementById('config-form');
const configStatus = document.getElementById('config-status');
const pagesInner = document.getElementById('pagesInner');
const dockItems = document.querySelectorAll('.dock-item');

let currentPage = 'chat';
function switchPage(page) {
    if (page === currentPage) return;
    currentPage = page;
    const offset = page === 'chat' ? 0 : -50;
    pagesInner.style.transform = `translateX(${offset}%)`;
    dockItems.forEach(btn => {
        if (btn.dataset.page === page) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    if (page === 'config') {
        loadConfig();
        loadTasks();
    }
}
dockItems.forEach(btn => {
    btn.addEventListener('click', () => switchPage(btn.dataset.page));
});

let mcpServers = [];
function renderMCPServers() {
    const container = document.getElementById('mcp-servers-list');
    if (!container) return;
    container.innerHTML = '';
    if (mcpServers.length === 0) { container.innerHTML = `<div>${t('mcp.no_servers')}</div>`; return; }
    mcpServers.forEach((server, index) => {
        const div = document.createElement('div'); div.className = 'mcp-server-item';
        div.innerHTML = `
            <input type="text" placeholder="${t('mcp.name_placeholder')}" value="${escapeHtml(server.name || '')}" data-field="name" data-index="${index}">
            <input type="text" placeholder="${t('mcp.command_placeholder')}" value="${escapeHtml(server.command || '')}" data-field="command" data-index="${index}">
            <input type="text" placeholder="${t('mcp.args_placeholder')}" value="${escapeHtml((server.args || []).join(' '))}" data-field="args" data-index="${index}">
            <button type="button" data-index="${index}" class="remove-mcp">${t('mcp.delete')}</button>
        `;
        container.appendChild(div);
    });
    document.querySelectorAll('.mcp-server-item input').forEach(input => {
        input.addEventListener('change', (e) => {
            const idx = parseInt(e.target.dataset.index);
            const field = e.target.dataset.field;
            if (field === 'args') {
                const argsStr = e.target.value.trim();
                mcpServers[idx].args = argsStr ? argsStr.split(/\s+/) : [];
            } else { mcpServers[idx][field] = e.target.value; }
        });
    });
    document.querySelectorAll('.remove-mcp').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(btn.dataset.index);
            mcpServers.splice(idx, 1);
            renderMCPServers();
        });
    });
}
document.getElementById('add-mcp-server')?.addEventListener('click', () => {
    mcpServers.push({ name: t('mcp.new_server'), command: "uvx", args: ["windows-mcp"] });
    renderMCPServers();
});

let tasks = {};
function renderTasks() {
    const container = document.getElementById('tasks-list');
    if (!container) return;
    container.innerHTML = '';
    const entries = Object.entries(tasks);
    if (entries.length === 0) { container.innerHTML = `<div>${t('task.no_tasks')}</div>`; return; }
    for (const [time, content] of entries) {
        const div = document.createElement('div'); div.className = 'task-item';
        div.innerHTML = `<div class="task-info"><span class="task-time">${escapeHtml(time)}</span><span class="task-content">${escapeHtml(content)}</span></div><button data-time="${escapeHtml(time)}" class="delete-task">${t('mcp.delete')}</button>`;
        container.appendChild(div);
    }
    document.querySelectorAll('.delete-task').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const time = btn.dataset.time;
            if (confirm(t('task.delete_confirm', { time }))) { await deleteTask(time); await loadTasks(); }
        });
    });
}
async function loadTasks() {
    try {
        const resp = await fetchWithAuth('/tasks');
        const data = await resp.json();
        tasks = data.error ? {} : data;
        renderTasks();
    } catch(e) { tasks = {}; renderTasks(); }
}
async function addTask(time, content) {
    try {
        const resp = await fetchWithAuth('/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'add', time, content }) });
        const result = await resp.json();
        if (result.status === 'success') return true;
        else { alert(t('task.add_failed', { message: result.error || t('task.unknown_error') })); return false; }
    } catch(e) { alert(t('chat.network_error', { message: e.message })); return false; }
}
async function deleteTask(time) {
    try {
        const resp = await fetchWithAuth('/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'delete', time }) });
        const result = await resp.json();
        if (result.status === 'success') return true;
        else { alert(t('task.delete_failed', { message: result.error || t('task.unknown_error') })); return false; }
    } catch(e) { alert(t('chat.network_error', { message: e.message })); return false; }
}
document.getElementById('add-task')?.addEventListener('click', async () => {
    const time = prompt(t('task.time_prompt'));
    if (!time) return;
    if (!/^\d{2}:\d{2}$/.test(time)) { alert(t('task.time_invalid')); return; }
    const content = prompt(t('task.content_prompt'));
    if (!content) return;
    if (await addTask(time, content)) await loadTasks();
});

async function loadConfig() {
    try {
        const resp = await fetchWithAuth('/config');
        const config = await resp.json();
        if (config.error) configStatus.innerText = t('config.load_failed', { message: config.error });
        else {
            document.getElementById('language').value = config.language || 'en';
            document.getElementById('api_key').value = config.api_key || '';
            document.getElementById('base_url').value = config.base_url || '';
            document.getElementById('model').value = config.model || '';
            document.getElementById('settings').value = config.settings || '';
            document.getElementById('temperature').value = config.temperature ?? 0.8;
            document.getElementById('thinking').checked = config.thinking ?? false;
            document.getElementById('max_iterations').value = config.max_iterations ?? 100;
            document.getElementById('threshold').value = config.threshold ?? 20;
            document.getElementById('knowledge_k').value = config.knowledge_k ?? 1;
            const ett = config.tools?.ett || {};
            document.getElementById('ett_api_key').value = ett.api_key || '';
            document.getElementById('ett_model').value = ett.model || 'glm-4.6v-flash';
            document.getElementById('ett_temperature').value = ett.temperature ?? 0.8;
            document.getElementById('ett_thinking').checked = ett.thinking ?? false;
            document.getElementById('ett_max_iterations').value = ett.max_iterations ?? 100;
            document.getElementById('ett_max_retries').value = ett.max_retries ?? 3;
            mcpServers = config.mcp_servers || [];
            renderMCPServers();
            configStatus.innerText = '';
        }
    } catch(err) { configStatus.innerText = t('config.load_failed', { message: err.message }); }
}
configForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newConfig = {
        language: document.getElementById('language').value,
        api_key: document.getElementById('api_key').value,
        base_url: document.getElementById('base_url').value,
        model: document.getElementById('model').value,
        settings: document.getElementById('settings').value,
        temperature: parseFloat(document.getElementById('temperature').value),
        thinking: document.getElementById('thinking').checked,
        max_iterations: parseInt(document.getElementById('max_iterations').value),
        threshold: parseInt(document.getElementById('threshold').value),
        knowledge_k: parseInt(document.getElementById('knowledge_k').value),
        tools: { ett: {
            api_key: document.getElementById('ett_api_key').value,
            model: document.getElementById('ett_model').value,
            temperature: parseFloat(document.getElementById('ett_temperature').value),
            thinking: document.getElementById('ett_thinking').checked,
            max_iterations: parseInt(document.getElementById('ett_max_iterations').value),
            max_retries: parseInt(document.getElementById('ett_max_retries').value)
        } },
        mcp_servers: mcpServers
    };
    try {
        const currentResp = await fetchWithAuth('/config');
        const currentConfig = await currentResp.json();
        const mergedConfig = { ...currentConfig, ...newConfig, tools: { ...currentConfig.tools, ...newConfig.tools } };
        const saveResp = await fetchWithAuth('/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mergedConfig) });
        const result = await saveResp.json();
        if (result.status === 'success') {
            await loadI18n();
            applyTranslations();
            renderTasks();
            renderMCPServers();
            configStatus.innerText = t('config.saved');
        } else {
            configStatus.innerText = t('config.save_failed', { message: result.error });
        }
    } catch(err) { configStatus.innerText = t('config.save_failed', { message: err.message }); }
});