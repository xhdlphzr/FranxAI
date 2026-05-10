// Copyright (C) 2026 xhdlphzr
// This file is part of FranxAgent.
// FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
// FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

let memoryToken = null;

function getAuthToken() {
  return memoryToken;
}
function setAuthToken(token) {
  memoryToken = token;
}
function redirectToLogin() {
  window.location.href = "/login";
}

async function checkAuth() {
  const token = getAuthToken();
  if (!token) {
    redirectToLogin();
    return false;
  }
  try {
    const resp = await fetch("/api/check-auth", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await resp.json();
    if (!data.authenticated) {
      setAuthToken(null);
      redirectToLogin();
      return false;
    }
    return true;
  } catch (err) {
    console.error(err);
    redirectToLogin();
    return false;
  }
}

function fetchWithAuth(url, options = {}) {
  const token = getAuthToken();
  const headers = options.headers || {};
  headers["Authorization"] = `Bearer ${token}`;
  return fetch(url, { ...options, headers });
}
