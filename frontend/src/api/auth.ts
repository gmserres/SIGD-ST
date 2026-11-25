import { API_URL } from './config';

const TOKEN_KEY = 'sigd_st_session_token';

export type UsuarioSesion = {
  id: string;
  nombre: string;
  email: string;
  rol: 'ADMINISTRADOR' | 'SECRETARIO_TECNICO' | 'OPERADOR' | 'CONSULTA';
  activo: boolean;
};

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

export async function authenticatedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await window.fetch(input, { ...init, headers });
  if (response.status === 401 && token) {
    clearToken();
    window.dispatchEvent(new Event('sigd-st-auth-expired'));
  }
  return response;
}

export async function iniciarSesion(email: string, password: string) {
  const response = await window.fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Correo o contraseña incorrectos.');
  const data = await response.json();
  setToken(data.access_token);
  return data.usuario as UsuarioSesion;
}

export async function obtenerSesion(): Promise<UsuarioSesion | null> {
  if (!getToken()) return null;
  const response = await authenticatedFetch(`${API_URL}/auth/me`);
  if (!response.ok) return null;
  return response.json();
}

export async function cerrarSesion(): Promise<void> {
  if (getToken()) {
    await authenticatedFetch(`${API_URL}/auth/logout`, { method: 'POST' });
  }
  clearToken();
}
