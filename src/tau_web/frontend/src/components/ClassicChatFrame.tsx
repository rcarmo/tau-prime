import type { ComponentChildren } from "preact";

/** Classic app-main-shell-render.ts hierarchy; Tau owns the slotted behavior. */
export function ClassicChatFrame({ sidebar, children, workspaceOpen = false }: {
  sidebar?: ComponentChildren;
  children: ComponentChildren;
  workspaceOpen?: boolean;
}) {
  return <div className={`app-shell${workspaceOpen ? "" : " workspace-collapsed"}`} style={{"--sidebar-width": "280px"}}>
    <aside className="workspace-sidebar" aria-label="Workspace" inert={!workspaceOpen}>
      {sidebar}
    </aside>
    <main className="container" aria-label="Chat">{children}</main>
  </div>;
}
