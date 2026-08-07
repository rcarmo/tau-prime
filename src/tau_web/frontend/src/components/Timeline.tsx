export function Timeline() {
  return (
    <main id="timeline-main" className="panel panel-main" tabIndex={-1}>
      <div className="panel-header sticky-header">
        <div><h2>Timeline</h2><p id="timeline-meta" className="muted">Load a session to inspect persisted messages.</p></div>
      </div>
      <section className="branch-strip" aria-labelledby="branch-strip-title">
        <div className="branch-strip-header"><h3 id="branch-strip-title">Branches</h3><p className="muted small-text">Select the active leaf for restored playback.</p></div>
        <div id="branch-list" className="branch-list" />
      </section>
      <section id="session-overview" className="session-overview" aria-label="Live session overview">
        <div className="extension-slot" data-extension-slot="dashboard" />
        <article className="overview-card" aria-labelledby="context-summary-title">
          <div className="overview-card-header"><div><h3 id="context-summary-title">Context</h3><p className="muted small-text">Session entry, message, and compaction summary.</p></div></div>
          <dl id="context-summary" className="stats-list" />
        </article>
        <article className="overview-card" aria-labelledby="usage-summary-title">
          <div className="overview-card-header"><div><h3 id="usage-summary-title">Usage</h3><p className="muted small-text">Durable token and cost records for this session.</p></div></div>
          <dl id="usage-totals" className="stats-list" />
          <ol id="usage-records" className="compact-list" aria-live="polite" />
        </article>
        <article className="overview-card" aria-labelledby="active-run-title">
          <div className="overview-card-header"><div><h3 id="active-run-title">Active run</h3><p id="active-run-note" className="muted small-text">Pending and running work for the selected session.</p></div></div>
          <div id="active-run-card" aria-live="polite" />
        </article>
        <article className="overview-card" aria-labelledby="queue-panel-title">
          <div className="overview-card-header"><div><h3 id="queue-panel-title">Queue</h3><p className="muted small-text">Follow-up and steer messages waiting for dispatch.</p></div></div>
          <form id="queue-form" className="stack-form">
            <label htmlFor="queue-input">Queue follow-up</label>
            <textarea id="queue-input" name="content" rows={3} placeholder="Add a follow-up message for this session." />
            <div className="button-row button-row-wrap" role="group" aria-label="Queue actions">
              <button id="queue-submit-button" type="submit">Enqueue follow-up</button>
              <button id="dispatch-follow-up-button" type="button">Dispatch follow-up</button>
              <button id="dispatch-steer-button" type="button">Dispatch steer</button>
            </div>
            <p id="queue-help" className="muted small-text">Enter submits. Shift+Enter inserts a newline.</p>
          </form>
          <ul id="queue-list" className="queue-list" aria-live="polite" />
        </article>
      </section>
      <div className="extension-slot" data-extension-slot="timeline_before" />
      <ol id="timeline-list" className="timeline-list" aria-live="polite" tabIndex={0} />
      <div className="extension-slot" data-extension-slot="timeline_after" />
    </main>
  );
}
