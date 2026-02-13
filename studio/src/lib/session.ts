/**
 * Session utilities for per-tab session management.
 * Each browser tab gets its own unique session ID.
 */

// Session ID key in sessionStorage (sessionStorage is already per-tab)
const SESSION_ID_KEY = "studio-session-id";

/**
 * Generate a UUID v4
 */
export function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get or create a session ID for this browser tab.
 * Uses sessionStorage which is automatically scoped per tab.
 */
export function getSessionId(): string {
  if (typeof window === "undefined") {
    return "server-side";
  }

  let sessionId = sessionStorage.getItem(SESSION_ID_KEY);

  if (!sessionId) {
    sessionId = generateUUID();
    sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Get a session-scoped storage key.
 * This prefixes the key with the session ID for isolation.
 */
export function getSessionKey(key: string, sessionId?: string): string {
  const id = sessionId || getSessionId();
  return `studio-session-${id}-${key}`;
}

/**
 * Store a value in session-scoped storage.
 * Uses sessionStorage for per-tab isolation.
 */
export function setSessionValue<T>(key: string, value: T, sessionId?: string): void {
  if (typeof window === "undefined") return;

  const fullKey = getSessionKey(key, sessionId);
  sessionStorage.setItem(fullKey, JSON.stringify(value));
}

/**
 * Get a value from session-scoped storage.
 */
export function getSessionValue<T>(key: string, defaultValue: T, sessionId?: string): T {
  if (typeof window === "undefined") return defaultValue;

  const fullKey = getSessionKey(key, sessionId);
  const stored = sessionStorage.getItem(fullKey);

  if (stored) {
    try {
      return JSON.parse(stored) as T;
    } catch {
      return defaultValue;
    }
  }

  return defaultValue;
}

/**
 * Remove a value from session-scoped storage.
 */
export function removeSessionValue(key: string, sessionId?: string): void {
  if (typeof window === "undefined") return;

  const fullKey = getSessionKey(key, sessionId);
  sessionStorage.removeItem(fullKey);
}

/**
 * Clear all session-scoped storage for this session.
 */
export function clearSession(sessionId?: string): void {
  if (typeof window === "undefined") return;

  const id = sessionId || getSessionId();
  const prefix = `studio-session-${id}-`;

  const keysToRemove: string[] = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && key.startsWith(prefix)) {
      keysToRemove.push(key);
    }
  }

  keysToRemove.forEach((key) => sessionStorage.removeItem(key));
}

/**
 * Get session info for debugging/display
 */
export function getSessionInfo(): { id: string; createdAt: string } {
  const sessionId = getSessionId();
  const createdAt = getSessionValue<string>("created-at", "");

  if (!createdAt) {
    const now = new Date().toISOString();
    setSessionValue("created-at", now);
    return { id: sessionId, createdAt: now };
  }

  return { id: sessionId, createdAt };
}
