import { Fragment } from "preact";

export function Timeline() {
  return (
    <Fragment>
      <div className="extension-slot" data-extension-slot="timeline_before" />
      <div id="timeline-main" className="message-list" tabIndex={-1}>
        <div id="timeline-meta" className="message-list__status-banner" aria-live="polite">Load a session to inspect persisted messages.</div>
        <ol id="timeline-list" className="timeline-list message-list__items" aria-live="polite" tabIndex={0} />
      </div>
      <div className="extension-slot" data-extension-slot="timeline_after" />
    </Fragment>
  );
}

/** Tau branch selection mapped to Piclaw's between-timeline-and-compose status surface. */
export function SessionRuntime() {
  return (
    <div className="agent-status-panel" aria-label="Session runtime">
      <div className="agent-status-panel__status" aria-live="polite">
        <span id="agent-status-indicator" className="agent-status-panel__status-dot" aria-hidden="true" />
        <span id="agent-status-text" className="agent-status-panel__status-text">No session selected</span>
      </div>
      <section className="agent-status-panel__section">
        <div className="agent-status-panel__title">Session branch</div>
        <div id="branch-list" className="agent-status-panel__tools" />
      </section>
    </div>
  );
}
