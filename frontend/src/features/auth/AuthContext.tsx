import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";

interface AuthContextValue {
  logged: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "rtk-auth";

function getInitialAuth(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY) === "1";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [logged, setLogged] = useState(getInitialAuth);

  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setLogged(e.newValue === "1");
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  const login = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, "1");
    setLogged(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setLogged(false);
  }, []);

  return (
    <AuthContext.Provider value={{ logged, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
