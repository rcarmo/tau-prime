import type { ComponentChildren } from "preact";

const SelectControl = ({ id, name, label, children }: { id: string; name: string; label: string; children?: ComponentChildren }) => (
  <div className="compose-control">
    <label htmlFor={id}>{label}</label>
    <select id={id} name={name}>{children}</select>
  </div>
);

export function Composer() {
  return (
    <footer className="chat__compose">
      <div className="extension-slot" data-extension-slot="compose_above" />
      <form id="compose-form" className="compose-form chat__compose-container">
        <details className="chat__prompt-options">
          <summary>Prompt options</summary>
        <section className="compose-toolbar chat__toolbar" aria-label="Prompt controls">
          <div className="compose-select-grid">
            <SelectControl id="compose-provider-select" name="provider_name" label="Provider" />
            <SelectControl id="compose-model-select" name="model" label="Model" />
            <SelectControl id="compose-thinking-select" name="compose_thinking_level" label="Thinking" />
            <SelectControl id="compose-delivery-mode" name="delivery_mode" label="Delivery">
              <option value="run">Run immediately</option><option value="follow_up">Queue follow-up</option><option value="steer">Queue steer</option>
            </SelectControl>
          </div>
          <p id="compose-context-readout" className="muted small-text">No session selected. Sending will create one.</p>
          <div className="compose-attachment-bar">
            <button id="compose-attachment-button" type="button">Attach files</button>
            <button id="compose-clear-attachments" type="button">Clear staged</button>
            <input id="compose-file-input" className="sr-only" type="file" multiple aria-label="Attach files" />
          </div>
          <ul id="compose-attachment-list" className="compose-attachment-list" aria-live="polite" aria-label="Staged attachments" />
        </section>
        </details>
        <label className="sr-only" htmlFor="compose-input">Send a prompt to Tau</label>
        <div className="compose-editor-group">
          <div className="compose-row">
            <textarea id="compose-input" className="chat__input" name="prompt" rows={3} autoComplete="off" role="combobox" aria-autocomplete="list" aria-controls="compose-completion-listbox" aria-describedby="compose-help compose-completion-status" aria-expanded="false" aria-haspopup="listbox" placeholder="Select or create a session, then send a prompt." />
            <button id="compose-submit" className="chat__send-btn" type="submit" aria-label="Run">↑</button>
          </div>
          <div id="compose-completion-popup" className="compose-completion-popup" hidden>
            <p id="compose-completion-status" className="muted small-text" aria-live="polite" />
            <ul id="compose-completion-listbox" className="compose-completion-listbox" role="listbox" aria-label="Composer completions" />
          </div>
        </div>
        <div className="compose-status-row">
          <p id="compose-help" className="muted small-text">Enter sends. Shift+Enter inserts a newline.</p>
          <p id="app-status" className="small-text" aria-live="polite">Loading Tau shell…</p>
        </div>
      </form>
      <div className="extension-slot" data-extension-slot="compose_below" />
    </footer>
  );
}
