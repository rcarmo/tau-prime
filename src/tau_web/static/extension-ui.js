const LIMITS = Object.freeze({
  viewBytes: 64 * 1024,
  payloadBytes: 8 * 1024,
  depth: 12,
  nodes: 256,
  textBytes: 16 * 1024,
  tableRows: 50,
  tableColumns: 20,
});
const VIEW_KINDS = Object.freeze(["card", "detail", "form"]);
const PLACEMENTS = Object.freeze([
  "compose_above",
  "compose_below",
  "sidebar",
  "timeline_before",
  "timeline_after",
  "dashboard",
]);
const TEXT_STYLES = Object.freeze(["normal", "muted", "code"]);
const BUTTON_VARIANTS = Object.freeze(["default", "primary", "secondary", "danger", "ghost"]);
const FIELD_TYPES = Object.freeze(["text", "textarea", "select"]);
const STACK_DIRECTIONS = Object.freeze(["row", "column"]);
const COMPONENT_KINDS = Object.freeze(["text", "button", "metric", "progress", "field", "table", "stack"]);
const VIEW_KEYS = Object.freeze(["kind", "id", "title", "placement", "components"]);
const COMPONENT_KEYS = Object.freeze({
  text: ["kind", "text", "style", "live"],
  button: ["kind", "label", "action_id", "accessible_label", "payload", "variant", "icon_only"],
  metric: ["kind", "label", "value", "unit"],
  progress: ["kind", "label", "value", "max"],
  field: ["kind", "name", "label", "input_type", "required", "value", "options"],
  table: ["kind", "label", "columns", "rows"],
  stack: ["kind", "direction", "accessible_label", "children"],
});
const SLUG_RE = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
const ENCODER = new TextEncoder();
const statusElement = document.getElementById("app-status");
const renderedViews = new Map();
const handledEvents = new WeakSet();
const slotElements = new Map(
  Array.from(document.querySelectorAll("[data-extension-slot]"), (node) => [
    node.getAttribute("data-extension-slot"),
    node,
  ]),
);
let fieldSerial = 0;

function announce(message) {
  if (statusElement) statusElement.textContent = message;
}

function failureMessage(prefix, error) {
  const detail = error instanceof Error && error.message ? error.message : "Unknown error.";
  return `${prefix}: ${detail}`;
}

function safely(prefix, action) {
  try {
    return action();
  } catch (error) {
    console.warn("tauExtensionUI", error);
    announce(failureMessage(prefix, error));
    return null;
  }
}

function create(tagName, className = "", text = null) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== null) node.textContent = text;
  return node;
}

function bytesForText(value) {
  return ENCODER.encode(value).length;
}

function jsonSize(value) {
  return bytesForText(JSON.stringify(value));
}

function ensureObject(value, path) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value;
  throw new Error(`${path} must be a JSON object`);
}

function ensureArray(value, path) {
  if (Array.isArray(value)) return value;
  throw new Error(`${path} must be a JSON array`);
}

function rejectUnknownKeys(value, path, allowed) {
  const unknown = Object.keys(value)
    .filter((key) => !allowed.includes(key))
    .sort()[0];
  if (unknown) throw new Error(`${path} contains unknown field: ${unknown}`);
}

function ensureOneOf(value, path, allowed) {
  if (typeof value !== "string" || !allowed.includes(value)) {
    throw new Error(`${path} must be one of: ${allowed.join(", ")}`);
  }
  return value;
}

function ensureBoolean(value, path) {
  if (typeof value !== "boolean") throw new Error(`${path} must be a boolean`);
  return value;
}

function ensureString(value, path, { nonBlank = false, maxChars = null, maxBytes = null } = {}) {
  if (typeof value !== "string") throw new Error(`${path} must be a string`);
  if (nonBlank && !value.trim()) throw new Error(`${path} must be non-blank`);
  if (maxChars !== null && value.length > maxChars) {
    throw new Error(`${path} must be at most ${maxChars} characters`);
  }
  if (maxBytes !== null && bytesForText(value) > maxBytes) {
    throw new Error(`${path} exceeds ${maxBytes} bytes`);
  }
  return value;
}

function ensureOptionalString(value, path, options) {
  if (value === undefined || value === null) return null;
  return ensureString(value, path, options);
}

function ensureSlug(value, path) {
  if (typeof value !== "string" || !SLUG_RE.test(value)) {
    throw new Error(`${path} must be a lowercase slug`);
  }
  return value;
}

function ensureNumber(value, path) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`${path} must be a finite number`);
  }
  return value;
}

function ensureMetricValue(value, path) {
  if (typeof value === "string") return ensureString(value, path, { nonBlank: true, maxBytes: LIMITS.textBytes });
  return ensureNumber(value, path);
}

function cloneJson(value, path, stack = []) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") return ensureNumber(value, path);
  if (Array.isArray(value)) {
    if (stack.includes(value)) throw new Error(`${path} must not contain circular data`);
    const nextStack = stack.concat([value]);
    return value.map((item) => cloneJson(item, `${path}[]`, nextStack));
  }
  const objectValue = ensureObject(value, path);
  if (stack.includes(objectValue)) throw new Error(`${path} must not contain circular data`);
  const nextStack = stack.concat([objectValue]);
  const clone = {};
  for (const [key, item] of Object.entries(objectValue)) {
    clone[key] = cloneJson(item, `${path}.${key}`, nextStack);
  }
  return clone;
}

function validateFieldOption(value, path) {
  const option = ensureObject(value, path);
  rejectUnknownKeys(option, path, ["label", "value"]);
  return {
    label: ensureString(option.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
    value: ensureString(option.value, `${path}.value`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
  };
}

function validateTableColumn(value, path) {
  const column = ensureObject(value, path);
  rejectUnknownKeys(column, path, ["label", "key"]);
  return {
    label: ensureString(column.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
    key: ensureSlug(column.key, `${path}.key`),
  };
}

function validateComponent(value, path, depth, state) {
  if (depth > LIMITS.depth) throw new Error(`${path} exceeds maximum depth ${LIMITS.depth}`);
  state.nodes += 1;
  if (state.nodes > LIMITS.nodes) throw new Error(`${path} exceeds maximum node count ${LIMITS.nodes}`);
  const component = ensureObject(value, path);
  const kind = ensureOneOf(component.kind, `${path}.kind`, COMPONENT_KINDS);
  rejectUnknownKeys(component, path, COMPONENT_KEYS[kind]);

  if (kind === "text") {
    return {
      kind,
      text: ensureString(component.text, `${path}.text`, { maxBytes: LIMITS.textBytes }),
      style: ensureOneOf(component.style ?? "normal", `${path}.style`, TEXT_STYLES),
      live: ensureBoolean(component.live ?? false, `${path}.live`),
    };
  }

  if (kind === "button") {
    const payload = cloneJson(ensureObject(component.payload ?? {}, `${path}.payload`), `${path}.payload`);
    if (jsonSize(payload) > LIMITS.payloadBytes) {
      throw new Error(`${path}.payload JSON exceeds ${LIMITS.payloadBytes} bytes`);
    }
    const iconOnly = ensureBoolean(component.icon_only ?? false, `${path}.icon_only`);
    const accessibleLabel = ensureOptionalString(component.accessible_label, `${path}.accessible_label`, {
      nonBlank: true,
      maxChars: 128,
      maxBytes: LIMITS.textBytes,
    });
    if (iconOnly && accessibleLabel === null) {
      throw new Error(`${path}.accessible_label is required when icon_only is true`);
    }
    return {
      kind,
      label: ensureString(component.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
      action_id: ensureSlug(component.action_id, `${path}.action_id`),
      accessible_label: accessibleLabel,
      payload,
      variant: ensureOneOf(component.variant ?? "default", `${path}.variant`, BUTTON_VARIANTS),
      icon_only: iconOnly,
    };
  }

  if (kind === "metric") {
    return {
      kind,
      label: ensureString(component.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
      value: ensureMetricValue(component.value, `${path}.value`),
      unit: ensureOptionalString(component.unit, `${path}.unit`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
    };
  }

  if (kind === "progress") {
    const maxValue = ensureNumber(component.max, `${path}.max`);
    const progressValue = ensureNumber(component.value, `${path}.value`);
    if (maxValue <= 0) throw new Error(`${path}.max must be greater than 0`);
    if (progressValue < 0 || progressValue > maxValue) {
      throw new Error(`${path}.value must be between 0 and max`);
    }
    return {
      kind,
      label: ensureString(component.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
      value: progressValue,
      max: maxValue,
    };
  }

  if (kind === "field") {
    const inputType = ensureOneOf(component.input_type, `${path}.input_type`, FIELD_TYPES);
    const valueText = ensureOptionalString(component.value, `${path}.value`, { maxBytes: LIMITS.textBytes });
    const required = ensureBoolean(component.required ?? false, `${path}.required`);
    const options = component.options === undefined ? null : ensureArray(component.options, `${path}.options`);
    const normalizedOptions = inputType === "select"
      ? (options || []).map((item, index) => validateFieldOption(item, `${path}.options[${index}]`))
      : [];
    if (inputType === "select" && normalizedOptions.length === 0) {
      throw new Error(`${path}.options is required when input_type is select`);
    }
    if (inputType !== "select" && options !== null) {
      throw new Error(`${path}.options is only allowed when input_type is select`);
    }
    if (inputType === "select" && valueText !== null && !normalizedOptions.some((item) => item.value === valueText)) {
      throw new Error(`${path}.value must match a declared option`);
    }
    return {
      kind,
      name: ensureSlug(component.name, `${path}.name`),
      label: ensureString(component.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
      input_type: inputType,
      required,
      value: valueText,
      options: normalizedOptions,
    };
  }

  if (kind === "table") {
    const columns = ensureArray(component.columns, `${path}.columns`).map((item, index) =>
      validateTableColumn(item, `${path}.columns[${index}]`),
    );
    if (columns.length === 0) throw new Error(`${path}.columns must not be empty`);
    if (columns.length > LIMITS.tableColumns) {
      throw new Error(`${path}.columns must contain at most ${LIMITS.tableColumns} items`);
    }
    const columnKeys = new Set();
    const columnLabels = new Set();
    for (const column of columns) {
      if (columnKeys.has(column.key)) throw new Error(`${path}.columns keys must be unique`);
      if (columnLabels.has(column.label)) throw new Error(`${path}.columns labels must be unique`);
      columnKeys.add(column.key);
      columnLabels.add(column.label);
    }
    const rows = ensureArray(component.rows ?? [], `${path}.rows`).map((item, index) => {
      const row = cloneJson(ensureObject(item, `${path}.rows[${index}]`), `${path}.rows[${index}]`);
      for (const key of Object.keys(row)) {
        if (!columnKeys.has(key)) throw new Error(`${path}.rows[${index}].${key} is not a declared column`);
      }
      return row;
    });
    if (rows.length > LIMITS.tableRows) {
      throw new Error(`${path}.rows must contain at most ${LIMITS.tableRows} items`);
    }
    return {
      kind,
      label: ensureString(component.label, `${path}.label`, { nonBlank: true, maxBytes: LIMITS.textBytes }),
      columns,
      rows,
    };
  }

  const children = ensureArray(component.children, `${path}.children`).map((item, index) =>
    validateComponent(item, `${path}.children[${index}]`, depth + 1, state),
  );
  if (children.length === 0) throw new Error(`${path}.children must not be empty`);
  return {
    kind,
    direction: ensureOneOf(component.direction, `${path}.direction`, STACK_DIRECTIONS),
    accessible_label: ensureOptionalString(component.accessible_label, `${path}.accessible_label`, {
      nonBlank: true,
      maxChars: 128,
      maxBytes: LIMITS.textBytes,
    }),
    children,
  };
}

function validateView(value) {
  const view = ensureObject(value, "view");
  rejectUnknownKeys(view, "view", VIEW_KEYS);
  const state = { nodes: 0 };
  const normalized = {
    kind: ensureOneOf(view.kind, "view.kind", VIEW_KINDS),
    id: ensureSlug(view.id, "view.id"),
    title: ensureString(view.title, "view.title", {
      nonBlank: true,
      maxChars: 128,
      maxBytes: LIMITS.textBytes,
    }),
    placement: ensureOneOf(view.placement, "view.placement", PLACEMENTS),
    components: ensureArray(view.components, "view.components").map((item, index) =>
      validateComponent(item, `view.components[${index}]`, 1, state),
    ),
  };
  if (jsonSize(normalized) > LIMITS.viewBytes) {
    throw new Error(`view JSON exceeds ${LIMITS.viewBytes} bytes`);
  }
  return normalized;
}

function resolveSlot(placement) {
  const target = slotElements.get(placement);
  if (target instanceof Element) return target;
  throw new Error(`Missing extension slot: ${placement}`);
}

function resolveTarget(target) {
  if (typeof target === "string") {
    if (PLACEMENTS.includes(target)) return resolveSlot(target);
    const matched = document.querySelector(target);
    if (matched instanceof Element) return matched;
    throw new Error(`Unknown extension target: ${target}`);
  }
  if (target instanceof Element) return target;
  throw new Error("target must be an Element, placement, or selector");
}

function detach(target, node) {
  const nextChildren = Array.from(target.childNodes).filter((child) => child !== node);
  target.replaceChildren(...nextChildren);
}

function collectControls(root) {
  return Array.from(root.querySelectorAll("input, textarea, select")).filter(
    (node) => node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement || node instanceof HTMLSelectElement,
  );
}

function validateControls(root) {
  for (const control of collectControls(root)) {
    if (typeof control.reportValidity === "function" && !control.reportValidity()) return false;
  }
  return true;
}

function collectControlValues(root) {
  const values = {};
  for (const control of collectControls(root)) {
    if (control.name) values[control.name] = control.value;
  }
  return values;
}

function jsonText(value) {
  if (value === undefined) return "";
  if (value === null) return "null";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function metricText(value, unit) {
  const base = typeof value === "string" ? value : String(value);
  return unit ? `${base} ${unit}` : base;
}

function buildText(component) {
  const tagName = component.style === "code" ? "pre" : "p";
  const node = create(tagName, `tau-extension-text tau-extension-text-${component.style}`, component.text);
  if (component.live) {
    node.classList.add("tau-extension-text-live");
    node.setAttribute("aria-live", "polite");
    node.setAttribute("aria-atomic", "true");
    if (tagName !== "pre") node.setAttribute("role", "status");
  }
  return node;
}

function buildButton(component, view) {
  const button = create("button", "tau-extension-button");
  const label = create(
    "span",
    component.icon_only ? "tau-extension-button-icon" : "tau-extension-button-label",
    component.label,
  );
  button.type = "button";
  button.dataset.variant = component.variant;
  button.dataset.iconOnly = String(component.icon_only);
  if (component.accessible_label) button.setAttribute("aria-label", component.accessible_label);
  if (component.icon_only) label.setAttribute("aria-hidden", "true");
  button.replaceChildren(label);
  button.addEventListener("click", (event) => {
    event.preventDefault();
    if (!validateControls(view)) return;
    const payload = cloneJson(component.payload, "payload");
    Object.assign(payload, collectControlValues(view));
    view.dispatchEvent(
      new CustomEvent("tau:extension-action", {
        bubbles: true,
        composed: true,
        detail: {
          view_id: view.dataset.extensionViewId,
          action_id: component.action_id,
          payload,
        },
      }),
    );
  });
  return button;
}

function buildMetric(component) {
  const metric = create("dl", "tau-extension-metric");
  const label = create("dt", "tau-extension-metric-label", component.label);
  const value = create("dd", "tau-extension-metric-value", metricText(component.value, component.unit));
  metric.replaceChildren(label, value);
  return metric;
}

function buildProgress(component) {
  const wrapper = create("div", "tau-extension-progress");
  const heading = create("div", "tau-extension-progress-header");
  const label = create("span", "tau-extension-progress-label", component.label);
  const value = create("span", "tau-extension-progress-value", `${component.value} / ${component.max}`);
  const progress = create("progress", "tau-extension-progress-bar");
  heading.replaceChildren(label, value);
  progress.max = component.max;
  progress.value = component.value;
  progress.setAttribute("aria-label", component.label);
  wrapper.replaceChildren(heading, progress);
  return wrapper;
}

function buildField(component, viewId) {
  const wrapper = create("div", "tau-extension-field");
  const label = create("label", "tau-extension-field-label", component.label);
  const controlId = `tau-extension-${viewId}-${component.name}-${++fieldSerial}`;
  let control = null;

  if (component.input_type === "text") {
    control = create("input", "tau-extension-field-control");
    control.type = "text";
  } else if (component.input_type === "textarea") {
    control = create("textarea", "tau-extension-field-control");
    control.rows = 4;
  } else {
    control = create("select", "tau-extension-field-control");
    const options = component.options.map((option) => {
      const node = create("option", "", option.label);
      node.value = option.value;
      return node;
    });
    control.replaceChildren(...options);
  }

  control.id = controlId;
  control.name = component.name;
  if (component.value !== null) control.value = component.value;
  if (component.required) control.required = true;
  label.htmlFor = controlId;
  wrapper.replaceChildren(label, control);
  return wrapper;
}

function buildTable(component) {
  const wrapper = create("div", "tau-extension-table-wrap");
  const table = create("table", "tau-extension-table");
  const caption = create("caption", "tau-extension-table-caption", component.label);
  const thead = create("thead", "");
  const headRow = create("tr", "");
  const headCells = component.columns.map((column) => {
    const cell = create("th", "", column.label);
    cell.scope = "col";
    return cell;
  });
  headRow.replaceChildren(...headCells);
  thead.replaceChildren(headRow);

  const tbody = create("tbody", "");
  const rows = component.rows.map((row) => {
    const bodyRow = create("tr", "");
    const cells = component.columns.map((column) => {
      const cell = create("td", "", jsonText(row[column.key]));
      cell.dataset.label = column.label;
      return cell;
    });
    bodyRow.replaceChildren(...cells);
    return bodyRow;
  });
  tbody.replaceChildren(...rows);
  table.replaceChildren(caption, thead, tbody);
  wrapper.replaceChildren(table);
  return wrapper;
}

function buildStack(component, view) {
  const stack = create("div", `tau-extension-stack tau-extension-stack-${component.direction}`);
  if (component.accessible_label) {
    stack.setAttribute("role", "group");
    stack.setAttribute("aria-label", component.accessible_label);
  }
  const children = component.children.map((child) => buildComponent(child, view));
  stack.replaceChildren(...children);
  return stack;
}

function buildComponent(component, view) {
  if (component.kind === "text") return buildText(component);
  if (component.kind === "button") return buildButton(component, view);
  if (component.kind === "metric") return buildMetric(component);
  if (component.kind === "progress") return buildProgress(component);
  if (component.kind === "field") return buildField(component, view.dataset.extensionViewId || "view");
  if (component.kind === "table") return buildTable(component);
  return buildStack(component, view);
}

function buildView(view) {
  const article = create("article", `tau-extension-view tau-extension-view-${view.kind}`);
  const header = create("header", "tau-extension-header");
  const title = create("h3", "tau-extension-title", view.title);
  const body = create(view.kind === "form" ? "form" : "div", "tau-extension-body");
  article.dataset.extensionViewId = view.id;
  article.dataset.kind = view.kind;
  if (body instanceof HTMLFormElement) {
    body.noValidate = false;
    body.addEventListener("submit", (event) => event.preventDefault());
    body.classList.add("tau-extension-form");
  }
  header.replaceChildren(title);
  body.replaceChildren(...view.components.map((component) => buildComponent(component, article)));
  article.replaceChildren(header, body);
  return article;
}

function mountView(target, view) {
  const existing = renderedViews.get(view.id);
  if (existing) detach(existing.target, existing.node);
  const node = buildView(view);
  const nextChildren = Array.from(target.childNodes).filter((child) => child !== existing?.node);
  target.replaceChildren(...nextChildren, node);
  renderedViews.set(view.id, { node, target });
  return node;
}

function removeView(id) {
  const viewId = ensureSlug(id, "id");
  const existing = renderedViews.get(viewId);
  if (!existing) return false;
  detach(existing.target, existing.node);
  renderedViews.delete(viewId);
  return true;
}

function render(view) {
  return safely("Extension view rejected", () => {
    const normalized = validateView(view);
    return mountView(resolveSlot(normalized.placement), normalized);
  });
}

function renderInto(target, view) {
  return safely("Extension view rejected", () => {
    const normalized = validateView(view);
    return mountView(resolveTarget(target), normalized);
  });
}

function remove(id) {
  return safely("Extension view removal failed", () => removeView(id));
}

function clear() {
  return safely("Extension views could not be cleared", () => {
    for (const viewId of Array.from(renderedViews.keys())) removeView(viewId);
    return true;
  });
}

function handleViewEvent(event) {
  if (!(event instanceof CustomEvent) || handledEvents.has(event)) return;
  handledEvents.add(event);
  render(event.detail);
}

window.addEventListener("tau:extension-view", handleViewEvent);
document.addEventListener("tau:extension-view", handleViewEvent);
window.tauExtensionUI = Object.freeze({ render, remove, clear, renderInto });
