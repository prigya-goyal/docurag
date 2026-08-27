import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "../types";
import { authApi } from "../api/endpoints";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("docurag_token");
    const cachedUser = localStorage.getItem("docurag_user");
    if (token && cachedUser) {
      setUser(JSON.parse(cachedUser));
      authApi
        .me()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem("docurag_user", JSON.stringify(res.data));
        })
        .catch(() => {
          localStorage.removeItem("docurag_token");
          localStorage.removeItem("docurag_user");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const persist = (token: string, user: User) => {
    localStorage.setItem("docurag_token", token);
    localStorage.setItem("docurag_user", JSON.stringify(user));
    setUser(user);
  };

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    persist(res.data.access_token, res.data.user);
  };

  const register = async (email: string, fullName: string, password: string) => {
    const res = await authApi.register({ email, full_name: fullName, password });
    persist(res.data.access_token, res.data.user);
  };

  const logout = () => {
    localStorage.removeItem("docurag_token");
    localStorage.removeItem("docurag_user");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
