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
      <div className="settings-row settings-row-vertical"><label className="tau-settings-label" htmlFor="provider-input">Provider</label><input id="provider-input" type="text" className="tau-settings-input" list="provider-options" autoComplete="off" /><datalist id="provider-options">{options.providers.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</datalist></div>
      <div className="settings-row settings-row-vertical"><label className="tau-settings-label" htmlFor="model-input">Model</label><input id="model-input" type="text" className="tau-settings-input" list="model-options" autoComplete="off" /><datalist id="model-options">{options.models.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</datalist></div>
      <div className="settings-row settings-row-vertical"><span className="tau-settings-label" /><button id="apply-model-button" className="tau-settings-button" type="submit">Apply to session</button><button id="refresh-button" className="tau-settings-button" type="button">Refresh</button></div>
    </form>
    <form id="thinking-form">
      <div className="settings-row settings-row-vertical"><label className="tau-settings-label" htmlFor="thinking-level-select">Thinking level</label><select id="thinking-level-select" className="tau-settings-input" name="thinking_level">{thinking.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select><button id="apply-thinking-button" className="tau-settings-button" type="submit">Apply</button></div>
      <p id="thinking-help" className="tau-settings-description">Updates session thinking with optimistic concurrency checks.</p>
    </form>
  </>;
}
