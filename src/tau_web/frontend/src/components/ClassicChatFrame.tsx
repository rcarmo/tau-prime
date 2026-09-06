import type { ComponentChildren } from "preact";

/** Classic app-main-shell-render.ts hierarchy; Tau owns the slotted behavior. */
export function ClassicChatFrame({ sidebar, children, workspaceOpen = false, onToggleWorkspace }: {
  onToggleWorkspace?: () => void;
  sidebar?: ComponentChildren;
  children: ComponentChildren;
  workspaceOpen?: boolean;
}) {
  return <div className={`app-shell${workspaceOpen ? "" : " workspace-collapsed"}`} style={{"--sidebar-width": "280px"}}>
    <aside className="workspace-sidebar" aria-label="Workspace" inert={!workspaceOpen}>
      {sidebar}
    </aside>
    {onToggleWorkspace && <>
      {workspaceOpen && <div className="workspace-drawer-backdrop" onClick={onToggleWorkspace} aria-hidden="true" />}
      <button type="button" className={`workspace-toggle-tab ${workspaceOpen ? "open" : "closed"}`} onClick={onToggleWorkspace} title={workspaceOpen ? "Hide workspace" : "Show workspace"} aria-label={workspaceOpen ? "Hide workspace" : "Show workspace"} aria-expanded={workspaceOpen}>
        <svg className="workspace-toggle-tab-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="6 3 11 8 6 13" /></svg>
      </button>
    </>}
    <main className="container" aria-label="Chat">{children}</main>
  </div>;
}
