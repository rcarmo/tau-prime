import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import type { ApprovalRecord } from "../api/types";

type Approval = ApprovalRecord & { tool_name?: string; description?: string; arguments?: unknown };

export function ApprovalDialog() {
  const [approval, setApproval] = useState<Approval | null>(null);
  const [busy, setBusy] = useState(false);
  const denyRef = useRef<HTMLButtonElement>(null);

  useLayoutEffect(() => {
    const update = (event: Event) => {
      setBusy(false);
      setApproval((event as CustomEvent<{ approval?: Approval | null }>).detail?.approval ?? null);
    };
    window.addEventListener("tau:approval-render", update);
    return () => window.removeEventListener("tau:approval-render", update);
  }, []);

  useEffect(() => {
    if (!approval) return;
    denyRef.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      respond("deny");
    };
    window.addEventListener("keydown", escape, true);
    return () => window.removeEventListener("keydown", escape, true);
  }, [approval]);

  const respond = (decision: "allow" | "deny") => {
    if (!approval || busy) return;
    setBusy(true);
    window.dispatchEvent(new CustomEvent("tau:approval-response", { detail: { approvalId: approval.approval_id, decision } }));
  };

  if (!approval) return null;
  return (
    <div className="modal-dialog__backdrop approval-backdrop" data-approval-id={approval.approval_id} role="presentation">
      <section className="modal-dialog approval-prompt" role="alertdialog" aria-modal="true" aria-labelledby="approval-title" aria-describedby="approval-description" onMouseDown={(event) => event.stopPropagation()}>
        <h2 id="approval-title" className="modal-dialog__title">Allow {approval.tool_name || "tool"}?</h2>
        <p id="approval-description" className="modal-dialog__description">{approval.description || "The agent requested permission to run this tool."}</p>
        <pre className="modal-dialog__description approval-arguments">{JSON.stringify(approval.arguments ?? {}, null, 2)}</pre>
        <div className="modal-dialog__actions approval-actions">
          <button ref={denyRef} type="button" className="modal-dialog__btn modal-dialog__btn--destructive" disabled={busy} onClick={() => respond("deny")}>Deny</button>
          <button type="button" className="modal-dialog__btn modal-dialog__btn--primary" disabled={busy} onClick={() => respond("allow")}>Allow once</button>
        </div>
      </section>
    </div>
  );
}
