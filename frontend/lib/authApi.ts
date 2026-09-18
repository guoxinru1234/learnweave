import axios from 'axios';

const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api';

export interface User {
  id: number;
  username: string;
  role: 'user' | 'admin';
  is_active?: boolean;
  created_at?: string;
  last_login_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  is_new_user: boolean;
  has_completed_guide: boolean;
}

export interface RegisterData { username: string; password: string; role?: string; }
export interface LoginData { username: string; password: string; }

export async function register(data: RegisterData): Promise<AuthResponse> {
  const r = await axios.post<AuthResponse>(`${BASE}/auth/register`, data, { timeout: 12000 });
  return r.data;
}

export async function login(data: LoginData): Promise<AuthResponse> {
  const r = await axios.post<AuthResponse>(`${BASE}/auth/login`, data, { timeout: 12000 });
  return r.data;
}

export async function getAllUsers(token: string): Promise<User[]> {
  const r = await axios.get(`${BASE}/admin/users`, { headers: { Authorization: `Bearer ${token}` } });
  return r.data;
}

export async function updateUserRole(token: string, userId: number, role: 'user' | 'admin'): Promise<User> {
  const r = await axios.patch(`${BASE}/admin/users/${userId}/role`, null, { params: { role }, headers: { Authorization: `Bearer ${token}` } });
  return r.data;
}

export async function toggleUserActive(token: string, userId: number): Promise<User> {
  const r = await axios.patch(`${BASE}/admin/users/${userId}/toggle-active`, null, { headers: { Authorization: `Bearer ${token}` } });
  return r.data;
}
