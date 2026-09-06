export function ClassicSessionControl({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return <div className="compose-session-trigger-group compose-session-trigger-top">
    <button type="button" className="compose-session-trigger compose-session-trigger-pill" aria-label="Open sessions" aria-expanded={open} aria-controls="panel-sessions" onClick={onToggle}>
      <span id="status-session" className="compose-current-agent-label active">No session selected</span>
    </button>
  </div>;
}
