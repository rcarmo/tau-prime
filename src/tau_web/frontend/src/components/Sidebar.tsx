import type { ComponentChildren } from "preact";

// Adapted from Piclaw 2.15.3 Sidebar.tsx (MIT; see PICLAW-LICENSE.md).
export function Sidebar({ title, children, id, label, actions }: {
  title: string;
  children: ComponentChildren;
  id?: string;
  label?: string;
  actions?: ComponentChildren;
}) {
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
