"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, AuthState } from "./api";
import { toast } from "sonner";

interface AuthContextType {
  authenticated: boolean;
  username: string | null;
  state: AuthState;
  verificationUrl: string | null;
  loading: boolean;
  login: (
    username: string,
    password: string,
    remember: boolean
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [state, setState] = useState<AuthState>("Logged Out");
  const [verificationUrl, setVerificationUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchStatus = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const status = await api.authStatus();
      setAuthenticated(status.authenticated);
      setUsername(status.username);
      setState(status.state);
      setVerificationUrl(status.verification_url);
    } catch (err) {
      console.error("Failed to fetch auth status:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Avoid synchronous state changes inside the effect by deferring the call
    const timer = setTimeout(() => {
      fetchStatus(false);
    }, 0);
    const interval = setInterval(() => {
      fetchStatus(false);
    }, 5000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [fetchStatus]);



  const login = async (
    username: string,
    password: string,
    remember: boolean
  ) => {
    try {
      setState("Authenticating");
      const res = await api.login({ username, password, remember });
      if (res.status === "success") {
        toast.success("Successfully logged in");
        setAuthenticated(true);
        setUsername(username);
        setState("Authenticated");
        router.push("/");
      } else if (res.status === "verification_required") {
        toast.info("Multi-factor/biometric verification required");
        setState("Waiting for Biometric Verification");
        if (res.verification_url) {
          setVerificationUrl(res.verification_url);
          window.open(res.verification_url, "_blank");
        }
      } else {
        toast.error(res.message || "Failed to log in");
        setState("Logged Out");
        setAuthenticated(false);
        setUsername(null);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An authentication error occurred";
      toast.error(message);
      setState("Logged Out");
      setAuthenticated(false);
      setUsername(null);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
      setAuthenticated(false);
      setUsername(null);
      setState("Logged Out");
      setVerificationUrl(null);
      toast.success("Successfully logged out");
      router.replace("/login");
    } catch {
      toast.error("Logout failed");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        authenticated,
        username,
        state,
        verificationUrl,
        loading,
        login,
        logout,
      }}
    >
      {loading ? (
        <div className="flex h-screen w-screen items-center justify-center bg-[#0a0e1a] text-foreground">
          <div className="flex flex-col items-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
            <p className="text-sm font-medium text-slate-400">
              Checking authentication status...
            </p>
          </div>
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
