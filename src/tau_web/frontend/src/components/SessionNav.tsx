import type { SessionFilter } from "../hooks/useSessionFilter";

export function SessionNav({ filter, onSelectFilter, onClose }: {
  filter: SessionFilter;
  onSelectFilter: (filter: SessionFilter) => void;
  onClose: () => void;
}) {
  return (
    <aside id="session-nav" className="sidebar panel-nav" aria-label="Session navigation">
      <header className="sidebar__header">
        <div><h2 className="sidebar__title">Sessions</h2><p className="muted">Persisted chats, archive, and restore.</p></div>
        <button id="close-nav-drawer" className="icon-button mobile-only" type="button" aria-label="Close sessions drawer" onClick={onClose}>Close</button>
      </header>
      <div className="sidebar__content">
      <div className="button-row button-row-wrap" role="group" aria-label="Session actions">
        <button id="new-session-button" type="button">New</button>
        <button id="archive-session-button" type="button">Archive</button>
        <button id="restore-session-button" type="button">Restore</button>
      </div>
      <div className="button-row" role="group" aria-label="Session list filter">
        <button id="show-active-sessions" type="button" aria-pressed={filter === "active"} onClick={() => onSelectFilter("active")}>Active</button>
        <button id="show-archived-sessions" type="button" aria-pressed={filter === "archived"} onClick={() => onSelectFilter("archived")}>Archived</button>
      </div>
      <p id="session-count" className="muted small-text">0 sessions</p>
      <ul id="session-list" className="session-list" aria-label="Available sessions" />
      </div>
    </aside>
  );
}
