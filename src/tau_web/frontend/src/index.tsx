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

/** Preact-owned Tau shell. Regions remain DOM-compatible while they are
 * incrementally replaced by typed components. */
function TauShell() {
  const { drawer, close, open, toggle } = useDrawers();
  const { activeTab, selectTab } = useSidebarTabs();
  return (
    <Fragment>
      <a className="skip-link" href="#timeline-main">Skip to timeline</a>
      <div className="app-layout">
        <ActivityBar activeTab={activeTab} onSelectTab={selectTab} onOpenPanel={() => open("panel")} />
        <div className="app-layout__main">
          <div className="app-layout__content-area">
            <div className="app-layout__panel">
              <div className="app-shell">
                <StatusBar drawer={drawer} onToggleDrawer={toggle} />
                <Dashboard />
                <div className="shell-layout">
                  <SessionNav onClose={close} />
                  <Timeline />
                  <SidePanel activeTab={activeTab} onSelectTab={selectTab} onClose={close} />
                </div>
                <Composer />
              </div>
            </div>
          </div>
        </div>
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
