import { useLayoutEffect, useState } from "preact/hooks";
import { SystemStats } from "./SystemStats";

export function StatusBar({ classic = false, dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions, onToggleDashboard, onToggleMetersEnabled, onToggleMetersCollapsed }: {
  classic?: boolean;
  dashboardOpen: boolean;
  metersEnabled: boolean;
  metersCollapsed: boolean;
  onOpenSessions: () => void;
  onToggleDashboard: () => void;
  onToggleMetersEnabled: () => void;
  onToggleMetersCollapsed: () => void;
}) {
  const [model, setModel] = useState("");
  const [connection, setConnection] = useState({ message: "Connecting…", state: "connecting" });
  useLayoutEffect(() => {
    const receive = (event: Event) => setConnection((event as CustomEvent<{ message: string; state: string }>).detail);
    window.addEventListener("tau:connection-state", receive);
    return () => window.removeEventListener("tau:connection-state", receive);
  }, []);
  useLayoutEffect(() => {
    const receive = (event: Event) => setModel((event as CustomEvent<{ model: string }>).detail.model);
    window.addEventListener("tau:status-model", receive);
    return () => window.removeEventListener("tau:status-model", receive);
  }, []);
  if (classic) return <div className="tau-classic-status">
    <span hidden={connection.state === "live"}><span className="compose-connection-status">
      <span id="status-stream" data-state={connection.state}>{connection.message}</span>
    </span></span>
    <span id="status-model" className="compose-model-hint">{model || "Unset"}</span>
    <span id="status-context" className="sr-only">No context loaded</span>
    <button id="dashboard-toggle" className="icon-btn" type="button" aria-label="Dashboard" aria-controls="session-dashboard" aria-expanded={dashboardOpen} onClick={onToggleDashboard}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" /></svg>
      <span id="dashboard-count" className="sr-only">0</span>
    </button>
  </div>;
  return (
    <footer className="app-layout__status-bar" role="banner" aria-label="Tau status bar">
      <span className="status-bar__conn">
        <span className={`status-bar__conn-dot status-bar__conn-dot--${connection.state === "live" ? "connected" : "disconnected"}`} aria-hidden="true" />
        <span id="status-stream" className="status-bar__conn-text" data-state={connection.state}>{connection.message}</span>
      </span>

      <span className="session-pill-wrap">
        <button className="session-pill" type="button" title="Open sessions" onClick={onOpenSessions}>
          <span className="session-pill__dot session-pill__dot--current" aria-hidden="true" />
          <span id="status-session" className="session-pill__label">No session selected</span>
        </button>
      </span>

      <span className="model-badge-wrapper">
        <span id="status-model" className={`model-badge${model ? "" : " model-badge--empty"}`}>
          {model ? <span className="model-badge__name-wrapper"><span className="model-badge__provider">{model.includes("/") ? model.slice(0, model.lastIndexOf("/") + 1) : ""}</span><span className="model-badge__name">{model.split("/").pop()}</span></span> : <span className="model-badge__empty">Unset</span>}
        </span>
        <span id="status-context" className="usage-badge">No context loaded</span>
      </span>

      <span className="status-bar__right">
        <SystemStats enabled={metersEnabled} collapsed={metersCollapsed} onToggleEnabled={onToggleMetersEnabled} onToggleCollapsed={onToggleMetersCollapsed} />
        <button id="dashboard-toggle" className="status-bar__terminal-btn" type="button" aria-controls="session-dashboard" aria-expanded={dashboardOpen} title="Toggle dashboard (`)" onClick={onToggleDashboard}>
          <i className="codicon codicon-dashboard" aria-hidden="true" />
          <span id="dashboard-count">0</span>
        </button>
      </span>
    </footer>
  );
}
