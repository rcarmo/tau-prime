import { useLayoutEffect, useState } from "preact/hooks";

type PlanViewState = {
  draft: string;
  revision: number;
  dirty: boolean;
  disabled: boolean;
  reloadDisabled: boolean;
  conflict: boolean;
  status: string;
};

const INITIAL: PlanViewState = {
  draft: "", revision: 0, dirty: false, disabled: true, reloadDisabled: true,
  conflict: false, status: "Select a session to edit its shared plan.",
};

export function PlanPanel({ hidden }: { hidden: boolean }) {
  const [view, setView] = useState(INITIAL);
  useLayoutEffect(() => {
    const update = (event: Event) => {
      const detail = (event as CustomEvent<PlanViewState>).detail;
      if (detail) setView(detail);
    };
    window.addEventListener("tau:plan-render", update);
    return () => window.removeEventListener("tau:plan-render", update);
  }, []);

  return (
    <section id="panel-plan" className="tau-plan-panel" aria-labelledby="tab-plan" hidden={hidden}>
      <div className="tau-plan-tasks">
        <form id="plan-form" className="tau-plan-card">
          <div className="tau-plan-card-header">
            <span className="tau-plan-card-id">Session plan</span>
            <span id="plan-revision" className="tau-plan-revision">Revision {view.revision}</span>
          </div>
          <label className="tau-plan-card-label" htmlFor="plan-editor">Shared checklist</label>
          <textarea id="plan-editor" className="plan-editor tau-plan-card-mono" spellcheck placeholder="- [ ] Add a concrete next step" aria-describedby="plan-status" value={view.draft} disabled={view.disabled} />
          <p id="plan-status" className="tau-plan-card-muted" aria-live="polite">{view.status}</p>
          <div id="plan-conflict" className="tau-plan-conflict" role="alert" hidden={!view.conflict}>The plan changed elsewhere. Reload the server version or save again after reviewing it.</div>
          <div className="tau-plan-card-actions">
            <button id="plan-save-button" type="submit" disabled={view.disabled || !view.dirty}>Save plan</button>
            <button id="plan-reload-button" type="button" disabled={view.reloadDisabled}>Reload</button>
          </div>
        </form>
      </div>
    </section>
  );
}
