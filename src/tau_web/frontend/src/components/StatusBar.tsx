const Meter = ({ id, label, icon }: { id: string; label: string; icon: string }) => (
  <span className="sys-stats__metric" title={`${label} usage`}>
    <i className={`sys-stats__icon codicon ${icon}`} aria-hidden="true" />
    <span className="sys-stats__label">{label}</span>
    <output id={`meter-${id}-value`} className="sys-stats__value">--</output>
    <svg id={`meter-${id}-sparkline`} className="sys-stats__sparkline" role="img" aria-label={`${label === "RSS" ? "Tau RSS" : label} history`} />
  </span>
);

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
        <span id="system-meters" className="sys-stats-bar" data-enabled={String(metersEnabled)} data-collapsed={String(metersCollapsed)}>
          <span className="sys-stats-bar__inline">
            <span id="meters-details" className="sys-stats">
              <Meter id="cpu" label="CPU" icon="codicon-pulse" />
              <Meter id="ram" label="RAM" icon="codicon-circuit-board" />
              <Meter id="rss" label="RSS" icon="codicon-package" />
              <Meter id="swap" label="SWP" icon="codicon-arrow-swap" />
            </span>
          </span>
          <output id="meters-summary" className="sys-stats-bar__compact" aria-live="polite">Meters loading…</output>
          <button id="meters-collapse-button" className="status-bar__terminal-btn" type="button" aria-controls="meters-details" aria-expanded={!metersCollapsed} title={metersCollapsed ? "Expand system meters" : "Compact system meters"} onClick={onToggleMetersCollapsed}>
            <i className={`codicon ${metersCollapsed ? "codicon-chevron-up" : "codicon-chevron-down"}`} aria-hidden="true" />
          </button>
          <button id="meters-visibility-button" className="status-bar__terminal-btn" type="button" aria-pressed={metersEnabled} title={metersEnabled ? "Hide system meters" : "Show system meters"} onClick={onToggleMetersEnabled}>
            <i className={`codicon ${metersEnabled ? "codicon-eye" : "codicon-eye-closed"}`} aria-hidden="true" />
          </button>
        </span>
        <button id="dashboard-toggle" className="status-bar__terminal-btn" type="button" aria-controls="session-dashboard" aria-expanded={dashboardOpen} title="Toggle dashboard (`)" onClick={onToggleDashboard}>
          <i className="codicon codicon-dashboard" aria-hidden="true" />
          <span id="dashboard-count">0</span>
        </button>
      </span>
    </footer>
  );
}
