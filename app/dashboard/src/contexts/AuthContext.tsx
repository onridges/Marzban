import React, { createContext, useContext, useEffect, useState } from 'react';
import { fetch, $fetch } from '../service/http';
import { getAuthToken, removeAuthToken, setAuthToken } from '../utils/authStorage';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (username: string, password: string) => Promise<"user" | "admin">;
  logout: () => void;
  register: (username: string, email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getAuthToken());
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    // 检查 token 有效性并获取用户信息
    const validateAuth = async () => {
      try {
        const token = getAuthToken();
        if (!token) {
          setIsAuthenticated(false);
          removeAuthToken();
        } else {
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Auth validation failed:', error);
        setIsAuthenticated(false);
        removeAuthToken();
      }
    };
    validateAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      // 确保登录请求不携带旧的 Authorization 头，避免首次尝试被拦截或预检失败
      removeAuthToken();

      // OAuth2PasswordRequestForm 期望 x-www-form-urlencoded
      const body = new URLSearchParams({
        username,
        password,
        grant_type: 'password',
      });

      // 先尝试普通用户登录
      try {
        const userResp = await $fetch('/token', {
          method: 'POST',
          body,
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          credentials: 'omit',
        });
        const { access_token, refresh_token } = userResp as { access_token?: string; refresh_token?: string };
        if (!access_token) {
          // 后端返回 200 但没有令牌，作为失败处理
          throw new Error('登录响应缺少访问令牌');
        }
        setAuthToken(access_token);
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token);
        }
        setIsAuthenticated(true);
        setUser(null);
        return "user" as const;
      } catch (userErr: any) {
        // 若用户登录失败，再尝试管理员登录
        try {
          const adminResp = await $fetch('/admin/token', {
            method: 'POST',
            body,
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            credentials: 'omit',
          });
          const { access_token, refresh_token } = adminResp as { access_token?: string; refresh_token?: string };
          if (!access_token) {
            throw new Error('管理员登录响应缺少访问令牌');
          }
          setAuthToken(access_token);
          if (refresh_token) {
            localStorage.setItem('refresh_token', refresh_token);
          }
          setIsAuthenticated(true);
          setUser(null);
          return "admin" as const;
        } catch (adminErr) {
          // 双重失败，抛出用户登录的原始错误，便于提示
          throw userErr || adminErr;
        }
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      await fetch('/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      // 注册成功后不自动登录，而是跳转到登录页
      return;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (refresh_token) {
        await fetch('/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token }),
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getAuthToken()}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      removeAuthToken();
      localStorage.removeItem('refresh_token');
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, register }}>
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