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
    <div className="sessions-panel__filters" role="group" aria-label="Session list filter">
      <button id="show-active-sessions" type="button" aria-pressed={filter === "active"} onClick={() => onSelectFilter("active")}>Active</button>
      <button id="show-archived-sessions" type="button" aria-pressed={filter === "archived"} onClick={() => onSelectFilter("archived")}>Archived</button>
      <span id="session-count" className="sessions-panel__count">{items.length} session{items.length === 1 ? "" : "s"}</span>
    </div>
    <ul id="session-list" className="sessions-panel__list" aria-label="Available sessions">
      {!items.length && <li className="sessions-panel__item sessions-panel__placeholder">No sessions available.</li>}
      {items.map((session) => <li className="sessions-panel__item" key={session.sessionId}>
        <button type="button" className="sessions-panel__session" data-active={String(session.active)} onClick={() => select(session.sessionId)}>
          <div className="sessions-panel__session-body">
            <strong className="sessions-panel__session-title">{session.title}</strong>
            <span className="sessions-panel__session-meta">{session.meta}</span>
          </div>
        </button>
      </li>)}
    </ul>
  </>;
}
