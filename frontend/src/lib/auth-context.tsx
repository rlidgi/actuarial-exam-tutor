"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type AuthResponse } from "./api";

const TOKEN_STORAGE_KEY = "actuarial_tutor_token";

interface AuthState {
  token: string | null;
  email: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

async function afterAuth(response: AuthResponse) {
  await api.ensureProfile(response.access_token);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) {
      setToken(stored);
    }
    setLoading(false);
  }, []);

  const login = async (loginEmail: string, password: string) => {
    const response = await api.login(loginEmail, password);
    await afterAuth(response);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setEmail(response.user.email);
  };

  const register = async (registerEmail: string, password: string) => {
    const response = await api.register(registerEmail, password);
    await afterAuth(response);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setEmail(response.user.email);
  };

  const logout = () => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setEmail(null);
  };

  return (
    <AuthContext.Provider value={{ token, email, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
