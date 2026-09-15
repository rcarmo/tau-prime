(() => {
  "use strict";

  const MAX_MESSAGE_BYTES = 16 * 1024;
  const pending = new Map();
  let nextRequestId = 1;

  function identity() {
    const body = document.body;
    return {
      extension_id: body?.dataset.extensionId || "",
      widget_id: body?.dataset.widgetId || "",
    };
  }

  function requestId() {
    if (globalThis.crypto?.randomUUID) {
      return globalThis.crypto.randomUUID();
    }
    const value = `widget-${Date.now()}-${nextRequestId}`;
    nextRequestId += 1;
    return value;
  }

  function send(kind, detail = {}, { expectResult = false } = {}) {
    const id = requestId();
    const message = {
      source: "tau-widget",
      version: 1,
      kind,
      request_id: id,
      ...identity(),
      ...detail,
    };
    let encoded;
    try {
      encoded = JSON.stringify(message);
    } catch {
      return expectResult
        ? Promise.reject(new Error("Widget message must be JSON serializable."))
        : id;
    }
    if (new TextEncoder().encode(encoded).byteLength > MAX_MESSAGE_BYTES) {
      return expectResult
        ? Promise.reject(new Error("Widget message exceeds the bridge limit."))
        : id;
    }
    window.parent.postMessage(message, "*");
    if (!expectResult) {
      return id;
    }
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      window.setTimeout(() => {
        if (pending.delete(id)) {
          reject(new Error("Widget action response timed out."));
        }
      }, 35_000);
    });
  }

  const api = Object.freeze({
    action({ name, payload = {} } = {}) {
      if (typeof name !== "string" || !name.trim() || !isJSONObject(payload)) {
        return Promise.reject(new Error("action requires a name and JSON object payload."));
      }
      return send("action", { name, payload }, { expectResult: true });
    },
    submit({ text, mode = "prefill" } = {}) {
      if (typeof text !== "string" || !["prefill", "submit"].includes(mode)) {
        throw new Error("submit requires text and a prefill or submit mode.");
      }
      return send("submit", { text, mode });
    },
    requestRefresh({ key = null } = {}) {
      if (key !== null && typeof key !== "string") {
        throw new Error("requestRefresh key must be a string or null.");
      }
      return send("refresh", { key });
    },
    close({ reason = null } = {}) {
      if (reason !== null && typeof reason !== "string") {
        throw new Error("close reason must be a string or null.");
      }
      return send("close", { reason });
    },
  });

  function isJSONObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  window.addEventListener("message", (event) => {
    if (event.source !== window.parent) {
      return;
    }
    const message = event.data;
    if (
      !isJSONObject(message) ||
      message.source !== "tau-host" ||
      message.version !== 1 ||
      typeof message.request_id !== "string"
    ) {
      return;
    }
    const waiter = pending.get(message.request_id);
    if (!waiter) {
      return;
    }
    pending.delete(message.request_id);
    if (typeof message.error === "string" && message.error) {
      waiter.reject(new Error(message.error));
    } else {
      waiter.resolve(message.result);
    }
    window.dispatchEvent(new CustomEvent("tau:widget-result", { detail: message }));
  });

  Object.defineProperty(window, "tauWidget", {
    value: api,
    configurable: false,
    enumerable: true,
    writable: false,
  });
})();
