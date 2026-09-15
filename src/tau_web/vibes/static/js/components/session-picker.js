// Registry adapter using deployed Piclaw classic picker class/role structure.
import { sessionLastMessage, sessionMessageCount } from './session-metrics.js';
import { groupSessions } from './session-groups.js';
import { html, useState, useMemo, useEffect, useLayoutEffect, useRef } from '../vendor/preact-htm.js';

export function sessionHandle(name) {
    const normalized=String(name||'').trim().toLowerCase().replace(/[^a-z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').replace(/-{2,}/g,'-');
    return normalized ? `@${normalized}` : '@session';
}

export function SessionPicker({ sessions = [], refreshError = '', currentId = 'default', onSelect, onClose, onCreate, onTools, onCreateBranch, onRename, onDelete, onPin, onArchive, onPopout }) {
    const [query, setQuery] = useState('');
    const [index, setIndex] = useState(0);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const actionPending = useRef(false);
    const typeahead = useRef({ query: '', time: 0 });
    const search = useRef(null);
    const results = useRef(null);
    const groups = useMemo(() => groupSessions(sessions, currentId).map(group => ({ ...group, items: group.items.filter(item => `${item.name} ${item.id}`.toLowerCase().includes(query.toLowerCase())) })).filter(group => group.items.length), [sessions, currentId, query]);
    const matches = groups.flatMap(group => group.items);
    const parents = new Set(sessions.map(item => item.parent_id).filter(Boolean));
    const selectedIndex = Math.max(0, Math.min(index, matches.length - 1));
    const selectedId = matches[selectedIndex]?.id;
    useLayoutEffect(() => {
        search.current?.focus();
        const position = () => {
            const popup = search.current?.closest('.compose-session-popup');
            const trigger = document.querySelector('.compose-input-main');
            if (!popup || !trigger) return;
            const rect = trigger.getBoundingClientRect();
            popup.style.bottom = `${Math.max(8, innerHeight - rect.top + 6)}px`;
            popup.style.left = `${rect.left}px`;
            popup.style.right = 'auto';
            popup.style.width = `${rect.width}px`;
        };
        position();window.addEventListener('resize', position);
        return () => window.removeEventListener('resize', position);
    }, []);
    useEffect(() => {
        const option = Array.from(results.current?.querySelectorAll('[role="option"]') || [])
            .find(node => node.id === `session-option-${selectedId}`);
        option?.scrollIntoView({ block: 'nearest' });
    }, [selectedId]);

    const act = async fn => {
        if (actionPending.current) return;
        actionPending.current = true;
        setBusy(true);
        try { setError(''); await fn?.(); }
        catch (err) { setError(err.message || 'Session action failed'); }
        finally { actionPending.current = false; setBusy(false); }
    };
    const keys = event => {
        if (event.isComposing || event.keyCode === 229) return;
        if (event.key === 'Escape') { event.preventDefault(); onClose?.(); }
        if (event.target !== search.current && event.key.length === 1 && event.key.trim() && !event.ctrlKey && !event.metaKey && !event.altKey) {
            const now = Date.now();
            const text = (now - typeahead.current.time > 700 ? '' : typeahead.current.query) + event.key.toLowerCase();
            typeahead.current = { query: text, time: now };
            const normalize = value => value.toLowerCase().replace(/^@/, '').replace(/\s+/g, ' ').trim();
            const needle = normalize(text);
            const labels = matches.map(item => normalize(item.name || item.id));
            let next = labels[selectedIndex]?.includes(needle) ? selectedIndex : labels.findIndex(label => label.startsWith(needle));
            if (next < 0) next = labels.findIndex(label => label.includes(needle));
            event.preventDefault();
            if (next >= 0) setIndex(next);
            return;
        }
        if (event.target?.closest('button')) return;
        if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp'].includes(event.key)) typeahead.current = { query: '', time: 0 };
        if (event.key === 'Home' || event.key === 'End') {
            event.preventDefault();
            setIndex(event.key === 'Home' ? 0 : Math.max(0, matches.length - 1));
        }
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            setIndex(matches.length ? (selectedIndex + (event.key === 'ArrowDown' ? 1 : -1) + matches.length) % matches.length : 0);
        }
        if (event.key === 'PageDown' || event.key === 'PageUp') {
            event.preventDefault();
            setIndex(Math.max(0, Math.min(matches.length - 1, selectedIndex + (event.key === 'PageDown' ? 8 : -8))));
        }
        const tabSelect = event.key === 'Tab' && !event.shiftKey && !event.altKey && !event.ctrlKey && !event.metaKey && event.target === search.current;
        if ((event.key === 'Enter' || tabSelect) && matches[selectedIndex]) {
            event.preventDefault();
            const item = matches[selectedIndex];
            if (event.altKey) { if (!event.repeat && !item.archived) act(() => onPin?.(item.id, !item.pinned)); return; }
            act(() => onSelect?.(item.id));
        }
    };
    return html`<div class="compose-model-popup compose-session-popup" data-testid="session-popup" tabindex="-1" aria-busy=${busy} onKeyDown=${keys}>
        <div class="compose-session-popup-header">
            <label class="compose-model-popup-title compose-session-search-heading" for="compose-session-search">Search sessions</label>
            <button type="button" class="compose-session-popup-close" aria-label="Close session picker" onClick=${onClose}>×</button>
        </div>
        <input id="compose-session-search" role="combobox" aria-autocomplete="list" aria-expanded="true" aria-controls="session-picker-results" aria-activedescendant=${selectedId ? `session-option-${selectedId}` : undefined} ref=${search} class="compose-session-search" type="search" autocomplete="off" value=${query} onInput=${e => { setQuery(e.target.value); setIndex(0); }} placeholder="Session name or ID" aria-label="Search sessions" />
        ${busy && html`<div class="compose-model-popup-empty" role="status">Updating session…</div>`}
        ${refreshError && html`<div class="compose-model-popup-empty" role="alert">${refreshError}</div>`}
        ${error && html`<div role="alert">${error}</div>`}
        ${matches.length === 0 && html`<div class="compose-model-popup-empty" role="status">No matching sessions</div>`}
        <div ref=${results} id="session-picker-results" class="compose-model-popup-menu compose-session-popup-results" role="listbox" aria-label="Sessions" aria-activedescendant=${matches[selectedIndex] ? `session-option-${matches[selectedIndex].id}` : undefined}>
            ${groups.map(group => html`<div class="session-popup-group" role="group" aria-label=${group.label}>
                <div class="compose-session-section-heading">${group.label}</div>
                ${group.items.map(item => { const lastMessage = sessionLastMessage(item.last_message_at); return html`<div key=${item.id} class=${`compose-model-popup-item-row session-picker-row${item.id === currentId ? ' active' : ''}${matches[selectedIndex]?.id === item.id ? ' keyboard-active' : ''}`}>
                <button type="button" class=${`compose-session-row-pin${item.pinned ? ' pinned' : ''}`} aria-label=${item.pinned ? 'Unpin session' : 'Pin session'} aria-pressed=${!!item.pinned} aria-keyshortcuts="Alt+Enter" disabled=${!!item.archived || !onPin} onClick=${() => act(() => onPin?.(item.id, !item.pinned))}>${item.pinned ? '★' : '☆'}</button>
                <button type="button" id=${`session-option-${item.id}`} class=${`compose-model-popup-item session-item${item.archived ? ' archived' : item.id === currentId ? ' active' : ''}`} role="option" aria-selected=${item.id === currentId} aria-description=${`Session ID: ${item.id}`} title=${`Session ID: ${item.id}`} onClick=${() => act(() => onSelect?.(item.id))}>
                    <span class="compose-session-row-content"><span class="compose-session-row-main"><span class="compose-session-row-label">${sessionHandle(item.name)}</span><span class="compose-session-row-meta" title=${sessionMessageCount(item.message_count)}><span class="compose-session-row-jid">${item.id}</span>${item.model&&html`<span class="compose-session-row-metrics"> · ${item.provider?`${item.provider}/`:''}${item.model}</span>`}</span>${lastMessage && html`<time class="compose-session-row-meta" datetime=${lastMessage.datetime} title="Last persisted message (not runtime activity)">Last message: ${lastMessage.label}</time>`}</span><span class="compose-session-row-pills">
                    ${item.id === currentId && html`<span class="compose-session-status-pill current">Current</span>`}
                    ${(item.archived || item.is_running === true) && html`<span class=${`compose-session-status-pill ${item.archived ? 'archived' : 'active'}`}>${item.archived ? 'Archived' : 'Running'}</span>`}
                    ${item.queued_count > 0 && html`<span class="compose-session-status-pill queued" title="Queued follow-ups and pending steering in this process">${item.queued_count} queued</span>`}
                    </span></span>
                </button>
                ${onPopout && html`<button type="button" class="compose-model-popup-item-popout" aria-label=${`Open ${item.name} in new window`} title=${`Open ${item.name} in new window`} onClick=${() => onPopout(item.id)}><svg width="10" height="10" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h8v8"/><path d="M14 2 7 9"/><path d="M12 9v5H2V4h5"/></svg></button>`}
                ${item.id !== 'default' && onArchive && html`<button type="button" class="session-row-action session-row-icon compose-model-popup-btn" aria-label=${`${item.archived ? 'Restore' : 'Archive'} ${item.name}`} disabled=${!item.archived && item.is_running === true} title=${!item.archived && item.is_running ? 'Stop the running turn before archiving' : `${item.archived ? 'Restore' : 'Archive'} ${item.name}`} onClick=${() => act(() => onArchive(item.id, !item.archived))}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 10v11h16V10M3 3h18v5H3Z"/><path d=${item.archived ? 'M12 18v-6m-3 3 3-3 3 3' : 'M9 13h6'}/></svg></button>`}
                ${item.id !== 'default' && html`<button type="button" class="compose-model-popup-item-delete" aria-label=${`Delete ${item.name}`} disabled=${!onDelete || item.is_running === true || item.message_count !== 0 || parents.has(item.id)} title=${item.is_running === true ? 'Stop the running turn before deleting' : parents.has(item.id) ? 'Sessions with children cannot be deleted' : item.message_count !== 0 ? 'Only sessions confirmed empty can be deleted' : undefined} onClick=${() => act(() => onDelete?.(item.id))}><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg></button>`}
            </div>`; })}
            </div>`)}
        </div>
        <div class="compose-model-popup-actions">
            ${onTools && html`<button type="button" class="compose-model-popup-btn" onClick=${onTools}>Session tools…</button>`}
            ${onCreateBranch && html`<button type="button" class="compose-model-popup-btn" title="Create an empty child session; history is not copied" onClick=${() => act(onCreateBranch)}>New branch</button>`}
            <button type="button" class="compose-model-popup-btn" title="Create an independent root session" disabled=${!onCreate} onClick=${() => act(onCreate)}>New root…</button>
            ${onRename && sessions.some(item => item.id === currentId) && html`<button type="button" class="compose-model-popup-btn" onClick=${() => act(() => onRename(currentId))}>Rename current…</button>`}
        </div>
    </div>`;
}
