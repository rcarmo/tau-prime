import { ClassicIcon } from "./ClassicIcon";
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
  return <section id="panel-workspace" className="tau-workspace" aria-labelledby="tab-workspace" hidden={hidden}>
    <div className="workspace-tree">
      <div className="workspace-header"><span>Files</span><div className="workspace-header-actions">
        <button id="workspace-up-button" className="icon-btn" type="button" title="Parent directory" aria-label="Parent directory"><ClassicIcon name="up" /></button>
        <button id="workspace-reload-button" className="icon-btn" type="button" title="Refresh" aria-label="Refresh workspace"><ClassicIcon name="refresh" /></button>
      </div></div>
      <p id="workspace-path" className="tau-workspace-path">{view.path}</p>
      <div id="workspace-list" className="workspace-tree-list" role="tree" aria-label="Workspace tree">
        {!view.entries.length && <div>No workspace entries available.</div>}
        {view.entries.map((entry) => <div key={`${entry.kind}:${entry.path ?? entry.name}`}><button type="button" className="workspace-row" role="treeitem" aria-label={entry.name} disabled={entry.kind !== "directory" && entry.kind !== "file"} onClick={() => window.dispatchEvent(new CustomEvent("tau:workspace-open", { detail: { entry } }))}>
          <ClassicIcon name={entry.kind === "directory" ? "folder" : "file"} /><span className="workspace-label"><span className="workspace-label-text">{entry.name}</span></span><span className="sr-only">{entry.kind}</span>
        </button></div>)}
      </div>
    </div>
    <div className="workspace-preview"><div className="workspace-preview-header">Preview</div><section className="workspace-preview-body" aria-labelledby="workspace-editor-title">
      <div id="workspace-editor-title" className="workspace-preview-title">Selected file</div><div id="workspace-editor-path" className="tau-workspace-path">{view.filePath ?? "No file selected"}</div>
      <label className="sr-only" htmlFor="workspace-editor">Workspace file editor</label><textarea id="workspace-editor" className="tau-workspace-source" spellcheck={false} aria-describedby={describedBy} value={view.content} readOnly />
      <p id="workspace-editor-note" className="tau-workspace-note">Local edits are not yet persisted through the web shell.</p>
      <section id="workspace-annotations" className="workspace-annotations" hidden={!view.annotations.length}><h4>Annotations</h4><ul id="workspace-annotation-list" className="workspace-annotation-list">{view.annotations.map((annotation, index) => <li className="workspace-annotation" data-severity={annotation.severity} key={`${annotation.line}:${index}`}>Line {annotation.line}{annotation.endLine ? `–${annotation.endLine}` : ""}{annotation.source ? ` · ${annotation.source}` : ""}: {annotation.message}</li>)}</ul></section>
      <section id="workspace-renderer" className="workspace-renderer" aria-label="Extension file preview" hidden />
    </section></div>
  </section>;
}
