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
    <section id="panel-plan" className="tasks-panel" aria-labelledby="tab-plan" hidden={hidden}>
      <div className="tasks-panel__tabs" role="tablist" aria-label="Plan views">
        <button className="tasks-panel__tab tasks-panel__tab--active" type="button" role="tab" aria-selected="true">Plan</button>
      </div>
      <div className="tasks-panel__tasks">
        <form id="plan-form" className="tasks-panel__card">
          <div className="tasks-panel__card-header">
            <span className="tasks-panel__card-id">Session plan</span>
            <span id="plan-revision" className="tasks-panel__badge tasks-panel__badge--kind">Revision {view.revision}</span>
          </div>
          <label className="tasks-panel__card-label" htmlFor="plan-editor">Shared checklist</label>
          <textarea id="plan-editor" className="plan-editor tasks-panel__card-mono" spellcheck placeholder="- [ ] Add a concrete next step" aria-describedby="plan-status" value={view.draft} disabled={view.disabled} />
          <p id="plan-status" className="tasks-panel__card-muted" aria-live="polite">{view.status}</p>
          <div id="plan-conflict" className="tasks-panel__sessions-error tasks-panel__sessions-error--inline" role="alert" hidden={!view.conflict}>The plan changed elsewhere. Reload the server version or save again after reviewing it.</div>
          <div className="tasks-panel__card-actions">
            <button id="plan-save-button" type="submit" disabled={view.disabled || !view.dirty}>Save plan</button>
            <button id="plan-reload-button" type="button" disabled={view.reloadDisabled}>Reload</button>
          </div>
        </form>
      </div>
    </section>
  );
}
