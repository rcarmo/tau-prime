import { useEffect, useState } from "preact/hooks";

export type Drawer = "nav" | "panel" | null;

export function useDrawers() {
  const [drawer, setDrawer] = useState<Drawer>(null);
  const close = () => setDrawer(null);
  const toggle = (next: Exclude<Drawer, null>) => {
    setDrawer((current) => current === next ? null : next);
  };

  useEffect(() => {
    document.body.dataset.navOpen = String(drawer === "nav");
    document.body.dataset.panelOpen = String(drawer === "panel");
  }, [drawer]);

  useEffect(() => {
    const closeRequested = () => close();
    const resize = () => { if (window.innerWidth > 960) close(); };
    const keydown = (event: KeyboardEvent) => { if (event.key === "Escape") close(); };
    window.addEventListener("tau:close-drawers", closeRequested);
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", keydown);
    return () => {
      window.removeEventListener("tau:close-drawers", closeRequested);
      window.removeEventListener("resize", resize);
      window.removeEventListener("keydown", keydown);
    };
  }, []);

  return { drawer, close, toggle };
}
