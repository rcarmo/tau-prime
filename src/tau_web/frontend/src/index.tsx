import { Fragment, render } from "preact";
import { installSystemTheme } from "./theme/applyTheme";
import { useState } from "preact/hooks";
import { ActivityBar } from "./components/ActivityBar";
import { TabBar } from "./components/TabBar";
import { StatusBar } from "./components/StatusBar";
import { Composer } from "./components/Composer";
import { Dashboard } from "./components/Dashboard";
import { SidePanel } from "./components/SidePanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { SessionRuntime, Timeline } from "./components/Timeline";
import { Onboarding } from "./components/Onboarding";
import { QueueStack } from "./components/QueueStack";
import { ApprovalDialog } from "./components/ApprovalDialog";
import { useDashboardVisibility } from "./hooks/useDashboardVisibility";
import { useDrawers } from "./hooks/useDrawers";
import { useMeterControls } from "./hooks/useMeterControls";
import { useSessionFilter } from "./hooks/useSessionFilter";
import { useSidebarTabs } from "./hooks/useSidebarTabs";

/** Piclaw's shell hierarchy with Tau's existing API bindings mapped into it. */
function TauShell() {
  const { drawer, close, toggle } = useDrawers();
  const { activeTab, selectTab } = useSidebarTabs();
  const [onboardingOpen, setOnboardingOpen] = useState(false);

  const { dashboardOpen, setDashboardOpen } = useDashboardVisibility();
  const { metersEnabled, metersCollapsed, toggleMetersEnabled, toggleMetersCollapsed } = useMeterControls();
  const { sessionFilter, selectSessionFilter } = useSessionFilter();
  const settingsOpen = activeTab === "settings";
  const sidebarOpen = drawer !== null && !settingsOpen;

  const selectPanel = (panel: Parameters<typeof selectTab>[0]) => {
    if (panel === "settings") {
      selectTab(settingsOpen ? "workspace" : "settings");
      close();
      return;
    }
    const target = panel === "sessions" ? "nav" : "panel";
    if (panel === activeTab && drawer === target) close();
    else {
      selectTab(panel);
      if (drawer !== target) toggle(target);
    }
  };

  return (
    <Fragment>
      <a className="skip-link" href="#timeline-main">Skip to timeline</a>
      <div className="app-layout">
        <ActivityBar activePanel={activeTab} onPanelChange={selectPanel} onDashboard={() => setDashboardOpen(true)} />
        <main className="app-layout__main">
          <div className="app-layout__content-area">
            <div className="app-layout__sidebar-wrapper" hidden={settingsOpen} style={{ width: sidebarOpen ? "250px" : "0" }}>
              <SidePanel activeTab={activeTab} onSelectTab={selectTab} onClose={close} sessionFilter={sessionFilter} onSelectSessionFilter={selectSessionFilter} />
            </div>
            <button id="drawer-backdrop" className="app-layout__sidebar-backdrop" type="button" aria-label="Close sidebar" hidden={!sidebarOpen} onClick={close} />
            {sidebarOpen && <div className="app-layout__resize-handle" role="separator" aria-orientation="vertical" aria-label="Resize sidebar" />}
            <div className="app-layout__panel">
              <SettingsPanel hidden={!settingsOpen} />
              {!settingsOpen && <TabBar />}
              <div className="app-layout__tab-viewport" hidden={settingsOpen}>
                <div className="app-layout__tab-content">
                  <Onboarding onOpenChange={setOnboardingOpen} />
                  <section className="chat" aria-label="Tau chat" hidden={onboardingOpen}>
                    <div className="chat__messages"><Timeline /></div>
                    <SessionRuntime />
                    <QueueStack />
                    <Dashboard open={dashboardOpen} onClose={() => setDashboardOpen(false)} />
                    <Composer />
                  </section>
                </div>
              </div>
            </div>
          </div>
          <StatusBar dashboardOpen={dashboardOpen} metersEnabled={metersEnabled} metersCollapsed={metersCollapsed} onOpenSessions={() => selectPanel("sessions")} onToggleDashboard={() => setDashboardOpen((current) => !current)} onToggleMetersEnabled={toggleMetersEnabled} onToggleMetersCollapsed={toggleMetersCollapsed} />
          <div className="mobile-toolbar">
            <button id="mobile-nav-toggle" className="mobile-toolbar__terminal-btn" type="button" aria-label="Open sessions" aria-expanded={drawer === "nav"} onClick={() => selectPanel("sessions")}>Sessions</button>
            <span className="mobile-toolbar__model-slot">Tau</span>
            <button id="mobile-panel-toggle" className="mobile-toolbar__terminal-btn" type="button" aria-label="Open workspace" aria-expanded={drawer === "panel"} onClick={() => selectPanel("workspace")}>Workspace</button>
          </div>
        </main>
      </div>
      <ApprovalDialog />
      {/* Temporary event-adapter anchors; visible shell markup is Piclaw-owned. */}
      <aside id="session-nav" hidden />
      <noscript><p className="noscript-banner">Tau Web requires JavaScript.</p></noscript>
    </Fragment>
  );
}

const mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
installSystemTheme();
render(<TauShell />, mount);
