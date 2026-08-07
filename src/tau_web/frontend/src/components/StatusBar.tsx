import { SystemStats } from "./SystemStats";

export function StatusBar({ dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions, onToggleDashboard, onToggleMetersEnabled, onToggleMetersCollapsed }: {
  dashboardOpen: boolean;
  metersEnabled: boolean;
  metersCollapsed: boolean;
  onOpenSessions: () => void;
  onToggleDashboard: () => void;
  onToggleMetersEnabled: () => void;
  onToggleMetersCollapsed: () => void;
}) {
  return (
    <footer className="app-layout__status-bar" role="banner" aria-label="Tau status bar">
      <span className="status-bar__conn">
        <span className="status-bar__conn-dot status-bar__conn-dot--disconnected" aria-hidden="true" />
        <span id="status-stream" className="status-bar__conn-text">Connecting…</span>
      </span>

      <span className="session-pill-wrap">
        <button className="session-pill" type="button" title="Open sessions" onClick={onOpenSessions}>
          <span className="session-pill__dot session-pill__dot--current" aria-hidden="true" />
          <span id="status-session" className="session-pill__label">No session selected</span>
        </button>
      </span>

      <span className="model-badge-wrapper">
        <span id="status-model" className="model-badge model-badge--empty">Unset</span>
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
