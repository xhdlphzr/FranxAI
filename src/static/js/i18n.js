// Copyright (C) 2026 xhdlphzr
// This file is part of FranxAgent.
// FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
// FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

window.i18n = { language: "en", translations: {} };

function t(key, params = {}) {
  let text =
    key.split(".").reduce((o, k) => (o || {})[k], window.i18n.translations) ||
    key;
  Object.entries(params).forEach(([k, v]) => {
    text = text.replaceAll(`{${k}}`, v);
  });
  return text;
}

async function loadI18n() {
  try {
    const resp = await fetch("/api/i18n");
    const data = await resp.json();
    window.i18n.language = data.language || "en";
    window.i18n.translations = data.translations || {};
  } catch (e) {
    console.error("Failed to load i18n", e);
  }
}

function applyTranslations() {
  document.documentElement.lang = window.i18n.language;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
}
