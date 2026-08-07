import { useEffect } from "preact/hooks";
import type { TauApi } from "../api/tau";

export type SessionEvent = { type?: string; [key: string]: unknown };

export function useSessionEvents(
  api: TauApi,
  sessionId: string | null,
  onEvent: (event: SessionEvent) => void,
  onError?: (error: Event) => void,
): void {
  useEffect(() => {
    if (!sessionId) return;
    const source = new EventSource(api.eventUrl(sessionId), { withCredentials: true });
    source.onmessage = (message) => {
      try {
        onEvent(JSON.parse(message.data) as SessionEvent);
      } catch {
        onEvent({ type: "message", data: message.data });
      }
    };
    if (onError) source.onerror = onError;
    return () => source.close();
  }, [api, sessionId, onEvent, onError]);
}
