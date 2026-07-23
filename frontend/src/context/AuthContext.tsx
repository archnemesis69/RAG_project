import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { loginAccount, registerAccount, setAuthToken } from "../api/client";

interface AuthState {
  token: string | null;
  email: string | null;
}

interface AuthContextValue extends AuthState {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const STORAGE_KEY = "rag-assistant-auth";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): AuthState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return { token: null, email: null };
  try {
    return JSON.parse(raw) as AuthState;
  } catch {
    return { token: null, email: null };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(readStoredAuth);

  useEffect(() => {
    setAuthToken(state.token);
    if (state.token) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [state]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isAuthenticated: Boolean(state.token),
      login: async (email, password) => {
        const res = await loginAccount(email, password);
        setState({ token: res.token, email: res.email });
      },
      register: async (email, password) => {
        const res = await registerAccount(email, password);
        setState({ token: res.token, email: res.email });
      },
      logout: () => setState({ token: null, email: null }),
    }),
    [state],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
