import type { SidebarTab } from "../hooks/useSidebarTabs";

type Panel = { id: SidebarTab | "dashboard"; label: string; icon: string; alignBottom?: boolean };

const PANELS: Panel[] = [
  { id: "sessions", label: "Sessions", icon: "codicon-comment-discussion" },
  { id: "workspace", label: "Workspace", icon: "codicon-files" },
  { id: "search", label: "Search", icon: "codicon-search" },
  { id: "plan", label: "Plan", icon: "codicon-checklist" },
  { id: "dashboard", label: "Dashboard", icon: "codicon-dashboard" },
  { id: "settings", label: "Settings", icon: "codicon-settings-gear", alignBottom: true },
];

export function ActivityBar({ activePanel, onPanelChange, onDashboard }: {
  activePanel: SidebarTab;
  onPanelChange: (panel: SidebarTab) => void;
  onDashboard: () => void;
}) {
  return (
    <nav className="activity-bar" aria-label="Activity bar">
      {PANELS.map((panel) => {
        const active = panel.id === activePanel;
        return (
          <button
            key={panel.id}
            type="button"
            className={`activity-bar__button ${active ? "is-active" : ""} ${panel.alignBottom ? "is-bottom" : ""}`}
            title={panel.label}
            aria-label={panel.label}
            aria-pressed={active}
            onClick={() => panel.id === "dashboard" ? onDashboard() : onPanelChange(panel.id)}
          >
            <i className={`codicon ${panel.icon} activity-bar__icon`} aria-hidden="true" />
          </button>
        );
      })}
    </nav>
  );
}
