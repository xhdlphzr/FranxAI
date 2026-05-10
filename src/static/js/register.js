// Copyright (C) 2026 xhdlphzr
// This file is part of FranxAgent.
// FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
// FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

const registerBtn = document.getElementById("registerBtn");
const passwordInput = document.getElementById("password");
const confirmInput = document.getElementById("confirmPassword");
const errorMsg = document.getElementById("errorMsg");
const agreeCheckbox = document.getElementById("agreeCheckbox");
const agreeContainer = document.getElementById("agreeContainer");
const agreeError = document.getElementById("agreeError");

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
  const btn = registerBtn;
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

async function register() {
  if (!validateAgreement()) {
    return;
  }
  const password = passwordInput.value.trim();
  const confirm = confirmInput.value.trim();
  if (!password) {
    errorMsg.textContent = t("register.enter_password");
    return;
  }
  if (password !== confirm) {
    errorMsg.textContent = t("register.password_mismatch");
    return;
  }
  registerBtn.classList.add("loading");
  errorMsg.textContent = "";
  try {
    const publicKeyPem = await fetchPublicKey();
    const encrypted = await eccEncrypt(publicKeyPem, password);
    const resp = await fetch("/api/setup", {
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
      errorMsg.textContent = result.error || t("register.setup_failed");
      registerBtn.classList.remove("loading");
    }
  } catch (err) {
    errorMsg.textContent = t("register.network_error");
    console.error(err);
    registerBtn.classList.remove("loading");
  }
}

registerBtn.addEventListener("click", register);
passwordInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") register();
});
confirmInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") register();
});
agreeCheckbox.addEventListener("change", () => {
  if (agreeCheckbox.checked) {
    agreeError.style.display = "none";
  }
});

(async function init() {
  await loadI18n();
  applyTranslations();
  document.title = t("register.title");
  document.getElementById("password").placeholder = t(
    "register.password_placeholder",
  );
  document.getElementById("confirmPassword").placeholder = t(
    "register.confirm_placeholder",
  );
  document.getElementById("agreeLabel").innerHTML = t("register.agree", {
    link: `<a href="${t("register.agree_url")}" target="_blank">${t("register.agree_link")}</a>`,
  });
  document.getElementById("agreeError").textContent = t("register.agree_error");
  registerBtn.textContent = t("register.submit");
  document.getElementById("loginLink").textContent = t("register.has_password");
})();
