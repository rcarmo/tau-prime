import type { SidebarTab } from "../hooks/useSidebarTabs";

type Panel = { id: SidebarTab | "dashboard" | "sessions"; label: string; target?: string; glyph: string; bottom?: boolean };

const PANELS: Panel[] = [
  { id: "sessions", label: "Sessions", target: "mobile-nav-toggle", glyph: "☰" },
  { id: "workspace", label: "Workspace", target: "tab-workspace", glyph: "▱" },
  { id: "search", label: "Search", target: "tab-search", glyph: "⌕" },
  { id: "plan", label: "Plan", target: "tab-plan", glyph: "☷" },
  { id: "dashboard", label: "Dashboard", target: "dashboard-toggle", glyph: "⌁" },
  { id: "settings", label: "Settings", target: "tab-settings", glyph: "⚙", bottom: true },
];

export function ActivityBar({ activeTab, onSelectTab, onOpenPanel }: {
  activeTab: SidebarTab;
  onSelectTab: (tab: SidebarTab) => void;
  onOpenPanel: () => void;
}) {
  const activate = (panel: Panel) => {
    if (panel.id === "dashboard") {
      document.getElementById("dashboard-toggle")?.click();
      return;
    }
    if (panel.id === "sessions") {
      document.getElementById("mobile-nav-toggle")?.click();
      return;
    }
    onSelectTab(panel.id);
    onOpenPanel();
  };
  return (
    <nav className="activity-bar" aria-label="Activity bar">
      {PANELS.map((panel) => (
        <button
          key={panel.id}
          type="button"
          className={`activity-bar__button ${activeTab === panel.id ? "is-active" : ""} ${panel.bottom ? "is-bottom" : ""}`}
          title={panel.label}
          aria-label={panel.label}
          aria-pressed={activeTab === panel.id}
          onClick={() => activate(panel)}
        >
          <span className="activity-bar__icon" aria-hidden="true">{panel.glyph}</span>
        </button>
      ))}
    </nav>
  );
}
