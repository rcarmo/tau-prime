/** Inline classic-style icons: no dependency on visual-mode Codicon fonts. */
export function ClassicIcon({ name }: { name: "copy" | "up" | "down" | "attach" | "refresh" | "folder" | "file" }) {
  return <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    {name === "copy" ? <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></> :
      name === "attach" ? <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l10.61-10.6a4 4 0 0 1 5.66 5.65L9.41 17.41a2 2 0 0 1-2.83-2.82l9.9-9.9" /> :
      name === "refresh" ? <><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 6a8 8 0 0 1 13 2M5 16a8 8 0 0 0 13 2"/></> :
      name === "folder" ? <path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/> :
      name === "file" ? <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></> :
      <path d={name === "up" ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} />}
  </svg>;
}
