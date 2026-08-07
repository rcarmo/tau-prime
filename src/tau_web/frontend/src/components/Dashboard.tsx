import { useEffect, useLayoutEffect, useState } from "preact/hooks";

type DashboardSession = {
  session_id?: string | null;
  agent_name?: string | null;
  title?: string | null;
  workspace?: string | null;
  model?: string | null;
  preview_kind?: string | null;
  preview?: string | null;
  queue_count?: number | null;
  context_used_tokens?: number | null;
  context_window_tokens?: number | null;
  context_percent?: number | null;
  activity_state?: string | null;
  has_error?: boolean | null;
  last_activity?: string | null;
};

type DashboardView = {
  sessions: DashboardSession[];
  page: number;
  totalPages: number;
  generatedAt: string | null;
  loading: boolean;
  selectedSessionId: string | null;
};

const EMPTY_DASHBOARD: DashboardView = {
  sessions: [],
  page: 1,
  totalPages: 1,
  generatedAt: null,
  loading: false,
  selectedSessionId: null,
};

const stringOrEmpty = (value: unknown) => typeof value === "string" ? value : "";
const numberOrZero = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? value : 0;

function shortId(value: unknown) {
  const text = stringOrEmpty(value);
  return text ? text.slice(0, 8) : "unknown";
}

function sentenceCase(value: unknown) {
  const text = stringOrEmpty(value).replace(/_/g, " ").trim();
  return text ? `${text.charAt(0).toUpperCase()}${text.slice(1)}` : "Unknown";
}

function sessionLabel(session: DashboardSession) {
  const title = stringOrEmpty(session.title).trim();
  if (title) return title;
  const agentName = stringOrEmpty(session.agent_name).trim();
  if (agentName) return agentName;
  return shortId(session.session_id);
}

function buildSessionUrl(sessionId: string) {
  const url = new URL(window.location.href);
  if (sessionId) url.searchParams.set("session_id", sessionId);
  else url.searchParams.delete("session_id");
  return `${url.pathname}${url.search}${url.hash}`;
}

function dashboardPreviewKindLabel(value: unknown) {
  switch (value) {
    case "draft":
      return "Draft";
    case "thinking":
      return "Thinking";
    case "tool":
      return "Tool";
    case "summary":
      return "Summary";
    default:
      return "Preview";
  }
}

function dashboardActivityLabel(session: DashboardSession) {
  return sentenceCase(stringOrEmpty(session.activity_state) || "idle");
}

function formatDashboardContextPercent(session: DashboardSession) {
  const value = typeof session.context_percent === "number" && Number.isFinite(session.context_percent)
    ? session.context_percent
    : 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function formatDashboardContext(session: DashboardSession) {
  const used = numberOrZero(session.context_used_tokens).toLocaleString();
  const windowTokens = numberOrZero(session.context_window_tokens).toLocaleString();
  return `${used} / ${windowTokens} · ${formatDashboardContextPercent(session)}%`;
}

function relativeTimeText(value: string | null | undefined, now: number) {
  const date = new Date(value ?? "");
  if (Number.isNaN(date.valueOf())) return "just now";
  const elapsedSeconds = Math.max(0, Math.round((now - date.valueOf()) / 1000));
  if (elapsedSeconds < 5) return "just now";
  if (elapsedSeconds < 60) return `${elapsedSeconds}s ago`;
  const elapsedMinutes = Math.round(elapsedSeconds / 60);
  if (elapsedMinutes < 60) return `${elapsedMinutes}m ago`;
  const elapsedHours = Math.round(elapsedMinutes / 60);
  if (elapsedHours < 24) return `${elapsedHours}h ago`;
  return `${Math.round(elapsedHours / 24)}d ago`;
}

export function Dashboard({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [view, setView] = useState<DashboardView>(EMPTY_DASHBOARD);
  const [now, setNow] = useState(() => Date.now());

  useLayoutEffect(() => {
    const update = (event: Event) => {
      const detail = (event as CustomEvent<Partial<DashboardView>>).detail;
      if (!detail) return;
      setView({
        sessions: Array.isArray(detail.sessions) ? detail.sessions : [],
        page: Number.isInteger(detail.page) && (detail.page as number) > 0 ? detail.page as number : 1,
        totalPages: Number.isInteger(detail.totalPages) && (detail.totalPages as number) > 0 ? detail.totalPages as number : 1,
        generatedAt: stringOrEmpty(detail.generatedAt) || null,
        loading: Boolean(detail.loading),
        selectedSessionId: stringOrEmpty(detail.selectedSessionId) || null,
      });
    };
    window.addEventListener("tau:dashboard-render", update);
    return () => window.removeEventListener("tau:dashboard-render", update);
  }, []);

  useEffect(() => {
    if (!open) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [open, view.generatedAt, view.sessions]);

  const dashboardAge = !view.generatedAt
    ? view.loading ? "Refreshing dashboard…" : "Not refreshed yet."
    : view.loading
      ? `Refreshing… last updated ${relativeTimeText(view.generatedAt, now)}.`
      : `Updated ${relativeTimeText(view.generatedAt, now)}.`;

  const selectSession = (sessionId: string) => {
    window.dispatchEvent(new CustomEvent("tau:session-select", { detail: { sessionId } }));
  };

  return (
    <div
      id="session-dashboard"
      className="modal-dialog__backdrop"
      data-open={String(open)}
      hidden={!open}
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}
    >
      <section
        className="modal-dialog session-dashboard__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dashboard-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="session-dashboard__header">
          <div>
            <h2 id="dashboard-title" className="modal-dialog__title">Session dashboard</h2>
            <p className="modal-dialog__description">Live Tau sessions, queue state, context estimates, and current activity.</p>
          </div>
          <button id="dashboard-close" className="modal-dialog__btn" type="button" onClick={onClose}>Close</button>
        </header>
        <div id="dashboard-grid" className="session-dashboard__grid" role="list" aria-live="polite" aria-busy={view.loading}>
          {!view.sessions.length && <p className="dashboard-empty">{view.loading ? "Loading dashboard sessions…" : "No active sessions."}</p>}
          {view.sessions.map((session) => {
            const sessionId = stringOrEmpty(session.session_id);
            const selected = sessionId !== "" && sessionId === view.selectedSessionId;
            return (
              <article key={sessionId || `${sessionLabel(session)}-${stringOrEmpty(session.last_activity)}`} className="dashboard-tile" data-selected={String(selected)} role="listitem">
                <a
                  href={buildSessionUrl(sessionId)}
                  className="dashboard-tile-button"
                  aria-current={selected ? "page" : "false"}
                  title="Open this session. Ctrl-click or Cmd-click opens it in a new tab."
                  onClick={(event) => {
                    if (!sessionId || event.metaKey || event.ctrlKey) return;
                    event.preventDefault();
                    selectSession(sessionId);
                  }}
                >
                  <div className="dashboard-tile-header">
                    <p className="dashboard-agent">{sessionLabel(session)}</p>
                    <span className="dashboard-state" data-state={stringOrEmpty(session.activity_state) || "idle"} data-error={String(Boolean(session.has_error))}>{dashboardActivityLabel(session)}</span>
                  </div>
                  <p className="dashboard-identity">{[session.agent_name ? `@${session.agent_name}` : null, shortId(session.session_id)].filter(Boolean).join(" · ")}</p>
                  <p className="dashboard-workspace">{stringOrEmpty(session.workspace) || "Workspace unavailable"}</p>
                  <p className="dashboard-model">{stringOrEmpty(session.model) || "Model unavailable"}</p>
                  <p className="dashboard-preview-kind">{dashboardPreviewKindLabel(session.preview_kind)}</p>
                  <p className="dashboard-preview">{stringOrEmpty(session.preview) || "No assistant summary yet."}</p>
                  <div className="dashboard-indicators">
                    <span>{`Queue ${numberOrZero(session.queue_count)}`}</span>
                    <div className="dashboard-context">
                      <span>{`Context ${formatDashboardContext(session)}`}</span>
                      <span className="dashboard-context-track"><span className="dashboard-context-fill" style={{ width: `${formatDashboardContextPercent(session)}%` }} /></span>
                    </div>
                    {session.has_error && <span className="dashboard-error">Error</span>}
                    <p className="dashboard-tile-age">{session.last_activity ? `Activity ${relativeTimeText(session.last_activity, now)}` : "Activity unknown"}</p>
                  </div>
                </a>
              </article>
            );
          })}
        </div>
        <footer className="session-dashboard__footer">
          <p id="dashboard-age" className="modal-dialog__description">{dashboardAge}</p>
          <div className="modal-dialog__actions" role="group" aria-label="Dashboard pages">
            <button id="dashboard-previous" className="modal-dialog__btn" type="button" disabled={view.loading || view.page <= 1} onClick={() => window.dispatchEvent(new CustomEvent("tau:dashboard-page", { detail: { delta: -1 } }))}>Previous</button>
            <output id="dashboard-page">Page {view.page} of {view.totalPages}</output>
            <button id="dashboard-next" className="modal-dialog__btn" type="button" disabled={view.loading || view.page >= view.totalPages} onClick={() => window.dispatchEvent(new CustomEvent("tau:dashboard-page", { detail: { delta: 1 } }))}>Next</button>
            <button id="dashboard-manage" className="modal-dialog__btn modal-dialog__btn--primary" type="button" onClick={() => window.dispatchEvent(new CustomEvent("tau:dashboard-manage"))}>All sessions</button>
          </div>
        </footer>
      </section>
    </div>
  );
}
