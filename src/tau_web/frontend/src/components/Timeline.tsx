import { Fragment } from "preact";
import { CopyButton } from "./CopyButton";
import { MarkdownContent } from "./MarkdownContent";
import { useEffect, useLayoutEffect, useState } from "preact/hooks";

type Attachment = { mediaId: string; filename: string; mediaType: string };
type ToolCall = { id?: string; name?: string; arguments?: unknown };
type TimelineMessage = {
  id?: string;
  role: string;
  content: string;
  attachments?: Attachment[];
  toolCalls?: ToolCall[];
  toolCallId?: string;
  toolName?: string;
  toolOk?: boolean;
  meta: string;
  live?: boolean;
};
type TimelineState = { selected: boolean; items: TimelineMessage[] };

function valueText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try { return JSON.stringify(value, null, 2); } catch { return String(value); }
}

export function ToolCallBlock({ call, result }: { call: ToolCall; result?: TimelineMessage }) {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const name = call.name || result?.toolName || "tool";
  const input = valueText(call.arguments);
  const output = result?.content ?? "";
  const lines = output.split("\n");
  const hiddenLines = !expanded && lines.length > 20 ? lines.length - 20 : 0;
  const displayedOutput = hiddenLines ? lines.slice(-20).join("\n") : output;
  return (
    <div className="message-list__tool-call">
      <button className="message-list__tool-call-header" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <span className="message-list__tool-call-icon">{open ? "▾" : "▸"}</span>
        <span className="message-list__tool-call-name">{name}</span>
        {result && <span className="message-list__tool-call-badge">{result.toolOk === false ? "failed" : "done"}</span>}
      </button>
      {open && (
        <div className="message-list__tool-call-body">
          {input && <div className="tool-call__pre-wrapper"><CopyButton text={input} /><pre className="message-list__tool-call-code">{input}</pre></div>}
          {output && <Fragment><div className="message-list__tool-call-result-label">Result</div><div className="tool-call__pre-wrapper">
            {hiddenLines > 0 && <button type="button" className="tool-call__hidden-lines" title="Show full output" onClick={() => setExpanded(true)}>{hiddenLines} lines hidden — click to expand</button>}
            {expanded && <button type="button" className="tool-call__hidden-lines tool-call__hidden-lines--collapse" onClick={() => setExpanded(false)}>collapse</button>}
            <CopyButton text={output} /><pre className="message-list__tool-call-code">{displayedOutput}</pre>
          </div></Fragment>}
        </div>
      )}
    </div>
  );
}

function AttachmentChip({ attachment }: { attachment: Attachment }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const contentUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/content`;
  const thumbnailUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/thumbnail`;
  const token = localStorage.getItem("tau.web.authToken");

  useEffect(() => {
    if (!token || !attachment.mediaType.startsWith("image/")) return;
    let objectUrl: string | null = null;
    const controller = new AbortController();
    void fetch(thumbnailUrl, { headers: { Authorization: `Bearer ${token}` }, credentials: "same-origin", signal: controller.signal })
      .then((response) => response.ok ? response.blob() : Promise.reject(new Error("Preview unavailable")))
      .then((blob) => { objectUrl = URL.createObjectURL(blob); setPreviewUrl(objectUrl); })
      .catch(() => undefined);
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [attachment.mediaType, thumbnailUrl, token]);

  const download = async (event: MouseEvent) => {
    if (!token) return;
    event.preventDefault();
    const response = await fetch(contentUrl, { headers: { Authorization: `Bearer ${token}` }, credentials: "same-origin" });
    if (!response.ok) return;
    const objectUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = attachment.filename;
    link.click();
    URL.revokeObjectURL(objectUrl);
  };

  return (
    <a className="attachment-chip" href={contentUrl} target="_blank" rel="noopener" title={attachment.filename} onClick={(event) => void download(event)}>
      {attachment.mediaType.startsWith("image/") ? (
        <img className="attachment-chip__preview" src={previewUrl ?? thumbnailUrl} alt="" loading="lazy" />
      ) : <span className="attachment-chip__icon" aria-hidden="true">📄</span>}
      <span className="attachment-chip__name">{attachment.filename}</span>
      <i className="codicon codicon-desktop-download attachment-chip__action" aria-hidden="true" />
    </a>
  );
}

export function MessageItem({ item, resultByCall }: { item: TimelineMessage; resultByCall: Map<string, TimelineMessage> }) {
  const isUser = item.role === "user";
  const isTool = item.role === "tool";
  if (isTool) return null;
  return (
    <div className={`message-list__item message-list__item--${isUser ? "user" : "agent"}`} data-message-id={item.id}>
      <div className={`message-list__avatar-circle message-list__avatar-circle--${isUser ? "user" : "agent"}`} aria-hidden="true">{isUser ? "Y" : "τ"}</div>
      <div className={item.live ? "message-list__body message-list__body--draft" : "message-list__body"}>
        <div className="message-list__header">
          <span className={`message-list__name message-list__name--${isUser ? "user" : "agent"}`}>{isUser ? "You" : "Tau"}</span>
          <span className="message-list__time">{item.live ? "live" : item.meta}</span>
        </div>
        {item.toolCalls && item.toolCalls.length > 0 && (
          <div className="message-list__tool-calls">
            {item.toolCalls.map((call, index) => <ToolCallBlock key={call.id ?? index} call={call} result={call.id ? resultByCall.get(call.id) : undefined} />)}
          </div>
        )}
        {item.content && (isUser ? <div className="message-list__content">{item.content}</div> : <MarkdownContent content={item.content} />)}
        {item.attachments && item.attachments.length > 0 && (
          <div className="message-list__attachments">{item.attachments.map((attachment) => <AttachmentChip key={attachment.mediaId} attachment={attachment} />)}</div>
        )}
      </div>
    </div>
  );
}

export function Timeline() {
  const [timeline, setTimeline] = useState<TimelineState>({ selected: false, items: [] });
  useLayoutEffect(() => {
    const update = (event: Event) => {
      const detail = (event as CustomEvent<TimelineState>).detail;
      if (detail && Array.isArray(detail.items)) setTimeline(detail);
    };
    window.addEventListener("tau:timeline-render", update);
    return () => window.removeEventListener("tau:timeline-render", update);
  }, []);

  const resultByCall = new Map<string, TimelineMessage>();
  for (const item of timeline.items) if (item.role === "tool" && item.toolCallId) resultByCall.set(item.toolCallId, item);
  const visibleItems = timeline.items.filter((item) => item.role !== "tool");
  const empty = !timeline.selected ? "Select or create a session to load the timeline." : "No persisted messages yet.";

  return (
    <Fragment>
      <div className="extension-slot" data-extension-slot="timeline_before" />
      <div id="timeline-main" className="message-list" tabIndex={-1}>
        <div id="timeline-meta" className="message-list__empty" aria-live="polite">Load a session to inspect persisted messages.</div>
        <div id="timeline-list" aria-live="polite" tabIndex={0}>
          {visibleItems.length === 0
            ? <div className="message-list__empty"><p>{empty}</p></div>
            : visibleItems.map((item, index) => <MessageItem key={item.id ?? index} item={item} resultByCall={resultByCall} />)}
        </div>
      </div>
      <div className="extension-slot" data-extension-slot="timeline_after" />
    </Fragment>
  );
}

/** Tau branch selection mapped to Piclaw's between-timeline-and-compose status surface. */
export function SessionRuntime() {
  const [branches, setBranches] = useState<Array<{ leafId: string; label: string; active: boolean }>>([]);
  useLayoutEffect(() => {
    const update = (event: Event) => setBranches((event as CustomEvent<{ items: Array<{ leafId: string; label: string; active: boolean }> }>).detail.items);
    window.addEventListener("tau:branches-render", update);
    return () => window.removeEventListener("tau:branches-render", update);
  }, []);
  return (
    <div className="agent-status-panel" aria-label="Session runtime">
      <div className="agent-status-panel__status" aria-live="polite">
        <span id="agent-status-indicator" className="agent-status-panel__status-dot" aria-hidden="true" />
        <span id="agent-status-text" className="agent-status-panel__status-text">No session selected</span>
      </div>
      <section className="agent-status-panel__section">
        <div className="agent-status-panel__title">Session branch</div>
        <div id="branch-list" className="agent-status-panel__tools">
          {branches.map((branch) => <button type="button" className="branch-button" data-active={String(branch.active)} onClick={() => window.dispatchEvent(new CustomEvent("tau:branch-select", { detail: { leafId: branch.leafId } }))}>{branch.label}</button>)}
          {!branches.length && <span className="muted-text">No persisted branches yet.</span>}
        </div>
      </section>
    </div>
  );
}
