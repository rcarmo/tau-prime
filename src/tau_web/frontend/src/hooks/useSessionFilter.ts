import { useState } from "preact/hooks";

export type SessionFilter = "active" | "archived";

export function useSessionFilter() {
  const [filter, setFilter] = useState<SessionFilter>(() =>
    window.localStorage.getItem("tau.web.sessionFilter") === "archived" ? "archived" : "active"
  );

  const selectFilter = (next: SessionFilter) => {
    setFilter(next);
    window.localStorage.setItem("tau.web.sessionFilter", next);
    window.dispatchEvent(new CustomEvent("tau:session-filter", { detail: { filter: next } }));
  };

  return { sessionFilter: filter, selectSessionFilter: selectFilter };
}
