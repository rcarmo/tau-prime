import type { SidebarTab } from "../hooks/useSidebarTabs";
import type { SessionFilter } from "../hooks/useSessionFilter";
import { PlanPanel } from "./PlanPanel";
import { SessionList } from "./SessionList";
import { SearchResults } from "./SearchResults";
import { WorkspacePanel } from "./WorkspacePanel";
import { Sidebar } from "./Sidebar";

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
    <Sidebar id="side-panel" title={TITLES[activeTab]} label={`${TITLES[activeTab]} sidebar`} actions={<>
        <button id="close-nav-drawer" className="sidebar__close mobile-only" type="button" aria-label="Close sessions drawer" hidden={activeTab !== "sessions"} onClick={onClose}>✕</button>
        <button id="close-panel-drawer" className="sidebar__close mobile-only" type="button" aria-label="Close workspace drawer" hidden={activeTab === "sessions"} onClick={onClose}>✕</button>
      </>}>
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
          <SessionList filter={sessionFilter} onSelectFilter={onSelectSessionFilter} />
        </section>

        <WorkspacePanel hidden={activeTab !== "workspace"} />

        <section id="panel-search" className="search-panel" aria-labelledby="tab-search" hidden={activeTab !== "search"}>
          <form id="search-form">
            <label className="sr-only" htmlFor="search-input">Search persisted content</label>
            <div className="search-panel__input-wrapper">
              <span className="search-panel__icon" aria-hidden="true">⌕</span>
              <input id="search-input" className="search-panel__input" name="query" type="search" autoComplete="off" spellcheck={false} placeholder="Search messages…" />
              <button id="search-submit-button" className="search-panel__submit" type="submit">Search</button>
            </div>
          </form>
          <SearchResults />
        </section>

        <PlanPanel hidden={activeTab !== "plan"} />


    </Sidebar>
  );
}
