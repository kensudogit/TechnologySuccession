const TOKEN_KEY = "ts_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as { exp?: number };
    return typeof payload.exp !== "number" || payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

export function isLoggedIn(): boolean {
  const token = getToken();
  if (!token) return false;
  if (isTokenExpired(token)) {
    clearToken();
    return false;
  }
  return true;
}
