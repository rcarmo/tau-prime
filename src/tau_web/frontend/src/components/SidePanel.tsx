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

        <section id="panel-plan" className="plan-panel" aria-labelledby="tab-plan" hidden={activeTab !== "plan"}>
          <form id="plan-form" className="stack-form">
            <div className="plan-editor-header"><label htmlFor="plan-editor">Session plan</label><span id="plan-revision" className="muted small-text">Revision 0</span></div>
            <textarea id="plan-editor" className="plan-editor" spellcheck placeholder="- [ ] Add a concrete next step" aria-describedby="plan-status" />
            <p id="plan-status" className="muted small-text" aria-live="polite">Select a session to edit its shared plan.</p>
            <div id="plan-conflict" className="plan-conflict" role="alert" hidden>The plan changed elsewhere while you had local edits. Reload the server version or save again after reviewing it.</div>
            <div className="button-row button-row-wrap"><button id="plan-save-button" type="submit">Save plan</button><button id="plan-reload-button" type="button">Reload server plan</button></div>
          </form>
        </section>

        <section id="panel-settings" className="settings-panel" aria-labelledby="tab-settings" hidden={activeTab !== "settings"}>
          <button className="settings-provider-setup" type="button" onClick={() => document.querySelector<HTMLButtonElement>(".provider-setup-trigger")?.click()}>Provider setup</button>
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
          <p id="streaming-note" className="muted small-text">Live streaming, queue controls, and persisted timeline playback use safe DOM updates.</p>
          <div className="extension-slot" data-extension-slot="sidebar" />
        </section>
      </div>
    </aside>
  );
}
