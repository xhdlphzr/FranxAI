let memoryToken = null;

function getAuthToken() { return memoryToken; }
function setAuthToken(token) { memoryToken = token; }
function redirectToLogin() { window.location.href = '/login'; }

async function checkAuth() {
    const token = getAuthToken();
    if (!token) { redirectToLogin(); return false; }
    try {
        const resp = await fetch('/api/check-auth', { headers: { 'Authorization': `Bearer ${token}` } });
        const data = await resp.json();
        if (!data.authenticated) { setAuthToken(null); redirectToLogin(); return false; }
        return true;
    } catch(err) { console.error(err); redirectToLogin(); return false; }
}

function fetchWithAuth(url, options = {}) {
    const token = getAuthToken();
    const headers = options.headers || {};
    headers['Authorization'] = `Bearer ${token}`;
    return fetch(url, { ...options, headers });
}