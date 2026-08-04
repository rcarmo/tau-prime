const STORAGE_KEYS = Object.freeze({ authToken: "tau.web.authToken", selectedSessionId: "tau.web.selectedSessionId" });
const API_ROOT = "/api";
const POLL_INTERVAL_MS = 2000;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 16000;
const MAX_BANNERS = 8;
const MAX_TOOL_UPDATES = 12;
const THINKING_LEVELS = Object.freeze([
  ["", "Default"], ["off", "Off — no reasoning"], ["minimal", "Minimal — very brief reasoning"],
  ["low", "Low — light reasoning"], ["medium", "Medium — moderate reasoning"],
  ["high", "High — deep reasoning"], ["xhigh", "XHigh — maximum reasoning"],
]);

const ui = bindUi();
const state = {
  authToken: loadStorage(STORAGE_KEYS.authToken),
  selectedSessionId: normalizeStorageText(loadStorage(STORAGE_KEYS.selectedSessionId)),
  session: null, context: null, usage: null, runs: [], queue: [],
  refreshPromise: null, refreshQueued: false,
  queueMessage: "Enter submits. Shift+Enter inserts a newline.",
  thinkingMessage: "Updates session thinking with optimistic concurrency checks.",
  stream: createStreamState(),
};

initialize();

function initialize() {
  populateThinkingSelect();
  bindEvents();
  renderAll();
  void syncFromStorage({ forceRefresh: true, restartStream: true });
  window.setInterval(() => void syncFromStorage({ forceRefresh: true }), POLL_INTERVAL_MS);
  window.addEventListener("focus", () => void syncFromStorage({ forceRefresh: true }));
  window.addEventListener("storage", () => void syncFromStorage({ forceRefresh: true, restartStream: true }));
}

function bindUi() {
  return {
    contextSummary: requiredElement("context-summary"), usageTotals: requiredElement("usage-totals"),
    usageRecords: requiredElement("usage-records"), activeRunCard: requiredElement("active-run-card"),
    activeRunNote: requiredElement("active-run-note"), queueForm: requiredElement("queue-form"),
    queueInput: requiredElement("queue-input"), queueSubmitButton: requiredElement("queue-submit-button"),
    dispatchFollowUpButton: requiredElement("dispatch-follow-up-button"), dispatchSteerButton: requiredElement("dispatch-steer-button"),
    queueHelp: requiredElement("queue-help"), queueList: requiredElement("queue-list"),
    thinkingForm: requiredElement("thinking-form"), thinkingLevelSelect: requiredElement("thinking-level-select"),
    applyThinkingButton: requiredElement("apply-thinking-button"), thinkingHelp: requiredElement("thinking-help"),
    composeForm: requiredElement("compose-form"), composeInput: requiredElement("compose-input"),
    timelineList: requiredElement("timeline-list"), streamingNote: requiredElement("streaming-note"),
  };
}

function bindEvents() {
  ui.queueForm.addEventListener("submit", (event) => void handleQueueSubmit(event));
  ui.queueInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); ui.queueForm.requestSubmit(); }
  });
  ui.queueInput.addEventListener("input", renderQueueControls);
  ui.dispatchFollowUpButton.addEventListener("click", () => void handleDispatch("follow_up"));
  ui.dispatchSteerButton.addEventListener("click", () => void handleDispatch("steer"));
  ui.thinkingForm.addEventListener("submit", (event) => void handleThinkingSubmit(event));
  ui.composeForm.addEventListener("submit", (event) => void handleComposeIntercept(event), true);
}

function populateThinkingSelect() {
  ui.thinkingLevelSelect.replaceChildren(
    ...THINKING_LEVELS.map(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      return option;
    }),
  );
}

async function syncFromStorage({ forceRefresh = false, restartStream = false } = {}) {
  const nextAuthToken = normalizeStorageText(loadStorage(STORAGE_KEYS.authToken));
  const nextSessionId = normalizeStorageText(loadStorage(STORAGE_KEYS.selectedSessionId));
  const authChanged = nextAuthToken !== state.authToken;
  const sessionChanged = nextSessionId !== state.selectedSessionId;
  state.authToken = nextAuthToken;
  if (sessionChanged) {
    state.selectedSessionId = nextSessionId;
    clearSelectedState();
    resetStreamForSessionChange();
    renderAll();
  } else {
    state.selectedSessionId = nextSessionId;
  }
  if (!state.selectedSessionId) {
    stopStream();
    renderAll();
    return;
  }
  if (forceRefresh || authChanged || sessionChanged) await refreshSelectedSession();
  if (restartStream || authChanged || sessionChanged || state.stream.sessionId !== state.selectedSessionId) startStream(state.selectedSessionId);
  renderStreamingNote();
}

function clearSelectedState() {
  state.session = null;
  state.context = null;
  state.usage = null;
  state.runs = [];
  state.queue = [];
  state.queueMessage = "Enter submits. Shift+Enter inserts a newline.";
  state.thinkingMessage = "Updates session thinking with optimistic concurrency checks.";
}

function createStreamState() {
  return {
    sessionId: null, runId: null, controller: null, reconnectTimer: 0, reconnectAttempt: 0,
    lastEventId: null, connectionState: "idle", errorText: "", assistantText: "", thinkingText: "",
    toolCards: new Map(), banners: [], card: null,
  };
}

function resetStreamForSessionChange() {
  stopStream();
  state.stream = createStreamState();
  removeLiveCard();
}

function stopStream() {
  if (state.stream.controller) { state.stream.controller.abort(); state.stream.controller = null; }
  if (state.stream.reconnectTimer) { window.clearTimeout(state.stream.reconnectTimer); state.stream.reconnectTimer = 0; }
  state.stream.connectionState = state.selectedSessionId ? "stopped" : "idle";
}

function resetLiveRun(runId) {
  state.stream.runId = runId;
  state.stream.assistantText = "";
  state.stream.thinkingText = "";
  state.stream.toolCards = new Map();
  state.stream.banners = [];
}

async function refreshSelectedSession() {
  if (!state.selectedSessionId) { clearSelectedState(); renderAll(); return; }
  if (state.refreshPromise) { state.refreshQueued = true; await state.refreshPromise; return; }
  const sessionId = state.selectedSessionId;
  state.refreshPromise = (async () => {
    try {
      const prefix = `${API_ROOT}/sessions/${encodeURIComponent(sessionId)}`;
      const [session, context, usage, runs, queue] = await Promise.all([
        apiFetch(prefix), apiFetch(`${prefix}/context`), apiFetch(`${prefix}/usage`),
        apiFetch(`${prefix}/runs?status=pending,running`), apiFetch(`${prefix}/queue`),
      ]);
      if (state.selectedSessionId !== sessionId) return;
      state.session = session;
      state.context = context;
      state.usage = usage;
      state.runs = Array.isArray(runs?.runs) ? runs.runs : [];
      state.queue = Array.isArray(queue?.queue) ? queue.queue : [];
      state.queueMessage = "Enter submits. Shift+Enter inserts a newline.";
      state.thinkingMessage = state.session?.updated_at
        ? `Updates session thinking with optimistic concurrency checks. Current session revision: ${formatTimestamp(state.session.updated_at)}.`
        : "Updates session thinking with optimistic concurrency checks.";
      renderAll();
    } catch (error) {
      if (state.selectedSessionId !== sessionId) return;
      clearSelectedState();
      state.queueMessage = messageFromError(error);
      state.thinkingMessage = messageFromError(error);
      renderAll();
    } finally {
      state.refreshPromise = null;
      if (state.refreshQueued && state.selectedSessionId === sessionId) {
        state.refreshQueued = false;
        void refreshSelectedSession();
      }
    }
  })();
  await state.refreshPromise;
}

function renderAll() {
  renderContextSummary();
  renderUsage();
  renderActiveRun();
  renderQueueControls();
  renderQueueList();
  renderThinkingControls();
  renderLiveCard();
  renderStreamingNote();
}

function renderContextSummary() {
  const items = [];
  if (!state.selectedSessionId) {
    items.push(createStatItem("Status", "Select a session."));
  } else if (!state.session || !state.context) {
    items.push(createStatItem("Status", "Loading context…"));
  } else {
    items.push(createStatItem("Session", state.session.title || shortId(state.session.session_id)));
    items.push(createStatItem("Model", state.context.model || state.session.model));
    items.push(createStatItem("Thinking", state.context.thinking_level || state.session.thinking_level || "Default"));
    items.push(createStatItem("Entries", String(state.context.entry_count ?? 0)));
    items.push(createStatItem("Messages", String(state.context.message_count ?? 0)));
    items.push(createStatItem("Compactions", String(state.context.compaction_count ?? 0)));
    items.push(createStatItem("Active leaf", state.context.active_leaf_entry_id || "None"));
    items.push(createStatItem("Updated", formatTimestamp(state.session.updated_at)));
  }
  ui.contextSummary.replaceChildren(...items);
}

function renderUsage() {
  const totalItems = [];
  if (!state.selectedSessionId) {
    totalItems.push(createStatItem("Status", "Select a session."));
  } else if (!state.usage) {
    totalItems.push(createStatItem("Status", "Loading usage…"));
  } else {
    const totals = state.usage.totals || {};
    totalItems.push(createStatItem("Input", formatNumber(totals.input)));
    totalItems.push(createStatItem("Output", formatNumber(totals.output)));
    totalItems.push(createStatItem("Cache read", formatNumber(totals.cache_read)));
    totalItems.push(createStatItem("Cost", formatMicrounits(totals.cost)));
  }
  ui.usageTotals.replaceChildren(...totalItems);

  const recordItems = [];
  if (!state.selectedSessionId) {
    recordItems.push(createListPlaceholder("Select a session to inspect usage records."));
  } else if (!state.usage) {
    recordItems.push(createListPlaceholder("Loading usage records…"));
  } else if (!Array.isArray(state.usage.records) || state.usage.records.length === 0) {
    recordItems.push(createListPlaceholder("No usage has been recorded yet."));
  } else {
    for (const record of state.usage.records) {
      const item = document.createElement("li");
      item.className = "usage-record";
      item.append(
        createMetaRow([`${record.provider_name || "provider"} · ${record.model || "model"}`, record.run_id ? `run ${shortId(record.run_id)}` : "session aggregate"]),
        createTextBlock(`${formatNumber(record.input_tokens)} in · ${formatNumber(record.output_tokens)} out · ${formatNumber(record.cached_input_tokens)} cached`, "usage-detail"),
        createTextBlock(formatTimestamp(record.recorded_at), "session-meta"),
      );
      recordItems.push(item);
    }
  }
  ui.usageRecords.replaceChildren(...recordItems);
}

function renderActiveRun() {
  const activeRun = currentActiveRun();
  if (!state.selectedSessionId) {
    ui.activeRunNote.textContent = "Select a session to inspect live work.";
    ui.activeRunCard.replaceChildren(createMutedText("No session selected."));
    return;
  }
  if (!state.session) {
    ui.activeRunNote.textContent = "Loading run state…";
    ui.activeRunCard.replaceChildren(createMutedText("Loading active run…"));
    return;
  }
  if (!activeRun) {
    ui.activeRunNote.textContent = "No pending or running work for the selected session.";
    ui.activeRunCard.replaceChildren(createMutedText("The session is idle."));
    return;
  }

  const runningCount = state.runs.filter((run) => run.status === "running").length;
  const pendingCount = state.runs.filter((run) => run.status === "pending").length;
  ui.activeRunNote.textContent = `${runningCount} running · ${pendingCount} pending`;

  const card = document.createElement("article");
  card.className = "run-card";
  card.append(
    createMetaRow([createBadge("run-status-badge", activeRun.status, activeRun.status), `run ${shortId(activeRun.run_id)}`]),
    createTextBlock(`Started ${formatTimestamp(activeRun.started_at)}`, "session-meta"),
    createTextBlock(`Updated ${formatTimestamp(activeRun.updated_at)}`, "session-meta"),
  );
  if (activeRun.last_event_type) card.append(createTextBlock(`Last event: ${activeRun.last_event_type}`, "session-meta"));
  if (activeRun.error?.message) card.append(createTextBlock(String(activeRun.error.message), "usage-detail"));

  const actions = document.createElement("div");
  actions.className = "run-action-row";
  actions.append(
    createActionButton("Cancel", () => void mutateRun(activeRun.run_id, "cancel")),
    createActionButton("Abort", () => void mutateRun(activeRun.run_id, "abort"), { danger: true }),
  );
  card.append(actions);
  ui.activeRunCard.replaceChildren(card);
}

function renderQueueControls() {
  const activeRun = currentActiveRun();
  const hasSession = Boolean(state.selectedSessionId);
  const trimmed = ui.queueInput.value.trim();
  const followUpCount = state.queue.filter((item) => item.queue_kind === "follow_up").length;
  const steerCount = state.queue.filter((item) => item.queue_kind === "steer").length;

  ui.queueSubmitButton.disabled = !hasSession || trimmed.length === 0;
  ui.dispatchFollowUpButton.disabled = !activeRun || followUpCount === 0;
  ui.dispatchSteerButton.disabled = !activeRun || steerCount === 0;
  ui.dispatchFollowUpButton.textContent = `Dispatch follow-up${followUpCount ? ` (${followUpCount})` : ""}`;
  ui.dispatchSteerButton.textContent = `Dispatch steer${steerCount ? ` (${steerCount})` : ""}`;
  ui.queueHelp.textContent = !hasSession
    ? "Select a session before enqueueing work."
    : !activeRun
      ? state.queueMessage
      : `${state.queueMessage} Active run: ${shortId(activeRun.run_id)}.`;
}

function renderQueueList() {
  const items = [];
  if (!state.selectedSessionId) {
    items.push(createListPlaceholder("Select a session to inspect queued messages."));
  } else if (!state.session) {
    items.push(createListPlaceholder("Loading queue…"));
  } else if (state.queue.length === 0) {
    items.push(createListPlaceholder("No queued follow-up or steer messages."));
  } else {
    for (const record of state.queue) {
      const item = document.createElement("li");
      item.className = "queue-item";
      item.append(
        createMetaRow([createBadge("queue-kind-badge", record.queue_kind, record.queue_kind), `position ${record.position}`]),
        createTextBlock(valueToText(record.content), "queue-content"),
        createTextBlock(formatTimestamp(record.created_at), "session-meta"),
      );
      items.push(item);
    }
  }
  ui.queueList.replaceChildren(...items);
}

function renderThinkingControls() {
  const hasSession = Boolean(state.selectedSessionId);
  ui.thinkingLevelSelect.value = state.session?.thinking_level || "";
  ui.thinkingLevelSelect.disabled = !hasSession || !state.session;
  ui.applyThinkingButton.disabled = !hasSession || !state.session;
  ui.thinkingHelp.textContent = hasSession ? state.thinkingMessage : "Select a session to update thinking.";
}

async function handleQueueSubmit(event) {
  event.preventDefault();
  if (!state.selectedSessionId) {
    state.queueMessage = "Select a session before enqueueing work.";
    renderQueueControls();
    return;
  }
  const content = ui.queueInput.value.trim();
  if (!content) {
    state.queueMessage = "Enter a follow-up message before enqueueing.";
    renderQueueControls();
    return;
  }
  try {
    await apiFetch(`${API_ROOT}/sessions/${encodeURIComponent(state.selectedSessionId)}/queue`, { method: "POST", json: { content, kind: "follow_up" } });
    ui.queueInput.value = "";
    state.queueMessage = "Queued follow-up message.";
    await refreshSelectedSession();
  } catch (error) {
    state.queueMessage = messageFromError(error);
  }
  renderQueueControls();
}

async function handleDispatch(kind) {
  const activeRun = currentActiveRun();
  if (!activeRun) {
    state.queueMessage = "Dispatch requires an active run.";
    renderQueueControls();
    return;
  }
  try {
    await apiFetch(`${API_ROOT}/runs/${encodeURIComponent(activeRun.run_id)}/queue/${kind}/dispatch`, { method: "POST" });
    state.queueMessage = `Dispatched next ${kind.replace("_", " ")} message.`;
    await refreshSelectedSession();
  } catch (error) {
    state.queueMessage = messageFromError(error);
  }
  renderQueueControls();
}

async function handleThinkingSubmit(event) {
  event.preventDefault();
  if (!state.selectedSessionId || !state.session) {
    state.thinkingMessage = "Select a session to update thinking.";
    renderThinkingControls();
    return;
  }
  const value = ui.thinkingLevelSelect.value;
  try {
    const updated = await apiFetch(`${API_ROOT}/sessions/${encodeURIComponent(state.selectedSessionId)}/thinking`, {
      method: "PATCH",
      json: { thinking_level: value || null, expected_updated_at: state.session.updated_at },
    });
    state.session = updated;
    state.thinkingMessage = `Thinking updated to ${value || "default"}.`;
    await refreshSelectedSession();
  } catch (error) {
    state.thinkingMessage = messageFromError(error);
  }
  renderThinkingControls();
}

async function handleComposeIntercept(event) {
  const activeRun = currentActiveRun();
  if (!activeRun) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const content = ui.composeInput.value.trim();
  if (!content) return;
  try {
    await apiFetch(`${API_ROOT}/runs/${encodeURIComponent(activeRun.run_id)}/messages`, { method: "POST", json: { content, kind: "follow_up" } });
    ui.composeInput.value = "";
    state.queueMessage = `Queued follow-up for active run ${shortId(activeRun.run_id)}.`;
    await refreshSelectedSession();
  } catch (error) {
    state.queueMessage = messageFromError(error);
  }
  renderQueueControls();
}

async function mutateRun(runId, action) {
  try {
    await apiFetch(`${API_ROOT}/runs/${encodeURIComponent(runId)}/${action}`, { method: "POST" });
    await refreshSelectedSession();
  } catch (error) {
    ui.activeRunNote.textContent = messageFromError(error);
  }
}

function currentActiveRun() { return state.runs.find((run) => run.status === "running") || state.runs[0] || null; }

function startStream(sessionId) {
  stopStream();
  resetLiveRun(null);
  state.stream.sessionId = sessionId;
  state.stream.connectionState = "connecting";
  state.stream.errorText = "";
  renderStreamingNote();
  void openStream(sessionId);
}

async function openStream(sessionId) {
  const controller = new AbortController();
  state.stream.controller = controller;
  try {
    const headers = buildHeaders({ acceptEventStream: true });
    if (state.stream.lastEventId !== null) headers.set("Last-Event-ID", String(state.stream.lastEventId));
    const response = await fetch(`${API_ROOT}/events?session_id=${encodeURIComponent(sessionId)}`, { method: "GET", headers, signal: controller.signal });
    if (!response.ok) throw new Error(await responseErrorMessage(response));
    state.stream.connectionState = "connected";
    state.stream.reconnectAttempt = 0;
    state.stream.errorText = "";
    renderStreamingNote();
    await readEventStream(response, (event) => {
      if (sessionId !== state.selectedSessionId) return;
      if (event.id !== null) state.stream.lastEventId = event.id;
      handleStreamEvent(event);
    });
    if (!controller.signal.aborted) throw new Error("Live stream closed.");
  } catch (error) {
    if (controller.signal.aborted || sessionId !== state.selectedSessionId) return;
    state.stream.connectionState = "reconnecting";
    state.stream.errorText = messageFromError(error);
    scheduleReconnect(sessionId);
  } finally {
    if (state.stream.controller === controller) state.stream.controller = null;
    renderStreamingNote();
  }
}

function scheduleReconnect(sessionId) {
  if (state.stream.reconnectTimer || sessionId !== state.selectedSessionId) return;
  const delay = Math.min(RECONNECT_BASE_MS * 2 ** state.stream.reconnectAttempt, RECONNECT_MAX_MS);
  state.stream.reconnectAttempt += 1;
  state.stream.reconnectTimer = window.setTimeout(() => {
    state.stream.reconnectTimer = 0;
    if (sessionId === state.selectedSessionId) void openStream(sessionId);
  }, delay);
}

function renderStreamingNote() {
  if (!state.selectedSessionId) {
    ui.streamingNote.textContent = "Select a session to follow live updates.";
  } else if (state.stream.connectionState === "connected") {
    ui.streamingNote.textContent = `Live updates connected for ${shortId(state.selectedSessionId)}.`;
  } else if (state.stream.connectionState === "connecting") {
    ui.streamingNote.textContent = `Connecting live updates for ${shortId(state.selectedSessionId)}…`;
  } else if (state.stream.connectionState === "reconnecting") {
    const delay = Math.min(RECONNECT_BASE_MS * 2 ** Math.max(state.stream.reconnectAttempt - 1, 0), RECONNECT_MAX_MS);
    ui.streamingNote.textContent = `${state.stream.errorText || "Live updates disconnected."} Reconnecting in ${Math.round(delay / 100) / 10}s…`;
  } else {
    ui.streamingNote.textContent = `Live updates paused for ${shortId(state.selectedSessionId)}.`;
  }
}

async function readEventStream(response, onEvent) {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Streaming response body is unavailable.");
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseEventChunk(buffer);
    buffer = parsed.buffer;
    for (const event of parsed.events) onEvent(event);
  }
  buffer += decoder.decode();
  const parsed = parseEventChunk(`${buffer}\n\n`);
  for (const event of parsed.events) onEvent(event);
}

function parseEventChunk(chunk) {
  const normalized = chunk.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const parts = normalized.split("\n\n");
  const buffer = parts.pop() || "";
  const events = [];
  for (const part of parts) {
    const event = parseEventBlock(part);
    if (event) events.push(event);
  }
  return { buffer, events };
}

function parseEventBlock(block) {
  const lines = block.split("\n");
  let id = null;
  let event = "message";
  const dataLines = [];
  for (const line of lines) {
    if (!line || line.startsWith(":")) continue;
    const separator = line.indexOf(":");
    const field = separator === -1 ? line : line.slice(0, separator);
    let value = separator === -1 ? "" : line.slice(separator + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "id") id = value || null;
    else if (field === "event") event = value || event;
    else if (field === "data") dataLines.push(value);
  }
  if (dataLines.length === 0) return null;
  const rawData = dataLines.join("\n");
  let data;
  try { data = JSON.parse(rawData); } catch { data = rawData; }
  return { id, event, data };
}

function handleStreamEvent(event) {
  if (event.event === "tau.snapshot") { applySnapshot(event.data); return; }
  const data = isRecord(event.data) ? event.data : {};
  if (data.session_id !== state.selectedSessionId) return;
  const payload = isRecord(data.payload) ? data.payload : {};
  const payloadType = typeof payload.type === "string" ? payload.type : normalizeEventName(event.event);
  if (typeof data.run_id === "string" && data.run_id !== state.stream.runId) resetLiveRun(data.run_id);

  if (payloadType === "message_delta") {
    state.stream.assistantText += stringValue(payload.delta);
  } else if (payloadType === "thinking_delta") {
    state.stream.thinkingText += stringValue(payload.delta);
  } else if (payloadType === "tool_execution_start") {
    const toolCall = isRecord(payload.tool_call) ? payload.tool_call : {};
    upsertToolCard(stringValue(toolCall.id) || stringValue(data.sequence), { name: stringValue(toolCall.name) || "tool", status: "running", argumentsText: objectToText(toolCall.arguments) });
  } else if (payloadType === "tool_execution_update") {
    const tool = upsertToolCard(stringValue(payload.tool_call_id), { name: "tool", status: "running" });
    const message = stringValue(payload.message);
    if (message) {
      tool.updates.push(message);
      if (tool.updates.length > MAX_TOOL_UPDATES) tool.updates.splice(0, tool.updates.length - MAX_TOOL_UPDATES);
    }
  } else if (payloadType === "tool_execution_end") {
    const result = isRecord(payload.result) ? payload.result : {};
    const tool = upsertToolCard(stringValue(result.tool_call_id), { name: stringValue(result.name) || "tool", status: result.ok === false ? "failed" : "completed" });
    tool.status = result.ok === false ? "failed" : "completed";
    tool.resultText = stringValue(result.content);
    tool.errorText = stringValue(result.error);
  } else if (payloadType === "retry") {
    pushBanner("retry", buildRetryMessage(payload));
  } else if (payloadType === "error") {
    pushBanner("error", stringValue(payload.message) || "Live stream error.");
  } else if (payloadType === "queue_update") {
    pushBanner("queue_update", "Queue updated.");
    void refreshSelectedSession();
  } else if (payloadType === "message_end") {
    void refreshSelectedSession();
  }
  renderLiveCard();
}

function applySnapshot(snapshot) {
  if (!isRecord(snapshot)) return;
  const sessions = Array.isArray(snapshot.sessions) ? snapshot.sessions : [];
  const runs = Array.isArray(snapshot.runs) ? snapshot.runs : [];
  const queue = Array.isArray(snapshot.queue) ? snapshot.queue : [];
  const matchingSession = sessions.find((entry) => isRecord(entry) && entry.session_id === state.selectedSessionId);
  if (matchingSession) state.session = matchingSession;
  state.runs = runs.filter((entry) => isRecord(entry) && entry.session_id === state.selectedSessionId);
  state.queue = queue.filter((entry) => isRecord(entry) && entry.session_id === state.selectedSessionId);
  renderActiveRun();
  renderQueueControls();
  renderQueueList();
}

function upsertToolCard(toolId, values) {
  const id = toolId || `tool-${state.stream.toolCards.size + 1}`;
  let tool = state.stream.toolCards.get(id);
  if (!tool) {
    tool = { id, name: values.name || "tool", status: values.status || "running", argumentsText: values.argumentsText || "", updates: [], resultText: "", errorText: "" };
    state.stream.toolCards.set(id, tool);
  }
  if (values.name) tool.name = values.name;
  if (values.status) tool.status = values.status;
  if (values.argumentsText) tool.argumentsText = values.argumentsText;
  return tool;
}

function pushBanner(kind, text) {
  if (!text) return;
  state.stream.banners.push({ kind, text });
  if (state.stream.banners.length > MAX_BANNERS) state.stream.banners.splice(0, state.stream.banners.length - MAX_BANNERS);
}

function renderLiveCard() {
  if (!hasLiveContent()) { removeLiveCard(); return; }
  const card = ensureLiveCard();
  const children = [createHeadingBlock("Live stream", state.stream.runId ? `run ${shortId(state.stream.runId)}` : "streaming")];
  if (state.stream.assistantText) children.push(createTextBlock(state.stream.assistantText, "queue-content"));
  if (state.stream.thinkingText) {
    const details = document.createElement("details");
    details.className = "live-thinking";
    details.open = true;
    const summary = document.createElement("summary");
    summary.textContent = "Thinking";
    details.append(summary, createTextBlock(state.stream.thinkingText, "queue-content"));
    children.push(details);
  }
  if (state.stream.banners.length > 0) children.push(renderLiveBanners());
  if (state.stream.toolCards.size > 0) children.push(renderToolCards());
  card.replaceChildren(...children);
  if (card.parentElement !== ui.timelineList) ui.timelineList.append(card);
}

function renderLiveBanners() {
  const list = document.createElement("ul");
  list.className = "live-banner-list";
  for (const banner of state.stream.banners) {
    const item = document.createElement("li");
    item.className = "live-banner";
    item.dataset.kind = banner.kind;
    item.append(createMetaRow([createBadge("live-banner-badge", banner.kind, banner.kind)]), createTextBlock(banner.text, "usage-detail"));
    list.append(item);
  }
  return list;
}

function renderToolCards() {
  const list = document.createElement("ul");
  list.className = "tool-live-list";
  for (const tool of state.stream.toolCards.values()) {
    const item = document.createElement("li");
    item.className = "tool-live-card";
    item.append(createMetaRow([createBadge("tool-status-badge", tool.status, tool.status), `${tool.name} · ${shortId(tool.id)}`]));
    if (tool.argumentsText) item.append(createTextBlock(tool.argumentsText, "live-tool-arguments"));
    if (tool.updates.length > 0) {
      const updates = document.createElement("ul");
      updates.className = "tool-update-list";
      for (const update of tool.updates) {
        const updateItem = document.createElement("li");
        updateItem.append(createTextBlock(update, "live-tool-update"));
        updates.append(updateItem);
      }
      item.append(updates);
    }
    if (tool.resultText) item.append(createTextBlock(tool.resultText, "live-tool-result"));
    if (tool.errorText) item.append(createTextBlock(tool.errorText, "live-tool-result"));
    list.append(item);
  }
  return list;
}

function ensureLiveCard() {
  if (state.stream.card && state.stream.card.isConnected && state.stream.card.parentElement === ui.timelineList) return state.stream.card;
  const card = state.stream.card || document.createElement("li");
  card.className = "timeline-card";
  card.dataset.liveUi = "card";
  state.stream.card = card;
  return card;
}

function removeLiveCard() { if (state.stream.card?.parentElement) state.stream.card.parentElement.removeChild(state.stream.card); }
function hasLiveContent() { return Boolean(state.selectedSessionId && (state.stream.assistantText || state.stream.thinkingText || state.stream.toolCards.size || state.stream.banners.length)); }

async function apiFetch(path, { method = "GET", json = null, signal = null, acceptEventStream = false } = {}) {
  const headers = buildHeaders({ method, acceptEventStream });
  const options = { method, headers, signal };
  if (json !== null) { headers.set("Content-Type", "application/json"); options.body = JSON.stringify(json); }
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(await responseErrorMessage(response));
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function buildHeaders({ method = "GET", acceptEventStream = false } = {}) {
  const headers = new Headers();
  headers.set("Accept", acceptEventStream ? "text/event-stream" : "application/json");
  if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method.toUpperCase())) headers.set("X-Tau-CSRF", "1");
  if (state.authToken) headers.set("Authorization", `Bearer ${state.authToken}`);
  return headers;
}

async function responseErrorMessage(response) {
  const fallback = `${response.status} ${response.statusText}`.trim() || "Request failed.";
  try {
    const payload = await response.json();
    return typeof payload?.error?.message === "string" && payload.error.message ? payload.error.message : fallback;
  } catch {
    return fallback;
  }
}

function requiredElement(id) {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing required element: #${id}`);
  return element;
}

function createHeadingBlock(title, detail) {
  const wrapper = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = title;
  wrapper.append(heading);
  if (detail) wrapper.append(createTextBlock(detail, "session-meta"));
  return wrapper;
}

function createStatItem(label, value) {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value;
  wrapper.append(term, description);
  return wrapper;
}

function createListPlaceholder(text) {
  const item = document.createElement("li");
  item.append(createMutedText(text));
  return item;
}

function createMutedText(text) {
  const element = document.createElement("p");
  element.className = "muted small-text";
  element.textContent = text;
  return element;
}

function createMetaRow(parts) {
  const row = document.createElement("div");
  row.className = "queue-meta-row";
  for (const part of parts) {
    if (!part) continue;
    if (typeof part === "string") {
      const span = document.createElement("span");
      span.textContent = part;
      row.append(span);
    } else {
      row.append(part);
    }
  }
  return row;
}

function createBadge(className, status, text) {
  const badge = document.createElement("span");
  badge.className = className;
  badge.dataset.status = status;
  badge.textContent = text;
  return badge;
}

function createTextBlock(text, className) {
  const block = document.createElement("p");
  block.className = className;
  block.textContent = text;
  return block;
}

function createActionButton(label, action, { danger = false } = {}) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  if (danger) button.classList.add("danger-button");
  button.addEventListener("click", action);
  return button;
}

function shortId(value) { return typeof value !== "string" || value.length <= 12 ? value || "unknown" : `${value.slice(0, 8)}…${value.slice(-4)}`; }
function formatTimestamp(value) { if (typeof value !== "string" || !value) return "Unknown"; const timestamp = Date.parse(value); return Number.isNaN(timestamp) ? value : new Date(timestamp).toLocaleString(); }
function formatMicrounits(value) { return `${formatNumber(typeof value === "number" ? value : 0)} µunits`; }
function formatNumber(value) { return typeof value === "number" && !Number.isNaN(value) ? value.toLocaleString() : "0"; }
function objectToText(value) { if (value === null || value === undefined || value === "") return ""; try { return JSON.stringify(value, null, 2); } catch { return String(value); } }
function valueToText(value) { return typeof value === "string" ? value : objectToText(value); }
function buildRetryMessage(payload) { const message = stringValue(payload.message) || "Retry scheduled."; const attempt = typeof payload.attempt === "number" ? payload.attempt : null; const maxAttempts = typeof payload.max_attempts === "number" ? payload.max_attempts : null; return attempt === null || maxAttempts === null ? message : `${message} Attempt ${attempt} of ${maxAttempts}.`; }
function normalizeEventName(eventName) { return typeof eventName === "string" && eventName.startsWith("tau.agent.") ? eventName.slice("tau.agent.".length) : typeof eventName === "string" ? eventName : ""; }
function normalizeStorageText(value) { if (typeof value !== "string") return null; const trimmed = value.trim(); return trimmed || null; }
function stringValue(value) { return typeof value === "string" ? value : ""; }
function isRecord(value) { return Boolean(value) && typeof value === "object" && !Array.isArray(value); }
function messageFromError(error) { return error instanceof Error && error.message ? error.message : "Request failed."; }
function loadStorage(key) { try { return window.localStorage.getItem(key); } catch { return null; } }
