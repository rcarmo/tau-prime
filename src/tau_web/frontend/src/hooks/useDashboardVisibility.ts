import { useEffect, useState } from "preact/hooks";

export function useDashboardVisibility() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    window.dispatchEvent(new CustomEvent("tau:dashboard-visibility", { detail: { open } }));
  }, [open]);

  useEffect(() => {
    const requested = (event: Event) => {
      setOpen(Boolean((event as CustomEvent<{ open?: boolean }>).detail?.open));
    };
    window.addEventListener("tau:set-dashboard", requested);
    return () => window.removeEventListener("tau:set-dashboard", requested);
  }, []);

  return { dashboardOpen: open, setDashboardOpen: setOpen };
}
