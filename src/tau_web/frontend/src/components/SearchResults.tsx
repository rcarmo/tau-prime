import { useLayoutEffect, useState } from "preact/hooks";

type Result = { entityType: string; entityId: string; meta: string; text: string; sessionId: string | null };

export function SearchResults() {
  const [items, setItems] = useState<Result[]>([]);
  useLayoutEffect(() => {
    const update = (event: Event) => setItems((event as CustomEvent<{ items: Result[] }>).detail.items);
    window.addEventListener("tau:search-render", update);
    return () => window.removeEventListener("tau:search-render", update);
  }, []);
  return <ol id="search-results" className="search-panel__results" tabIndex={0} aria-label="Search results" aria-live="polite">
    {!items.length && <li>Search results will appear here.</li>}
    {items.map((result, index) => <li className="search-panel__item" key={`${result.entityType}-${result.entityId}-${index}`}>
      <article>
        <div className="search-panel__item-header">
          <strong className="search-panel__item-type">{result.entityType} · {result.entityId}</strong>
          <span className="search-panel__item-time">{result.meta}</span>
        </div>
        <span className="search-panel__item-text">{result.text}</span>
        {result.sessionId && <button type="button" onClick={() => window.dispatchEvent(new CustomEvent("tau:search-open-session", { detail: { sessionId: result.sessionId } }))}>Open session</button>}
      </article>
    </li>)}
  </ol>;
}
