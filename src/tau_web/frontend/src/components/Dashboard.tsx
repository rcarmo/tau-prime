export function Dashboard({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <section id="session-dashboard" className="session-dashboard" aria-labelledby="dashboard-title" data-open={String(open)} hidden={!open}>
      <div className="dashboard-shell">
        <header className="dashboard-header">
          <div>
            <h2 id="dashboard-title">Session dashboard</h2>
            <p className="muted small-text">Live Tau sessions, queue state, context estimates, and current activity.</p>
          </div>
          <button id="dashboard-close" className="icon-button" type="button" onClick={onClose}>Close</button>
        </header>
        <div id="dashboard-grid" className="dashboard-grid" role="list" aria-live="polite" aria-busy="false" />
        <footer className="dashboard-footer">
          <p id="dashboard-age" className="muted small-text">Not refreshed yet.</p>
          <div className="dashboard-pagination" role="group" aria-label="Dashboard pages">
            <button id="dashboard-previous" type="button">Previous</button>
            <output id="dashboard-page">Page 1 of 1</output>
            <button id="dashboard-next" type="button">Next</button>
            <button id="dashboard-manage" type="button">All sessions</button>
          </div>
        </footer>
      </div>
    </section>
  );
}
