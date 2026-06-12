/**
 * Authentication context — manages JWT lifecycle and protected routes.
 *
 * Stores the token in localStorage for persistence across refreshes.
 * Decodes the JWT payload to extract user info without extra API calls.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, ApiRequestError } from "./api";
import type { TokenResponse } from "../types/api";

interface AuthUser {
  userId: string;
  email: string;
  organizationId: string;
  role: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function extractUserFromToken(token: string): AuthUser | null {
  const payload = decodeTokenPayload(token);
  if (!payload || !payload.sub || !payload.org) return null;

  return {
    userId: payload.sub as string,
    email: "", // Not in JWT; would need a /me endpoint or stored locally
    organizationId: payload.org as string,
    role: (payload.role as string) || "viewer",
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session from stored token on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      const decoded = extractUserFromToken(token);
      if (decoded) {
        // Check if token is expired
        const payload = decodeTokenPayload(token);
        const exp = payload?.exp as number | undefined;
        if (exp && exp * 1000 > Date.now()) {
          setUser(decoded);
        } else {
          localStorage.removeItem("access_token");
        }
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<TokenResponse>("/api/v1/auth/login", {
        email,
        password,
      });
      const { access_token } = response.data;
      localStorage.setItem("access_token", access_token);

      const decoded = extractUserFromToken(access_token);
      if (decoded) {
        decoded.email = email;
        setUser(decoded);
      }
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : "Giriş başarısız. Lütfen tekrar deneyin.";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        isLoading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/**
 * Route guard — redirects unauthenticated users to the login page.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin h-8 w-8 rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
