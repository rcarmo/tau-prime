import { Fragment, render } from "preact";
import { ActivityBar } from "./components/ActivityBar";
import { StatusBar } from "./components/StatusBar";
import { Composer } from "./components/Composer";
import { Dashboard } from "./components/Dashboard";
import { SessionNav } from "./components/SessionNav";
import { Timeline } from "./components/Timeline";
import { SidePanel } from "./components/SidePanel";
import { Onboarding } from "./components/Onboarding";
import { useDrawers } from "./hooks/useDrawers";
import { useSidebarTabs } from "./hooks/useSidebarTabs";
import { useDashboardVisibility } from "./hooks/useDashboardVisibility";
import { useMeterControls } from "./hooks/useMeterControls";
import { useSessionFilter } from "./hooks/useSessionFilter";

/** Preact-owned Tau shell. Regions remain DOM-compatible while they are
 * incrementally replaced by typed components. */
function TauShell() {
  const { drawer, close, open, toggle } = useDrawers();
  const { activeTab, selectTab } = useSidebarTabs();
  const { dashboardOpen, setDashboardOpen } = useDashboardVisibility();
  const { metersEnabled, metersCollapsed, toggleMetersEnabled, toggleMetersCollapsed } = useMeterControls();
  const { sessionFilter, selectSessionFilter } = useSessionFilter();
  return (
    <Fragment>
      <a className="skip-link" href="#timeline-main">Skip to timeline</a>
      <div className="app-layout">
        <ActivityBar activeTab={activeTab} onSelectTab={selectTab} onOpenPanel={() => open("panel")} />
        <main className="app-layout__main">
          <div className="app-layout__content-area">
            <div className="app-layout__sidebar-wrapper">
              <SessionNav filter={sessionFilter} onSelectFilter={selectSessionFilter} onClose={close} />
            </div>
            <div className="app-layout__panel">
              <div className="app-layout__tab-viewport">
                <div className="app-layout__tab-content">
                  <section className="chat" aria-label="Tau chat">
                    <Timeline />
                    <Dashboard open={dashboardOpen} onClose={() => setDashboardOpen(false)} />
                    <Composer />
                  </section>
                </div>
              </div>
            </div>
            <SidePanel activeTab={activeTab} onSelectTab={selectTab} onClose={close} />
          </div>
          <StatusBar drawer={drawer} dashboardOpen={dashboardOpen} metersEnabled={metersEnabled} metersCollapsed={metersCollapsed} onToggleDrawer={toggle} onToggleDashboard={() => setDashboardOpen((current) => !current)} onToggleMetersEnabled={toggleMetersEnabled} onToggleMetersCollapsed={toggleMetersCollapsed} />
          <div className="mobile-toolbar" role="banner" aria-label="Tau status bar">
            <button id="mobile-nav-toggle" className="mobile-toolbar__terminal-btn" type="button" aria-controls="session-nav" aria-expanded={drawer === "nav"} aria-label="Open sessions drawer" onClick={() => toggle("nav")}>Sessions</button>
            <span className="mobile-toolbar__model-slot">Tau</span>
            <button id="mobile-panel-toggle" className="mobile-toolbar__terminal-btn" type="button" aria-controls="side-panel" aria-expanded={drawer === "panel"} aria-label="Open workspace and settings drawer" onClick={() => toggle("panel")}>Panels</button>
          </div>
        </main>
      </div>
      <Onboarding />
      <button
        id="drawer-backdrop"
        className="drawer-backdrop"
        type="button"
        hidden={drawer === null}
        aria-label="Close open drawers"
        onClick={close}
      />
      <noscript><p className="noscript-banner">Tau Web Shell requires JavaScript to load persisted sessions.</p></noscript>
    </Fragment>
  );
}

const mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
render(<TauShell />, mount);
