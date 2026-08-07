import type { SidebarTab } from "../hooks/useSidebarTabs";
import type { SessionFilter } from "../hooks/useSessionFilter";

const TITLES: Record<SidebarTab, string> = {
  sessions: "Sessions", workspace: "Workspace", search: "Search", plan: "Plan", settings: "Settings",
};

const LegacyTabAnchor = ({ name, selected, onSelect }: {
  name: Exclude<SidebarTab, "sessions">;
  selected: boolean;
  onSelect: (tab: SidebarTab) => void;
}) => (
  <button id={`tab-${name}`} type="button" aria-controls={`panel-${name}`} aria-selected={selected} onClick={() => onSelect(name)}>{TITLES[name]}</button>
);

export function SidePanel({ activeTab, onSelectTab, onClose, sessionFilter, onSelectSessionFilter }: {
  activeTab: SidebarTab;
  onSelectTab: (tab: SidebarTab) => void;
  onClose: () => void;
  sessionFilter: SessionFilter;
  onSelectSessionFilter: (filter: SessionFilter) => void;
}) {
  return (
    <aside id="side-panel" className="sidebar" aria-label={`${TITLES[activeTab]} sidebar`}>
      <header className="sidebar__header">
        <span className="sidebar__title">{TITLES[activeTab].toUpperCase()}</span>
        <button id="close-nav-drawer" className="sidebar__close mobile-only" type="button" aria-label="Close sessions drawer" hidden={activeTab !== "sessions"} onClick={onClose}>✕</button>
        <button id="close-panel-drawer" className="sidebar__close mobile-only" type="button" aria-label="Close workspace drawer" hidden={activeTab === "sessions"} onClick={onClose}>✕</button>
      </header>
      <div className="sidebar__content">
        <div hidden>
          <LegacyTabAnchor name="workspace" selected={activeTab === "workspace"} onSelect={onSelectTab} />
          <LegacyTabAnchor name="search" selected={activeTab === "search"} onSelect={onSelectTab} />
          <LegacyTabAnchor name="plan" selected={activeTab === "plan"} onSelect={onSelectTab} />
          <LegacyTabAnchor name="settings" selected={activeTab === "settings"} onSelect={onSelectTab} />
        </div>

        <section id="panel-sessions" className="sessions-panel" aria-label="Session navigation" hidden={activeTab !== "sessions"}>
          <div className="sessions-panel__toolbar" role="group" aria-label="Session actions">
            <button id="new-session-button" className="sessions-panel__new" type="button"><i className="codicon codicon-add" aria-hidden="true" /> New</button>
            <button id="archive-session-button" className="sessions-panel__action" type="button">Archive</button>
            <button id="restore-session-button" className="sessions-panel__action" type="button">Restore</button>
          </div>
          <div className="sessions-panel__filters" role="group" aria-label="Session list filter">
            <button id="show-active-sessions" type="button" aria-pressed={sessionFilter === "active"} onClick={() => onSelectSessionFilter("active")}>Active</button>
            <button id="show-archived-sessions" type="button" aria-pressed={sessionFilter === "archived"} onClick={() => onSelectSessionFilter("archived")}>Archived</button>
            <span id="session-count" className="sessions-panel__count">0 sessions</span>
          </div>
          <ul id="session-list" className="sessions-panel__list" aria-label="Available sessions" />
        </section>

        <section id="panel-workspace" className="workspace" aria-labelledby="tab-workspace" hidden={activeTab !== "workspace"}>
          <div className="workspace__pane-top">
            <div className="workspace__section-header workspace__section-header--padded">
              <span>Files</span>
              <div className="workspace__files-toolbar">
                <button id="workspace-up-button" className="workspace__files-toolbar-icon codicon codicon-arrow-up" type="button" title="Parent directory" aria-label="Parent directory" />
                <button id="workspace-reload-button" className="workspace__files-toolbar-icon codicon codicon-refresh" type="button" title="Refresh" aria-label="Refresh workspace" />
              </div>
            </div>
            <p id="workspace-path" className="workspace__current-path">.</p>
            <div id="workspace-list" className="file-tree" role="tree" aria-label="Workspace tree" />
          </div>
          <div className="workspace__drag-handle" role="separator" aria-orientation="horizontal" />
          <div className="workspace__pane-bottom">
            <div className="workspace__preview-header">Preview</div>
            <section className="workspace__preview-info" aria-labelledby="workspace-editor-title">
              <div id="workspace-editor-title" className="workspace__preview-name">Selected file</div>
              <div id="workspace-editor-path" className="workspace__preview-path">No file selected</div>
              <label className="sr-only" htmlFor="workspace-editor">Workspace file editor</label>
              <textarea id="workspace-editor" className="workspace__preview-content" spellcheck={false} aria-describedby="workspace-editor-note" />
              <p id="workspace-editor-note" className="workspace__preview-meta">Local edits are not yet persisted through the web shell.</p>
              <section id="workspace-annotations" className="workspace-annotations" hidden><h4>Annotations</h4><ul id="workspace-annotation-list" className="workspace-annotation-list" /></section>
              <section id="workspace-renderer" className="workspace-renderer" aria-label="Extension file preview" hidden />
            </section>
          </div>
        </section>

        <section id="panel-search" className="search-panel" aria-labelledby="tab-search" hidden={activeTab !== "search"}>
          <form id="search-form">
            <label className="sr-only" htmlFor="search-input">Search persisted content</label>
            <div className="search-panel__input-wrapper">
              <span className="search-panel__icon" aria-hidden="true">⌕</span>
              <input id="search-input" className="search-panel__input" name="query" type="search" autoComplete="off" spellcheck={false} placeholder="Search messages…" />
              <button id="search-submit-button" className="search-panel__submit" type="submit">Search</button>
            </div>
          </form>
          <ol id="search-results" className="search-panel__results" tabIndex={0} aria-label="Search results" aria-live="polite" />
        </section>

        <section id="panel-plan" className="tasks-panel" aria-labelledby="tab-plan" hidden={activeTab !== "plan"}>
          <div className="tasks-panel__tabs" role="tablist" aria-label="Plan views">
            <button className="tasks-panel__tab tasks-panel__tab--active" type="button" role="tab" aria-selected="true">Plan</button>
          </div>
          <div className="tasks-panel__tasks">
            <form id="plan-form" className="tasks-panel__card">
              <div className="tasks-panel__card-header">
                <span className="tasks-panel__card-id">Session plan</span>
                <span id="plan-revision" className="tasks-panel__badge tasks-panel__badge--kind">Revision 0</span>
              </div>
              <label className="tasks-panel__card-label" htmlFor="plan-editor">Shared checklist</label>
              <textarea id="plan-editor" className="plan-editor tasks-panel__card-mono" spellcheck placeholder="- [ ] Add a concrete next step" aria-describedby="plan-status" />
              <p id="plan-status" className="tasks-panel__card-muted" aria-live="polite">Select a session to edit its shared plan.</p>
              <div id="plan-conflict" className="tasks-panel__sessions-error tasks-panel__sessions-error--inline" role="alert" hidden>The plan changed elsewhere. Reload the server version or save again after reviewing it.</div>
              <div className="tasks-panel__card-actions"><button id="plan-save-button" type="submit">Save plan</button><button id="plan-reload-button" type="button">Reload</button></div>
            </form>
          </div>
        </section>

        <section id="panel-settings" className="settings-panel" aria-labelledby="tab-settings" hidden={activeTab !== "settings"}>
          <nav className="settings-panel__nav" aria-label="Settings categories">
            <a className="settings-panel__nav-item settings-panel__nav-item--active" href="#tau-settings-auth"><i className="codicon codicon-shield" aria-hidden="true" />Authentication</a>
            <a className="settings-panel__nav-item" href="#tau-settings-model"><i className="codicon codicon-symbol-parameter" aria-hidden="true" />Model</a>
            <a className="settings-panel__nav-item" href="#tau-settings-runtime"><i className="codicon codicon-server" aria-hidden="true" />Runtime</a>
          </nav>
          <div className="settings-panel__content">
            <section id="tau-settings-auth" className="settings-panel__section">
              <h2 className="settings-panel__section-title">Authentication</h2>
              <button className="settings-panel__provider-btn settings-provider-setup" type="button" onClick={() => document.querySelector<HTMLButtonElement>(".provider-setup-trigger")?.click()}>Provider setup</button>
              <form id="auth-form">
                <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="auth-token">Bearer token</label><input id="auth-token" className="settings-panel__input" type="password" autoComplete="off" /></div>
                <div className="settings-panel__field"><span className="settings-panel__label" /><button id="save-auth-button" className="settings-panel__provider-btn" type="submit">Save token</button><button id="clear-auth-button" className="settings-panel__provider-btn settings-panel__provider-btn--logout" type="button">Clear token</button></div>
              </form>
            </section>
            <section id="tau-settings-model" className="settings-panel__section">
              <h2 className="settings-panel__section-title">Model</h2>
              <form id="model-form">
                <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="provider-input">Provider</label><input id="provider-input" className="settings-panel__input" list="provider-options" autoComplete="off" /><datalist id="provider-options" /></div>
                <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="model-input">Model</label><input id="model-input" className="settings-panel__input" list="model-options" autoComplete="off" /><datalist id="model-options" /></div>
                <div className="settings-panel__field"><span className="settings-panel__label" /><button id="apply-model-button" className="settings-panel__provider-btn" type="submit">Apply to session</button><button id="refresh-button" className="settings-panel__provider-btn" type="button">Refresh</button></div>
              </form>
              <form id="thinking-form">
                <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="thinking-level-select">Thinking level</label><select id="thinking-level-select" className="settings-panel__select" name="thinking_level" /><button id="apply-thinking-button" className="settings-panel__provider-btn" type="submit">Apply</button></div>
                <p id="thinking-help" className="settings-panel__description">Updates session thinking with optimistic concurrency checks.</p>
              </form>
            </section>
            <section id="tau-settings-runtime" className="settings-panel__section" aria-labelledby="settings-summary-title">
              <h2 id="settings-summary-title" className="settings-panel__section-title">Runtime</h2>
              <dl id="settings-summary" className="settings-summary" />
              <p id="streaming-note" className="settings-panel__description">Live streaming, queue controls, and persisted timeline playback use safe DOM updates.</p>
              <div className="extension-slot" data-extension-slot="sidebar" />
            </section>
          </div>
        </section>
      </div>
    </aside>
  );
}
