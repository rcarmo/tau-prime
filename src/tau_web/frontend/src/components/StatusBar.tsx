const Meter = ({ id, label }: { id: string; label: string }) => (
  <figure className="meter-tile">
    <figcaption>{label} <output id={`meter-${id}-value`}>--</output></figcaption>
    <svg id={`meter-${id}-sparkline`} role="img" aria-label={`${label === "RSS" ? "Tau RSS" : label} history`} />
  </figure>
);

export function StatusBar({ dashboardOpen, metersEnabled, metersCollapsed, onToggleDashboard, onToggleMetersEnabled, onToggleMetersCollapsed }: {
  dashboardOpen: boolean;
  metersEnabled: boolean;
  metersCollapsed: boolean;
  onToggleDashboard: () => void;
  onToggleMetersEnabled: () => void;
  onToggleMetersCollapsed: () => void;
}) {
  return (
    <footer className="app-layout__status-bar" role="banner" aria-label="Tau status bar">
      <div className="status-bar__conn">
        <span className="status-bar__conn-dot status-bar__conn-dot--disconnected" aria-hidden="true" />
        <div className="brand-block"><h1 className="sr-only">Tau</h1><p id="status-stream" className="status-bar__conn-text">Connecting…</p></div>
      </div>
      <dl className="status-grid model-badge-wrapper" aria-label="Current Tau status">
        <div><dt>Session</dt><dd id="status-session">No session selected</dd></div>
        <div><dt>Model</dt><dd id="status-model">Unset</dd></div>
        <div><dt>Context</dt><dd id="status-context">No context loaded</dd></div>
      </dl>
      <div className="topbar-group topbar-dashboard-control">
        <button id="dashboard-toggle" className="dashboard-toggle" type="button" aria-controls="session-dashboard" aria-expanded={dashboardOpen} title="Toggle dashboard (`)" onClick={onToggleDashboard}>Dashboard <span id="dashboard-count" className="dashboard-count">0</span></button>
      </div>
      <div className="status-bar__right">
        <section id="system-meters" className="system-meters" aria-label="System meters" data-enabled={String(metersEnabled)} data-collapsed={String(metersCollapsed)}>
          <div className="meters-toolbar">
            <output id="meters-summary" className="meters-summary" aria-live="polite">Meters loading…</output>
            <button id="meters-collapse-button" className="meter-control" type="button" aria-controls="meters-details" aria-expanded={!metersCollapsed} onClick={onToggleMetersCollapsed}>{metersCollapsed ? "Expand" : "Compact"}</button>
            <button id="meters-visibility-button" className="meter-control" type="button" aria-pressed={metersEnabled} onClick={onToggleMetersEnabled}>{metersEnabled ? "Hide" : "Show"}</button>
          </div>
          <div id="meters-details" className="meters-details">
            <Meter id="cpu" label="CPU" /><Meter id="ram" label="RAM" /><Meter id="rss" label="RSS" /><Meter id="swap" label="Swap" />
          </div>
        </section>
      </div>
    </footer>
  );
}
