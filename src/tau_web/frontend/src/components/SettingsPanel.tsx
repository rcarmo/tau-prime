import { useState } from "preact/hooks";
import { ModelControls } from "./ModelControls";
import { SettingsSummary } from "./SettingsSummary";

export function SettingsPanel({ hidden }: { hidden: boolean }) {
  const [category, setCategory] = useState("auth");
  const categories = [
    { id: "auth", label: "Authentication", icon: "shield" },
    { id: "model", label: "Model", icon: "symbol-parameter" },
    { id: "runtime", label: "Runtime", icon: "server" },
  ];
  return (
        <section id="panel-settings" className="settings-panel" aria-labelledby="tab-settings" hidden={hidden}>
          <nav className="settings-panel__nav" aria-label="Settings categories">
            {categories.map(item => <a key={item.id}
              className={`settings-panel__nav-item${category === item.id ? " settings-panel__nav-item--active" : ""}`}
              aria-current={category === item.id ? "location" : undefined}
              href={`#tau-settings-${item.id}`}
              onClick={event => {
                if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
                setCategory(item.id);
              }}><i className={`codicon codicon-${item.icon}`} aria-hidden="true" />{item.label}</a>)}
          </nav>
          <div className="settings-panel__content">
            <section id="tau-settings-auth" className="settings-panel__section">
              <h2 className="settings-panel__section-title">Authentication</h2>
              <button className="settings-panel__provider-btn settings-provider-setup" type="button" onClick={() => {
                window.dispatchEvent(new CustomEvent("tau:switch-tab", { detail: { tab: "workspace" } }));
                window.dispatchEvent(new CustomEvent("tau:close-drawers"));
                document.querySelector<HTMLButtonElement>(".provider-setup-trigger")?.click();
              }}>Provider setup</button>
              <form id="auth-form">
                <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="auth-token">Bearer token</label><input id="auth-token" className="settings-panel__input" type="password" autoComplete="off" /></div>
                <div className="settings-panel__field"><span className="settings-panel__label" /><button id="save-auth-button" className="settings-panel__provider-btn" type="submit">Save token</button><button id="clear-auth-button" className="settings-panel__provider-btn settings-panel__provider-btn--logout" type="button">Clear token</button></div>
              </form>
            </section>
            <section id="tau-settings-model" className="settings-panel__section">
              <h2 className="settings-panel__section-title">Model</h2>
              <ModelControls />
            </section>
            <section id="tau-settings-runtime" className="settings-panel__section" aria-labelledby="settings-summary-title">
              <h2 id="settings-summary-title" className="settings-panel__section-title">Runtime</h2>
              <SettingsSummary />
              <p id="streaming-note" className="settings-panel__description">Live streaming, queue controls, and persisted timeline playback use safe DOM updates.</p>
              <div className="extension-slot" data-extension-slot="sidebar" />
            </section>
          </div>
        </section>
  );
}
