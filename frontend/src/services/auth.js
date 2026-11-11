import { apiFetch } from "./api.js";

const TOKEN_KEY = "auth_token";

export function storeToken(token) {
  if (typeof token !== "string" || !token.trim()) {
    throw new Error("El servidor no devolvió un token válido.");
  }

  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export async function login(username, password) {
  const data = await apiFetch("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  storeToken(data?.token);
  return data.token;
}

export async function logout() {
  const token = getToken();

  try {
    if (token) {
      await apiFetch("/auth/logout/", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    }
  } finally {
    localStorage.removeItem(TOKEN_KEY);
  }
}
