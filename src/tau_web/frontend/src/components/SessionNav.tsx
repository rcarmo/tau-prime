export function SessionNav({ onClose }: { onClose: () => void }) {
  return (
    <aside id="session-nav" className="panel panel-nav" aria-label="Session navigation">
      <div className="panel-header sticky-header">
        <div><h2>Sessions</h2><p className="muted">Persisted chats, archive, and restore.</p></div>
        <button id="close-nav-drawer" className="icon-button mobile-only" type="button" aria-label="Close sessions drawer" onClick={onClose}>Close</button>
      </div>
      <div className="button-row button-row-wrap" role="group" aria-label="Session actions">
        <button id="new-session-button" type="button">New</button>
        <button id="archive-session-button" type="button">Archive</button>
        <button id="restore-session-button" type="button">Restore</button>
      </div>
      <div className="button-row" role="group" aria-label="Session list filter">
        <button id="show-active-sessions" type="button" aria-pressed="true">Active</button>
        <button id="show-archived-sessions" type="button" aria-pressed="false">Archived</button>
      </div>
      <p id="session-count" className="muted small-text">0 sessions</p>
      <ul id="session-list" className="session-list" aria-label="Available sessions" />
    </aside>
  );
}
