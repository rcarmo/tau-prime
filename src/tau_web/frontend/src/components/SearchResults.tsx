import { useLayoutEffect, useState } from "preact/hooks";

type Result = { entityType: string; entityId: string; meta: string; text: string; sessionId: string | null };

export function SearchResults() {
  const [items, setItems] = useState<Result[]>([]);
  useLayoutEffect(() => {
    const update = (event: Event) => setItems((event as CustomEvent<{ items: Result[] }>).detail.items);
    window.addEventListener("tau:search-render", update);
    return () => window.removeEventListener("tau:search-render", update);
  }, []);
  return <ol id="search-results" className="tau-search-results" tabIndex={0} aria-label="Search results" aria-live="polite">
    {!items.length && <li>Search results will appear here.</li>}
    {items.map((result, index) => <li className="tau-search-result" key={`${result.entityType}-${result.entityId}-${index}`}>
      <article className="post">
        <div className="post-body">
        <div className="post-meta">
          <strong className="post-author">{result.entityType} · {result.entityId}</strong>
          <span className="post-time">{result.meta}</span>
        </div>
        <span className="post-content">{result.text}</span>
        {result.sessionId && <button className="settings-panel__provider-btn" type="button" onClick={() => window.dispatchEvent(new CustomEvent("tau:search-open-session", { detail: { sessionId: result.sessionId } }))}>Open session</button>}
        </div>
      </article>
    </li>)}
  </ol>;
}
