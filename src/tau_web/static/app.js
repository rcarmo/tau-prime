const STORAGE_KEYS = Object.freeze({
  authToken: "tau.web.authToken",
  provider: "tau.web.provider",
  model: "tau.web.model",
  selectedSessionId: "tau.web.selectedSessionId",
  sessionFilter: "tau.web.sessionFilter",
});

const API_PATHS = Object.freeze({
  sessions: "/api/sessions",
  settings: "/api/settings",
  models: "/api/models",
  files: "/api/files",
  search: "/api/search",
  events: "/api/events",
});

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
const SESSION_FILTERS = new Set(["active", "archived"]);
const TABS = ["workspace", "search", "settings"];

class ApiError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "ApiError";
    this.status = details.status ?? 0;
    this.code = details.code ?? "request_failed";
    this.requestId = details.requestId ?? null;
    this.details = details;
  }
}

const ui = bindUi();
const state = {
  authToken: loadStorage(STORAGE_KEYS.authToken),
  sessions: [],
  sessionFilter: normalizeSessionFilter(loadStorage(STORAGE_KEYS.sessionFilter)),
  selectedSessionId: loadStorage(STORAGE_KEYS.selectedSessionId),
  selectedSession: null,
  context: null,
  branches: [],
  messages: [],
  liveDraft: null,
  settings: null,
  models: [],
  activeTab: "workspace",
  workspacePath: ".",
  workspaceEntries: [],
  workspaceFilePath: null,
  workspaceFileContent: "",
  searchResults: [],
  composing: false,
  stream: {
    controller: null,
    reconnectTimer: null,
    reconnectAttempts: 0,
    activeSessionId: null,
    lastEventIds: new Map(),
  },
};

ui.authToken.value = state.authToken ?? "";
ui.workspaceEditor.readOnly = true;

installEventHandlers();
renderShell();
void init();

async function init() {
  try {
    switchTab("workspace");
    applySessionFilter(state.sessionFilter);
    closeDrawers();
    await refreshShell({ reconnect: true, announceMessage: "Tau shell ready." });
    await registerServiceWorker();
  } catch (error) {
    handleError(error, "Unable to load the Tau shell.");
  }
}

function bindUi() {
  return {
    statusStream: requiredElement("status-stream"),
    statusSession: requiredElement("status-session"),
    statusModel: requiredElement("status-model"),
    statusContext: requiredElement("status-context"),
    mobileNavToggle: requiredElement("mobile-nav-toggle"),
    mobilePanelToggle: requiredElement("mobile-panel-toggle"),
    sessionNav: requiredElement("session-nav"),
    closeNavDrawer: requiredElement("close-nav-drawer"),
    newSessionButton: requiredElement("new-session-button"),
    archiveSessionButton: requiredElement("archive-session-button"),
    restoreSessionButton: requiredElement("restore-session-button"),
    showActiveSessions: requiredElement("show-active-sessions"),
    showArchivedSessions: requiredElement("show-archived-sessions"),
    sessionCount: requiredElement("session-count"),
    sessionList: requiredElement("session-list"),
    timelineMain: requiredElement("timeline-main"),
    timelineMeta: requiredElement("timeline-meta"),
    branchList: requiredElement("branch-list"),
    timelineList: requiredElement("timeline-list"),
    sidePanel: requiredElement("side-panel"),
    closePanelDrawer: requiredElement("close-panel-drawer"),
    tabWorkspace: requiredElement("tab-workspace"),
    tabSearch: requiredElement("tab-search"),
    tabSettings: requiredElement("tab-settings"),
    panelWorkspace: requiredElement("panel-workspace"),
    panelSearch: requiredElement("panel-search"),
    panelSettings: requiredElement("panel-settings"),
    workspaceUpButton: requiredElement("workspace-up-button"),
    workspaceReloadButton: requiredElement("workspace-reload-button"),
    workspacePath: requiredElement("workspace-path"),
    workspaceList: requiredElement("workspace-list"),
    workspaceEditorPath: requiredElement("workspace-editor-path"),
    workspaceEditor: requiredElement("workspace-editor"),
    searchForm: requiredElement("search-form"),
    searchInput: requiredElement("search-input"),
    searchSubmitButton: requiredElement("search-submit-button"),
    searchResults: requiredElement("search-results"),
    authForm: requiredElement("auth-form"),
    authToken: requiredElement("auth-token"),
    saveAuthButton: requiredElement("save-auth-button"),
    clearAuthButton: requiredElement("clear-auth-button"),
    modelForm: requiredElement("model-form"),
    providerInput: requiredElement("provider-input"),
    providerOptions: requiredElement("provider-options"),
    modelInput: requiredElement("model-input"),
    modelOptions: requiredElement("model-options"),
    applyModelButton: requiredElement("apply-model-button"),
    refreshButton: requiredElement("refresh-button"),
    settingsSummary: requiredElement("settings-summary"),
    composeForm: requiredElement("compose-form"),
    composeInput: requiredElement("compose-input"),
    composeSubmit: requiredElement("compose-submit"),
    appStatus: requiredElement("app-status"),
    drawerBackdrop: requiredElement("drawer-backdrop"),
  };
}

function installEventHandlers() {
  ui.mobileNavToggle.addEventListener("click", () => toggleDrawer("nav"));
  ui.mobilePanelToggle.addEventListener("click", () => toggleDrawer("panel"));
  ui.closeNavDrawer.addEventListener("click", closeDrawers);
  ui.closePanelDrawer.addEventListener("click", closeDrawers);
  ui.drawerBackdrop.addEventListener("click", closeDrawers);

  ui.newSessionButton.addEventListener("click", () => {
    void createSession({ focusComposer: true });
  });
  ui.archiveSessionButton.addEventListener("click", () => {
    void archiveSelectedSession();
  });
  ui.restoreSessionButton.addEventListener("click", () => {
    void restoreSelectedSession();
  });

  ui.showActiveSessions.addEventListener("click", () => {
    applySessionFilter("active");
  });
  ui.showArchivedSessions.addEventListener("click", () => {
    applySessionFilter("archived");
  });

  ui.tabWorkspace.addEventListener("click", () => switchTab("workspace"));
  ui.tabSearch.addEventListener("click", () => switchTab("search"));
  ui.tabSettings.addEventListener("click", () => switchTab("settings"));

  ui.workspaceUpButton.addEventListener("click", () => {
    void loadWorkspaceDirectory(parentPath(state.workspacePath));
  });
  ui.workspaceReloadButton.addEventListener("click", () => {
    void reloadWorkspace();
  });

  ui.searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void runSearch();
  });

  ui.authForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void saveAuthToken();
  });
  ui.clearAuthButton.addEventListener("click", () => {
    void clearAuthToken();
  });

  ui.modelForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void applyModelSettings();
  });
  ui.refreshButton.addEventListener("click", () => {
    void refreshShell({ reconnect: true, announceMessage: "Shell refreshed." });
  });

  ui.composeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitPrompt();
  });

  window.addEventListener("keydown", handleKeyboardShortcuts);
  window.addEventListener("beforeunload", () => {
    stopEventStream();
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 960) {
      closeDrawers();
    }
  });
}

async function refreshShell({ reconnect = true, announceMessage = null } = {}) {
  const previousSelection = state.selectedSessionId;
  const responses = await Promise.all([
    apiFetch(API_PATHS.settings),
    apiFetch(API_PATHS.models),
    apiFetch(`${API_PATHS.sessions}?include_archived=true`),
    apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(state.workspacePath)}`),
  ]);

  state.settings = responses[0];
  state.models = Array.isArray(responses[1]?.models) ? responses[1].models : [];
  state.sessions = Array.isArray(responses[2]?.sessions) ? responses[2].sessions : [];

  applyWorkspaceResponse(responses[3], { preserveFile: true });
  syncSelection(previousSelection);
  renderShell();
  await refreshSelectedSessionData({ reconnect });

  if (announceMessage) {
    announce(announceMessage);
  }
}

async function createSession({ focusComposer = false } = {}) {
  try {
    const defaults = selectedProviderModel();
    const created = await apiFetch(API_PATHS.sessions, {
      method: "POST",
      json: {
        provider_name: defaults.provider_name,
        model: defaults.model,
      },
    });
    state.sessionFilter = "active";
    persistStorage(STORAGE_KEYS.sessionFilter, state.sessionFilter);
    await loadSessions({ preferredSessionId: created.session_id });
    await selectSession(created.session_id, { reconnect: true });
    announce(`Created session ${sessionLabel(created)}.`);
    if (focusComposer) {
      ui.composeInput.focus();
    }
  } catch (error) {
    handleError(error, "Unable to create a session.");
  }
}

async function archiveSelectedSession() {
  if (!state.selectedSession) {
    announce("Select a session to archive.");
    return;
  }
  if (state.selectedSession.archived_at) {
    announce("Selected session is already archived.");
    return;
  }
  try {
    await apiFetch(sessionPath(state.selectedSession.session_id), { method: "DELETE" });
    await loadSessions({ preferredSessionId: nextVisibleSessionId(state.selectedSession.session_id) });
    await refreshSelectedSessionData({ reconnect: true });
    announce("Session archived.");
  } catch (error) {
    handleError(error, "Unable to archive the selected session.");
  }
}

async function restoreSelectedSession() {
  if (!state.selectedSession) {
    announce("Select a session to restore.");
    return;
  }
  if (!state.selectedSession.archived_at) {
    announce("Selected session is already active.");
    return;
  }
  try {
    const restored = await apiFetch(`${sessionPath(state.selectedSession.session_id)}/restore`, {
      method: "POST",
      json: {},
    });
    state.sessionFilter = "active";
    persistStorage(STORAGE_KEYS.sessionFilter, state.sessionFilter);
    await loadSessions({ preferredSessionId: restored.session_id });
    await selectSession(restored.session_id, { reconnect: true });
    announce("Session restored.");
  } catch (error) {
    handleError(error, "Unable to restore the selected session.");
  }
}

async function loadSessions({ preferredSessionId = state.selectedSessionId } = {}) {
  const data = await apiFetch(`${API_PATHS.sessions}?include_archived=true`);
  state.sessions = Array.isArray(data?.sessions) ? data.sessions : [];
  syncSelection(preferredSessionId);
  renderShell();
}

async function selectSession(sessionId, { reconnect = true } = {}) {
  state.selectedSessionId = sessionId;
  persistStorage(STORAGE_KEYS.selectedSessionId, sessionId);
  syncSelection(sessionId);
  renderShell();
  closeDrawers();
  await refreshSelectedSessionData({ reconnect });
  ui.timelineMain.focus();
}

async function refreshSelectedSessionData({ reconnect = false } = {}) {
  if (!state.selectedSessionId) {
    clearSelectedSessionState();
    renderShell();
    stopEventStream();
    return;
  }

  const sessionId = state.selectedSessionId;
  try {
    const [session, branches, messages, context] = await Promise.all([
      apiFetch(sessionPath(sessionId)),
      apiFetch(`${sessionPath(sessionId)}/branches`),
      apiFetch(`${sessionPath(sessionId)}/messages`),
      apiFetch(`${sessionPath(sessionId)}/context`),
    ]);
    if (state.selectedSessionId !== sessionId) {
      return;
    }
    mergeSessions([session]);
    state.selectedSession = session;
    state.branches = Array.isArray(branches?.branches) ? branches.branches : [];
    state.messages = Array.isArray(messages?.messages) ? messages.messages : [];
    state.context = context;
    state.liveDraft = null;
    syncProviderInputs(session.provider_name, session.model);
    renderShell();
    if (reconnect) {
      startEventStream(sessionId);
    }
  } catch (error) {
    handleError(error, "Unable to load the selected session.");
  }
}

function clearSelectedSessionState() {
  state.selectedSession = null;
  state.context = null;
  state.branches = [];
  state.messages = [];
  state.liveDraft = null;
}

async function applyModelSettings() {
  if (!state.selectedSession) {
    announce("Select a session before applying a model.");
    return;
  }
  if (state.selectedSession.archived_at) {
    announce("Restore the session before applying a model.");
    return;
  }

  const providerName = ui.providerInput.value.trim();
  const model = ui.modelInput.value.trim();
  if (!providerName || !model) {
    announce("Provider and model are required.");
    return;
  }

  try {
    const updated = await apiFetch(`${sessionPath(state.selectedSession.session_id)}/model`, {
      method: "PATCH",
      json: {
        provider_name: providerName,
        model,
        expected_updated_at: state.selectedSession.updated_at,
      },
    });
    mergeSessions([updated]);
    state.selectedSession = updated;
    syncProviderInputs(updated.provider_name, updated.model);
    renderShell();
    await refreshSelectedSessionData({ reconnect: false });
    announce("Session model updated.");
  } catch (error) {
    handleError(error, "Unable to update the session model.");
  }
}

async function loadWorkspaceDirectory(path, { announceMessage = null } = {}) {
  try {
    const response = await apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(path)}`);
    applyWorkspaceResponse(response, { preserveFile: false });
    renderWorkspace();
    if (announceMessage) {
      announce(announceMessage);
    }
  } catch (error) {
    handleError(error, "Unable to load the workspace path.");
  }
}

async function reloadWorkspace() {
  try {
    const directory = await apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(state.workspacePath)}`);
    applyWorkspaceResponse(directory, { preserveFile: true });
    if (state.workspaceFilePath) {
      try {
        const file = await apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(state.workspaceFilePath)}`);
        if (file?.kind === "file") {
          state.workspaceFilePath = file.path;
          state.workspaceFileContent = stringOrEmpty(file.content);
        }
      } catch {
        state.workspaceFilePath = null;
        state.workspaceFileContent = "";
      }
    }
    renderWorkspace();
    announce("Workspace reloaded.");
  } catch (error) {
    handleError(error, "Unable to reload the workspace.");
  }
}

async function openWorkspaceEntry(entry) {
  if (!entry || typeof entry.path !== "string") {
    return;
  }
  if (entry.kind === "directory") {
    await loadWorkspaceDirectory(entry.path);
    return;
  }
  if (entry.kind !== "file") {
    announce(`Cannot open ${entry.kind} entries.`);
    return;
  }
  try {
    const response = await apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(entry.path)}`);
    if (response?.kind !== "file") {
      throw new ApiError("Selected workspace path is not a file.");
    }
    state.workspaceFilePath = response.path;
    state.workspaceFileContent = stringOrEmpty(response.content);
    renderWorkspace();
    announce(`Opened ${response.path}.`);
  } catch (error) {
    handleError(error, "Unable to open the selected file.");
  }
}

async function runSearch() {
  const query = ui.searchInput.value.trim();
  if (!query) {
    announce("Enter a search query.");
    return;
  }

  const params = new URLSearchParams({ q: query, limit: "20" });
  if (state.selectedSessionId && !state.showArchivedSessions.matches?.(":focus")) {
    params.set("session_id", state.selectedSessionId);
  }

  try {
    const response = await apiFetch(`${API_PATHS.search}?${params.toString()}`);
    state.searchResults = Array.isArray(response?.results) ? response.results : [];
    renderSearchResults();
    announce(`Found ${state.searchResults.length} search result${state.searchResults.length === 1 ? "" : "s"}.`);
  } catch (error) {
    handleError(error, "Unable to run search.");
  }
}

async function saveAuthToken() {
  state.authToken = ui.authToken.value.trim() || null;
  persistStorage(STORAGE_KEYS.authToken, state.authToken);
  announce(state.authToken ? "Token saved." : "Token cleared.");
  await refreshShell({ reconnect: true, announceMessage: "Shell refreshed." });
}

async function clearAuthToken() {
  ui.authToken.value = "";
  state.authToken = null;
  persistStorage(STORAGE_KEYS.authToken, null);
  announce("Token cleared.");
  await refreshShell({ reconnect: true, announceMessage: "Shell refreshed." });
}

async function submitPrompt() {
  const prompt = ui.composeInput.value.trim();
  if (!prompt) {
    announce("Enter a prompt before running.");
    return;
  }
  if (state.selectedSession?.archived_at) {
    announce("Restore the selected session before running a prompt.");
    return;
  }

  try {
    if (!state.selectedSessionId) {
      await createSession({ focusComposer: false });
    }
    if (!state.selectedSessionId) {
      throw new ApiError("No session is available for this run.");
    }

    state.composing = true;
    renderControls();
    const sessionId = state.selectedSessionId;
    const run = await apiFetch(`${sessionPath(sessionId)}/runs`, {
      method: "POST",
      json: { content: prompt },
    });
    ui.composeInput.value = "";
    state.liveDraft = null;
    renderTimeline();
    announce(`Run ${run.run_id} submitted.`);
  } catch (error) {
    handleError(error, "Unable to submit the prompt.");
  } finally {
    state.composing = false;
    renderControls();
  }
}

function startEventStream(sessionId) {
  if (!sessionId) {
    stopEventStream();
    return;
  }
  if (state.stream.activeSessionId === sessionId && state.stream.controller) {
    return;
  }
  stopEventStream();
  state.stream.activeSessionId = sessionId;
  state.stream.reconnectAttempts = 0;
  void connectEventStream(sessionId);
}

function stopEventStream() {
  if (state.stream.reconnectTimer !== null) {
    window.clearTimeout(state.stream.reconnectTimer);
    state.stream.reconnectTimer = null;
  }
  if (state.stream.controller) {
    state.stream.controller.abort();
    state.stream.controller = null;
  }
  state.stream.activeSessionId = null;
}

async function connectEventStream(sessionId) {
  if (state.stream.activeSessionId !== sessionId) {
    return;
  }

  const controller = new AbortController();
  state.stream.controller = controller;
  setStreamStatus(state.stream.lastEventIds.has(sessionId) ? "Reconnecting…" : "Connecting…");

  try {
    const headers = buildHeaders("GET", { accept: "text/event-stream" });
    const lastEventId = state.stream.lastEventIds.get(sessionId);
    if (lastEventId) {
      headers.set("Last-Event-ID", lastEventId);
    }

    const url = new URL(API_PATHS.events, window.location.origin);
    url.searchParams.set("session_id", sessionId);

    const response = await fetch(url, {
      method: "GET",
      headers,
      credentials: "same-origin",
      signal: controller.signal,
    });
    if (!response.ok) {
      throw await apiErrorFromResponse(response);
    }
    if (!response.body) {
      throw new Error("Streaming response body is unavailable.");
    }

    state.stream.reconnectAttempts = 0;
    setStreamStatus("Live");

    for await (const frame of readEventStream(response.body, controller.signal)) {
      if (controller.signal.aborted || state.stream.activeSessionId !== sessionId) {
        return;
      }
      if (frame.id) {
        state.stream.lastEventIds.set(sessionId, frame.id);
      }
      await handleStreamFrame(frame, sessionId);
    }

    if (!controller.signal.aborted) {
      scheduleReconnect(sessionId, "Stream closed.");
    }
  } catch (error) {
    if (controller.signal.aborted || state.stream.activeSessionId !== sessionId) {
      return;
    }
    scheduleReconnect(sessionId, messageForError(error, "Stream connection failed."));
  } finally {
    if (state.stream.controller === controller) {
      state.stream.controller = null;
    }
  }
}

function scheduleReconnect(sessionId, reason) {
  if (state.stream.activeSessionId !== sessionId) {
    return;
  }
  state.stream.reconnectAttempts += 1;
  const delay = Math.min(10000, 500 * 2 ** (state.stream.reconnectAttempts - 1));
  setStreamStatus(`Retrying in ${formatDelay(delay)}…`);
  announce(reason);
  state.stream.reconnectTimer = window.setTimeout(() => {
    state.stream.reconnectTimer = null;
    if (state.stream.activeSessionId === sessionId) {
      void connectEventStream(sessionId);
    }
  }, delay);
}

async function handleStreamFrame(frame, sessionId) {
  if (!frame.event) {
    return;
  }
  if (frame.event === "tau.snapshot") {
    mergeSnapshot(frame.data);
    renderSessions();
    await refreshSelectedSessionData({ reconnect: false });
    setStreamStatus("Live");
    return;
  }
  if (!frame.data || frame.data.session_id !== sessionId) {
    return;
  }

  switch (frame.event) {
    case "tau.agent.message_start": {
      const messageRole = frame.data.payload?.message_role;
      if (messageRole === "assistant") {
        state.liveDraft = { runId: frame.data.run_id ?? null, content: "" };
        renderTimeline();
      }
      break;
    }
    case "tau.agent.message_delta": {
      const delta = frame.data.payload?.delta;
      if (typeof delta === "string") {
        appendLiveDraft(frame.data.run_id ?? null, delta);
        renderTimeline();
      }
      break;
    }
    case "tau.agent.message_end": {
      state.liveDraft = null;
      renderTimeline();
      await refreshSelectedSessionData({ reconnect: false });
      break;
    }
    case "tau.agent.error": {
      const message = frame.data.payload?.message;
      if (typeof message === "string" && message) {
        announce(message);
      }
      break;
    }
    default:
      break;
  }
}

function appendLiveDraft(runId, delta) {
  if (!state.liveDraft || state.liveDraft.runId !== runId) {
    state.liveDraft = { runId, content: "" };
  }
  state.liveDraft.content += delta;
}

async function* readEventStream(stream, signal) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      if (signal.aborted) {
        return;
      }
      const { value, done } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        yield* parseEventBuffer(buffer);
        return;
      }
      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const frame = parseEventChunk(chunk);
        if (frame) {
          yield frame;
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function* parseEventBuffer(buffer) {
  const normalized = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  for (const chunk of normalized.split("\n\n")) {
    const frame = parseEventChunk(chunk);
    if (frame) {
      yield frame;
    }
  }
}

function parseEventChunk(chunk) {
  if (!chunk.trim()) {
    return null;
  }
  const frame = { id: null, event: null, data: null };
  const dataLines = [];
  for (const line of chunk.split("\n")) {
    if (!line || line.startsWith(":")) {
      continue;
    }
    const separatorIndex = line.indexOf(":");
    const field = separatorIndex === -1 ? line : line.slice(0, separatorIndex);
    const rawValue = separatorIndex === -1 ? "" : line.slice(separatorIndex + 1);
    const value = rawValue.startsWith(" ") ? rawValue.slice(1) : rawValue;
    if (field === "id") {
      frame.id = value;
    } else if (field === "event") {
      frame.event = value;
    } else if (field === "data") {
      dataLines.push(value);
    }
  }
  if (dataLines.length) {
    try {
      frame.data = JSON.parse(dataLines.join("\n"));
    } catch {
      frame.data = null;
    }
  }
  return frame;
}

function mergeSnapshot(data) {
  const sessions = Array.isArray(data?.sessions) ? data.sessions : [];
  mergeSessions(sessions);
}

function mergeSessions(nextSessions) {
  if (!Array.isArray(nextSessions) || !nextSessions.length) {
    return;
  }
  const byId = new Map(state.sessions.map((session) => [session.session_id, session]));
  for (const session of nextSessions) {
    if (session && typeof session.session_id === "string") {
      byId.set(session.session_id, session);
    }
  }
  state.sessions = Array.from(byId.values());
  syncSelection(state.selectedSessionId);
}

function syncSelection(preferredSessionId) {
  const visible = visibleSessions();
  const preferred = typeof preferredSessionId === "string" ? preferredSessionId : null;
  const selected =
    visible.find((session) => session.session_id === preferred) ??
    visible[0] ??
    null;

  state.selectedSession = selected;
  state.selectedSessionId = selected?.session_id ?? null;
  persistStorage(STORAGE_KEYS.selectedSessionId, state.selectedSessionId);
}

function visibleSessions() {
  return state.sessions.filter((session) => {
    const archived = Boolean(session.archived_at);
    return state.sessionFilter === "archived" ? archived : !archived;
  });
}

function nextVisibleSessionId(excludingSessionId) {
  for (const session of visibleSessions()) {
    if (session.session_id !== excludingSessionId) {
      return session.session_id;
    }
  }
  return null;
}

function applySessionFilter(filter) {
  state.sessionFilter = normalizeSessionFilter(filter);
  persistStorage(STORAGE_KEYS.sessionFilter, state.sessionFilter);
  syncSelection(state.selectedSessionId);
  renderShell();
  void refreshSelectedSessionData({ reconnect: true });
}

function switchTab(name) {
  if (!TABS.includes(name)) {
    return;
  }
  state.activeTab = name;
  const mappings = [
    ["workspace", ui.tabWorkspace, ui.panelWorkspace],
    ["search", ui.tabSearch, ui.panelSearch],
    ["settings", ui.tabSettings, ui.panelSettings],
  ];
  for (const [tabName, button, panel] of mappings) {
    const selected = tabName === name;
    button.setAttribute("aria-selected", String(selected));
    panel.hidden = !selected;
  }
}

function toggleDrawer(which) {
  if (which === "nav") {
    const open = document.body.dataset.navOpen === "true";
    setDrawerState("nav", !open);
  }
  if (which === "panel") {
    const open = document.body.dataset.panelOpen === "true";
    setDrawerState("panel", !open);
  }
}

function closeDrawers() {
  setDrawerState("nav", false);
  setDrawerState("panel", false);
}

function setDrawerState(which, open) {
  const key = which === "nav" ? "navOpen" : "panelOpen";
  document.body.dataset[key] = open ? "true" : "false";
  ui.drawerBackdrop.hidden = !(document.body.dataset.navOpen === "true" || document.body.dataset.panelOpen === "true");
  if (which === "nav") {
    ui.mobileNavToggle.setAttribute("aria-expanded", String(open));
  } else {
    ui.mobilePanelToggle.setAttribute("aria-expanded", String(open));
  }
}

function renderShell() {
  renderSessions();
  renderSessionDetails();
  renderBranches();
  renderTimeline();
  renderWorkspace();
  renderSearchResults();
  renderSettings();
  renderControls();
}

function renderSessions() {
  ui.showActiveSessions.setAttribute("aria-pressed", String(state.sessionFilter === "active"));
  ui.showArchivedSessions.setAttribute("aria-pressed", String(state.sessionFilter === "archived"));

  const sessions = visibleSessions();
  ui.sessionCount.textContent = `${sessions.length} session${sessions.length === 1 ? "" : "s"}`;
  ui.sessionList.replaceChildren();

  if (!sessions.length) {
    ui.sessionList.append(createPlaceholderItem("No sessions available."));
    return;
  }

  for (const session of sessions) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "session-button";
    button.dataset.active = String(session.session_id === state.selectedSessionId);
    button.addEventListener("click", () => {
      void selectSession(session.session_id, { reconnect: true });
    });

    const card = document.createElement("div");
    card.className = "session-card";

    const title = document.createElement("strong");
    title.textContent = sessionLabel(session);
    card.append(title);

    const meta = document.createElement("p");
    meta.className = "session-meta";
    meta.textContent = sessionMeta(session);
    card.append(meta);

    button.append(card);
    item.append(button);
    ui.sessionList.append(item);
  }
}

function renderSessionDetails() {
  if (!state.selectedSession) {
    ui.statusSession.textContent = "No session selected";
    ui.statusModel.textContent = ui.modelInput.value.trim() ? `${ui.providerInput.value.trim()}/${ui.modelInput.value.trim()}` : "Unset";
    ui.statusContext.textContent = "No context loaded";
    ui.timelineMeta.textContent = "Load a session to inspect persisted messages.";
    return;
  }

  const session = state.selectedSession;
  ui.statusSession.textContent = sessionLabel(session);
  ui.statusModel.textContent = `${session.provider_name}/${state.context?.model ?? session.model}`;
  ui.statusContext.textContent = contextSummaryText();
  ui.timelineMeta.textContent = contextSummaryText(true);
}

function renderBranches() {
  ui.branchList.replaceChildren();
  if (!state.selectedSessionId) {
    ui.branchList.append(createMutedText("Select a session to load branches."));
    return;
  }
  if (!state.branches.length) {
    ui.branchList.append(createMutedText("No persisted branches yet."));
    return;
  }

  for (const branch of state.branches) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "branch-button";
    button.dataset.active = String(Boolean(branch.active));
    button.textContent = `Depth ${numberOrZero(branch.depth)} · ${shortId(branch.leaf_entry_id)}`;
    button.addEventListener("click", () => {
      void selectBranch(branch.leaf_entry_id);
    });
    ui.branchList.append(button);
  }
}

async function selectBranch(leafEntryId) {
  if (!state.selectedSessionId) {
    return;
  }
  try {
    await apiFetch(`${sessionPath(state.selectedSessionId)}/branches/select`, {
      method: "POST",
      json: { leaf_entry_id: leafEntryId },
    });
    await refreshSelectedSessionData({ reconnect: false });
    announce(`Selected branch ${shortId(leafEntryId)}.`);
  } catch (error) {
    handleError(error, "Unable to select the branch.");
  }
}

function renderTimeline() {
  ui.timelineList.replaceChildren();
  const timelineItems = state.messages.map((entry) => ({
    role: entry?.message?.role ?? "assistant",
    content: messageContent(entry?.message),
    meta: typeof entry?.id === "string" ? `Entry ${shortId(entry.id)}` : "Persisted message",
  }));

  if (state.liveDraft?.content) {
    timelineItems.push({
      role: "assistant",
      content: state.liveDraft.content,
      meta: "Streaming draft",
      live: true,
    });
  }

  if (!state.selectedSessionId) {
    ui.timelineList.append(createPlaceholderItem("Select or create a session to load the timeline."));
    return;
  }
  if (!timelineItems.length) {
    ui.timelineList.append(createPlaceholderItem("No persisted messages yet."));
    return;
  }

  for (const item of timelineItems) {
    const listItem = document.createElement("li");
    const card = document.createElement("article");
    card.className = "timeline-card";

    const role = document.createElement("p");
    role.className = "timeline-role";
    role.textContent = item.live ? `${item.role} · live` : item.role;

    const meta = document.createElement("p");
    meta.className = "timeline-entry-meta";
    meta.textContent = item.meta;

    const content = document.createElement("p");
    content.className = "timeline-content";
    content.textContent = item.content || "(empty)";

    card.append(role, meta, content);
    listItem.append(card);
    ui.timelineList.append(listItem);
  }
}

function renderWorkspace() {
  ui.workspacePath.textContent = state.workspacePath;
  ui.workspaceEditorPath.textContent = state.workspaceFilePath ?? "No file selected";
  ui.workspaceEditor.value = state.workspaceFileContent;
  ui.workspaceList.replaceChildren();

  if (!state.workspaceEntries.length) {
    ui.workspaceList.append(createPlaceholderItem("No workspace entries available."));
    return;
  }

  for (const entry of state.workspaceEntries) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "workspace-entry-button";
    button.disabled = entry.kind !== "directory" && entry.kind !== "file";
    button.addEventListener("click", () => {
      void openWorkspaceEntry(entry);
    });

    const label = document.createElement("span");
    label.textContent = entry.name;

    const kind = document.createElement("span");
    kind.className = "workspace-entry-kind";
    kind.textContent = entry.kind;

    button.append(label, kind);
    item.append(button);
    ui.workspaceList.append(item);
  }
}

function renderSearchResults() {
  ui.searchResults.replaceChildren();
  if (!state.searchResults.length) {
    ui.searchResults.append(createPlaceholderItem("Search results will appear here."));
    return;
  }

  for (const result of state.searchResults) {
    const item = document.createElement("li");
    const card = document.createElement("article");
    card.className = "search-card";

    const title = document.createElement("strong");
    title.textContent = `${result.entity_type} · ${result.entity_id}`;

    const meta = document.createElement("p");
    meta.className = "search-meta";
    meta.textContent = [
      result.session_id ? `Session ${shortId(result.session_id)}` : "Global",
      typeof result.rank === "number" ? `Rank ${result.rank.toFixed(2)}` : null,
    ]
      .filter(Boolean)
      .join(" · ");

    const text = document.createElement("p");
    text.className = "timeline-content";
    text.textContent = stringOrEmpty(result.text) || "(empty)";

    card.append(title, meta, text);

    if (typeof result.session_id === "string" && result.session_id) {
      const action = document.createElement("button");
      action.type = "button";
      action.textContent = "Open session";
      action.addEventListener("click", () => {
        switchTab("workspace");
        void selectSession(result.session_id, { reconnect: true });
      });
      card.append(action);
    }

    item.append(card);
    ui.searchResults.append(item);
  }
}

function renderSettings() {
  renderModelOptions();
  ui.settingsSummary.replaceChildren();

  const settings = state.settings;
  if (!settings) {
    ui.settingsSummary.append(createMutedText("Runtime settings unavailable."));
    return;
  }

  const items = [
    ["Host", `${settings.host}:${settings.port}`],
    ["Workspace", stringOrEmpty(settings.cwd)],
    ["Database", stringOrEmpty(settings.database_path)],
    ["Auth", settings.auth_required ? "Required" : "Disabled"],
    ["Origins", Array.isArray(settings.allowed_origins) && settings.allowed_origins.length ? settings.allowed_origins.join(", ") : "Same origin only"],
    ["Concurrency", String(settings.max_active_runs ?? "")],
    ["Request size", String(settings.max_request_size ?? "")],
  ];

  for (const [label, value] of items) {
    const wrapper = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    wrapper.append(dt, dd);
    ui.settingsSummary.append(wrapper);
  }
}

function renderModelOptions() {
  const providerValues = new Set();
  const modelValues = new Set();

  for (const item of state.models) {
    if (typeof item?.provider_name === "string" && item.provider_name) {
      providerValues.add(item.provider_name);
    }
    if (typeof item?.model === "string" && item.model) {
      modelValues.add(item.model);
    }
  }

  const providerInput = ui.providerInput.value.trim();
  const modelInput = ui.modelInput.value.trim();
  if (providerInput) {
    providerValues.add(providerInput);
  }
  if (modelInput) {
    modelValues.add(modelInput);
  }

  replaceOptions(ui.providerOptions, Array.from(providerValues).sort());
  replaceOptions(ui.modelOptions, Array.from(modelValues).sort());
}

function renderControls() {
  const session = state.selectedSession;
  const archived = Boolean(session?.archived_at);
  ui.archiveSessionButton.disabled = !session || archived;
  ui.restoreSessionButton.disabled = !session || !archived;
  ui.applyModelButton.disabled = !session || archived;
  ui.composeSubmit.disabled = archived || state.composing;
}

function applyWorkspaceResponse(response, { preserveFile = false } = {}) {
  if (response?.kind === "directory") {
    state.workspacePath = response.path || ".";
    state.workspaceEntries = Array.isArray(response.entries) ? response.entries : [];
    if (!preserveFile) {
      state.workspaceFilePath = null;
      state.workspaceFileContent = "";
    }
    return;
  }
  if (response?.kind === "file") {
    state.workspaceFilePath = response.path;
    state.workspaceFileContent = stringOrEmpty(response.content);
  }
}

function syncProviderInputs(providerName, model) {
  ui.providerInput.value = providerName ?? "";
  ui.modelInput.value = model ?? "";
  persistStorage(STORAGE_KEYS.provider, ui.providerInput.value.trim() || null);
  persistStorage(STORAGE_KEYS.model, ui.modelInput.value.trim() || null);
}

function selectedProviderModel() {
  const provider_name =
    ui.providerInput.value.trim() ||
    state.selectedSession?.provider_name ||
    loadStorage(STORAGE_KEYS.provider) ||
    state.models[0]?.provider_name ||
    "test";
  const model =
    ui.modelInput.value.trim() ||
    state.selectedSession?.model ||
    loadStorage(STORAGE_KEYS.model) ||
    state.models[0]?.model ||
    "model";
  syncProviderInputs(provider_name, model);
  return { provider_name, model };
}

function handleKeyboardShortcuts(event) {
  const isModifier = event.metaKey || event.ctrlKey;
  if (isModifier && event.key.toLowerCase() === "k") {
    event.preventDefault();
    switchTab("search");
    setDrawerState("panel", true);
    ui.searchInput.focus();
    ui.searchInput.select();
    return;
  }
  if (isModifier && event.key.toLowerCase() === "n") {
    event.preventDefault();
    void createSession({ focusComposer: true });
    return;
  }
  if (event.key === "Escape") {
    closeDrawers();
  }
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  try {
    await navigator.serviceWorker.register("/sw.js", { scope: "/" });
  } catch {
    announce("Offline support is unavailable.");
  }
}

async function apiFetch(path, options = {}) {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = buildHeaders(method, options.headers);
  const request = {
    method,
    headers,
    credentials: "same-origin",
    signal: options.signal,
  };

  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    request.body = JSON.stringify(options.json);
  }

  const response = await fetch(path, request);
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    throw await apiErrorFromResponse(response);
  }
  if (!expectsJson(response)) {
    return await response.text();
  }
  return await response.json();
}

function buildHeaders(method, source = {}) {
  const headers = new Headers(source);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (!SAFE_METHODS.has(method)) {
    headers.set("X-Tau-CSRF", "1");
  }
  if (state.authToken) {
    headers.set("Authorization", `Bearer ${state.authToken}`);
  }
  return headers;
}

async function apiErrorFromResponse(response) {
  let payload = null;
  try {
    payload = expectsJson(response) ? await response.json() : await response.text();
  } catch {
    payload = null;
  }

  const error = payload && typeof payload === "object" ? payload.error : null;
  const message = typeof error?.message === "string" ? error.message : `${response.status} ${response.statusText}`.trim();
  return new ApiError(message, {
    status: response.status,
    code: typeof error?.code === "string" ? error.code : "request_failed",
    requestId: typeof error?.request_id === "string" ? error.request_id : null,
    payload,
  });
}

function expectsJson(response) {
  const contentType = response.headers.get("Content-Type") || "";
  return contentType.includes("application/json");
}

function announce(message) {
  ui.appStatus.textContent = message;
}

function setStreamStatus(message) {
  ui.statusStream.textContent = message;
}

function handleError(error, fallbackMessage) {
  const message = messageForError(error, fallbackMessage);
  console.error(error);
  announce(message);
  setStreamStatus(message);
}

function messageForError(error, fallbackMessage) {
  if (error instanceof ApiError && error.message) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallbackMessage;
}

function normalizeSessionFilter(value) {
  return SESSION_FILTERS.has(value) ? value : "active";
}

function requiredElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required element: ${id}`);
  }
  return element;
}

function replaceOptions(container, values) {
  container.replaceChildren();
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    container.append(option);
  }
}

function createPlaceholderItem(message) {
  const item = document.createElement("li");
  item.append(createMutedText(message));
  return item;
}

function createMutedText(message) {
  const element = document.createElement("p");
  element.className = "muted small-text";
  element.textContent = message;
  return element;
}

function sessionPath(sessionId) {
  return `${API_PATHS.sessions}/${encodeURIComponent(sessionId)}`;
}

function sessionLabel(session) {
  const title = stringOrEmpty(session?.title).trim();
  if (title) {
    return title;
  }
  const agentName = stringOrEmpty(session?.agent_name).trim();
  if (agentName) {
    return agentName;
  }
  return shortId(session?.session_id);
}

function sessionMeta(session) {
  const details = [`${session.provider_name}/${session.model}`];
  if (session.archived_at) {
    details.push("archived");
  }
  if (session.updated_at) {
    details.push(`updated ${formatTimestamp(session.updated_at)}`);
  }
  return details.join(" · ");
}

function contextSummaryText(longForm = false) {
  if (!state.context) {
    return longForm ? "No context loaded." : "No context loaded";
  }
  const parts = [
    `${numberOrZero(state.context.message_count)} messages`,
    `${numberOrZero(state.context.compaction_count)} compactions`,
  ];
  if (state.context.active_leaf_entry_id) {
    parts.push(`leaf ${shortId(state.context.active_leaf_entry_id)}`);
  }
  return parts.join(" · ");
}

function parentPath(path) {
  const current = (path || ".").replace(/^\/+|\/+$/g, "");
  if (!current || current === ".") {
    return ".";
  }
  const parts = current.split("/");
  parts.pop();
  return parts.length ? parts.join("/") : ".";
}

function messageContent(message) {
  if (!message || typeof message !== "object") {
    return "";
  }
  const role = stringOrEmpty(message.role);
  const content = stringOrEmpty(message.content);
  if (role === "tool") {
    const header = stringOrEmpty(message.name) ? `Tool ${message.name}` : "Tool";
    return [header, content].filter(Boolean).join("\n");
  }
  if (Array.isArray(message.tool_calls) && message.tool_calls.length) {
    const calls = message.tool_calls.map((call) => `Tool call ${stringOrEmpty(call.name) || shortId(call.id)}`);
    return [content, ...calls].filter(Boolean).join("\n");
  }
  return content;
}

function shortId(value) {
  const text = stringOrEmpty(value);
  if (!text) {
    return "unknown";
  }
  return text.length > 12 ? text.slice(0, 12) : text;
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return stringOrEmpty(value);
  }
  return date.toLocaleString();
}

function formatDelay(milliseconds) {
  return milliseconds >= 1000 ? `${(milliseconds / 1000).toFixed(1)}s` : `${milliseconds}ms`;
}

function stringOrEmpty(value) {
  return typeof value === "string" ? value : "";
}

function numberOrZero(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function loadStorage(key) {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function persistStorage(key, value) {
  try {
    if (value === null || value === undefined || value === "") {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    return;
  }
}
