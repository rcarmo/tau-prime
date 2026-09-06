import { useState } from "preact/hooks";
import { ModelControls } from "./ModelControls";
import { SettingsSummary } from "./SettingsSummary";

export function SettingsPanel({ hidden }: { hidden: boolean }) {
  const [category, setCategory] = useState("auth");
  const categories = [
    { id: "auth", label: "Authentication" },
    { id: "model", label: "Model" },
    { id: "runtime", label: "Runtime" },
  ];
  return (
        <section id="panel-settings" className="settings-panel" aria-labelledby="tab-settings" hidden={hidden}>
          <nav className="settings-nav" aria-label="Settings categories">
            {categories.map(item => <a key={item.id}
              className={`settings-nav-item${category === item.id ? " active" : ""}`}
              aria-current={category === item.id ? "location" : undefined}
              href={`#tau-settings-${item.id}`}
              onClick={event => {
                if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
                setCategory(item.id);
              }}><span className="settings-nav-label">{item.label}</span></a>)}
          </nav>
          <div className="tau-settings-content">
            <section id="tau-settings-auth" className="settings-section">
              <h2 className="tau-settings-heading">Authentication</h2>
              <button className="tau-settings-button settings-provider-setup" type="button" onClick={() => {
                window.dispatchEvent(new CustomEvent("tau:switch-tab", { detail: { tab: "workspace" } }));
                window.dispatchEvent(new CustomEvent("tau:close-drawers"));
                document.querySelector<HTMLButtonElement>(".provider-setup-trigger")?.click();
              }}>Provider setup</button>
              <form id="auth-form">
                <div className="settings-row settings-row-vertical"><label className="tau-settings-label" htmlFor="auth-token">Bearer token</label><input id="auth-token" className="tau-settings-input" type="password" autoComplete="off" /></div>
                <div className="settings-row settings-row-vertical"><span className="tau-settings-label" /><button id="save-auth-button" className="tau-settings-button" type="submit">Save token</button><button id="clear-auth-button" className="tau-settings-button tau-settings-button--logout" type="button">Clear token</button></div>
              </form>
            </section>
            <section id="tau-settings-model" className="settings-section">
              <h2 className="tau-settings-heading">Model</h2>
              <ModelControls />
            </section>
            <section id="tau-settings-runtime" className="settings-section" aria-labelledby="settings-summary-title">
              <h2 id="settings-summary-title" className="tau-settings-heading">Runtime</h2>
              <SettingsSummary />
              <p id="streaming-note" className="tau-settings-description">Live streaming, queue controls, and persisted timeline playback use safe DOM updates.</p>
              <div className="extension-slot" data-extension-slot="sidebar" />
            </section>
          </div>
        </section>
  );
}
