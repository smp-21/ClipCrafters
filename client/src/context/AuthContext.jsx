import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/index.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cc_user') || 'null'); } catch { return null; }
  });
  const [loading, setLoading] = useState(true);

  // Rehydrate on mount
  useEffect(() => {
    const token = localStorage.getItem('cc_token');
    if (!token) { setLoading(false); return; }
    authService.getMe()
      .then((res) => {
        setUser(res.data.data);
        localStorage.setItem('cc_user', JSON.stringify(res.data.data));
      })
      .catch(() => {
        localStorage.removeItem('cc_token');
        localStorage.removeItem('cc_user');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback((token, userData) => {
    localStorage.setItem('cc_token', token);
    localStorage.setItem('cc_user', JSON.stringify(userData));
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('cc_token');
    localStorage.removeItem('cc_user');
    setUser(null);
  }, []);

  const updateUser = useCallback((data) => {
    const updated = { ...user, ...data };
    localStorage.setItem('cc_user', JSON.stringify(updated));
    setUser(updated);
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateUser, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
