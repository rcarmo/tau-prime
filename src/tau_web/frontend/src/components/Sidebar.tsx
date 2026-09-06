import type { ComponentChildren } from "preact";

// Classic workspace-header structure with Tau panel content.
export function Sidebar({ title, children, id, label, actions }: {
  title: string;
  children: ComponentChildren;
  id?: string;
  label?: string;
  actions?: ComponentChildren;
}) {
  return <section id={id} className="tau-classic-panel" aria-label={label}>
    <header className="workspace-header"><div className="workspace-header-left">{title}</div><div className="workspace-header-actions">{actions}</div></header>
    <div className="tau-classic-panel-content">{children}</div>
  </section>;
}
