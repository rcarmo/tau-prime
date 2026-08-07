const STORAGE_KEYS = Object.freeze({
  authToken: "tau.web.authToken",
  provider: "tau.web.provider",
  model: "tau.web.model",
  selectedSessionId: "tau.web.selectedSessionId",
  sessionFilter: "tau.web.sessionFilter",
  metersEnabled: "tau.web.metersEnabled",
  metersCollapsed: "tau.web.metersCollapsed",
});

const API_PATHS = Object.freeze({
  sessions: "/api/sessions",
  settings: "/api/settings",
  models: "/api/models",
  commands: "/api/commands",
  files: "/api/files",
  media: "/api/media",
  search: "/api/search",
  events: "/api/events",
  meters: "/meters",
  dashboard: "/dashboard",
});

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
const SESSION_FILTERS = new Set(["active", "archived"]);
const DELIVERY_MODES = new Set(["run", "follow_up", "steer"]);
const MAX_COMPOSER_ATTACHMENTS = 8;
const MAX_ATTACHMENT_REFERENCE_ITEMS = MAX_COMPOSER_ATTACHMENTS;
const DEFAULT_THINKING_LEVELS = Object.freeze([
  ["", "Default"],
  ["off", "Off -- no reasoning"],
  ["minimal", "Minimal -- very brief reasoning"],
  ["low", "Low -- light reasoning"],
  ["medium", "Medium -- moderate reasoning"],
  ["high", "High -- deep reasoning"],
  ["xhigh", "XHigh -- maximum reasoning"],
]);
const TABS = ["workspace", "search", "plan", "settings"];

let trustedFrontendConfigured = false;
let trustedFrontendLoading = null;
let trustedFrontendLoaded = false;

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
  selectedSessionId: sessionFromLocation() ?? loadStorage(STORAGE_KEYS.selectedSessionId),
  selectedSession: null,
  context: null,
  branches: [],
  messages: [],
  liveDraft: null,
  settings: null,
  meters: null,
  metersEnabled: loadBooleanStorage(STORAGE_KEYS.metersEnabled, true),
  metersCollapsed: loadBooleanStorage(STORAGE_KEYS.metersCollapsed, true),
  metersTimer: null,
  dashboard: {
    open: false,
    sessions: [],
    page: 1,
    pageSize: dashboardCapacity(),
    total: 0,
    totalPages: 1,
    generatedAt: null,
    loading: false,
    fullRefreshTimer: null,
    previewRefreshTimer: null,
    ageTimer: null,
    invalidationTimer: null,
    needsRefresh: false,
  },
  models: [],
  commands: [],
  activeTab: "workspace",
  workspacePath: ".",
  workspaceEntries: [],
  workspaceFilePath: null,
  workspaceFileContent: "",
  workspaceFileRenderer: null,
  workspaceAnnotations: [],
  searchResults: [],
  plan: null,
  planDraft: "",
  planDirty: false,
  planConflict: null,
  approvals: [],
  composing: false,
  uploadingAttachments: false,
  composer: createComposerState(),
  stream: {
    controller: null,
    reconnectTimer: null,
    reconnectAttempts: 0,
    activeSessionId: null,
    lastEventIds: new Map(),
  },
};

ui.authToken.value = state.authToken ?? "";
ui.providerInput.value = loadStorage(STORAGE_KEYS.provider) ?? "";
ui.modelInput.value = loadStorage(STORAGE_KEYS.model) ?? "";
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
    void initializeTrustedFrontendModules();
    await refreshMeters();
    startMetersPolling();
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
    systemMeters: requiredElement("system-meters"),
    metersSummary: requiredElement("meters-summary"),
    metersDetails: requiredElement("meters-details"),
    metersCollapseButton: requiredElement("meters-collapse-button"),
    metersVisibilityButton: requiredElement("meters-visibility-button"),
    meterCpuValue: requiredElement("meter-cpu-value"),
    meterRamValue: requiredElement("meter-ram-value"),
    meterRssValue: requiredElement("meter-rss-value"),
    meterSwapValue: requiredElement("meter-swap-value"),
    meterCpuSparkline: requiredElement("meter-cpu-sparkline"),
    meterRamSparkline: requiredElement("meter-ram-sparkline"),
    meterRssSparkline: requiredElement("meter-rss-sparkline"),
    meterSwapSparkline: requiredElement("meter-swap-sparkline"),
    dashboardToggle: requiredElement("dashboard-toggle"),
    dashboardCount: requiredElement("dashboard-count"),
    sessionDashboard: requiredElement("session-dashboard"),
    dashboardClose: requiredElement("dashboard-close"),
    dashboardGrid: requiredElement("dashboard-grid"),
    dashboardAge: requiredElement("dashboard-age"),
    dashboardPrevious: requiredElement("dashboard-previous"),
    dashboardPage: requiredElement("dashboard-page"),
    dashboardNext: requiredElement("dashboard-next"),
    dashboardManage: requiredElement("dashboard-manage"),
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
    agentStatusIndicator: requiredElement("agent-status-indicator"),
    agentStatusText: requiredElement("agent-status-text"),
    branchList: requiredElement("branch-list"),
    timelineList: requiredElement("timeline-list"),
    sidePanel: requiredElement("side-panel"),
    closePanelDrawer: requiredElement("close-panel-drawer"),
    tabWorkspace: requiredElement("tab-workspace"),
    tabSearch: requiredElement("tab-search"),
    tabPlan: requiredElement("tab-plan"),
    tabSettings: requiredElement("tab-settings"),
    panelWorkspace: requiredElement("panel-workspace"),
    panelSearch: requiredElement("panel-search"),
    panelPlan: requiredElement("panel-plan"),
    panelSettings: requiredElement("panel-settings"),
    workspaceUpButton: requiredElement("workspace-up-button"),
    workspaceReloadButton: requiredElement("workspace-reload-button"),
    workspacePath: requiredElement("workspace-path"),
    workspaceList: requiredElement("workspace-list"),
    workspaceEditorPath: requiredElement("workspace-editor-path"),
    workspaceEditor: requiredElement("workspace-editor"),
    workspaceAnnotations: requiredElement("workspace-annotations"),
    workspaceAnnotationList: requiredElement("workspace-annotation-list"),
    workspaceRenderer: requiredElement("workspace-renderer"),
    searchForm: requiredElement("search-form"),
    searchInput: requiredElement("search-input"),
    searchSubmitButton: requiredElement("search-submit-button"),
    searchResults: requiredElement("search-results"),
    planForm: requiredElement("plan-form"),
    planEditor: requiredElement("plan-editor"),
    planRevision: requiredElement("plan-revision"),
    planStatus: requiredElement("plan-status"),
    planConflict: requiredElement("plan-conflict"),
    planSaveButton: requiredElement("plan-save-button"),
    planReloadButton: requiredElement("plan-reload-button"),
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
    thinkingForm: requiredElement("thinking-form"),
    thinkingLevelSelect: requiredElement("thinking-level-select"),
    settingsSummary: requiredElement("settings-summary"),
    composeForm: requiredElement("compose-form"),
    composeProviderSelect: requiredElement("compose-provider-select"),
    composeModelSelect: requiredElement("compose-model-select"),
    composeThinkingSelect: requiredElement("compose-thinking-select"),
    composeDeliveryMode: requiredElement("compose-delivery-mode"),
    composeContextReadout: requiredElement("compose-context-readout"),
    composeAttachmentButton: requiredElement("compose-attachment-button"),
    composeFileInput: requiredElement("compose-file-input"),
    composeAttachmentList: requiredElement("compose-attachment-list"),
    composeClearAttachments: requiredElement("compose-clear-attachments"),
    composeInput: requiredElement("compose-input"),
    composeCompletionPopup: requiredElement("compose-completion-popup"),
    composeCompletionListbox: requiredElement("compose-completion-listbox"),
    composeCompletionStatus: requiredElement("compose-completion-status"),
    composeSubmit: requiredElement("compose-submit"),
    appStatus: requiredElement("app-status"),
    drawerBackdrop: requiredElement("drawer-backdrop"),
  };
}

function installEventHandlers() {
  window.addEventListener("tau:meter-controls", (event) => {
    applyMeterControls(Boolean(event.detail?.enabled), Boolean(event.detail?.collapsed));
  });
  window.addEventListener("tau:dashboard-visibility", (event) => {
    applyDashboardOpen(Boolean(event.detail?.open));
  });
  ui.dashboardPrevious.addEventListener("click", () => changeDashboardPage(-1));
  ui.dashboardNext.addEventListener("click", () => changeDashboardPage(1));
  ui.dashboardManage.addEventListener("click", openSessionManager);

  ui.newSessionButton.addEventListener("click", () => {
    void createSession({ focusComposer: true });
  });
  ui.archiveSessionButton.addEventListener("click", () => {
    void archiveSelectedSession();
  });
  ui.restoreSessionButton.addEventListener("click", () => {
    void restoreSelectedSession();
  });

  window.addEventListener("tau:session-filter", (event) => {
    applySessionFilter(event.detail?.filter);
  });

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

  ui.planEditor.addEventListener("input", () => {
    state.planDraft = ui.planEditor.value;
    state.planDirty = state.planDraft !== (state.plan?.markdown ?? "");
    renderPlan();
  });
  ui.planForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void savePlan();
  });
  ui.planReloadButton.addEventListener("click", () => {
    void loadPlan({ force: true });
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
  ui.providerInput.addEventListener("input", handleProviderModelInputChange);
  ui.modelInput.addEventListener("input", handleProviderModelInputChange);
  ui.providerInput.addEventListener("change", handleProviderModelInputChange);
  ui.modelInput.addEventListener("change", handleProviderModelInputChange);
  ui.refreshButton.addEventListener("click", () => {
    void refreshShell({ reconnect: true, announceMessage: "Shell refreshed." });
  });

  ui.composeProviderSelect.addEventListener("change", () => {
    void handleComposerModelControlChange();
  });
  ui.composeModelSelect.addEventListener("change", () => {
    void handleComposerModelControlChange();
  });
  ui.composeThinkingSelect.addEventListener("change", () => {
    void handleComposerThinkingControlChange();
  });
  ui.composeDeliveryMode.addEventListener("change", () => {
    state.composer.deliveryMode = normalizeDeliveryMode(ui.composeDeliveryMode.value);
    renderControls();
  });
  ui.composeAttachmentButton.addEventListener("click", () => {
    ui.composeFileInput.click();
  });
  ui.composeFileInput.addEventListener("change", () => {
    void handleComposerFileSelection();
  });
  ui.composeClearAttachments.addEventListener("click", () => {
    clearComposerAttachments({ announceMessage: "Cleared staged attachments." });
  });
  ui.composeInput.addEventListener("input", handleComposeInputChange);
  ui.composeInput.addEventListener("click", updateComposerCompletion);
  ui.composeInput.addEventListener("keyup", handleComposeCursorMove);
  ui.composeInput.addEventListener("keydown", handleComposeInputKeydown);
  ui.composeInput.addEventListener("blur", handleComposeInputBlur);

  ui.composeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitPrompt();
  });

  document.addEventListener("tau:widget-action", (event) => {
    void handleWidgetAction(event);
  });
  document.addEventListener("tau:widget-submit", (event) => {
    void handleWidgetSubmit(event);
  });
  document.addEventListener("tau:widget-refresh", (event) => {
    void handleWidgetRefresh(event);
  });

  window.addEventListener("keydown", handleKeyboardShortcuts);
  document.addEventListener("visibilitychange", handleMetersVisibilityChange);
  window.addEventListener("beforeunload", () => {
    stopEventStream();
    stopMetersPolling();
    stopDashboardTimers();
    if (trustedFrontendConfigured) {
      void window.tauFrontendSDK?.disposeAll?.();
    }
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 960) {
      closeDrawers();
    }
    handleDashboardResize();
  });
}

async function refreshShell({ reconnect = true, announceMessage = null } = {}) {
  const previousSelection = state.selectedSessionId;
  const responses = await Promise.all([
    apiFetch(API_PATHS.settings),
    apiFetch(API_PATHS.models),
    apiFetch(API_PATHS.commands),
    apiFetch(`${API_PATHS.sessions}?include_archived=true`),
    apiFetch(`${API_PATHS.files}?path=${encodeURIComponent(state.workspacePath)}`),
  ]);

  state.settings = responses[0];
  state.models = Array.isArray(responses[1]?.models) ? responses[1].models : [];
  state.commands = Array.isArray(responses[2]?.commands) ? responses[2].commands : [];
  state.sessions = Array.isArray(responses[3]?.sessions) ? responses[3].sessions : [];

  applyWorkspaceResponse(responses[4], { preserveFile: true });
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

async function selectSession(sessionId, { reconnect = true, focusTimeline = true } = {}) {
  if (
    state.planDirty &&
    state.selectedSessionId &&
    state.selectedSessionId !== sessionId &&
    !window.confirm("Discard unsaved plan edits and switch sessions?")
  ) {
    return;
  }
  state.selectedSessionId = sessionId;
  persistStorage(STORAGE_KEYS.selectedSessionId, sessionId);
  syncSelection(sessionId);
  renderShell();
  closeDrawers();
  await refreshSelectedSessionData({ reconnect });
  if (focusTimeline) {
    ui.timelineMain.focus();
  }
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
    const [session, branches, messages, context, plan, approvals] = await Promise.all([
      apiFetch(sessionPath(sessionId)),
      apiFetch(`${sessionPath(sessionId)}/branches`),
      apiFetch(`${sessionPath(sessionId)}/messages`),
      apiFetch(`${sessionPath(sessionId)}/context`),
      apiFetch(`${sessionPath(sessionId)}/plan`),
      apiFetch(`${sessionPath(sessionId)}/approvals`),
    ]);
    if (state.selectedSessionId !== sessionId) {
      return;
    }
    mergeSessions([session]);
    state.selectedSession = session;
    state.branches = Array.isArray(branches?.branches) ? branches.branches : [];
    state.messages = Array.isArray(messages?.messages) ? messages.messages : [];
    state.context = context;
    applyPlanResponse(plan, { sessionId });
    state.approvals = Array.isArray(approvals?.approvals) ? approvals.approvals : [];
    state.liveDraft = null;
    syncProviderInputs(session.provider_name, session.model);
    renderShell();
    renderApprovalPrompt();
    if (reconnect) {
      startEventStream(sessionId);
    }
  } catch (error) {
    if (state.selectedSessionId !== sessionId) {
      return;
    }
    handleError(error, "Unable to load the selected session.");
  }
}

function clearSelectedSessionState() {
  state.selectedSession = null;
  state.context = null;
  state.branches = [];
  state.messages = [];
  state.liveDraft = null;
  state.plan = null;
  state.planDraft = "";
  state.planDirty = false;
  state.planConflict = null;
  state.approvals = [];
  document.querySelector(".approval-backdrop")?.remove();
}

function applyPlanResponse(plan, { sessionId, force = false } = {}) {
  if (!plan || plan.session_id !== sessionId) {
    return;
  }
  const samePlan = state.plan?.session_id === sessionId;
  const changedRemotely = samePlan && plan.revision !== state.plan.revision;
  if (!force && state.planDirty && changedRemotely) {
    state.planConflict = plan;
    renderPlan();
    return;
  }
  state.plan = plan;
  state.planDraft = typeof plan.markdown === "string" ? plan.markdown : "";
  state.planDirty = false;
  state.planConflict = null;
}

async function loadPlan({ force = false } = {}) {
  const sessionId = state.selectedSessionId;
  if (!sessionId) {
    return;
  }
  try {
    const plan = await apiFetch(`${sessionPath(sessionId)}/plan`);
    if (state.selectedSessionId !== sessionId) {
      return;
    }
    applyPlanResponse(plan, { sessionId, force });
    renderPlan();
    if (force) {
      announce("Reloaded the server plan.");
    }
  } catch (error) {
    handleError(error, "Unable to load the session plan.");
  }
}

async function loadApprovals() {
  const sessionId = state.selectedSessionId;
  if (!sessionId) {
    state.approvals = [];
    renderApprovalPrompt();
    return;
  }
  try {
    const payload = await apiFetch(`${sessionPath(sessionId)}/approvals`);
    if (state.selectedSessionId !== sessionId) {
      return;
    }
    state.approvals = Array.isArray(payload?.approvals) ? payload.approvals : [];
    renderApprovalPrompt();
  } catch (error) {
    handleError(error, "Unable to load tool approvals.");
  }
}

function renderApprovalPrompt() {
  const existing = document.querySelector(".approval-backdrop");
  const approval = state.approvals[0];
  if (!approval) {
    existing?.remove();
    return;
  }
  if (existing?.dataset.approvalId === approval.approval_id) {
    return;
  }
  existing?.remove();

  const backdrop = document.createElement("div");
  backdrop.className = "approval-backdrop";
  backdrop.dataset.approvalId = approval.approval_id;
  const panel = document.createElement("section");
  panel.className = "approval-prompt";
  panel.setAttribute("role", "alertdialog");
  panel.setAttribute("aria-modal", "true");
  panel.setAttribute("aria-labelledby", "approval-title");
  panel.setAttribute("aria-describedby", "approval-description");

  const title = document.createElement("h2");
  title.id = "approval-title";
  title.textContent = `Allow ${approval.tool_name}?`;
  const description = document.createElement("p");
  description.id = "approval-description";
  description.textContent = approval.description || "The agent requested permission to run this tool.";
  const argumentsView = document.createElement("pre");
  argumentsView.className = "approval-arguments";
  argumentsView.textContent = JSON.stringify(approval.arguments ?? {}, null, 2);
  const actions = document.createElement("div");
  actions.className = "approval-actions";
  const denyButton = document.createElement("button");
  denyButton.type = "button";
  denyButton.className = "secondary-button";
  denyButton.textContent = "Deny";
  const allowButton = document.createElement("button");
  allowButton.type = "button";
  allowButton.className = "primary-button";
  allowButton.textContent = "Allow once";
  denyButton.addEventListener("click", () => void settleApproval(approval.approval_id, "deny"));
  allowButton.addEventListener("click", () => void settleApproval(approval.approval_id, "allow"));
  actions.append(denyButton, allowButton);
  panel.append(title, description, argumentsView, actions);
  backdrop.append(panel);
  document.body.append(backdrop);
  denyButton.focus();
}

function setApprovalButtonsDisabled(disabled) {
  const buttons = document.querySelectorAll(".approval-prompt button");
  for (const button of buttons) {
    button.disabled = disabled;
  }
}

async function settleApproval(approvalId, decision) {
  setApprovalButtonsDisabled(true);
  try {
    await apiFetch(`/api/approvals/${encodeURIComponent(approvalId)}`, {
      method: "POST",
      json: { decision },
    });
    state.approvals = state.approvals.filter((item) => item.approval_id !== approvalId);
    renderApprovalPrompt();
    announce(`Tool request ${decision === "allow" ? "allowed" : "denied"}.`);
  } catch (error) {
    setApprovalButtonsDisabled(false);
    handleError(error, "Unable to resolve the tool request.");
  }
}

async function savePlan() {
  const session = state.selectedSession;
  if (!session || session.archived_at) {
    announce("Select an active session before saving its plan.");
    return;
  }
  try {
    const plan = await apiFetch(`${sessionPath(session.session_id)}/plan`, {
      method: "PUT",
      json: {
        markdown: state.planDraft,
        expected_revision: state.planConflict?.revision ?? state.plan?.revision ?? 0,
      },
    });
    applyPlanResponse(plan, { sessionId: session.session_id, force: true });
    renderPlan();
    announce("Session plan saved.");
  } catch (error) {
    const current = error instanceof ApiError ? error.details?.payload?.current : null;
    if (error instanceof ApiError && error.status === 409 && current) {
      state.planConflict = current;
      renderPlan();
      announce("The plan changed elsewhere. Review the conflict before saving.");
      return;
    }
    handleError(error, "Unable to save the session plan.");
  }
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
          applyWorkspaceFileResponse(file);
        }
      } catch {
        clearWorkspaceFile();
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
    applyWorkspaceFileResponse(response);
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
  if (state.selectedSessionId) {
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
  const content = buildSubmittedPromptContent(prompt);
  if (!content) {
    announce("Enter a prompt or stage an attachment before sending.");
    return;
  }
  if (state.selectedSession?.archived_at) {
    announce("Restore the selected session before sending a prompt.");
    return;
  }

  try {
    state.composing = true;
    renderControls();

    const sessionId = await ensureComposerSessionId();
    if (!sessionId) {
      throw new ApiError("No session is available for this prompt.");
    }

    const mode = normalizeDeliveryMode(ui.composeDeliveryMode.value);
    const activeRun = currentComposerActiveRun();
    if (mode === "run") {
      const run = await apiFetch(`${sessionPath(sessionId)}/runs`, {
        method: "POST",
        json: { content },
      });
      state.liveDraft = null;
      renderTimeline();
      announce(`Run ${run.run_id} submitted.`);
    } else if (activeRun) {
      await submitComposerQueuedMessage(activeRun.run_id, mode, content);
      announce(`${mode === "steer" ? "Steer" : "Follow-up"} queued for ${shortId(activeRun.run_id)}.`);
    } else {
      await enqueueComposerSessionMessage(sessionId, mode, content);
      announce(`${mode === "steer" ? "Steer" : "Follow-up"} queued for ${sessionLabel(state.selectedSession ?? { session_id: sessionId })}.`);
    }

    ui.composeInput.value = "";
    clearComposerAttachments();
    closeComposerCompletion();
    renderControls();
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
  if (frame.event === "tau.meters.updated") {
    applyMetersSnapshot(frame.data?.payload);
    return;
  }
  if (frame.event === "tau.dashboard.updated") {
    scheduleDashboardInvalidation();
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
    case "tau.plan.updated": {
      await loadPlan({ force: false });
      break;
    }
    case "tau.approval.requested":
    case "tau.approval.resolved": {
      await loadApprovals();
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
  const previousSessionId = state.selectedSessionId;
  const visible = visibleSessions();
  const preferred = typeof preferredSessionId === "string" ? preferredSessionId : null;
  const selected =
    visible.find((session) => session.session_id === preferred) ??
    visible[0] ??
    null;

  state.selectedSession = selected;
  state.selectedSessionId = selected?.session_id ?? null;
  persistStorage(STORAGE_KEYS.selectedSessionId, state.selectedSessionId);
  replaceSessionLocation(state.selectedSessionId);
  if (previousSessionId !== state.selectedSessionId) {
    handleComposerSessionChange(previousSessionId, state.selectedSessionId);
    notifySelectedSessionChanged();
  }
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
  window.dispatchEvent(new CustomEvent("tau:switch-tab", { detail: { tab: name } }));
}

function closeDrawers() {
  window.dispatchEvent(new CustomEvent("tau:close-drawers"));
}

function renderShell() {
  renderMeters();
  renderDashboard();
  renderSessions();
  renderSessionDetails();
  renderBranches();
  renderTimeline();
  renderWorkspace();
  renderSearchResults();
  renderPlan();
  renderSettings();
  renderControls();
}

function toggleDashboard() {
  setDashboardOpen(!state.dashboard.open);
}

function setDashboardOpen(open) {
  const nextOpen = Boolean(open);
  applyDashboardOpen(nextOpen);
  window.dispatchEvent(new CustomEvent("tau:set-dashboard", { detail: { open: nextOpen } }));
}

function applyDashboardOpen(nextOpen) {
  state.dashboard.open = nextOpen;
  state.dashboard.pageSize = dashboardCapacity();
  renderDashboard();
  if (!nextOpen || document.hidden) {
    stopDashboardTimers();
    return;
  }
  void refreshDashboard({ announceError: true });
  startDashboardTimers();
}

function renderDashboard() {
  const dashboard = state.dashboard;
  const hasSnapshot = dashboard.generatedAt !== null || dashboard.sessions.length > 0 || dashboard.loading;
  const activeSessionCount = currentActiveSessions().length;
  const total = hasSnapshot ? dashboard.total : activeSessionCount;

  ui.dashboardCount.textContent = String(total);
  ui.dashboardGrid.setAttribute("aria-busy", String(dashboard.loading));
  ui.dashboardPage.textContent = `Page ${dashboard.page} of ${dashboard.totalPages}`;
  ui.dashboardPrevious.disabled = dashboard.loading || dashboard.page <= 1;
  ui.dashboardNext.disabled = dashboard.loading || dashboard.page >= dashboard.totalPages;

  if (!dashboard.open) {
    return;
  }

  const tiles = [];
  if (!dashboard.sessions.length) {
    const empty = document.createElement("p");
    empty.className = "dashboard-empty";
    empty.textContent = dashboard.loading ? "Loading dashboard sessions…" : "No active sessions.";
    tiles.push(empty);
  } else {
    for (const session of dashboard.sessions) {
      tiles.push(renderDashboardTile(session));
    }
  }

  ui.dashboardGrid.replaceChildren(...tiles);
  updateDashboardAgeLabels();
}

function renderDashboardTile(session) {
  const selected = session?.session_id === state.selectedSessionId;
  const tile = document.createElement("article");
  tile.className = "dashboard-tile";
  tile.dataset.selected = String(selected);
  tile.setAttribute("role", "listitem");

  const button = document.createElement("button");
  button.type = "button";
  button.className = "dashboard-tile-button";
  button.setAttribute("aria-current", selected ? "page" : "false");
  button.title = "Open this session. Ctrl-click or Cmd-click opens it in a new tab.";
  button.addEventListener("click", (event) => {
    if (event.metaKey || event.ctrlKey) {
      window.open(buildSessionUrl(session.session_id), "_blank", "noopener");
      return;
    }
    void selectSession(session.session_id, { reconnect: true, focusTimeline: true });
  });

  const header = document.createElement("div");
  header.className = "dashboard-tile-header";

  const agent = document.createElement("p");
  agent.className = "dashboard-agent";
  agent.textContent = sessionLabel(session);

  const status = document.createElement("span");
  status.className = "dashboard-state";
  status.dataset.state = stringOrEmpty(session?.activity_state) || "idle";
  status.dataset.error = String(Boolean(session?.has_error));
  status.textContent = dashboardActivityLabel(session);

  header.append(agent, status);

  const identity = document.createElement("p");
  identity.className = "dashboard-identity";
  const agentName = stringOrEmpty(session?.agent_name);
  identity.textContent = [
    agentName ? `@${agentName}` : null,
    shortId(session?.session_id),
  ]
    .filter(Boolean)
    .join(" · ");

  const workspace = document.createElement("p");
  workspace.className = "dashboard-workspace";
  workspace.textContent = stringOrEmpty(session?.workspace) || "Workspace unavailable";

  const model = document.createElement("p");
  model.className = "dashboard-model";
  model.textContent = stringOrEmpty(session?.model) || "Model unavailable";

  const previewKind = document.createElement("p");
  previewKind.className = "dashboard-preview-kind";
  previewKind.textContent = dashboardPreviewKindLabel(session?.preview_kind);

  const preview = document.createElement("p");
  preview.className = "dashboard-preview";
  preview.textContent = stringOrEmpty(session?.preview) || "No assistant summary yet.";

  const indicators = document.createElement("div");
  indicators.className = "dashboard-indicators";

  const queue = document.createElement("span");
  queue.textContent = `Queue ${numberOrZero(session?.queue_count)}`;

  const context = document.createElement("div");
  context.className = "dashboard-context";

  const contextLabel = document.createElement("span");
  contextLabel.textContent = `Context ${formatDashboardContext(session)}`;

  const contextTrack = document.createElement("span");
  contextTrack.className = "dashboard-context-track";

  const contextFill = document.createElement("span");
  contextFill.className = "dashboard-context-fill";
  contextFill.style.width = `${formatDashboardContextPercent(session)}%`;
  contextTrack.append(contextFill);
  context.append(contextLabel, contextTrack);

  indicators.append(queue, context);

  if (session?.has_error) {
    const error = document.createElement("span");
    error.className = "dashboard-error";
    error.textContent = "Error";
    indicators.append(error);
  }

  const age = document.createElement("p");
  age.className = "dashboard-tile-age";
  age.dataset.dashboardAgeSource = stringOrEmpty(session?.last_activity);
  age.textContent = "Activity unknown";
  indicators.append(age);

  button.append(header, identity, workspace, model, previewKind, preview, indicators);
  tile.append(button);
  return tile;
}

async function refreshDashboard({ announceError = false } = {}) {
  if (!state.dashboard.open) {
    return;
  }
  if (state.dashboard.loading) {
    state.dashboard.needsRefresh = true;
    return;
  }

  state.dashboard.loading = true;
  state.dashboard.needsRefresh = false;
  renderDashboard();

  const requestedPage = state.dashboard.page;
  const requestedPageSize = state.dashboard.pageSize;
  const params = new URLSearchParams({
    page: String(requestedPage),
    page_size: String(requestedPageSize),
  });

  try {
    const payload = await apiFetch(`${API_PATHS.dashboard}?${params.toString()}`);
    if (state.dashboard.page !== requestedPage || state.dashboard.pageSize !== requestedPageSize) {
      state.dashboard.needsRefresh = true;
      return;
    }

    state.dashboard.sessions = Array.isArray(payload?.sessions) ? payload.sessions : [];
    state.dashboard.page = Math.max(1, numberOrZero(payload?.page) || requestedPage);
    state.dashboard.pageSize = Math.max(1, numberOrZero(payload?.page_size) || requestedPageSize);
    state.dashboard.total = Math.max(0, numberOrZero(payload?.total));
    state.dashboard.totalPages = Math.max(1, numberOrZero(payload?.total_pages) || 1);
    state.dashboard.generatedAt = stringOrEmpty(payload?.generated_at) || new Date().toISOString();
  } catch (error) {
    if (announceError) {
      handleError(error, "Unable to load the session dashboard.");
    }
  } finally {
    state.dashboard.loading = false;
    renderDashboard();
    if (state.dashboard.needsRefresh && state.dashboard.open && !document.hidden) {
      state.dashboard.needsRefresh = false;
      void refreshDashboard({ announceError: false });
    }
  }
}

function startDashboardTimers() {
  stopDashboardTimers();
  if (!state.dashboard.open || document.hidden) {
    return;
  }
  state.dashboard.fullRefreshTimer = window.setInterval(() => {
    void refreshDashboard({ announceError: false });
  }, 15000);
  state.dashboard.previewRefreshTimer = window.setInterval(() => {
    void refreshDashboard({ announceError: false });
  }, 3000);
  updateDashboardAgeLabels();
  state.dashboard.ageTimer = window.setInterval(updateDashboardAgeLabels, 1000);
}

function stopDashboardTimers() {
  if (state.dashboard.fullRefreshTimer !== null) {
    window.clearInterval(state.dashboard.fullRefreshTimer);
    state.dashboard.fullRefreshTimer = null;
  }
  if (state.dashboard.previewRefreshTimer !== null) {
    window.clearInterval(state.dashboard.previewRefreshTimer);
    state.dashboard.previewRefreshTimer = null;
  }
  if (state.dashboard.ageTimer !== null) {
    window.clearInterval(state.dashboard.ageTimer);
    state.dashboard.ageTimer = null;
  }
  if (state.dashboard.invalidationTimer !== null) {
    window.clearTimeout(state.dashboard.invalidationTimer);
    state.dashboard.invalidationTimer = null;
  }
}

function scheduleDashboardInvalidation() {
  if (!state.dashboard.open || document.hidden) {
    return;
  }
  if (state.dashboard.invalidationTimer !== null) {
    window.clearTimeout(state.dashboard.invalidationTimer);
  }
  state.dashboard.invalidationTimer = window.setTimeout(() => {
    state.dashboard.invalidationTimer = null;
    void refreshDashboard({ announceError: false });
  }, 400);
}

function updateDashboardAgeLabels() {
  if (!state.dashboard.open) {
    return;
  }

  if (!state.dashboard.generatedAt) {
    ui.dashboardAge.textContent = state.dashboard.loading ? "Refreshing dashboard…" : "Not refreshed yet.";
  } else if (state.dashboard.loading) {
    ui.dashboardAge.textContent = `Refreshing… last updated ${relativeTimeText(state.dashboard.generatedAt)}.`;
  } else {
    ui.dashboardAge.textContent = `Updated ${relativeTimeText(state.dashboard.generatedAt)}.`;
  }

  for (const element of ui.dashboardGrid.querySelectorAll(".dashboard-tile-age")) {
    const timestamp = stringOrEmpty(element.dataset.dashboardAgeSource);
    element.textContent = timestamp ? `Activity ${relativeTimeText(timestamp)}` : "Activity unknown";
  }
}

function changeDashboardPage(delta) {
  const nextPage = Math.max(1, Math.min(state.dashboard.totalPages, state.dashboard.page + delta));
  if (nextPage === state.dashboard.page) {
    return;
  }
  state.dashboard.page = nextPage;
  renderDashboard();
  if (state.dashboard.open && !document.hidden) {
    void refreshDashboard({ announceError: true });
  }
}

function handleDashboardResize() {
  const nextPageSize = dashboardCapacity();
  if (state.dashboard.pageSize === nextPageSize) {
    return;
  }
  state.dashboard.pageSize = nextPageSize;
  renderDashboard();
  if (state.dashboard.open && !document.hidden) {
    void refreshDashboard({ announceError: false });
  }
}

function openSessionManager() {
  setDashboardOpen(false);
  closeDrawers();
  if (window.innerWidth <= 960) {
    window.dispatchEvent(new CustomEvent("tau:open-drawer", { detail: { drawer: "nav" } }));
  }
  const target = ui.sessionList.querySelector("button") ?? ui.newSessionButton;
  if (target instanceof HTMLElement) {
    target.focus();
  }
}

async function refreshMeters() {
  if (!state.metersEnabled || document.hidden) {
    return;
  }
  try {
    applyMetersSnapshot(await apiFetch(API_PATHS.meters));
  } catch {
    if (!state.meters) {
      renderMeters();
    }
  }
}

function applyMetersSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") {
    return;
  }
  state.meters = snapshot;
  renderMeters();
}

function startMetersPolling() {
  stopMetersPolling();
  if (!state.metersEnabled || document.hidden) {
    return;
  }
  const interval = Number(state.meters?.sample_interval_ms);
  const delay = Number.isFinite(interval) && interval >= 500 ? interval : 2000;
  state.metersTimer = window.setInterval(() => {
    void refreshMeters();
  }, delay);
}

function stopMetersPolling() {
  if (state.metersTimer !== null) {
    window.clearInterval(state.metersTimer);
    state.metersTimer = null;
  }
}

function handleMetersVisibilityChange() {
  if (document.hidden) {
    stopMetersPolling();
    stopDashboardTimers();
    return;
  }
  void refreshMeters();
  startMetersPolling();
  if (state.dashboard.open) {
    void refreshDashboard({ announceError: false });
    startDashboardTimers();
  }
}

function applyMeterControls(enabled, collapsed) {
  const enabledChanged = state.metersEnabled !== enabled;
  state.metersEnabled = enabled;
  state.metersCollapsed = collapsed;
  persistStorage(STORAGE_KEYS.metersEnabled, String(enabled));
  persistStorage(STORAGE_KEYS.metersCollapsed, String(collapsed));
  renderMeters();
  if (!enabledChanged) {
    return;
  }
  if (enabled) {
    void refreshMeters();
    startMetersPolling();
  } else {
    stopMetersPolling();
  }
}

function renderMeters() {
  if (!state.metersEnabled) {
    ui.metersSummary.textContent = "Meters hidden";
    return;
  }

  const meters = state.meters;
  if (!meters) {
    ui.metersSummary.textContent = "Meters unavailable";
    setMeterValues(null, null, null, null);
    drawSparkline(ui.meterCpuSparkline, [], 100);
    drawSparkline(ui.meterRamSparkline, [], 100);
    drawSparkline(ui.meterRssSparkline, [], null);
    drawSparkline(ui.meterSwapSparkline, [], 100);
    return;
  }

  const cpu = finiteNumberOrNull(meters.cpu_percent);
  const ram = finiteNumberOrNull(meters.ram_percent);
  const rss = finiteNumberOrNull(meters.process_rss_bytes);
  const swap = finiteNumberOrNull(meters.swap_percent);
  ui.metersSummary.textContent = [
    `CPU ${formatPercent(cpu)}`,
    `RAM ${formatPercent(ram)}`,
    `RSS ${formatBytes(rss)}`,
    `Swap ${formatPercent(swap)}`,
  ].join(" · ");
  setMeterValues(cpu, ram, rss, swap);
  drawSparkline(ui.meterCpuSparkline, meters.cpu_series, 100);
  drawSparkline(ui.meterRamSparkline, meters.ram_series, 100);
  drawSparkline(ui.meterRssSparkline, meters.process_rss_series_bytes, null);
  drawSparkline(ui.meterSwapSparkline, meters.swap_series, 100);
}

function setMeterValues(cpu, ram, rss, swap) {
  ui.meterCpuValue.textContent = formatPercent(cpu);
  ui.meterRamValue.textContent = formatPercent(ram);
  ui.meterRssValue.textContent = formatBytes(rss);
  ui.meterSwapValue.textContent = formatPercent(swap);
}

function drawSparkline(svg, rawSeries, fixedMaximum) {
  svg.replaceChildren();
  svg.setAttribute("viewBox", "0 0 100 28");
  const series = Array.isArray(rawSeries) ? rawSeries.map(finiteNumberOrNull) : [];
  const values = series.filter((value) => value !== null);
  if (values.length < 2) {
    return;
  }
  const maximum = fixedMaximum ?? Math.max(...values, 1);
  const divisor = Math.max(series.length - 1, 1);
  const points = series
    .map((value, index) => {
      if (value === null) {
        return null;
      }
      const x = (index / divisor) * 100;
      const y = 27 - Math.min(Math.max(value / maximum, 0), 1) * 26;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .filter((point) => point !== null);
  if (points.length < 2) {
    return;
  }
  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("class", "meter-sparkline");
  line.setAttribute("points", points.join(" "));
  svg.append(line);
}

function finiteNumberOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
}

function formatPercent(value) {
  return value === null ? "--" : `${Math.round(value)}%`;
}

function formatBytes(value) {
  if (value === null) {
    return "--";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let amount = value;
  let unitIndex = 0;
  while (amount >= 1024 && unitIndex < units.length - 1) {
    amount /= 1024;
    unitIndex += 1;
  }
  const precision = unitIndex > 1 && amount < 10 ? 1 : 0;
  return `${amount.toFixed(precision)} ${units[unitIndex]}`;
}

function renderPlan() {
  const session = state.selectedSession;
  const disabled = !session || Boolean(session.archived_at);
  if (ui.planEditor.value !== state.planDraft) {
    ui.planEditor.value = state.planDraft;
  }
  ui.planEditor.disabled = disabled;
  ui.planSaveButton.disabled = disabled || !state.planDirty;
  ui.planReloadButton.disabled = !session;
  ui.planRevision.textContent = `Revision ${state.plan?.revision ?? 0}`;
  ui.planConflict.hidden = !state.planConflict;
  if (!session) {
    ui.planStatus.textContent = "Select a session to edit its shared plan.";
  } else if (session.archived_at) {
    ui.planStatus.textContent = "Restore this session before editing its plan.";
  } else if (state.planConflict) {
    ui.planStatus.textContent = `Server revision ${state.planConflict.revision} is newer than your draft.`;
  } else if (state.planDirty) {
    ui.planStatus.textContent = "Unsaved local changes.";
  } else {
    ui.planStatus.textContent = "Shared with the agent and refreshed before each new turn.";
  }
}

function renderSessions() {
  const sessions = visibleSessions();
  ui.sessionCount.textContent = `${sessions.length} session${sessions.length === 1 ? "" : "s"}`;
  ui.sessionList.replaceChildren();

  if (!sessions.length) {
    ui.sessionList.append(createPlaceholderItem("No sessions available."));
    return;
  }

  for (const session of sessions) {
    const item = document.createElement("li");
    item.className = "sessions-panel__item";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sessions-panel__session";
    button.dataset.active = String(session.session_id === state.selectedSessionId);
    button.addEventListener("click", () => {
      void selectSession(session.session_id, { reconnect: true });
    });

    const card = document.createElement("div");
    card.className = "sessions-panel__session-body";

    const title = document.createElement("strong");
    title.className = "sessions-panel__session-title";
    title.textContent = sessionLabel(session);
    card.append(title);

    const meta = document.createElement("span");
    meta.className = "sessions-panel__session-meta";
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
    ui.agentStatusText.textContent = "No session selected";
    ui.agentStatusIndicator.hidden = true;
    return;
  }

  const session = state.selectedSession;
  const activeRun = currentComposerActiveRun();
  ui.statusSession.textContent = sessionLabel(session);
  ui.statusModel.textContent = `${session.provider_name}/${state.context?.model ?? session.model}`;
  ui.statusContext.textContent = contextSummaryText();
  ui.timelineMeta.textContent = contextSummaryText(true);
  ui.agentStatusText.textContent = activeRun ? `Running ${shortId(activeRun.run_id)}` : "Ready";
  ui.agentStatusIndicator.hidden = false;
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

function displayMessageContent(message) {
  const content = messageContent(message);
  const marker = "\n\nAttachment references (uploaded separately; not inline media):\n";
  const markerIndex = content.indexOf(marker);
  return markerIndex >= 0 ? content.slice(0, markerIndex) : content;
}

function messageAttachments(message) {
  if (!message || typeof message !== "object") {
    return [];
  }
  if (Array.isArray(message.attachments) && message.attachments.length) {
    return message.attachments
      .filter((attachment) => typeof attachment?.media_id === "string" && attachment.media_id)
      .map((attachment) => ({
        mediaId: attachment.media_id,
        filename: stringOrEmpty(attachment.filename) || "attachment",
        mediaType: stringOrEmpty(attachment.media_type) || "application/octet-stream",
      }));
  }

  const content = messageContent(message);
  const references = [];
  const pattern = /\[media:([A-Za-z0-9._-]+)\]\s+([^\n(]+?)\s*\(([^)\n]+)\)/g;
  for (const match of content.matchAll(pattern)) {
    references.push({
      mediaId: match[1],
      filename: match[2].trim() || "attachment",
      mediaType: match[3].trim() || "application/octet-stream",
    });
  }
  return references;
}

function createTimelineAttachments(attachments) {
  if (!attachments.length) {
    return null;
  }
  const gallery = document.createElement("div");
  gallery.className = "timeline-attachments";
  for (const attachment of attachments) {
    const link = document.createElement("a");
    link.className = "timeline-attachment";
    const contentUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/content`;
    link.href = contentUrl;
    link.target = "_blank";
    link.rel = "noopener";
    link.title = attachment.filename;
    if (state.authToken) {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        void downloadAuthenticatedMedia(contentUrl, attachment.filename);
      });
    }

    if (attachment.mediaType.startsWith("image/")) {
      const image = document.createElement("img");
      image.className = "timeline-attachment-image";
      const thumbnailUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/thumbnail`;
      image.alt = attachment.filename;
      image.loading = "lazy";
      if (state.authToken) {
        void loadAuthenticatedImage(image, thumbnailUrl);
      } else {
        image.src = thumbnailUrl;
      }
      link.append(image);
    }

    const label = document.createElement("span");
    label.className = "timeline-attachment-label";
    label.textContent = attachment.filename;
    link.append(label);
    gallery.append(link);
  }
  return gallery;
}

async function fetchMediaBlob(url) {
  const response = await fetch(url, {
    method: "GET",
    headers: buildHeaders("GET", { Accept: "*/*" }),
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw await apiErrorFromResponse(response);
  }
  return await response.blob();
}

async function loadAuthenticatedImage(image, url) {
  try {
    const blob = await fetchMediaBlob(url);
    const objectUrl = URL.createObjectURL(blob);
    image.addEventListener("load", () => URL.revokeObjectURL(objectUrl), { once: true });
    image.src = objectUrl;
  } catch (error) {
    image.alt = `${image.alt} (preview unavailable)`;
    console.warn("Unable to load attachment preview", error);
  }
}

async function downloadAuthenticatedMedia(url, filename) {
  try {
    const blob = await fetchMediaBlob(url);
    const objectUrl = URL.createObjectURL(blob);
    const download = document.createElement("a");
    download.href = objectUrl;
    download.download = filename;
    document.body.append(download);
    download.click();
    download.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  } catch (error) {
    handleError(error, "Unable to download the attachment.");
  }
}

function renderTimeline() {
  ui.timelineList.replaceChildren();
  const timelineItems = state.messages.map((entry) => ({
    role: entry?.message?.role ?? "assistant",
    content: displayMessageContent(entry?.message),
    attachments: messageAttachments(entry?.message),
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
    const isUser = item.role === "user";
    const listItem = document.createElement("li");
    listItem.className = `message-list__item message-list__item--${isUser ? "user" : "agent"}`;

    const avatar = document.createElement("div");
    avatar.className = `message-list__avatar-circle message-list__avatar-circle--${isUser ? "user" : "agent"}`;
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = isUser ? "Y" : "τ";

    const body = document.createElement("div");
    body.className = item.live ? "message-list__body message-list__body--draft" : "message-list__body";

    const header = document.createElement("div");
    header.className = "message-list__header";
    const name = document.createElement("span");
    name.className = `message-list__name message-list__name--${isUser ? "user" : "agent"}`;
    name.textContent = isUser ? "You" : "Tau";
    const meta = document.createElement("span");
    meta.className = "message-list__time";
    meta.textContent = item.live ? "live" : item.meta;
    header.append(name, meta);

    const content = document.createElement("div");
    content.className = "message-list__content";
    content.textContent = item.content || "(empty)";
    body.append(header, content);

    const attachmentGallery = createTimelineAttachments(item.attachments ?? []);
    if (attachmentGallery) {
      attachmentGallery.classList.add("message-list__attachments");
      body.append(attachmentGallery);
    }
    listItem.append(avatar, body);
    ui.timelineList.append(listItem);
  }
}

function renderWorkspace() {
  ui.workspacePath.textContent = state.workspacePath;
  ui.workspaceEditorPath.textContent = state.workspaceFilePath ?? "No file selected";
  ui.workspaceEditor.value = state.workspaceFileContent;
  renderWorkspaceAnnotations();
  void renderWorkspaceRenderer();
  ui.workspaceList.replaceChildren();

  if (!state.workspaceEntries.length) {
    ui.workspaceList.append(createPlaceholderItem("No workspace entries available."));
    return;
  }

  for (const entry of state.workspaceEntries) {
    const item = document.createElement("div");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "file-tree__item";
    button.setAttribute("role", "treeitem");
    button.disabled = entry.kind !== "directory" && entry.kind !== "file";
    button.addEventListener("click", () => {
      void openWorkspaceEntry(entry);
    });

    const icon = document.createElement("span");
    icon.className = `file-tree__icon codicon codicon-${entry.kind === "directory" ? "folder" : "file"}`;
    icon.setAttribute("aria-hidden", "true");

    const label = document.createElement("span");
    label.className = "file-tree__name";
    label.textContent = entry.name;

    const kind = document.createElement("span");
    kind.className = "file-tree__meta";
    kind.textContent = entry.kind;

    button.append(icon, label, kind);
    item.append(button);
    ui.workspaceList.append(item);
  }
}

function renderWorkspaceAnnotations() {
  ui.workspaceAnnotationList.replaceChildren();
  const annotations = state.workspaceAnnotations.filter(
    (item) => item && typeof item === "object" && Number.isInteger(item.line) && item.line > 0,
  );
  ui.workspaceAnnotations.hidden = annotations.length === 0;
  ui.workspaceEditor.setAttribute(
    "aria-describedby",
    annotations.length ? "workspace-editor-note workspace-annotations" : "workspace-editor-note",
  );
  for (const annotation of annotations) {
    const item = document.createElement("li");
    item.className = "workspace-annotation";
    item.dataset.severity = ["info", "warning", "error"].includes(annotation.severity)
      ? annotation.severity
      : "info";
    const endLine = Number.isInteger(annotation.end_line) && annotation.end_line >= annotation.line
      ? `–${annotation.end_line}`
      : "";
    const source = typeof annotation.source === "string" && annotation.source
      ? ` · ${annotation.source}`
      : "";
    item.textContent = `Line ${annotation.line}${endLine}${source}: ${stringOrEmpty(annotation.message)}`;
    ui.workspaceAnnotationList.append(item);
  }
}

async function renderWorkspaceRenderer() {
  const renderer = state.workspaceFileRenderer;
  const target = ui.workspaceRenderer;
  if (!renderer || typeof renderer !== "object" || !window.tauExtensionUI) {
    const frameId = target.dataset.widgetFrameId;
    if (frameId) window.tauExtensionUI?.removeWidget(frameId);
    target.replaceChildren();
    target.hidden = true;
    delete target.dataset.rendererKey;
    delete target.dataset.widgetFrameId;
    return;
  }

  const rendererKey = JSON.stringify(renderer);
  if (target.dataset.rendererKey === rendererKey && target.childNodes.length) return;
  const previousFrameId = target.dataset.widgetFrameId;
  if (previousFrameId) window.tauExtensionUI.removeWidget(previousFrameId);
  target.replaceChildren();
  target.hidden = false;
  target.dataset.rendererKey = rendererKey;
  delete target.dataset.widgetFrameId;

  if (renderer.type === "view" && renderer.view && typeof renderer.view === "object") {
    window.tauExtensionUI.renderInto(target, renderer.view);
    return;
  }
  if (
    renderer.type !== "widget" ||
    typeof renderer.extension_id !== "string" ||
    !renderer.widget ||
    typeof renderer.widget.id !== "string"
  ) {
    target.hidden = true;
    return;
  }

  const url = `/api/extensions/widgets/${encodeURIComponent(renderer.extension_id)}/${encodeURIComponent(renderer.widget.id)}`;
  try {
    const documentText = await apiFetch(url);
    if (target.dataset.rendererKey !== rendererKey) return;
    const frameId = window.tauExtensionUI.mountWidget(
      target,
      { ...renderer.widget, extension_id: renderer.extension_id, url },
      documentText,
    );
    if (frameId) target.dataset.widgetFrameId = frameId;
  } catch (error) {
    if (target.dataset.rendererKey === rendererKey) {
      target.replaceChildren(createMutedText(messageForError(error, "Unable to load file preview.")));
    }
  }
}

async function handleWidgetAction(event) {
  const detail = event instanceof CustomEvent ? event.detail : null;
  if (!detail || typeof detail !== "object") return;
  const { frame_id: frameId, extension_id: extensionId, widget_id: widgetId, request_id: requestId } = detail;
  if (![frameId, extensionId, widgetId, requestId, detail.name].every((value) => typeof value === "string" && value)) return;
  const path = `/api/extensions/widgets/${encodeURIComponent(extensionId)}/${encodeURIComponent(widgetId)}/actions/${encodeURIComponent(detail.name)}`;
  try {
    const result = await apiFetch(path, { method: "POST", json: { payload: detail.payload } });
    window.tauExtensionUI?.respondWidget(frameId, requestId, { result });
  } catch (error) {
    window.tauExtensionUI?.respondWidget(frameId, requestId, {
      error: messageForError(error, "Widget action failed."),
    });
  }
}

async function handleWidgetSubmit(event) {
  const detail = event instanceof CustomEvent ? event.detail : null;
  if (!detail || typeof detail.text !== "string") return;
  ui.composeInput.value = detail.text;
  handleComposeInputChange();
  ui.composeInput.focus();
  if (detail.mode === "submit") await submitPrompt();
}

async function handleWidgetRefresh(event) {
  const detail = event instanceof CustomEvent ? event.detail : null;
  const renderer = state.workspaceFileRenderer;
  if (
    !detail ||
    renderer?.type !== "widget" ||
    detail.extension_id !== renderer.extension_id ||
    detail.widget_id !== renderer.widget?.id
  ) return;
  const url = `/api/extensions/widgets/${encodeURIComponent(detail.extension_id)}/${encodeURIComponent(detail.widget_id)}`;
  try {
    const documentText = await apiFetch(url);
    window.tauExtensionUI?.refreshWidget(detail.frame_id, documentText);
  } catch (error) {
    handleError(error, "Unable to refresh widget.");
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
    item.className = "search-panel__item";
    const card = document.createElement("article");

    const header = document.createElement("div");
    header.className = "search-panel__item-header";
    const title = document.createElement("strong");
    title.className = "search-panel__item-type";
    title.textContent = `${result.entity_type} · ${result.entity_id}`;

    const meta = document.createElement("span");
    meta.className = "search-panel__item-time";
    meta.textContent = [
      result.session_id ? `Session ${shortId(result.session_id)}` : "Global",
      typeof result.rank === "number" ? `Rank ${result.rank.toFixed(2)}` : null,
    ]
      .filter(Boolean)
      .join(" · ");

    const text = document.createElement("span");
    text.className = "search-panel__item-text";
    text.textContent = stringOrEmpty(result.text) || "(empty)";

    header.append(title, meta);
    card.append(header, text);

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

  const providerItems = Array.from(providerValues).sort().map((value) => ({ value, label: value }));
  const modelItems = Array.from(modelValues).sort().map((value) => ({ value, label: value }));
  replaceOptions(ui.providerOptions, providerItems.map((item) => item.value));
  replaceOptions(ui.modelOptions, modelItems.map((item) => item.value));
  replaceSelectOptions(ui.composeProviderSelect, providerItems);
  replaceSelectOptions(ui.composeModelSelect, modelItems);
}

function renderControls() {
  const session = state.selectedSession;
  const archived = Boolean(session?.archived_at);
  const selectedModel = currentProviderModelSelection();
  const selectedThinkingLevel = session?.thinking_level ?? "";

  renderThinkingOptions();
  syncSelectValue(ui.composeProviderSelect, selectedModel.provider_name);
  syncSelectValue(ui.composeModelSelect, selectedModel.model);
  syncSelectValue(ui.composeThinkingSelect, selectedThinkingLevel, selectedThinkingLevel || "Default");

  state.composer.deliveryMode = normalizeDeliveryMode(ui.composeDeliveryMode.value || state.composer.deliveryMode);
  ui.composeDeliveryMode.value = state.composer.deliveryMode;
  ui.composeContextReadout.textContent = composeContextReadoutText();
  const attachmentLabel = state.uploadingAttachments ? "Uploading…" : "Attach file";
  ui.composeAttachmentButton.setAttribute("aria-label", attachmentLabel);
  ui.composeAttachmentButton.setAttribute("title", attachmentLabel);
  const attachmentButtonText = ui.composeAttachmentButton.querySelector(".sr-only");
  if (attachmentButtonText) attachmentButtonText.textContent = attachmentLabel;
  ui.archiveSessionButton.disabled = !session || archived;
  ui.restoreSessionButton.disabled = !session || !archived;
  ui.applyModelButton.disabled = !session || archived;
  ui.composeProviderSelect.disabled = state.composing || state.uploadingAttachments;
  ui.composeModelSelect.disabled = state.composing || state.uploadingAttachments;
  ui.composeThinkingSelect.disabled = !session || archived || state.composing || state.uploadingAttachments;
  ui.composeDeliveryMode.disabled = state.composing || state.uploadingAttachments;
  ui.composeAttachmentButton.disabled = archived || state.composing || state.uploadingAttachments;
  ui.composeFileInput.disabled = archived || state.composing || state.uploadingAttachments;
  ui.composeClearAttachments.hidden = !state.composer.attachments.length;
  ui.composeClearAttachments.disabled = !state.composer.attachments.length || state.composing || state.uploadingAttachments;
  ui.composeSubmit.disabled = archived || state.composing || state.uploadingAttachments;
  const submitLabel = state.composer.deliveryMode === "run" ? "Run" : "Send";
  ui.composeSubmit.setAttribute("aria-label", submitLabel);
  const submitButtonText = ui.composeSubmit.querySelector(".sr-only");
  if (submitButtonText) submitButtonText.textContent = submitLabel;
  renderComposerAttachments();
  renderComposerCompletion();
}

function applyWorkspaceResponse(response, { preserveFile = false } = {}) {
  if (response?.kind === "directory") {
    state.workspacePath = response.path || ".";
    state.workspaceEntries = Array.isArray(response.entries) ? response.entries : [];
    if (!preserveFile) {
      clearWorkspaceFile();
    }
    return;
  }
  if (response?.kind === "file") {
    applyWorkspaceFileResponse(response);
  }
}

function applyWorkspaceFileResponse(response) {
  state.workspaceFilePath = response.path;
  state.workspaceFileContent = stringOrEmpty(response.content);
  state.workspaceFileRenderer = response.renderer && typeof response.renderer === "object"
    ? response.renderer
    : null;
  state.workspaceAnnotations = Array.isArray(response.annotations) ? response.annotations : [];
}

function clearWorkspaceFile() {
  state.workspaceFilePath = null;
  state.workspaceFileContent = "";
  state.workspaceFileRenderer = null;
  state.workspaceAnnotations = [];
}

function syncProviderInputs(providerName, model) {
  ui.providerInput.value = providerName ?? "";
  ui.modelInput.value = model ?? "";
  syncSelectValue(ui.composeProviderSelect, ui.providerInput.value.trim());
  syncSelectValue(ui.composeModelSelect, ui.modelInput.value.trim());
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

function createComposerState() {
  return {
    deliveryMode: "run",
    attachments: [],
    completion: createComposerCompletionState(),
  };
}

function createComposerCompletionState() {
  return {
    open: false,
    kind: null,
    start: 0,
    end: 0,
    index: 0,
    items: [],
  };
}

function handleProviderModelInputChange() {
  persistStorage(STORAGE_KEYS.provider, ui.providerInput.value.trim() || null);
  persistStorage(STORAGE_KEYS.model, ui.modelInput.value.trim() || null);
  renderModelOptions();
  renderControls();
}

async function handleComposerModelControlChange() {
  syncProviderInputs(ui.composeProviderSelect.value.trim(), ui.composeModelSelect.value.trim());
  renderModelOptions();
  renderControls();
  if (!state.selectedSession || state.selectedSession.archived_at) {
    return;
  }
  if (
    state.selectedSession.provider_name === ui.providerInput.value.trim() &&
    state.selectedSession.model === ui.modelInput.value.trim()
  ) {
    return;
  }
  ui.modelForm.requestSubmit();
}

async function handleComposerThinkingControlChange() {
  const value = ui.composeThinkingSelect.value;
  syncSelectValue(ui.thinkingLevelSelect, value, value || "Default");
  ui.thinkingLevelSelect.value = value;
  if (!state.selectedSession || state.selectedSession.archived_at) {
    return;
  }
  if ((state.selectedSession.thinking_level ?? "") === value) {
    return;
  }
  ui.thinkingForm.requestSubmit();
}

function handleComposeInputChange() {
  renderControls();
  updateComposerCompletion();
}

function handleComposeCursorMove(event) {
  if (["ArrowUp", "ArrowDown", "Enter", "Tab", "Escape"].includes(event.key)) {
    return;
  }
  updateComposerCompletion();
}

function handleComposeInputKeydown(event) {
  if (state.composer.completion.open) {
    const itemCount = state.composer.completion.items.length;
    if (itemCount === 0) {
      closeComposerCompletion();
    } else {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        state.composer.completion.index = (state.composer.completion.index + 1) % itemCount;
        renderComposerCompletion();
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        state.composer.completion.index =
          (state.composer.completion.index + itemCount - 1) % itemCount;
        renderComposerCompletion();
        return;
      }
      if (event.key === "Tab" || event.key === "Enter") {
        event.preventDefault();
        void chooseComposerCompletion(state.composer.completion.index);
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeComposerCompletion();
        return;
      }
    }
  }

  if (
    event.key === "Enter" &&
    !event.shiftKey &&
    !event.altKey &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.isComposing
  ) {
    event.preventDefault();
    ui.composeForm.requestSubmit();
  }
}

function handleComposeInputBlur() {
  window.setTimeout(() => {
    if (document.activeElement !== ui.composeInput) {
      closeComposerCompletion();
    }
  }, 0);
}

function updateComposerCompletion() {
  const token = activeComposerToken();
  if (!token) {
    closeComposerCompletion();
    return;
  }

  const items = token.kind === "command"
    ? collectCommandCompletions(token.query)
    : collectSessionCompletions(token.query);
  if (!items.length) {
    closeComposerCompletion();
    return;
  }

  const nextIndex = Math.min(state.composer.completion.index, items.length - 1);
  state.composer.completion = {
    open: true,
    kind: token.kind,
    start: token.start,
    end: token.end,
    index: nextIndex < 0 ? 0 : nextIndex,
    items,
  };
  renderComposerCompletion();
}

function renderComposerCompletion() {
  const completion = state.composer.completion;
  ui.composeCompletionListbox.replaceChildren();
  ui.composeCompletionPopup.hidden = !completion.open;
  ui.composeInput.setAttribute("aria-expanded", String(completion.open));

  if (!completion.open) {
    ui.composeCompletionStatus.textContent = "";
    ui.composeInput.removeAttribute("aria-activedescendant");
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const [index, item] of completion.items.entries()) {
    const option = document.createElement("li");
    option.id = `compose-completion-option-${index}`;
    option.className = "compose-completion-option";
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", String(index === completion.index));
    option.dataset.active = String(index === completion.index);
    option.addEventListener("mousedown", (event) => {
      event.preventDefault();
    });
    option.addEventListener("click", () => {
      void chooseComposerCompletion(index);
    });

    const title = document.createElement("strong");
    title.className = "compose-completion-title";
    title.textContent = item.label;

    const detail = document.createElement("p");
    detail.className = "compose-completion-detail muted small-text";
    detail.textContent = item.detail;

    option.append(title, detail);
    fragment.append(option);
  }
  ui.composeCompletionListbox.append(fragment);
  ui.composeCompletionStatus.textContent = `${completion.items.length} completion${completion.items.length === 1 ? "" : "s"} available.`;
  ui.composeInput.setAttribute("aria-activedescendant", `compose-completion-option-${completion.index}`);
}

function renderComposerAttachments() {
  ui.composeAttachmentList.replaceChildren();
  if (!state.composer.attachments.length) return;

  const fragment = document.createDocumentFragment();
  for (const attachment of state.composer.attachments) {
    const item = document.createElement("span");
    item.className = "chat__attachment-pill";

    const label = document.createElement("span");
    label.className = "chat__attachment-name";
    label.textContent = attachmentLabel(attachment);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "chat__attachment-remove";
    button.setAttribute("aria-label", `Remove attachment ${attachment.filename}`);
    button.textContent = "✕";
    button.addEventListener("click", () => {
      removeComposerAttachment(attachment.media_id);
    });

    item.append(label, button);
    fragment.append(item);
  }
  ui.composeAttachmentList.append(fragment);
}

async function chooseComposerCompletion(index) {
  const completion = state.composer.completion;
  const item = completion.items[index];
  if (!completion.open || !item) {
    closeComposerCompletion();
    return;
  }
  if (item.kind === "command") {
    applyComposerCommandCompletion(item);
    return;
  }
  await applyComposerSessionCompletion(item);
}

function applyComposerCommandCompletion(item) {
  replaceComposerToken(`/${item.name} `);
  closeComposerCompletion();
  updateComposerCompletion();
}

async function applyComposerSessionCompletion(item) {
  removeComposerToken();
  closeComposerCompletion();
  if (state.sessionFilter !== "active") {
    state.sessionFilter = "active";
    persistStorage(STORAGE_KEYS.sessionFilter, state.sessionFilter);
  }
  await selectSession(item.session_id, { reconnect: true, focusTimeline: false });
  ui.composeInput.focus();
}

function handleComposerSessionChange(previousSessionId, nextSessionId) {
  const attachmentSessionId = state.composer.attachments[0]?.session_id ?? previousSessionId;
  if (state.composer.attachments.length && attachmentSessionId && attachmentSessionId !== nextSessionId) {
    clearComposerAttachments({ announceMessage: "Cleared staged attachments after switching sessions." });
  }
  closeComposerCompletion();
}

function currentActiveSessions() {
  return state.sessions.filter((session) => !session?.archived_at);
}

function collectCommandCompletions(query) {
  const normalizedQuery = query.toLowerCase();
  return state.commands
    .filter((command) => {
      const haystack = [command?.name, command?.usage, command?.description]
        .map((value) => stringOrEmpty(value).toLowerCase())
        .join(" ");
      return !normalizedQuery || haystack.includes(normalizedQuery);
    })
    .map((command) => ({
      kind: "command",
      name: stringOrEmpty(command.name),
      label: `/${stringOrEmpty(command.name)}`,
      detail: stringOrEmpty(command.description) || stringOrEmpty(command.usage) || "Slash command",
    }));
}

function collectSessionCompletions(query) {
  const normalizedQuery = query.toLowerCase();
  return currentActiveSessions()
    .filter((session) => {
      const haystack = [session?.agent_name, session?.title, session?.session_id]
        .map((value) => stringOrEmpty(value).toLowerCase())
        .join(" ");
      return !normalizedQuery || haystack.includes(normalizedQuery);
    })
    .map((session) => ({
      kind: "session",
      session_id: session.session_id,
      label: `@${stringOrEmpty(session.agent_name) || shortId(session.session_id)}`,
      detail: `${sessionLabel(session)} · ${session.provider_name}/${session.model}`,
    }));
}

function activeComposerToken() {
  if (ui.composeInput.selectionStart !== ui.composeInput.selectionEnd) {
    return null;
  }
  const text = ui.composeInput.value;
  const caret = ui.composeInput.selectionStart ?? text.length;
  let start = caret;
  while (start > 0 && !/\s/.test(text[start - 1])) {
    start -= 1;
  }
  let end = caret;
  while (end < text.length && !/\s/.test(text[end])) {
    end += 1;
  }
  if (start === end) {
    return null;
  }
  const prefix = text[start];
  if (prefix !== "/" && prefix !== "@") {
    return null;
  }
  const query = text.slice(start + 1, caret);
  return {
    kind: prefix === "/" ? "command" : "session",
    start,
    end,
    query,
  };
}

function replaceComposerToken(replacement) {
  const { start, end } = state.composer.completion;
  const before = ui.composeInput.value.slice(0, start);
  const after = ui.composeInput.value.slice(end).replace(/^\s+/, " ");
  const nextValue = `${before}${replacement}${after}`;
  ui.composeInput.value = nextValue;
  restoreComposerCaret(before.length + replacement.length);
}

function removeComposerToken() {
  const { start, end } = state.composer.completion;
  const before = ui.composeInput.value.slice(0, start);
  let after = ui.composeInput.value.slice(end);
  if (!before) {
    after = after.replace(/^[ \t]+/, "");
  } else if (/\s$/.test(before)) {
    after = after.replace(/^[ \t]+/, "");
  }
  ui.composeInput.value = `${before}${after}`;
  restoreComposerCaret(before.length);
}

function restoreComposerCaret(position) {
  ui.composeInput.focus();
  ui.composeInput.setSelectionRange(position, position);
}

function closeComposerCompletion() {
  state.composer.completion = createComposerCompletionState();
  renderComposerCompletion();
}

function clearComposerAttachments({ announceMessage = null } = {}) {
  state.composer.attachments = [];
  ui.composeFileInput.value = "";
  renderControls();
  if (announceMessage) {
    announce(announceMessage);
  }
}

function removeComposerAttachment(mediaId) {
  state.composer.attachments = state.composer.attachments.filter((attachment) => attachment.media_id !== mediaId);
  renderControls();
}

async function handleComposerFileSelection() {
  const selectedFiles = Array.from(ui.composeFileInput.files ?? []);
  ui.composeFileInput.value = "";
  if (!selectedFiles.length) {
    return;
  }
  if (state.selectedSession?.archived_at) {
    announce("Restore the selected session before attaching files.");
    return;
  }

  const remainingSlots = MAX_COMPOSER_ATTACHMENTS - state.composer.attachments.length;
  if (remainingSlots <= 0) {
    announce(`You can stage up to ${MAX_COMPOSER_ATTACHMENTS} attachments.`);
    return;
  }

  const files = selectedFiles.slice(0, remainingSlots);
  const ignoredCount = selectedFiles.length - files.length;

  try {
    state.uploadingAttachments = true;
    renderControls();
    const sessionId = await ensureComposerSessionId();
    if (!sessionId) {
      throw new ApiError("No session is available for attachments.");
    }
    for (const file of files) {
      const uploaded = await uploadComposerAttachment(file, sessionId);
      const mediaId = stringOrEmpty(uploaded?.media_id);
      if (!mediaId) {
        throw new ApiError("Uploaded attachment response did not include a media id.");
      }
      state.composer.attachments.push({
        media_id: mediaId,
        session_id: stringOrEmpty(uploaded?.session_id) || sessionId,
        filename: stringOrEmpty(uploaded?.filename) || file.name || `media-${state.composer.attachments.length + 1}`,
        media_type: stringOrEmpty(uploaded?.media_type) || file.type || "application/octet-stream",
      });
    }
    if (ignoredCount > 0) {
      announce(`Staged ${files.length} attachment${files.length === 1 ? "" : "s"}. Ignored ${ignoredCount} over the limit.`);
    } else {
      announce(`Staged ${files.length} attachment${files.length === 1 ? "" : "s"}.`);
    }
  } catch (error) {
    handleError(error, "Unable to upload attachments.");
  } finally {
    state.uploadingAttachments = false;
    renderControls();
  }
}

async function ensureComposerSessionId() {
  if (!state.selectedSessionId) {
    await createSession({ focusComposer: false });
  }
  return state.selectedSessionId;
}

async function uploadComposerAttachment(file, sessionId) {
  const formData = new FormData();
  const uploadFile = file.type ? file : new File([file], file.name || "attachment", { type: "application/octet-stream" });
  formData.append("file", uploadFile, uploadFile.name);
  formData.append("session_id", sessionId);
  return apiFetch(API_PATHS.media, {
    method: "POST",
    body: formData,
  });
}

function buildSubmittedPromptContent(prompt) {
  const attachmentBlock = buildAttachmentReferenceBlock();
  const content = [prompt, attachmentBlock].filter(Boolean).join("\n\n").trim();
  return content;
}

function buildAttachmentReferenceBlock() {
  if (!state.composer.attachments.length) {
    return "";
  }
  const visible = state.composer.attachments.slice(0, MAX_ATTACHMENT_REFERENCE_ITEMS);
  const lines = visible.map((attachment) => {
    const filename = truncateText(stringOrEmpty(attachment.filename) || "attachment", 48);
    const mediaType = stringOrEmpty(attachment.media_type) || "application/octet-stream";
    const mediaId = stringOrEmpty(attachment.media_id);
    return mediaId
      ? `- [media:${mediaId}] ${filename} (${mediaType})`
      : `- ${filename} (${mediaType})`;
  });
  if (state.composer.attachments.length > visible.length) {
    const remaining = state.composer.attachments.length - visible.length;
    lines.push(`- ${remaining} more uploaded item${remaining === 1 ? "" : "s"} available in session media.`);
  }
  return `Attachment references (uploaded separately; not inline media):\n${lines.join("\n")}`;
}

function currentComposerActiveRun() {
  const liveUi = window.tauLiveUI;
  if (!liveUi || typeof liveUi.getActiveRun !== "function") {
    return null;
  }
  const run = liveUi.getActiveRun();
  return run && typeof run.run_id === "string" ? run : null;
}

async function submitComposerQueuedMessage(runId, kind, content) {
  const liveUi = window.tauLiveUI;
  if (liveUi && typeof liveUi.submitComposerMessage === "function") {
    await liveUi.submitComposerMessage({ runId, kind, content });
    return;
  }
  await apiFetch(`/api/runs/${encodeURIComponent(runId)}/messages`, {
    method: "POST",
    json: { content, kind },
  });
}

async function enqueueComposerSessionMessage(sessionId, kind, content) {
  await apiFetch(`${sessionPath(sessionId)}/queue`, {
    method: "POST",
    json: { content, kind },
  });
}

function renderThinkingOptions() {
  const configuredOptions = Array.from(ui.thinkingLevelSelect.options).map((option) => ({
    value: option.value,
    label: option.textContent || option.value || "Default",
  }));
  const sourceOptions = configuredOptions.length ? configuredOptions : DEFAULT_THINKING_LEVELS.map(([value, label]) => ({ value, label }));
  replaceSelectOptions(ui.composeThinkingSelect, sourceOptions);
}

function currentProviderModelSelection() {
  return {
    provider_name:
      ui.providerInput.value.trim() ||
      state.selectedSession?.provider_name ||
      loadStorage(STORAGE_KEYS.provider) ||
      state.models[0]?.provider_name ||
      "",
    model:
      ui.modelInput.value.trim() ||
      state.selectedSession?.model ||
      loadStorage(STORAGE_KEYS.model) ||
      state.models[0]?.model ||
      "",
  };
}

function composeContextReadoutText() {
  if (!state.selectedSession) {
    return state.composer.attachments.length
      ? `${state.composer.attachments.length} attachment${state.composer.attachments.length === 1 ? "" : "s"} staged for the next session.`
      : "No session selected. Sending will create one.";
  }
  const parts = [`@${state.selectedSession.agent_name}`, contextSummaryText()];
  parts.push(`thinking ${state.selectedSession.thinking_level || "default"}`);
  if (state.composer.attachments.length) {
    parts.push(`${state.composer.attachments.length} attachment${state.composer.attachments.length === 1 ? "" : "s"} staged`);
  }
  return parts.join(" · ");
}

function notifySelectedSessionChanged() {
  window.dispatchEvent(new CustomEvent("tau:session-selected", {
    detail: { sessionId: state.selectedSessionId },
  }));
}

function handleKeyboardShortcuts(event) {
  const isModifier = event.metaKey || event.ctrlKey;
  if (isModifier && event.key.toLowerCase() === "k") {
    event.preventDefault();
    switchTab("search");
    window.dispatchEvent(new CustomEvent("tau:open-drawer", { detail: { drawer: "panel" } }));
    ui.searchInput.focus();
    ui.searchInput.select();
    return;
  }
  if (isModifier && event.key.toLowerCase() === "n") {
    event.preventDefault();
    void createSession({ focusComposer: true });
    return;
  }
  if (!isModifier && !event.altKey && event.code === "Backquote" && !isDashboardShortcutEditableTarget(event.target)) {
    event.preventDefault();
    toggleDashboard();
    return;
  }
  if (event.key === "Escape") {
    if (state.dashboard.open) {
      setDashboardOpen(false);
    }
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

async function authenticatedFetch(path, options = {}) {
  const url = new URL(path, location.origin);
  if (url.origin !== location.origin) {
    throw new Error("Cross-origin requests are not allowed.");
  }

  const inputOptions = options && typeof options === "object" ? options : {};
  const { headers: sourceHeaders = {}, ...requestOptions } = inputOptions;
  const method = stringOrEmpty(requestOptions.method).trim().toUpperCase() || "GET";
  return fetch(url, {
    ...requestOptions,
    method,
    headers: buildHeaders(method, sourceHeaders || {}),
  });
}

async function submitTrustedFrontendMessage(payload) {
  if (
    !payload ||
    typeof payload !== "object" ||
    Array.isArray(payload) ||
    Object.getPrototypeOf(payload) !== Object.prototype
  ) {
    throw new Error("Trusted frontend payload must be a plain object.");
  }

  const keys = Object.keys(payload);
  if (!keys.includes("text") || keys.some((key) => key !== "text" && key !== "mode")) {
    throw new Error("Trusted frontend payload must only include text and mode.");
  }

  const text = stringOrEmpty(payload.text).trim();
  if (text.length < 1 || text.length > 16384) {
    throw new Error("Trusted frontend text must be between 1 and 16384 characters.");
  }

  const rawMode = payload.mode === undefined ? "run" : stringOrEmpty(payload.mode).trim();
  const mode = normalizeDeliveryMode(rawMode);
  if (!DELIVERY_MODES.has(rawMode)) {
    throw new Error("Trusted frontend mode is unsupported.");
  }

  const sessionId = await ensureComposerSessionId();
  if (!sessionId) {
    throw new Error("No session is available for trusted frontend messages.");
  }

  if (mode === "run") {
    await apiFetch(`${sessionPath(sessionId)}/runs`, {
      method: "POST",
      json: { content: text },
    });
  } else {
    const active = currentComposerActiveRun();
    if (active) {
      await submitComposerQueuedMessage(active.run_id, mode, text);
    } else {
      await enqueueComposerSessionMessage(sessionId, mode, text);
    }
  }

  return { accepted: true, mode };
}

async function navigateTrustedFrontend(target) {
  const sessionTarget = typeof target === "string" ? target.trim() : "";
  if (!sessionTarget || sessionTarget.length > 256) {
    throw new Error("Trusted frontend navigation target must be 1 to 256 characters.");
  }

  const session = state.sessions.find((entry) => {
    if (!entry || typeof entry !== "object") {
      return false;
    }
    const candidates = [
      stringOrEmpty(entry.session_id).trim(),
      stringOrEmpty(entry.chat_jid).trim(),
      stringOrEmpty(entry.name).trim(),
      stringOrEmpty(entry.alias).trim(),
    ].filter(Boolean);
    return candidates.includes(sessionTarget);
  });

  const sessionId = stringOrEmpty(session?.session_id).trim();
  if (!sessionId) {
    throw new Error("Unknown trusted frontend navigation target.");
  }

  await selectSession(sessionId, { reconnect: true, focusTimeline: true });
  return { session_id: sessionId };
}

async function initializeTrustedFrontendModules() {
  if (trustedFrontendLoaded) {
    return;
  }
  if (trustedFrontendLoading) {
    await trustedFrontendLoading;
    return;
  }

  const sdk = window.tauFrontendSDK;
  if (!sdk || typeof sdk.configure !== "function" || typeof sdk.loadAll !== "function") {
    return;
  }

  trustedFrontendLoading = (async () => {
    if (!trustedFrontendConfigured) {
      sdk.configure({
        fetchAsset: authenticatedFetch,
        request: apiFetch,
        submit: submitTrustedFrontendMessage,
        navigate: navigateTrustedFrontend,
      });
      trustedFrontendConfigured = true;
    }

    const response = await apiFetch("/api/extensions/frontend-modules");
    if (!response || typeof response !== "object" || Array.isArray(response) || !Array.isArray(response.modules)) {
      throw new Error("Invalid trusted frontend module response.");
    }

    const summary = await sdk.loadAll(response.modules);
    const errors = Array.isArray(summary?.errors) ? summary.errors.slice(0, 16) : [];
    for (const entry of errors) {
      const extensionId = truncateText(stringOrEmpty(entry?.extension_id), 96) || "unknown-extension";
      const moduleId = truncateText(stringOrEmpty(entry?.module_id), 96) || "unknown-module";
      const message = truncateText(stringOrEmpty(entry?.message), 256) || "load failed";
      console.warn(`[trusted-frontend] ${extensionId}/${moduleId}: ${message}`);
    }

    trustedFrontendLoaded = true;
  })().catch((error) => {
    const message = truncateText(
      error instanceof Error && typeof error.message === "string" ? error.message : "initialization failed",
      256,
    ) || "initialization failed";
    console.warn(`[trusted-frontend] initialization failed: ${message}`);
  });

  try {
    await trustedFrontendLoading;
  } finally {
    trustedFrontendLoading = null;
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
  } else if (options.body !== undefined) {
    request.body = options.body;
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

function replaceSelectOptions(select, items) {
  const currentValue = select.value;
  select.replaceChildren();
  for (const item of items) {
    const option = document.createElement("option");
    option.value = stringOrEmpty(item?.value);
    option.textContent = stringOrEmpty(item?.label) || option.value || "Default";
    select.append(option);
  }
  if (currentValue) {
    syncSelectValue(select, currentValue, currentValue);
  }
}

function syncSelectValue(select, value, fallbackLabel = null) {
  const normalized = stringOrEmpty(value);
  if (!normalized) {
    const emptyOption = Array.from(select.options).find((option) => option.value === "");
    select.value = emptyOption ? "" : select.options[0]?.value ?? "";
    return;
  }

  let option = Array.from(select.options).find((entry) => entry.value === normalized);
  if (!option) {
    option = document.createElement("option");
    option.value = normalized;
    option.textContent = fallbackLabel ?? normalized;
    select.append(option);
  }
  select.value = normalized;
}

function normalizeDeliveryMode(value) {
  return DELIVERY_MODES.has(value) ? value : "run";
}

function truncateText(value, maxLength) {
  const text = stringOrEmpty(value);
  if (!text || !Number.isFinite(maxLength) || maxLength < 4 || text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

function announce(message) {
  ui.appStatus.textContent = message;
}

function setStreamStatus(message) {
  ui.statusStream.textContent = message;
  if (/^live$/i.test(message)) {
    ui.statusStream.dataset.state = "live";
  } else if (/^connect/i.test(message)) {
    ui.statusStream.dataset.state = "connecting";
  } else if (/^retry/i.test(message)) {
    ui.statusStream.dataset.state = "retrying";
  } else {
    ui.statusStream.dataset.state = "offline";
  }
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

function dashboardCapacity() {
  if (window.innerWidth < 760) {
    return 4;
  }
  if (window.innerWidth < 1080) {
    return 6;
  }
  return 8;
}

function sessionFromLocation() {
  try {
    const sessionId = new URL(window.location.href).searchParams.get("session_id");
    return sessionId && sessionId.trim() ? sessionId.trim() : null;
  } catch {
    return null;
  }
}

function buildSessionUrl(sessionId) {
  const url = new URL(window.location.href);
  if (sessionId) {
    url.searchParams.set("session_id", sessionId);
  } else {
    url.searchParams.delete("session_id");
  }
  return `${url.pathname}${url.search}${url.hash}`;
}

function replaceSessionLocation(sessionId) {
  const nextUrl = buildSessionUrl(sessionId);
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (nextUrl === currentUrl) {
    return;
  }
  window.history.replaceState(null, "", nextUrl);
}

function dashboardPreviewKindLabel(value) {
  switch (value) {
    case "draft":
      return "Draft";
    case "thinking":
      return "Thinking";
    case "tool":
      return "Tool";
    case "summary":
      return "Summary";
    default:
      return "Preview";
  }
}

function dashboardActivityLabel(session) {
  return sentenceCase(stringOrEmpty(session?.activity_state) || "idle");
}

function formatDashboardContext(session) {
  const used = numberOrZero(session?.context_used_tokens).toLocaleString();
  const windowTokens = numberOrZero(session?.context_window_tokens).toLocaleString();
  return `${used} / ${windowTokens} · ${formatDashboardContextPercent(session)}%`;
}

function formatDashboardContextPercent(session) {
  const value = typeof session?.context_percent === "number" && Number.isFinite(session.context_percent)
    ? session.context_percent
    : 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function relativeTimeText(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return "just now";
  }
  const elapsedSeconds = Math.max(0, Math.round((Date.now() - date.valueOf()) / 1000));
  if (elapsedSeconds < 5) {
    return "just now";
  }
  if (elapsedSeconds < 60) {
    return `${elapsedSeconds}s ago`;
  }
  const elapsedMinutes = Math.round(elapsedSeconds / 60);
  if (elapsedMinutes < 60) {
    return `${elapsedMinutes}m ago`;
  }
  const elapsedHours = Math.round(elapsedMinutes / 60);
  if (elapsedHours < 24) {
    return `${elapsedHours}h ago`;
  }
  const elapsedDays = Math.round(elapsedHours / 24);
  return `${elapsedDays}d ago`;
}

function sentenceCase(value) {
  const text = stringOrEmpty(value).replace(/_/g, " ").trim();
  if (!text) {
    return "Unknown";
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function isDashboardShortcutEditableTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  return target.closest(
    "input, textarea, select, form, [contenteditable=''], [contenteditable='true'], [role='textbox'], .cm-editor, .CodeMirror, .monaco-editor"
  ) !== null;
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

function loadBooleanStorage(key, fallback) {
  const stored = loadStorage(key);
  if (stored === "true") {
    return true;
  }
  if (stored === "false") {
    return false;
  }
  return fallback;
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
