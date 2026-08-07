import { useEffect, useState } from "preact/hooks";

export type Drawer = "nav" | "panel" | null;

export function useDrawers() {
  const [drawer, setDrawer] = useState<Drawer>(null);
  const close = () => setDrawer(null);
  const open = (next: Exclude<Drawer, null>) => setDrawer(next);
  const toggle = (next: Exclude<Drawer, null>) => {
    setDrawer((current) => current === next ? null : next);
  };

  useEffect(() => {
    document.body.dataset.navOpen = String(drawer === "nav");
    document.body.dataset.panelOpen = String(drawer === "panel");
  }, [drawer]);

  useEffect(() => {
    const closeRequested = () => close();
    const openRequested = (event: Event) => {
      const next = (event as CustomEvent<{ drawer?: string }>).detail?.drawer;
      if (next === "nav" || next === "panel") open(next);
    };
    const resize = () => { if (window.innerWidth > 960) close(); };
    const keydown = (event: KeyboardEvent) => { if (event.key === "Escape") close(); };
    window.addEventListener("tau:close-drawers", closeRequested);
    window.addEventListener("tau:open-drawer", openRequested);
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", keydown);
    return () => {
      window.removeEventListener("tau:close-drawers", closeRequested);
      window.removeEventListener("tau:open-drawer", openRequested);
      window.removeEventListener("resize", resize);
      window.removeEventListener("keydown", keydown);
    };
  }, []);

  return { drawer, close, open, toggle };
}
