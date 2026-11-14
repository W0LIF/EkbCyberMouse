import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

interface AuthContextValue {
  logged: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [logged, setLogged] = useState(false);

  const login = useCallback(() => {
    setLogged(true);
  }, []);

  const logout = useCallback(() => {
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
