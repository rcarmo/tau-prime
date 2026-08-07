import { Fragment } from "preact";
import { useLayoutEffect, useState } from "preact/hooks";

type CompletionItem = { label: string; detail: string };
type CompletionView = { open: boolean; index: number; items: CompletionItem[] };
type AttachmentView = { items: Array<{ mediaId: string; filename: string; label: string }>; busy: boolean };

export function Composer() {
  const [completion, setCompletion] = useState<CompletionView>({ open: false, index: 0, items: [] });
  const [attachments, setAttachments] = useState<AttachmentView>({ items: [], busy: false });
  useLayoutEffect(() => {
    const update = (event: Event) => setCompletion((event as CustomEvent<CompletionView>).detail);
    const updateAttachments = (event: Event) => setAttachments((event as CustomEvent<AttachmentView>).detail);
    window.addEventListener("tau:completion-render", update);
    window.addEventListener("tau:attachments-render", updateAttachments);
    return () => {
      window.removeEventListener("tau:completion-render", update);
      window.removeEventListener("tau:attachments-render", updateAttachments);
    };
  }, []);
  const activeDescendant = completion.open ? `compose-completion-option-${completion.index}` : undefined;
  const choose = (index: number) => window.dispatchEvent(new CustomEvent("tau:completion-select", { detail: { index } }));
  return (
    <Fragment>
      <div className="extension-slot" data-extension-slot="compose_above" />
      <form id="compose-form" className="chat__compose">
        <div className="chat__compose-container">
          <div className="chat__toolbar" aria-label="Prompt controls">
            <button id="compose-attachment-button" className="chat__toolbar-btn" type="button" aria-label="Attach file" title="Attach file">
              <i className="codicon codicon-attach" aria-hidden="true" />
            </button>
            <input id="compose-file-input" type="file" multiple hidden aria-label="Attach files" />
            <label className="thinking-badge-wrapper" title="Message delivery">
              <span className="sr-only">Delivery</span>
              <select id="compose-delivery-mode" className="thinking-badge" name="delivery_mode" aria-label="Message delivery">
                <option value="run">Run</option>
                <option value="follow_up">Follow-up</option>
                <option value="steer">Steer</option>
              </select>
            </label>
            <span id="compose-context-readout" className="usage-badge">No session selected. Sending will create one.</span>
          </div>

          <div className="sr-only" aria-hidden="true">
            <select id="compose-provider-select" name="provider_name" tabIndex={-1} aria-label="Provider adapter" />
            <select id="compose-model-select" name="model" tabIndex={-1} aria-label="Model adapter" />
            <select id="compose-thinking-select" name="compose_thinking_level" tabIndex={-1} aria-label="Thinking adapter" />
          </div>

          <div id="compose-attachment-list" className="chat__attachments" role="region" aria-live="polite" aria-label="Staged attachments">
            {attachments.items.map((attachment) => <span className="chat__attachment-pill" key={attachment.mediaId}>
              <span className="chat__attachment-name">{attachment.label}</span>
              <button className="chat__attachment-remove" type="button" aria-label={`Remove attachment ${attachment.filename}`} disabled={attachments.busy} onClick={() => window.dispatchEvent(new CustomEvent("tau:attachment-remove", { detail: { mediaId: attachment.mediaId } }))}>✕</button>
            </span>)}
          </div>
          <button id="compose-clear-attachments" className="chat__attachment-clear" type="button" aria-label="Clear all attachments" hidden={!attachments.items.length} disabled={!attachments.items.length || attachments.busy} onClick={() => window.dispatchEvent(new CustomEvent("tau:attachments-clear"))}>Clear all</button>

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
            aria-expanded={completion.open}
            aria-activedescendant={activeDescendant}
            aria-haspopup="listbox"
            placeholder="Type a message..."
          />
          <div id="compose-completion-popup" className="command-palette compose-completion-popup" hidden={!completion.open}>
            <p id="compose-completion-status" className="command-palette__step-hint" aria-live="polite">{completion.open ? `${completion.items.length} completion${completion.items.length === 1 ? "" : "s"} available.` : ""}</p>
            <ul id="compose-completion-listbox" className="command-palette__results" role="listbox" aria-label="Composer completions">
              {completion.items.map((item, index) => <li
                id={`compose-completion-option-${index}`}
                className={`command-palette__row${index === completion.index ? " is-active" : ""}`}
                role="option"
                aria-selected={index === completion.index}
                data-active={String(index === completion.index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(index)}
              ><strong className="command-palette__label">{item.label}</strong><p className="command-palette__description">{item.detail}</p></li>)}
            </ul>
          </div>
        </div>

        <button id="compose-submit" className="chat__send-btn" type="submit" aria-label="Run" title="Send (Enter)">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
        </button>
      </form>
      <div className="sr-only">
        <p id="compose-help">Enter sends. Shift+Enter inserts a newline.</p>
        <p id="app-status" aria-live="polite">Loading Tau shell…</p>
      </div>
      <div className="extension-slot" data-extension-slot="compose_below" />
    </Fragment>
  );
}
