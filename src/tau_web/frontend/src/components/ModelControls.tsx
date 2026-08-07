import { useLayoutEffect, useState } from "preact/hooks";

type Option = { value: string; label: string };
const thinking: Option[] = [
  { value: "", label: "Default" }, { value: "off", label: "Off — no reasoning" },
  { value: "minimal", label: "Minimal — very brief reasoning" }, { value: "low", label: "Low — light reasoning" },
  { value: "medium", label: "Medium — moderate reasoning" }, { value: "high", label: "High — deep reasoning" },
  { value: "xhigh", label: "XHigh — maximum reasoning" },
];

export function ModelControls() {
  const [options, setOptions] = useState<{ providers: Option[]; models: Option[] }>({ providers: [], models: [] });
  useLayoutEffect(() => {
    const update = (event: Event) => setOptions((event as CustomEvent<typeof options>).detail);
    window.addEventListener("tau:model-options-render", update);
    return () => window.removeEventListener("tau:model-options-render", update);
  }, []);
  return <>
    <form id="model-form">
      <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="provider-input">Provider</label><input id="provider-input" className="settings-panel__input" list="provider-options" autoComplete="off" /><datalist id="provider-options">{options.providers.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</datalist></div>
      <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="model-input">Model</label><input id="model-input" className="settings-panel__input" list="model-options" autoComplete="off" /><datalist id="model-options">{options.models.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</datalist></div>
      <div className="settings-panel__field"><span className="settings-panel__label" /><button id="apply-model-button" className="settings-panel__provider-btn" type="submit">Apply to session</button><button id="refresh-button" className="settings-panel__provider-btn" type="button">Refresh</button></div>
    </form>
    <form id="thinking-form">
      <div className="settings-panel__field"><label className="settings-panel__label" htmlFor="thinking-level-select">Thinking level</label><select id="thinking-level-select" className="settings-panel__select" name="thinking_level">{thinking.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select><button id="apply-thinking-button" className="settings-panel__provider-btn" type="submit">Apply</button></div>
      <p id="thinking-help" className="settings-panel__description">Updates session thinking with optimistic concurrency checks.</p>
    </form>
  </>;
}
