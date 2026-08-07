import { useLayoutEffect, useState } from "preact/hooks";

type Entry = { name: string; kind: string; path?: string };
type Annotation = { line: number; endLine: number | null; severity: string; source: string; message: string };
type WorkspaceView = { path: string; filePath: string | null; content: string; entries: Entry[]; annotations: Annotation[] };
const empty: WorkspaceView = { path: ".", filePath: null, content: "", entries: [], annotations: [] };

export function WorkspacePanel({ hidden }: { hidden: boolean }) {
  const [view, setView] = useState(empty);
  useLayoutEffect(() => {
    const update = (event: Event) => setView((event as CustomEvent<WorkspaceView>).detail);
    window.addEventListener("tau:workspace-render", update);
    return () => window.removeEventListener("tau:workspace-render", update);
  }, []);
  const describedBy = view.annotations.length ? "workspace-editor-note workspace-annotations" : "workspace-editor-note";
  return <section id="panel-workspace" className="workspace" aria-labelledby="tab-workspace" hidden={hidden}>
    <div className="workspace__pane-top">
      <div className="workspace__section-header workspace__section-header--padded"><span>Files</span><div className="workspace__files-toolbar">
        <button id="workspace-up-button" className="workspace__files-toolbar-icon codicon codicon-arrow-up" type="button" title="Parent directory" aria-label="Parent directory" />
        <button id="workspace-reload-button" className="workspace__files-toolbar-icon codicon codicon-refresh" type="button" title="Refresh" aria-label="Refresh workspace" />
      </div></div>
      <p id="workspace-path" className="workspace__current-path">{view.path}</p>
      <div id="workspace-list" className="file-tree" role="tree" aria-label="Workspace tree">
        {!view.entries.length && <div>No workspace entries available.</div>}
        {view.entries.map((entry) => <div key={`${entry.kind}:${entry.path ?? entry.name}`}><button type="button" className="file-tree__item" role="treeitem" disabled={entry.kind !== "directory" && entry.kind !== "file"} onClick={() => window.dispatchEvent(new CustomEvent("tau:workspace-open", { detail: { entry } }))}>
          <span className={`file-tree__icon codicon codicon-${entry.kind === "directory" ? "folder" : "file"}`} aria-hidden="true" /><span className="file-tree__name">{entry.name}</span><span className="file-tree__meta">{entry.kind}</span>
        </button></div>)}
      </div>
    </div>
    <div className="workspace__drag-handle" role="separator" aria-orientation="horizontal" />
    <div className="workspace__pane-bottom"><div className="workspace__preview-header">Preview</div><section className="workspace__preview-info" aria-labelledby="workspace-editor-title">
      <div id="workspace-editor-title" className="workspace__preview-name">Selected file</div><div id="workspace-editor-path" className="workspace__preview-path">{view.filePath ?? "No file selected"}</div>
      <label className="sr-only" htmlFor="workspace-editor">Workspace file editor</label><textarea id="workspace-editor" className="workspace__preview-content" spellcheck={false} aria-describedby={describedBy} value={view.content} readOnly />
      <p id="workspace-editor-note" className="workspace__preview-meta">Local edits are not yet persisted through the web shell.</p>
      <section id="workspace-annotations" className="workspace-annotations" hidden={!view.annotations.length}><h4>Annotations</h4><ul id="workspace-annotation-list" className="workspace-annotation-list">{view.annotations.map((annotation, index) => <li className="workspace-annotation" data-severity={annotation.severity} key={`${annotation.line}:${index}`}>Line {annotation.line}{annotation.endLine ? `–${annotation.endLine}` : ""}{annotation.source ? ` · ${annotation.source}` : ""}: {annotation.message}</li>)}</ul></section>
      <section id="workspace-renderer" className="workspace-renderer" aria-label="Extension file preview" hidden />
    </section></div>
  </section>;
}
