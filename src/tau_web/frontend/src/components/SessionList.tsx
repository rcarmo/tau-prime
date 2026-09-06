import { useLayoutEffect, useState } from "preact/hooks";
import type { SessionFilter } from "../hooks/useSessionFilter";

type SessionItem = { sessionId: string; title: string; meta: string; active: boolean };

export function SessionList({ filter, onSelectFilter }: { filter: SessionFilter; onSelectFilter: (filter: SessionFilter) => void }) {
  const [items, setItems] = useState<SessionItem[]>([]);
  useLayoutEffect(() => {
    const update = (event: Event) => setItems((event as CustomEvent<{ items: SessionItem[] }>).detail.items);
    window.addEventListener("tau:sessions-render", update);
    return () => window.removeEventListener("tau:sessions-render", update);
  }, []);
  const select = (sessionId: string) => window.dispatchEvent(new CustomEvent("tau:session-select", { detail: { sessionId } }));
  return <>
    <div className="tau-session-filters" role="group" aria-label="Session list filter">
      <button id="show-active-sessions" className="settings-panel__provider-btn" type="button" aria-pressed={filter === "active"} onClick={() => onSelectFilter("active")}>Active</button>
      <button id="show-archived-sessions" className="settings-panel__provider-btn" type="button" aria-pressed={filter === "archived"} onClick={() => onSelectFilter("archived")}>Archived</button>
      <span id="session-count" className="tau-session-count">{items.length} session{items.length === 1 ? "" : "s"}</span>
    </div>
    <ul id="session-list" className="tau-session-list" aria-label="Available sessions">
      {!items.length && <li className="compose-model-popup-empty">No sessions available.</li>}
      {items.map((session) => <li className="tau-session-item" key={session.sessionId}>
        <button type="button" className={`compose-model-popup-item session-item${session.active ? " active" : ""}`} aria-current={session.active ? "true" : undefined} data-active={String(session.active)} onClick={() => select(session.sessionId)}>
          <div className="compose-model-popup-label">
            <strong className="tau-session-title">{session.title}</strong>
            <span className="compose-model-popup-jid">{session.meta}</span>
          </div>
        </button>
      </li>)}
    </ul>
  </>;
}
