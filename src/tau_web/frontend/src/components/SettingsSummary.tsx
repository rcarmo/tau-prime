import { useLayoutEffect, useState } from "preact/hooks";

type Setting = { label: string; value: string };

export function SettingsSummary() {
  const [items, setItems] = useState<Setting[] | null>(null);
  useLayoutEffect(() => {
    const update = (event: Event) => setItems((event as CustomEvent<{ items: Setting[] | null }>).detail.items);
    window.addEventListener("tau:settings-render", update);
    return () => window.removeEventListener("tau:settings-render", update);
  }, []);
  return <dl id="settings-summary" className="settings-summary">
    {items === null
      ? <div><dd className="muted-text">Runtime settings unavailable.</dd></div>
      : items.map((item) => <div key={item.label}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}
  </dl>;
}
