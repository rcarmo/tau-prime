import { Fragment, type ComponentChildren } from "preact";

const SelectControl = ({ id, name, label, children }: { id: string; name: string; label: string; children?: ComponentChildren }) => (
  <div className="compose-control">
    <label htmlFor={id}>{label}</label>
    <select id={id} name={name}>{children}</select>
  </div>
);

export function Composer() {
  return (
    <Fragment>
      <div className="extension-slot" data-extension-slot="compose_above" />
      <form id="compose-form" className="chat__compose">
        <div className="chat__compose-container">
          <div className="chat__toolbar" aria-label="Prompt controls">
            <button id="compose-attachment-button" className="chat__toolbar-btn" type="button" aria-label="Attach file" title="Attach file">
              <i className="codicon codicon-attach" aria-hidden="true" />
              <span className="sr-only">Attach file</span>
            </button>
            <input id="compose-file-input" type="file" multiple hidden aria-label="Attach files" />
            <details className="chat__prompt-options">
              <summary className="chat__toolbar-btn" aria-label="Prompt options" title="Prompt options">
                <i className="codicon codicon-settings-gear" aria-hidden="true" />
              </summary>
              <section className="compose-toolbar" aria-label="Model and delivery controls">
                <div className="compose-select-grid">
                  <SelectControl id="compose-provider-select" name="provider_name" label="Provider" />
                  <SelectControl id="compose-model-select" name="model" label="Model" />
                  <SelectControl id="compose-thinking-select" name="compose_thinking_level" label="Thinking" />
                  <SelectControl id="compose-delivery-mode" name="delivery_mode" label="Delivery">
                    <option value="run">Run immediately</option>
                    <option value="follow_up">Queue follow-up</option>
                    <option value="steer">Queue steer</option>
                  </SelectControl>
                </div>
                <p id="compose-context-readout" className="muted small-text">No session selected. Sending will create one.</p>
              </section>
            </details>
          </div>

          <div id="compose-attachment-list" className="chat__attachments" role="region" aria-live="polite" aria-label="Staged attachments" />
          <button id="compose-clear-attachments" className="chat__attachment-clear" type="button" aria-label="Clear all attachments" hidden>Clear all</button>

          <label className="sr-only" htmlFor="compose-input">Send a prompt to Tau</label>
          <textarea
            id="compose-input"
            className="chat__input"
            name="prompt"
            rows={3}
            autoComplete="off"
            role="combobox"
            aria-autocomplete="list"
            aria-controls="compose-completion-listbox"
            aria-describedby="compose-help compose-completion-status"
            aria-expanded="false"
            aria-haspopup="listbox"
            placeholder="Type a message..."
          />
          <div id="compose-completion-popup" className="compose-completion-popup" hidden>
            <p id="compose-completion-status" className="muted small-text" aria-live="polite" />
            <ul id="compose-completion-listbox" className="compose-completion-listbox" role="listbox" aria-label="Composer completions" />
          </div>
        </div>

        <button id="compose-submit" className="chat__send-btn" type="submit" aria-label="Run" title="Send (Enter)">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
          <span className="sr-only">Run</span>
        </button>
      </form>
      <div className="sr-only">
        <p id="compose-help" className="muted small-text">Enter sends. Shift+Enter inserts a newline.</p>
        <p id="app-status" className="small-text" aria-live="polite">Loading Tau shell…</p>
      </div>
      <div className="extension-slot" data-extension-slot="compose_below" />
    </Fragment>
  );
}
