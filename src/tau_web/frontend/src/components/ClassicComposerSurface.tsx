import type { ComponentChildren } from "preact";
import { useLayoutEffect, useRef, useState } from "preact/hooks";

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
  const root = useRef<HTMLDivElement>(null);
  const drag = useRef<{ y: number; height: number } | null>(null);
  const [height, setHeight] = useState(50);
  // Match the pinned classic chat.css/responsive.css textarea limits.
  const limits = () => ({ min: window.innerWidth >= 1024 ? 70 : 50, max: window.innerWidth < 640 ? Math.min(window.innerHeight * 0.3, 200) : Math.min(window.innerHeight * 0.5, 520) });
  const bounds = limits();
  useLayoutEffect(() => {
    const textarea = root.current?.querySelector("textarea");
    if (textarea) { textarea.style.height = `${Math.max(bounds.min, Math.min(bounds.max, height))}px`; textarea.style.flex = "none"; textarea.style.boxSizing = "border-box"; }
  });
  const resize = (value: number) => {
    const minimum = parseFloat(getComputedStyle(root.current!.querySelector("textarea")!).minHeight) || 50;
    const next = Math.max(minimum, Math.min(limits().max, value));
    const textarea = root.current?.querySelector("textarea");
    if (textarea) { textarea.style.height = `${next}px`; textarea.style.flex = "none"; textarea.style.boxSizing = "border-box"; }
    setHeight(next);
  };
  return <div ref={root} className="compose-box" data-testid="compose-box">
    <div className="compose-resize-handle" role="separator" tabIndex={0} aria-label="Resize message input" aria-orientation="horizontal" aria-valuemin={bounds.min} aria-valuemax={Math.floor(bounds.max)} aria-valuenow={Math.round(Math.max(bounds.min, Math.min(bounds.max, height)))}
      onPointerDown={event => { event.preventDefault(); drag.current = {y:event.clientY,height:root.current?.querySelector("textarea")?.getBoundingClientRect().height ?? height}; event.currentTarget.setPointerCapture(event.pointerId); }}
      onPointerMove={event => { if (drag.current) resize(drag.current.height + drag.current.y - event.clientY); }}
      onPointerUp={event => { drag.current=null; if(event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }}
      onPointerCancel={() => { drag.current=null; }}
      onKeyDown={event => { if(event.key==='ArrowUp'||event.key==='ArrowDown'||event.key==='Home') {event.preventDefault();resize(event.key==='Home'?50:(root.current?.querySelector("textarea")?.getBoundingClientRect().height ?? height)+(event.key==='ArrowUp'?10:-10));} }} />
    {notices}
    {attachments}
    <div className="compose-input-wrapper">
      {session}
      <div className="compose-input-main">{input}</div>
      {completions}
      <div className="compose-footer">
        <div className="compose-meta-row"><div className="compose-model-meta">{metadata}</div></div>
        <div className="compose-actions">{actions}</div>
      </div>
    </div>
  </div>;
}
