import type { ComponentChildren } from "preact";

// Adapted from Piclaw 2.15.3 Sidebar.tsx (MIT; see PICLAW-LICENSE.md).
export function Sidebar({ title, children, id, label, actions, classic = false }: {
  classic?: boolean;
  title: string;
  children: ComponentChildren;
  id?: string;
  label?: string;
  actions?: ComponentChildren;
}) {
  if (classic) return <section id={id} className="tau-classic-panel" aria-label={label}>
    <header className="workspace-header"><div className="workspace-header-left">{title}</div><div className="workspace-header-actions">{actions}</div></header>
    <div className="tau-classic-panel-content">{children}</div>
  </section>;
  return (
    <aside id={id} className="sidebar" aria-label={label}>
      <header className="sidebar__header">
        <span className="sidebar__title">{title.toUpperCase()}</span>
        {actions}
      </header>
      <div className="sidebar__content">{children}</div>
    </aside>
  );
}
