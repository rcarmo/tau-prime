import { ClassicIcon } from "./ClassicIcon";
import type { RefObject } from "preact";
import { useState } from "preact/hooks";

/** Supported Tau message actions in Piclaw's action-bar hierarchy. */
export function MessageActionBar({ content, collapsed, onToggle, toggleRef }: { content: string; collapsed: boolean; onToggle: () => void; toggleRef: RefObject<HTMLButtonElement> }) {
  const [feedback, setFeedback] = useState("");
  return <div className="post-action-controls" onClick={event => event.stopPropagation()}>
    {content && <button type="button" className="post-action-btn post-copy-btn" aria-label="Copy message" title="Copy message" onClick={async () => {
      try { await navigator.clipboard.writeText(content); setFeedback("Message copied"); }
      catch { setFeedback("Unable to copy message"); }
    }}><ClassicIcon name="copy" /></button>}
    <button ref={toggleRef} type="button" className="post-action-btn" title={collapsed ? "Expand message" : "Collapse message"} aria-label={collapsed ? "Expand message" : "Collapse message"} aria-expanded={!collapsed} onClick={onToggle}>
      <ClassicIcon name={collapsed ? "down" : "up"} />
    </button>
    <span className="sr-only" role="status">{feedback}</span>
  </div>;
}
