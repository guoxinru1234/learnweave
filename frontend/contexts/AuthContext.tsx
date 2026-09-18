// frontend/contexts/AuthContext.tsx
'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User, login, register, LoginData, RegisterData } from '@/lib/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (data: LoginData) => Promise<{ is_new_user: boolean }>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isNewUser: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);

  // ✅ 从 sessionStorage 恢复登录状态（关闭标签页即失效）
  useEffect(() => {
    const storedToken = sessionStorage.getItem('auth_token');
    const storedUser = sessionStorage.getItem('auth_user');
    const storedIsNewUser = sessionStorage.getItem('auth_is_new_user');
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        setIsNewUser(storedIsNewUser === 'true');
      } catch {
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_user');
        sessionStorage.removeItem('auth_is_new_user');
      }
    }
    setIsLoading(false);
  }, []);

  // 登录
  const handleLogin = useCallback(async (data: LoginData) => {
    const response = await login(data);
    const { access_token, user, is_new_user } = response;
    setToken(access_token);
    setUser(user);
    setIsNewUser(is_new_user);
    sessionStorage.setItem('auth_token', access_token);
    sessionStorage.setItem('auth_user', JSON.stringify(user));
    sessionStorage.setItem('auth_is_new_user', String(is_new_user));
    return { is_new_user };
  }, []);

  // 注册（注册成功后自动登录）
  const handleRegister = useCallback(async (data: RegisterData) => {
    const response = await register(data);
    const { access_token, user, is_new_user } = response;
    setToken(access_token);
    setUser(user);
    setIsNewUser(is_new_user);
    sessionStorage.setItem('auth_token', access_token);
    sessionStorage.setItem('auth_user', JSON.stringify(user));
    sessionStorage.setItem('auth_is_new_user', String(is_new_user));
  }, []);

  // 退出登录
  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setIsNewUser(false);
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_user');
    sessionStorage.removeItem('auth_is_new_user');
  }, []);

  const isAuthenticated = !!user && !!token;
  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isLoading,
      login: handleLogin,
      register: handleRegister,
      logout,
      isAuthenticated,
      isAdmin,
      isNewUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}