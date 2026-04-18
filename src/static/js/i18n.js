window.i18n = { language: 'en', translations: {} };

function t(key, params = {}) {
    let text = key.split('.').reduce((o, k) => (o || {})[k], window.i18n.translations) || key;
    Object.entries(params).forEach(([k, v]) => { text = text.replaceAll(`{${k}}`, v); });
    return text;
}

async function loadI18n() {
    try {
        const resp = await fetch('/api/i18n');
        const data = await resp.json();
        window.i18n.language = data.language || 'en';
        window.i18n.translations = data.translations || {};
    } catch (e) {
        console.error('Failed to load i18n', e);
    }
}

function applyTranslations() {
    document.documentElement.lang = window.i18n.language;
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });
}