const Tab = ({ id, panel, selected, children }: { id: string; panel: string; selected: boolean; children: string }) => (
  <button id={id} className="tab-button" type="button" role="tab" aria-controls={panel} aria-selected={selected}>{children}</button>
);

export function SidePanel({ onClose }: { onClose: () => void }) {
  return (
    <aside id="side-panel" className="panel panel-side" aria-label="Workspace search and settings">
      <div className="panel-header sticky-header">
        <div><h2>Workspace</h2><p className="muted">Files, search, and Tau settings.</p></div>
        <button id="close-panel-drawer" className="icon-button mobile-only" type="button" aria-label="Close workspace drawer" onClick={onClose}>Close</button>
      </div>
      <div className="tabs" role="tablist" aria-label="Sidebar sections">
        <Tab id="tab-workspace" panel="panel-workspace" selected>Workspace</Tab>
        <Tab id="tab-search" panel="panel-search" selected={false}>Search</Tab>
        <Tab id="tab-plan" panel="panel-plan" selected={false}>Plan</Tab>
        <Tab id="tab-settings" panel="panel-settings" selected={false}>Settings</Tab>
      </div>
      <section id="panel-workspace" className="tab-panel" role="tabpanel" aria-labelledby="tab-workspace">
        <div className="toolbar-row"><button id="workspace-up-button" type="button">Up</button><button id="workspace-reload-button" type="button">Reload</button></div>
        <p id="workspace-path" className="muted small-text">.</p>
        <div className="workspace-split">
          <nav className="workspace-browser" aria-label="Workspace tree"><ul id="workspace-list" className="workspace-list" /></nav>
          <section className="workspace-editor-panel" aria-labelledby="workspace-editor-title">
            <div className="workspace-editor-header"><h3 id="workspace-editor-title">Editor</h3><p id="workspace-editor-path" className="muted small-text">No file selected</p></div>
            <label className="sr-only" htmlFor="workspace-editor">Workspace file editor</label>
            <textarea id="workspace-editor" spellcheck={false} aria-describedby="workspace-editor-note" />
            <p id="workspace-editor-note" className="muted small-text">Local edits are not yet persisted through the web shell.</p>
            <section id="workspace-annotations" className="workspace-annotations" hidden><h4>Annotations</h4><ul id="workspace-annotation-list" className="workspace-annotation-list" /></section>
            <section id="workspace-renderer" className="workspace-renderer" aria-label="Extension file preview" hidden />
          </section>
        </div>
      </section>
      <section id="panel-search" className="tab-panel" role="tabpanel" aria-labelledby="tab-search" hidden>
        <form id="search-form" className="stack-form">
          <label htmlFor="search-input">Search persisted content</label>
          <div className="toolbar-row"><input id="search-input" name="query" type="search" autoComplete="off" placeholder="Search messages and indexed content" /><button id="search-submit-button" type="submit">Search</button></div>
          <p className="muted small-text">Shortcut: Ctrl/Cmd+K</p>
        </form>
        <ol id="search-results" className="search-results" tabIndex={0} aria-label="Search results" aria-live="polite" />
      </section>
      <section id="panel-plan" className="tab-panel plan-panel" role="tabpanel" aria-labelledby="tab-plan" hidden>
        <form id="plan-form" className="stack-form">
          <div className="plan-editor-header"><label htmlFor="plan-editor">Session plan</label><span id="plan-revision" className="muted small-text">Revision 0</span></div>
          <textarea id="plan-editor" className="plan-editor" spellcheck placeholder="- [ ] Add a concrete next step" aria-describedby="plan-status" />
          <p id="plan-status" className="muted small-text" aria-live="polite">Select a session to edit its shared plan.</p>
          <div id="plan-conflict" className="plan-conflict" role="alert" hidden>The plan changed elsewhere while you had local edits. Reload the server version or save again after reviewing it.</div>
          <div className="button-row button-row-wrap"><button id="plan-save-button" type="submit">Save plan</button><button id="plan-reload-button" type="button">Reload server plan</button></div>
        </form>
      </section>
      <section id="panel-settings" className="tab-panel" role="tabpanel" aria-labelledby="tab-settings" hidden>
        <form id="auth-form" className="stack-form">
          <label htmlFor="auth-token">Bearer token</label><input id="auth-token" type="password" autoComplete="off" />
          <div className="button-row button-row-wrap"><button id="save-auth-button" type="submit">Save token</button><button id="clear-auth-button" type="button">Clear token</button></div>
        </form>
        <form id="model-form" className="stack-form">
          <label htmlFor="provider-input">Provider</label><input id="provider-input" list="provider-options" autoComplete="off" /><datalist id="provider-options" />
          <label htmlFor="model-input">Model</label><input id="model-input" list="model-options" autoComplete="off" /><datalist id="model-options" />
          <div className="button-row button-row-wrap"><button id="apply-model-button" type="submit">Apply to session</button><button id="refresh-button" type="button">Refresh shell</button></div>
        </form>
        <form id="thinking-form" className="stack-form">
          <label htmlFor="thinking-level-select">Thinking level</label>
          <div className="toolbar-row toolbar-row-wrap"><select id="thinking-level-select" name="thinking_level" /><button id="apply-thinking-button" type="submit">Apply thinking</button></div>
          <p id="thinking-help" className="muted small-text">Updates session thinking with optimistic concurrency checks.</p>
        </form>
        <section aria-labelledby="settings-summary-title"><h3 id="settings-summary-title">Runtime summary</h3><dl id="settings-summary" className="settings-summary" /></section>
        <p id="streaming-note" className="muted small-text">Live streaming, queue controls, and persisted timeline playback are rendered with safe DOM updates only.</p>
        <div className="extension-slot" data-extension-slot="sidebar" />
      </section>
    </aside>
  );
}
