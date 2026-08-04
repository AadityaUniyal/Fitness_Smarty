import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthAPI, AuthTokens } from '../services/apiService';

interface User {
  id: string;
  email: string;
  full_name?: string;
  age?: number;
  weight_kg?: number;
  height_cm?: number;
  gender?: string;
  activity_level?: string;
  primary_goal?: string;
  femmecare_enabled?: boolean;
  is_admin?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  googleLogin: (idToken: string) => Promise<void>;
  appleLogin: (idToken: string, fullName?: string, email?: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User>) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = 'smarty_access_token';
const REFRESH_KEY = 'smarty_refresh_token';
const USER_KEY = 'smarty_user_data';
const LEGACY_USER_KEY = 'smarty_user';
const USER_ID_KEY = 'smarty_user_id';

const setLegacyUserState = (user: User) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(USER_ID_KEY, user.id);
  localStorage.setItem(LEGACY_USER_KEY, JSON.stringify({
    id: user.id,
    name: user.full_name || user.email.split('@')[0],
    email: user.email,
    loggedIn: true,
  }));
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const getRefreshToken = () => localStorage.getItem(REFRESH_KEY);

  const setTokens = (tokens: AuthTokens) => {
    localStorage.setItem(TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  };

  const clearTokens = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(LEGACY_USER_KEY);
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem('smarty_profile');
  };

  const refreshUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const userData = await AuthAPI.getCurrentUser(token);
      setUser(userData);
      setLegacyUserState(userData);
    } catch {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          const tokens = await AuthAPI.refreshToken(refreshToken);
          setTokens(tokens);
          const userData = await AuthAPI.getCurrentUser(tokens.access_token);
          setUser(userData);
          setLegacyUserState(userData);
        } catch {
          clearTokens();
          setUser(null);
        }
      } else {
        clearTokens();
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const cached = localStorage.getItem(USER_KEY);
    if (cached) {
      try { setUser(JSON.parse(cached)); } catch {}
    }
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const tokens = await AuthAPI.login({ email, password });
      setTokens(tokens);
      const userData = await AuthAPI.getCurrentUser(tokens.access_token);
      setUser(userData);
      setLegacyUserState(userData);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setLoading(true);
    try {
      const tokens = await AuthAPI.register({ email, password, name });
      setTokens(tokens);
      const userData = await AuthAPI.getCurrentUser(tokens.access_token);
      setUser(userData);
      setLegacyUserState(userData);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthTokens = async (tokens: AuthTokens) => {
    setTokens(tokens);
    const userData = await AuthAPI.getCurrentUser(tokens.access_token);
    setUser(userData);
    setLegacyUserState(userData);
  };

  const googleLogin = async (idToken: string) => {
    setLoading(true);
    try {
      const tokens = await AuthAPI.googleLogin(idToken);
      await handleOAuthTokens(tokens);
    } finally {
      setLoading(false);
    }
  };

  const appleLogin = async (idToken: string, fullName?: string, email?: string) => {
    setLoading(true);
    try {
      const tokens = await AuthAPI.appleLogin(idToken, fullName, email);
      await handleOAuthTokens(tokens);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    const token = getToken();
    if (token) AuthAPI.logout(token).catch(() => {});
    clearTokens();
    setUser(null);
  };

  const updateProfile = async (data: Partial<User>) => {
    const token = getToken();
    if (!token) return;
    const updated = await AuthAPI.updateProfile(token, data);
    const mergedUser = user ? { ...user, ...updated } : updated;
    setUser(mergedUser);
    setLegacyUserState(mergedUser);
  };

  return (
    <AuthContext.Provider value={{
      user, loading, isAuthenticated: !!user,
      login, register, googleLogin, appleLogin, logout, updateProfile, refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY);
