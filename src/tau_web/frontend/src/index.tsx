import { ClassicChatFrame } from "./components/ClassicChatFrame";
import { ClassicSessionControl } from "./components/ClassicSessionControl";
import { SystemStats } from "./components/SystemStats";
import { Fragment, render } from "preact";
import { useState } from "preact/hooks";
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

  return <Fragment>
    <ClassicChatFrame workspaceOpen={sidebarOpen || settingsOpen} onToggleWorkspace={() => { if(sidebarOpen || settingsOpen) { close(); if(settingsOpen) selectTab("workspace"); } else selectPanel("workspace"); }} sidebar={<>
      <SidePanel activeTab={activeTab} onSelectTab={selectTab} onClose={() => { close(); if(settingsOpen) selectTab("sessions"); }} sessionFilter={sessionFilter} onSelectSessionFilter={selectSessionFilter} />
      <SettingsPanel hidden={!settingsOpen} />
      <SystemStats enabled={metersEnabled} collapsed={metersCollapsed} onToggleEnabled={toggleMetersEnabled} onToggleCollapsed={toggleMetersCollapsed} />
    </>}>
      <Onboarding onOpenChange={setOnboardingOpen} />
      <div className="tau-classic-chat" hidden={onboardingOpen}>
        <Timeline />
        <SessionRuntime /><QueueStack />
        <Composer session={<ClassicSessionControl open={sidebarOpen} onToggle={() => selectPanel("sessions")} />} metadata={<StatusBar onOpenModel={() => { selectTab("settings"); close(); window.dispatchEvent(new CustomEvent("tau:open-model-settings")); requestAnimationFrame(() => document.getElementById("model-input")?.focus()); }} dashboardOpen={dashboardOpen} onToggleDashboard={() => setDashboardOpen(value=>!value)} />} />
      </div>
    </ClassicChatFrame>
    <Dashboard open={dashboardOpen} onClose={() => setDashboardOpen(false)} />
    <ApprovalDialog />
    <div hidden><aside id="session-nav" /><button id="mobile-nav-toggle" onClick={() => selectPanel("sessions")} /><button id="mobile-panel-toggle" onClick={() => selectPanel("workspace")} /><button id="drawer-backdrop" onClick={close} /></div>
  </Fragment>;

}

const mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
document.documentElement.dataset.tauUi = "classic";
render(<TauShell />, mount);
