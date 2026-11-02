import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../services/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isOrganizer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Charger l'utilisateur au démarrage via /auth/me
  useEffect(() => {
    if (token) {
      api.get('/auth/me')
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });

    // Gérer la 2FA
    if (res.data.requires_2fa) {
      throw new Error('2FA_REQUIRED');
    }

    localStorage.setItem('token', res.data.access_token);
    setToken(res.data.access_token);

    // Charger le profil via /auth/me (et non /users)
    const userRes = await api.get('/auth/me');
    setUser(userRes.data);
  };

  const register = async (data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) => {
    await api.post('/auth/register', data);
    await login(data.email, data.password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === 'super_admin';
  const isOrganizer = user !== null;

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout, isAdmin, isOrganizer }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};