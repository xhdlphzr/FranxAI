const loginBtn = document.getElementById('loginBtn');
const passwordInput = document.getElementById('password');
const errorMsg = document.getElementById('errorMsg');
const agreeCheckbox = document.getElementById('agreeCheckbox');
const agreeContainer = document.getElementById('agreeContainer');
const agreeError = document.getElementById('agreeError');
const registerLink = document.getElementById('registerLink');

const overlay = document.createElement('div');
overlay.className = 'expand-overlay';
document.body.appendChild(overlay);

async function fetchPublicKey() {
    const resp = await fetch('/api/public-key');
    const data = await resp.json();
    return data.public_key;
}

function validateAgreement() {
    if (!agreeCheckbox.checked) {
        agreeContainer.classList.add('shake');
        agreeError.style.display = 'block';
        setTimeout(() => {
            agreeContainer.classList.remove('shake');
        }, 300);
        return false;
    } else {
        agreeError.style.display = 'none';
        return true;
    }
}

function playExpandAnimation(callback) {
    const btn = loginBtn;
    const rect = btn.getBoundingClientRect();
    const clone = btn.cloneNode(true);
    clone.style.position = 'fixed';
    clone.style.top = rect.top + 'px';
    clone.style.left = rect.left + 'px';
    clone.style.width = rect.width + 'px';
    clone.style.height = rect.height + 'px';
    clone.style.margin = '0';
    clone.style.zIndex = '10000';
    clone.style.transition = 'all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1)';
    clone.style.backgroundColor = getComputedStyle(btn).backgroundColor;
    clone.style.borderRadius = getComputedStyle(btn).borderRadius;
    document.body.appendChild(clone);
    clone.offsetHeight;
    clone.style.top = '0';
    clone.style.left = '0';
    clone.style.width = '100%';
    clone.style.height = '100%';
    clone.style.borderRadius = '0';
    clone.style.backgroundColor = '#ffffff';
    overlay.classList.add('active');
    setTimeout(() => {
        clone.remove();
        if (callback) callback();
    }, 300);
}

async function login() {
    if (!validateAgreement()) {
        return;
    }
    try {
        const checkResp = await fetch('/api/check-auth');
        const checkData = await checkResp.json();
        if (!checkData.password_set) {
            if (registerLink) {
                registerLink.classList.add('shake');
                setTimeout(() => registerLink.classList.remove('shake'), 300);
            }
            errorMsg.textContent = t('login.password_not_set');
            return;
        }
    } catch (err) {
        console.error('Failed to check password status', err);
    }
    const password = passwordInput.value.trim();
    if (!password) {
        errorMsg.textContent = t('login.enter_password');
        return;
    }
    loginBtn.classList.add('loading');
    errorMsg.textContent = '';
    try {
        const publicKeyPem = await fetchPublicKey();
        const encrypt = new JSEncrypt();
        encrypt.setKey(publicKeyPem);
        const encrypted = encrypt.encrypt(password);
        if (!encrypted) {
            throw new Error(t('login.encryption_failed'));
        }
        const resp = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: encrypted })
        });
        const result = await resp.json();
        if (resp.ok) {
            localStorage.setItem('FranxAgent_temp_token', result.token);
            playExpandAnimation(() => {
                window.location.href = '/';
            });
        } else {
            errorMsg.textContent = result.error || t('login.login_failed');
            loginBtn.classList.remove('loading');
        }
    } catch (err) {
        errorMsg.textContent = t('login.network_error');
        console.error(err);
        loginBtn.classList.remove('loading');
    }
}

loginBtn.addEventListener('click', login);
passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') login();
});
agreeCheckbox.addEventListener('change', () => {
    if (agreeCheckbox.checked) {
        agreeError.style.display = 'none';
    }
});

(async function init() {
    await loadI18n();
    applyTranslations();
    document.title = t('login.title');
    document.getElementById('password').placeholder = t('login.password_placeholder');
    document.getElementById('agreeLabel').innerHTML = t('login.agree', {
        link: `<a href="${t('login.agree_url')}" target="_blank">${t('login.agree_link')}</a>`
    });
    document.getElementById('agreeError').textContent = t('login.agree_error');
    loginBtn.textContent = t('login.submit');
    registerLink.textContent = t('login.no_password');
})();