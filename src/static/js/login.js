// Copyright (C) 2026 xhdlphzr
// This file is part of FranxAgent.
// FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
// FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

const loginBtn = document.getElementById("loginBtn");
const passwordInput = document.getElementById("password");
const errorMsg = document.getElementById("errorMsg");
const agreeCheckbox = document.getElementById("agreeCheckbox");
const agreeContainer = document.getElementById("agreeContainer");
const agreeError = document.getElementById("agreeError");
const registerLink = document.getElementById("registerLink");

const overlay = document.createElement("div");
overlay.className = "expand-overlay";
document.body.appendChild(overlay);

async function fetchPublicKey() {
  const resp = await fetch("/api/public-key");
  const data = await resp.json();
  return data.public_key;
}

// ECIES encryption using Web Crypto API (ECDH + HKDF + AES-256-GCM)
async function eccEncrypt(publicKeyPem, plaintext) {
  // 1. Parse PEM to DER bytes
  const pemHeader = "-----BEGIN PUBLIC KEY-----";
  const pemFooter = "-----END PUBLIC KEY-----";
  const pemContents = publicKeyPem
    .replace(pemHeader, "")
    .replace(pemFooter, "")
    .replace(/\s/g, "");
  const derBytes = Uint8Array.from(atob(pemContents), (c) => c.charCodeAt(0));

  // 2. Import server's P-256 public key
  const serverPublicKey = await crypto.subtle.importKey(
    "spki",
    derBytes,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    [],
  );

  // 3. Generate ephemeral key pair
  const ephemeralKeyPair = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveBits"],
  );

  // 4. Export ephemeral public key as SPKI DER
  const ephemeralPubDer = await crypto.subtle.exportKey(
    "spki",
    ephemeralKeyPair.publicKey,
  );

  // 5. ECDH derive shared secret
  const sharedSecret = await crypto.subtle.deriveBits(
    { name: "ECDH", public: serverPublicKey },
    ephemeralKeyPair.privateKey,
    256,
  );

  // 6. Import shared secret as HKDF key material
  const hkdfKey = await crypto.subtle.importKey(
    "raw",
    sharedSecret,
    { name: "HKDF" },
    false,
    ["deriveBits"],
  );

  // 7. HKDF derive AES-256 key
  const aesKeyBits = await crypto.subtle.deriveBits(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt: new Uint8Array(0),
      info: new TextEncoder().encode("franxagent-ecc-encryption"),
    },
    hkdfKey,
    256,
  );

  // 8. Import AES-GCM key
  const aesKey = await crypto.subtle.importKey(
    "raw",
    aesKeyBits,
    { name: "AES-GCM" },
    false,
    ["encrypt"],
  );

  // 9. Encrypt with random 12-byte IV
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    aesKey,
    encoded,
  );

  // 10. Return as ECIES payload object
  return {
    ephemeral_key: btoa(
      String.fromCharCode(...new Uint8Array(ephemeralPubDer)),
    ),
    iv: btoa(String.fromCharCode(...iv)),
    ciphertext: btoa(String.fromCharCode(...new Uint8Array(ciphertext))),
  };
}

function validateAgreement() {
  if (!agreeCheckbox.checked) {
    agreeContainer.classList.add("shake");
    agreeError.style.display = "block";
    setTimeout(() => {
      agreeContainer.classList.remove("shake");
    }, 300);
    return false;
  } else {
    agreeError.style.display = "none";
    return true;
  }
}

function playExpandAnimation(callback) {
  const btn = loginBtn;
  const rect = btn.getBoundingClientRect();
  const clone = btn.cloneNode(true);
  clone.style.position = "fixed";
  clone.style.top = rect.top + "px";
  clone.style.left = rect.left + "px";
  clone.style.width = rect.width + "px";
  clone.style.height = rect.height + "px";
  clone.style.margin = "0";
  clone.style.zIndex = "10000";
  clone.style.transition = "all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1)";
  clone.style.backgroundColor = getComputedStyle(btn).backgroundColor;
  clone.style.borderRadius = getComputedStyle(btn).borderRadius;
  document.body.appendChild(clone);
  clone.offsetHeight;
  clone.style.top = "0";
  clone.style.left = "0";
  clone.style.width = "100%";
  clone.style.height = "100%";
  clone.style.borderRadius = "0";
  clone.style.backgroundColor = "#ffffff";
  overlay.classList.add("active");
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
    const checkResp = await fetch("/api/check-auth");
    const checkData = await checkResp.json();
    if (!checkData.password_set) {
      if (registerLink) {
        registerLink.classList.add("shake");
        setTimeout(() => registerLink.classList.remove("shake"), 300);
      }
      errorMsg.textContent = t("login.password_not_set");
      return;
    }
  } catch (err) {
    console.error("Failed to check password status", err);
  }
  const password = passwordInput.value.trim();
  if (!password) {
    errorMsg.textContent = t("login.enter_password");
    return;
  }
  loginBtn.classList.add("loading");
  errorMsg.textContent = "";
  try {
    const publicKeyPem = await fetchPublicKey();
    const encrypted = await eccEncrypt(publicKeyPem, password);
    const resp = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: encrypted }),
    });
    const result = await resp.json();
    if (resp.ok) {
      localStorage.setItem("FranxAgent_temp_token", result.token);
      playExpandAnimation(() => {
        window.location.href = "/";
      });
    } else {
      errorMsg.textContent = result.error || t("login.login_failed");
      loginBtn.classList.remove("loading");
    }
  } catch (err) {
    errorMsg.textContent = t("login.network_error");
    console.error(err);
    loginBtn.classList.remove("loading");
  }
}

loginBtn.addEventListener("click", login);
passwordInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") login();
});
agreeCheckbox.addEventListener("change", () => {
  if (agreeCheckbox.checked) {
    agreeError.style.display = "none";
  }
});

(async function init() {
  await loadI18n();
  applyTranslations();
  document.title = t("login.title");
  document.getElementById("password").placeholder = t(
    "login.password_placeholder",
  );
  document.getElementById("agreeLabel").innerHTML = t("login.agree", {
    link: `<a href="${t("login.agree_url")}" target="_blank">${t("login.agree_link")}</a>`,
  });
  document.getElementById("agreeError").textContent = t("login.agree_error");
  loginBtn.textContent = t("login.submit");
  registerLink.textContent = t("login.no_password");
})();
