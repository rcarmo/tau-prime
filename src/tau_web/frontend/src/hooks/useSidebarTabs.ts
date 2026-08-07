import { useEffect, useState } from "preact/hooks";

export type SidebarTab = "workspace" | "search" | "plan" | "settings";
const TABS = new Set<SidebarTab>(["workspace", "search", "plan", "settings"]);

export function useSidebarTabs() {
  const [activeTab, setActiveTab] = useState<SidebarTab>("workspace");

  useEffect(() => {
    const requested = (event: Event) => {
      const tab = (event as CustomEvent<{ tab?: string }>).detail?.tab;
      if (TABS.has(tab as SidebarTab)) setActiveTab(tab as SidebarTab);
    };
    window.addEventListener("tau:switch-tab", requested);
    return () => window.removeEventListener("tau:switch-tab", requested);
  }, []);

  const selectTab = (tab: SidebarTab) => {
    setActiveTab(tab);
    window.dispatchEvent(new CustomEvent("tau:tab-selected", { detail: { tab } }));
  };

  return { activeTab, selectTab };
}
