import type { ComponentChildren } from "preact";

/** Structure ported from classic components/compose-box.ts.
 * Slots keep Tau's adapter IDs, state and event ownership in the caller.
 */
export function ClassicComposerSurface({ session, input, metadata, actions, notices, attachments, completions }: {
  session: ComponentChildren;
  input: ComponentChildren;
  metadata: ComponentChildren;
  actions: ComponentChildren;
  notices?: ComponentChildren;
  attachments?: ComponentChildren;
  completions?: ComponentChildren;
}) {
  return <div className="compose-box" data-testid="compose-box">
    {notices}
    {attachments}
    <div className="compose-input-wrapper">
      <div className="compose-top-session-row">{session}</div>
      <div className="compose-input-main">{input}</div>
      {completions}
      <div className="compose-footer">
        <div className="compose-meta-row"><div className="compose-model-meta">{metadata}</div></div>
        <div className="compose-actions">{actions}</div>
      </div>
    </div>
  </div>;
}
