import { useLayoutEffect, useState } from "preact/hooks";

export function StatusBar({ dashboardOpen, onToggleDashboard }: {
  dashboardOpen: boolean;
  onToggleDashboard: () => void;
}) {
  const [model, setModel] = useState("");
  const [connection, setConnection] = useState({ message: "Connecting…", state: "connecting" });
  useLayoutEffect(() => {
    const receive = (event: Event) => setConnection((event as CustomEvent<{ message: string; state: string }>).detail);
    window.addEventListener("tau:connection-state", receive);
    return () => window.removeEventListener("tau:connection-state", receive);
  }, []);
  useLayoutEffect(() => {
    const receive = (event: Event) => setModel((event as CustomEvent<{ model: string }>).detail.model);
    window.addEventListener("tau:status-model", receive);
    return () => window.removeEventListener("tau:status-model", receive);
  }, []);
  return <div className="tau-classic-status">
    <span hidden={connection.state === "live"}><span className="compose-connection-status">
      <span id="status-stream" data-state={connection.state}>{connection.message}</span>
    </span></span>
    <span id="status-model" className="compose-model-hint">{model || "Unset"}</span>
    <span id="status-context" className="sr-only">No context loaded</span>
    <button id="dashboard-toggle" className="icon-btn" type="button" aria-label="Dashboard" aria-controls="session-dashboard" aria-expanded={dashboardOpen} onClick={onToggleDashboard}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" /></svg>
      <span id="dashboard-count" className="sr-only">0</span>
    </button>
  </div>;
}
