import { useEffect, useState } from "preact/hooks";

const readBoolean = (key: string, fallback: boolean) => {
  const value = window.localStorage.getItem(key);
  return value === null ? fallback : value === "true";
};

export function useMeterControls() {
  const [enabled, setEnabled] = useState(() => readBoolean("tau.web.metersEnabled", true));
  const [collapsed, setCollapsed] = useState(() => readBoolean("tau.web.metersCollapsed", true));

  useEffect(() => {
    window.localStorage.setItem("tau.web.metersEnabled", String(enabled));
    window.localStorage.setItem("tau.web.metersCollapsed", String(collapsed));
    window.dispatchEvent(new CustomEvent("tau:meter-controls", { detail: { enabled, collapsed } }));
  }, [enabled, collapsed]);

  return {
    metersEnabled: enabled,
    metersCollapsed: collapsed,
    toggleMetersEnabled: () => setEnabled((current) => !current),
    toggleMetersCollapsed: () => setCollapsed((current) => !current),
  };
}
