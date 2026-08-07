import { useState } from "preact/hooks";

type Panel = { id: string; label: string; target: string; glyph: string; bottom?: boolean };

const PANELS: Panel[] = [
  { id: "workspace", label: "Workspace", target: "tab-workspace", glyph: "▱" },
  { id: "search", label: "Search", target: "tab-search", glyph: "⌕" },
  { id: "plan", label: "Plan", target: "tab-plan", glyph: "☷" },
  { id: "dashboard", label: "Dashboard", target: "dashboard-toggle", glyph: "⌁" },
  { id: "settings", label: "Settings", target: "tab-settings", glyph: "⚙", bottom: true },
];

export function ActivityBar() {
  const [activePanel, setActivePanel] = useState("workspace");
  const activate = (panel: Panel) => {
    document.getElementById(panel.target)?.click();
    setActivePanel(panel.id);
  };
  return (
    <nav className="activity-bar" aria-label="Activity bar">
      {PANELS.map((panel) => (
        <button
          key={panel.id}
          type="button"
          className={`activity-bar__button ${activePanel === panel.id ? "is-active" : ""} ${panel.bottom ? "is-bottom" : ""}`}
          title={panel.label}
          aria-label={panel.label}
          aria-pressed={activePanel === panel.id}
          onClick={() => activate(panel)}
        >
          <span className="activity-bar__icon" aria-hidden="true">{panel.glyph}</span>
        </button>
      ))}
    </nav>
  );
}
