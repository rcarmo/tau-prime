const Meter = ({ id, label }: { id: string; label: string }) => (
  <figure className="meter-tile">
    <figcaption>{label} <output id={`meter-${id}-value`}>--</output></figcaption>
    <svg id={`meter-${id}-sparkline`} role="img" aria-label={`${label === "RSS" ? "Tau RSS" : label} history`} />
  </figure>
);

export function StatusBar() {
  return (
    <header className="topbar" aria-label="Tau status bar">
      <div className="topbar-group topbar-branding">
        <button id="mobile-nav-toggle" className="icon-button mobile-only" type="button" aria-controls="session-nav" aria-expanded="false" aria-label="Open sessions drawer">Sessions</button>
        <div className="brand-block"><h1>Tau</h1><p id="status-stream" className="muted">Connecting…</p></div>
      </div>
      <dl className="status-grid" aria-label="Current Tau status">
        <div><dt>Session</dt><dd id="status-session">No session selected</dd></div>
        <div><dt>Model</dt><dd id="status-model">Unset</dd></div>
        <div><dt>Context</dt><dd id="status-context">No context loaded</dd></div>
      </dl>
      <div className="topbar-group topbar-dashboard-control">
        <button id="dashboard-toggle" className="dashboard-toggle" type="button" aria-controls="session-dashboard" aria-expanded="false" title="Toggle dashboard (`)">Dashboard <span id="dashboard-count" className="dashboard-count">0</span></button>
      </div>
      <div className="topbar-group topbar-actions">
        <section id="system-meters" className="system-meters" aria-label="System meters" data-enabled="true" data-collapsed="true">
          <div className="meters-toolbar">
            <output id="meters-summary" className="meters-summary" aria-live="polite">Meters loading…</output>
            <button id="meters-collapse-button" className="meter-control" type="button" aria-controls="meters-details" aria-expanded="false">Expand</button>
            <button id="meters-visibility-button" className="meter-control" type="button" aria-pressed="true">Hide</button>
          </div>
          <div id="meters-details" className="meters-details">
            <Meter id="cpu" label="CPU" /><Meter id="ram" label="RAM" /><Meter id="rss" label="RSS" /><Meter id="swap" label="Swap" />
          </div>
        </section>
        <button id="mobile-panel-toggle" className="icon-button mobile-only" type="button" aria-controls="side-panel" aria-expanded="false" aria-label="Open workspace and settings drawer">Panels</button>
      </div>
    </header>
  );
}
