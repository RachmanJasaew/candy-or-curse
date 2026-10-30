/**
 * QR Session Synchronization Hook (Developer A2)
 * Polls `GET /api/sessions/{id}` on desktop so mobile camera scans appear live.
 */
import { useCallback, useEffect, useState } from "react";
import { createSession, getSession } from "../api/client";
import { CreateSessionRequest, SessionResponse } from "../types/api";

export function useSessionSync(initialSessionId?: string, pollIntervalMs = 2500) {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const initOrFetch = useCallback(async (id?: string, createReq?: CreateSessionRequest) => {
    setLoading(true);
    setError(null);
    try {
      const data = id ? await getSession(id) : await createSession(createReq);
      setSession(data);
      return data;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to sync session";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void initOrFetch(initialSessionId);
  }, [initialSessionId, initOrFetch]);

  useEffect(() => {
    if (!session?.session_id || pollIntervalMs <= 0) return;
    const timer = window.setInterval(async () => {
      try {
        const updated = await getSession(session.session_id);
        setSession(updated);
      } catch {
        // Keep existing state on transient network hiccup
      }
    }, pollIntervalMs);
    return () => window.clearInterval(timer);
  }, [session?.session_id, pollIntervalMs]);

  return {
    session,
    setSession,
    loading,
    error,
    refreshSession: () => (session ? initOrFetch(session.session_id) : Promise.resolve(null)),
  };
}
