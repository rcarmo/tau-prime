import { ClassicIcon } from "./ClassicIcon";
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

const PanelNavigationButton = ({ name, selected, onSelect }: {
  name: Exclude<SidebarTab, "sessions">;
  selected: boolean;
  onSelect: (tab: SidebarTab) => void;
}) => (
  <button id={`tab-${name}`} type="button" aria-controls={`panel-${name}`} aria-pressed={selected} onClick={() => onSelect(name)}>{TITLES[name]}</button>
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
        <button id="close-nav-drawer" className="icon-btn" type="button" aria-label="Close sessions drawer" hidden={activeTab !== "sessions"} onClick={onClose}>✕</button>
        <button id="close-panel-drawer" className="icon-btn" type="button" aria-label="Close workspace drawer" hidden={activeTab === "sessions"} onClick={onClose}>✕</button>
      </>}>
        <div role="group" aria-label="Navigation">
          <button type="button" aria-pressed={activeTab === "sessions"} onClick={() => onSelectTab("sessions")}>Sessions</button>
          <PanelNavigationButton name="workspace" selected={activeTab === "workspace"} onSelect={onSelectTab} />
          <PanelNavigationButton name="search" selected={activeTab === "search"} onSelect={onSelectTab} />
          <PanelNavigationButton name="plan" selected={activeTab === "plan"} onSelect={onSelectTab} />
          <PanelNavigationButton name="settings" selected={activeTab === "settings"} onSelect={onSelectTab} />
        </div>

        <section id="panel-sessions" className="sessions-panel" aria-label="Session navigation" hidden={activeTab !== "sessions"}>
          <div className="tau-session-actions" role="group" aria-label="Session actions">
            <button id="new-session-button" className="tau-panel-button" type="button"><ClassicIcon name="add" /> New</button>
            <button id="archive-session-button" className="tau-panel-button" type="button">Archive</button>
            <button id="restore-session-button" className="tau-panel-button" type="button">Restore</button>
          </div>
          <SessionList filter={sessionFilter} onSelectFilter={onSelectSessionFilter} />
        </section>

        <WorkspacePanel hidden={activeTab !== "workspace"} />

        <section id="panel-search" className="tau-search-panel" aria-labelledby="tab-search" hidden={activeTab !== "search"}>
          <form id="search-form">
            <label className="sr-only" htmlFor="search-input">Search persisted content</label>
            <div className="tau-search-controls">
              <input id="search-input" className="tau-search-input" name="query" type="search" autoComplete="off" spellcheck={false} placeholder="Search messages…" />
              <button id="search-submit-button" className="tau-search-submit" type="submit">Search</button>
            </div>
          </form>
          <SearchResults />
        </section>

        <PlanPanel hidden={activeTab !== "plan"} />


    </Sidebar>
  );
}
