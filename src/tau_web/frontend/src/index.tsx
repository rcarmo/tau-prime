import { Fragment, render } from "preact";
import { ActivityBar } from "./components/ActivityBar";
import { StatusBar } from "./components/StatusBar";
import { Composer } from "./components/Composer";
import { Dashboard } from "./components/Dashboard";
import { SessionNav } from "./components/SessionNav";
import { Timeline } from "./components/Timeline";
import { SidePanel } from "./components/SidePanel";

/** Preact-owned Tau shell. Regions remain DOM-compatible while they are
 * incrementally replaced by typed components. */
function TauShell() {
  return (
    <Fragment>
      <a className="skip-link" href="#timeline-main">Skip to timeline</a>
      <div className="app-layout">
        <ActivityBar />
        <div className="app-layout__main">
          <div className="app-layout__content-area">
            <div className="app-layout__panel">
              <div className="app-shell">
                <StatusBar />
                <Dashboard />
                <div className="shell-layout">
                  <SessionNav />
                  <Timeline />
                  <SidePanel />
                </div>
                <Composer />
              </div>
            </div>
          </div>
        </div>
      </div>
      <button
        id="drawer-backdrop"
        className="drawer-backdrop"
        type="button"
        hidden
        aria-label="Close open drawers"
      />
      <noscript><p className="noscript-banner">Tau Web Shell requires JavaScript to load persisted sessions.</p></noscript>
    </Fragment>
  );
}

const mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
render(<TauShell />, mount);
