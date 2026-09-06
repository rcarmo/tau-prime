import type { RefObject } from "preact";
import { useState } from "preact/hooks";

/** Supported Tau message actions in Piclaw's action-bar hierarchy. */
export function MessageActionBar({ content, collapsed, onToggle, toggleRef }: { content: string; collapsed: boolean; onToggle: () => void; toggleRef: RefObject<HTMLButtonElement> }) {
  const [feedback, setFeedback] = useState("");
  return <div className="message-action-bar" onClick={event => event.stopPropagation()}>
    <button type="button" className="message-action-bar__btn" aria-label="Copy message" title="Copy message" onClick={async () => {
      try { await navigator.clipboard.writeText(content); setFeedback("Message copied"); }
      catch { setFeedback("Unable to copy message"); }
    }}><i className="codicon codicon-copy" aria-hidden="true" /></button>
    <button ref={toggleRef} type="button" className="message-action-bar__btn" title={collapsed ? "Expand message" : "Collapse message"} aria-label={collapsed ? "Expand message" : "Collapse message"} aria-expanded={!collapsed} onClick={onToggle}>
      <i className={`codicon codicon-${collapsed ? "chevron-down" : "chevron-up"}`} aria-hidden="true" />
    </button>
    <span className="sr-only" role="status">{feedback}</span>
  </div>;
}
