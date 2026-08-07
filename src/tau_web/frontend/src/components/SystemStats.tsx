import { useLayoutEffect, useState } from "preact/hooks";

type MeterSnapshot = {
  cpu_percent?: number | null; ram_percent?: number | null; process_rss_bytes?: number | null; swap_percent?: number | null;
  cpu_series?: number[]; ram_series?: number[]; process_rss_series_bytes?: number[]; swap_series?: number[];
};

type SystemStatsState = { enabled: boolean; collapsed: boolean; meters: MeterSnapshot | null };

const formatPercent = (value: number | null | undefined) => Number.isFinite(value) ? `${Math.round(value as number)}%` : "--";
const formatBytes = (value: number | null | undefined) => {
  if (!Number.isFinite(value)) return "--";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let amount = value as number;
  let unit = 0;
  while (amount >= 1024 && unit < units.length - 1) { amount /= 1024; unit += 1; }
  return `${amount.toFixed(unit > 1 && amount < 10 ? 1 : 0)} ${units[unit]}`;
};
const severity = (value: number | null | undefined) => value != null && value > 85 ? "error" : value != null && value >= 60 ? "warning" : "normal";
const points = (series: number[] | undefined, maximum: number | null) => {
  const values = (series ?? []).filter(Number.isFinite);
  if (values.length < 2) return "";
  const max = maximum ?? Math.max(...values, 1);
  return values.map((value, index) => `${(index / (values.length - 1)) * 48},${12 - Math.min(1, Math.max(0, value / max)) * 12}`).join(" ");
};

function Metric({ id, label, icon, value, series, maximum }: { id: string; label: string; icon: string; value: string; series?: number[]; maximum: number | null }) {
  const numeric = series?.at(-1);
  const level = id === "swap" && numeric && numeric > 0 ? "warning" : severity(numeric);
  return <span className="sys-stats__metric" title={`${label} usage`}>
    <i className={`sys-stats__icon codicon ${icon}`} aria-hidden="true" />
    <span className="sys-stats__label">{label}</span>
    <output id={`meter-${id}-value`} className={`sys-stats__value${level === "normal" ? "" : ` sys-stats__value--${level}`}`}>{value}</output>
    <svg id={`meter-${id}-sparkline`} className="sys-stats__sparkline" viewBox="0 0 48 12" role="img" aria-label={`${label === "RSS" ? "Tau RSS" : label} history`}>
      {points(series, maximum) && <polyline className="meter-sparkline" points={points(series, maximum)} />}
    </svg>
  </span>;
}

export function SystemStats({ enabled, collapsed, onToggleEnabled, onToggleCollapsed }: { enabled: boolean; collapsed: boolean; onToggleEnabled: () => void; onToggleCollapsed: () => void }) {
  const [state, setState] = useState<SystemStatsState>({ enabled, collapsed, meters: null });
  useLayoutEffect(() => {
    const update = (event: Event) => setState((event as CustomEvent<SystemStatsState>).detail);
    window.addEventListener("tau:meters-render", update);
    return () => window.removeEventListener("tau:meters-render", update);
  }, []);
  const meters = state.meters;
  const cpu = formatPercent(meters?.cpu_percent), ram = formatPercent(meters?.ram_percent);
  const rss = formatBytes(meters?.process_rss_bytes), swap = formatPercent(meters?.swap_percent);
  const summary = !state.enabled ? "Meters hidden" : !meters ? "Meters unavailable" : `CPU ${cpu} · RAM ${ram} · RSS ${rss} · Swap ${swap}`;
  return <span id="system-meters" className="sys-stats-bar" data-enabled={String(state.enabled)} data-collapsed={String(state.collapsed)}>
    <span className="sys-stats-bar__inline"><span id="meters-details" className="sys-stats">
      <Metric id="cpu" label="CPU" icon="codicon-pulse" value={cpu} series={meters?.cpu_series} maximum={100} />
      <Metric id="ram" label="RAM" icon="codicon-circuit-board" value={ram} series={meters?.ram_series} maximum={100} />
      <Metric id="rss" label="RSS" icon="codicon-package" value={rss} series={meters?.process_rss_series_bytes} maximum={null} />
      <Metric id="swap" label="SWP" icon="codicon-arrow-swap" value={swap} series={meters?.swap_series} maximum={100} />
    </span></span>
    <output id="meters-summary" className="sys-stats-bar__compact" aria-live="polite">{summary}</output>
    <button id="meters-collapse-button" className="status-bar__terminal-btn" type="button" aria-controls="meters-details" aria-expanded={!state.collapsed} title={state.collapsed ? "Expand system meters" : "Compact system meters"} onClick={onToggleCollapsed}><i className={`codicon ${state.collapsed ? "codicon-chevron-up" : "codicon-chevron-down"}`} aria-hidden="true" /></button>
    <button id="meters-visibility-button" className="status-bar__terminal-btn" type="button" aria-pressed={state.enabled} title={state.enabled ? "Hide system meters" : "Show system meters"} onClick={onToggleEnabled}><i className={`codicon ${state.enabled ? "codicon-eye" : "codicon-eye-closed"}`} aria-hidden="true" /></button>
  </span>;
}
