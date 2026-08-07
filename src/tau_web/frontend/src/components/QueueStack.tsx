import { useCallback, useLayoutEffect, useMemo, useState } from "preact/hooks";
import { TauApi } from "../api/tau";
import type { QueueItem, QueueKind, RunRecord } from "../api/types";

const api = new TauApi();
const ACTIVE_RUN_STATUSES = new Set(["pending", "running"]);

type QueueState = {
  sessionId: string | null;
  items: QueueItem[];
  activeRun: RunRecord | null;
};

function queueText(content: QueueItem["content"]): string {
  if (typeof content === "string") return content;
  try {
    return JSON.stringify(content);
  } catch {
    return String(content);
  }
}

function findActiveRun(runs: RunRecord[]): RunRecord | null {
  return runs.find((run) => ACTIVE_RUN_STATUSES.has(run.status)) ?? null;
}

export function QueueStack() {
  const [state, setState] = useState<QueueState>({ sessionId: null, items: [], activeRun: null });
  const [busyKind, setBusyKind] = useState<QueueKind | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async (sessionId: string | null) => {
    if (!sessionId) {
      setState({ sessionId: null, items: [], activeRun: null });
      return;
    }
    try {
      const [items, runs] = await Promise.all([api.queue(sessionId), api.runs(sessionId)]);
      setState({ sessionId, items, activeRun: findActiveRun(runs) });
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load queued messages.");
    }
  }, []);

  useLayoutEffect(() => {
    window.dispatchEvent(new CustomEvent("tau:active-run", { detail: { run: state.activeRun } }));
  }, [state.activeRun]);

  useLayoutEffect(() => {
    const selected = (event: Event) => {
      const sessionId = (event as CustomEvent<{ sessionId?: string | null }>).detail?.sessionId ?? null;
      setState({ sessionId, items: [], activeRun: null });
      void refresh(sessionId);
    };
    const changed = () => void refresh(state.sessionId);
    window.addEventListener("tau:session-selected", selected);
    window.addEventListener("tau:queue-changed", changed);
    return () => {
      window.removeEventListener("tau:session-selected", selected);
      window.removeEventListener("tau:queue-changed", changed);
    };
  }, [refresh, state.sessionId]);

  const items = useMemo(
    () => [...state.items].sort((left, right) =>
      left.queue_kind.localeCompare(right.queue_kind) || left.position - right.position),
    [state.items],
  );

  const dispatch = useCallback(async (kind: QueueKind) => {
    if (!state.activeRun) return;
    setBusyKind(kind);
    try {
      await api.dispatchNext(state.activeRun.run_id, kind);
      await refresh(state.sessionId);
      window.dispatchEvent(new CustomEvent("tau:queue-dispatched", { detail: { kind } }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to dispatch queued message.");
    } finally {
      setBusyKind(null);
    }
  }, [refresh, state.activeRun, state.sessionId]);

  const copyToComposer = useCallback((item: QueueItem) => {
    const input = document.getElementById("compose-input") as HTMLTextAreaElement | null;
    if (!input) return;
    input.value = queueText(item.content);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.focus();
  }, []);

  if (items.length === 0 && !error) return null;

  const firstByKind = new Map<QueueKind, string>();
  for (const item of items) {
    if (!firstByKind.has(item.queue_kind)) firstByKind.set(item.queue_kind, item.queue_id);
  }

  return (
    <div className="queue-stack" aria-label="Queued messages">
      {error && <div className="queue-stack__error" role="status">{error}</div>}
      {items.map((item) => {
        const text = queueText(item.content);
        const isHead = firstByKind.get(item.queue_kind) === item.queue_id;
        return (
          <div key={item.queue_id} className="queue-stack__item">
            <div className="queue-stack__content" title={text}>
              <span className="queue-stack__kind">{item.queue_kind === "follow_up" ? "Follow-up" : "Steer"}</span>
              {text.length > 80 ? `${text.slice(0, 80)}\u2026` : text}
            </div>
            <div className="queue-stack__actions">
              <button type="button" className="queue-stack__btn queue-stack__btn--edit" onClick={() => copyToComposer(item)} title="Copy to compose" aria-label="Copy queued message to compose">
                <i className="codicon codicon-edit" aria-hidden="true" />
              </button>
              {isHead && (
                <button type="button" className="queue-stack__btn queue-stack__btn--steer" disabled={!state.activeRun || busyKind === item.queue_kind} onClick={() => void dispatch(item.queue_kind)} title={state.activeRun ? `Dispatch next ${item.queue_kind === "follow_up" ? "follow-up" : "steer"}` : "A pending or running run is required"}>
                  ↵ Dispatch
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
