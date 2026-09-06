export function ClassicSessionControl({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return <div className="compose-session-switcher-trigger-wrap">
    <button type="button" className="compose-session-switcher-pill" aria-label="Open sessions" aria-expanded={open} aria-controls="panel-sessions" onClick={onToggle}>
      <span id="status-session" className="compose-session-switcher-pill-label">No session selected</span>
      <span className="compose-session-switcher-pill-chevron" aria-hidden="true">▾</span>
    </button>
  </div>;
}
