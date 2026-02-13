"use client";

import * as React from "react";
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  getSessionId,
  getSessionValue,
  setSessionValue,
  clearSession,
  getSessionInfo,
} from "@/lib/session";

interface SessionContextType {
  sessionId: string;
  isReady: boolean;
  getSessionValue: <T>(key: string, defaultValue: T) => T;
  setSessionValue: <T>(key: string, value: T) => void;
  clearSession: () => void;
  sessionInfo: { id: string; createdAt: string };
}

const SessionContext = createContext<SessionContextType | null>(null);

interface SessionProviderProps {
  children: React.ReactNode;
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [sessionId, setSessionId] = useState<string>("");
  const [isReady, setIsReady] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<{ id: string; createdAt: string }>({
    id: "",
    createdAt: "",
  });

  // Initialize session on mount (client-side only)
  useEffect(() => {
    const id = getSessionId();
    const info = getSessionInfo();
    setSessionId(id);
    setSessionInfo(info);
    setIsReady(true);

    // Log session info for debugging
    console.log(`[Session] Initialized session: ${id.substring(0, 8)}...`);
  }, []);

  const getValue = useCallback(
    <T,>(key: string, defaultValue: T): T => {
      return getSessionValue(key, defaultValue, sessionId);
    },
    [sessionId]
  );

  const setValue = useCallback(
    <T,>(key: string, value: T): void => {
      setSessionValue(key, value, sessionId);
    },
    [sessionId]
  );

  const clear = useCallback(() => {
    clearSession(sessionId);
  }, [sessionId]);

  const contextValue: SessionContextType = {
    sessionId,
    isReady,
    getSessionValue: getValue,
    setSessionValue: setValue,
    clearSession: clear,
    sessionInfo,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
}

// Default session context for SSR or when provider is not available
const defaultSessionContext: SessionContextType = {
  sessionId: "",
  isReady: false,
  getSessionValue: <T,>(_key: string, defaultValue: T): T => defaultValue,
  setSessionValue: <T,>(_key: string, _value: T): void => {},
  clearSession: () => {},
  sessionInfo: { id: "", createdAt: "" },
};

export function useSession(): SessionContextType {
  const context = useContext(SessionContext);
  // Return default context during SSR or if provider is missing
  // This prevents errors and allows graceful degradation
  return context || defaultSessionContext;
}

// Hook to get just the session ID (commonly needed)
export function useSessionId(): string {
  const { sessionId } = useSession();
  return sessionId;
}
