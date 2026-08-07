export function Dashboard({ open, onClose }: { open: boolean; onClose: () => void }) {
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
        <div id="dashboard-grid" className="session-dashboard__grid" role="list" aria-live="polite" aria-busy="false" />
        <footer className="session-dashboard__footer">
          <p id="dashboard-age" className="modal-dialog__description">Not refreshed yet.</p>
          <div className="modal-dialog__actions" role="group" aria-label="Dashboard pages">
            <button id="dashboard-previous" className="modal-dialog__btn" type="button">Previous</button>
            <output id="dashboard-page">Page 1 of 1</output>
            <button id="dashboard-next" className="modal-dialog__btn" type="button">Next</button>
            <button id="dashboard-manage" className="modal-dialog__btn modal-dialog__btn--primary" type="button">All sessions</button>
          </div>
        </footer>
      </section>
    </div>
  );
}
