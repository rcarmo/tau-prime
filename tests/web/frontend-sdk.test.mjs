import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const sdkSource = await readFile(
  new URL("../../src/tau_web/static/frontend-sdk.js", import.meta.url),
  "utf8",
);

const nodeCrypto = globalThis.crypto;
assert.ok(nodeCrypto && nodeCrypto.subtle, "Node WebCrypto is required for frontend-sdk tests");

function partToBuffer(part) {
  if (typeof part === "string") {
    return Buffer.from(part, "utf8");
  }
  if (part instanceof ArrayBuffer) {
    return Buffer.from(part);
  }
  if (ArrayBuffer.isView(part)) {
    return Buffer.from(part.buffer, part.byteOffset, part.byteLength);
  }
  throw new TypeError(`Unsupported blob part: ${typeof part}`);
}

function toArrayBuffer(buffer) {
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

class FakeHeaders {
  constructor(init = {}) {
    this._map = new Map();
    for (const [key, value] of Object.entries(init)) {
      this._map.set(String(key).toLowerCase(), String(value));
    }
  }

  get(name) {
    return this._map.get(String(name).toLowerCase()) ?? null;
  }
}

class FakeResponse {
  constructor(body, options = {}) {
    this._body = partToBuffer(body);
    this.status = Number(options.status ?? 200);
    this.ok = this.status >= 200 && this.status < 300;
    this.headers = new FakeHeaders(options.headers ?? {});
  }

  async arrayBuffer() {
    return toArrayBuffer(this._body);
  }
}

class FakeBlob {
  constructor(parts = [], options = {}) {
    this.type = String(options.type ?? "");
    this._bytes = Buffer.concat(parts.map((part) => partToBuffer(part)));
    this.size = this._bytes.length;
  }

  async arrayBuffer() {
    return toArrayBuffer(this._bytes);
  }
}

function createHarness(options = {}) {
  function createFakeElement(tagName) {
    return {
      tagName: String(tagName).toUpperCase(),
      className: "",
      attributes: Object.create(null),
      children: [],
      parentNode: null,
      replaceChildrenCalls: 0,
      appendChild(child) {
        if (!child || typeof child !== "object") {
          throw new TypeError("appendChild requires an object child");
        }
        if (child.parentNode) {
          child.remove();
        }
        child.parentNode = this;
        this.children.push(child);
        return child;
      },
      remove() {
        if (!this.parentNode) {
          return;
        }
        const siblings = this.parentNode.children;
        const index = siblings.indexOf(this);
        if (index >= 0) {
          siblings.splice(index, 1);
        }
        this.parentNode = null;
      },
      setAttribute(name, value) {
        this.attributes[String(name)] = String(value);
      },
      getAttribute(name) {
        const key = String(name);
        return Object.prototype.hasOwnProperty.call(this.attributes, key)
          ? this.attributes[key]
          : null;
      },
      replaceChildren(...newChildren) {
        this.replaceChildrenCalls += 1;
        for (const child of this.children) {
          child.parentNode = null;
        }
        this.children = [];
        for (const child of newChildren) {
          this.appendChild(child);
        }
      },
    };
  }

  const slots = new Map();
  const slotNames = [
    "dashboard",
    "timeline_before",
    "timeline_after",
    "sidebar",
    "compose_above",
    "compose_below",
  ];
  for (const name of slotNames) {
    const slot = createFakeElement("div");
    slot.name = name;
    slot.setAttribute("data-extension-slot", name);

    const declarativeChild = createFakeElement("div");
    declarativeChild.setAttribute("data-fixture", "declarative-child");
    const preexistingChild = createFakeElement("div");
    preexistingChild.setAttribute("data-fixture", "preexisting-child");

    slot.appendChild(declarativeChild);
    slot.appendChild(preexistingChild);
    slot.declarativeChild = declarativeChild;
    slot.preexistingChild = preexistingChild;

    slots.set(name, slot);
  }

  const document = {
    createElement(tagName) {
      return createFakeElement(tagName);
    },
    querySelector(selector) {
      const match = /\[data-extension-slot="([^"]+)"\]/.exec(String(selector));
      if (!match) {
        return null;
      }
      return slots.get(match[1]) ?? null;
    },
  };

  const controllers = [];
  class FakeAbortController {
    constructor() {
      this.signal = { aborted: false };
      this.abortCalls = 0;
      controllers.push(this);
    }

    abort() {
      this.abortCalls += 1;
      this.signal.aborted = true;
    }
  }

  const window = {
    location: {
      href: "https://tau.test/index.html",
      origin: "https://tau.test",
    },
  };

  const context = vm.createContext({
    window,
    document,
    URL,
    Uint8Array,
    ArrayBuffer,
    Blob: FakeBlob,
    AbortController: FakeAbortController,
    Response: FakeResponse,
    atob: (value) => Buffer.from(String(value), "base64").toString("binary"),
    crypto: {
      subtle: {
        digest: (algorithm, data) => nodeCrypto.subtle.digest(algorithm, data),
      },
    },
  });

  new vm.Script(sdkSource, { filename: "frontend-sdk.js" }).runInContext(context);
  const sdk = window.tauFrontendSDK;
  assert.ok(sdk, "window.tauFrontendSDK should be defined");

  const assets = options.assets ?? new Map();
  const importQueue = options.importQueue ? [...options.importQueue] : [];

  let objectUrlCounter = 0;
  const objectUrls = [];
  const revokedObjectUrls = [];
  const requestCalls = [];
  const fetchCalls = [];

  sdk.configure({
    fetchAsset: async (assetUrl) => {
      fetchCalls.push(assetUrl);
      const record = assets.get(assetUrl);
      if (!record) {
        return new FakeResponse("not found", {
          status: 404,
          headers: { "content-type": "text/plain" },
        });
      }
      return new FakeResponse(record.bytes, {
        status: record.status ?? 200,
        headers: { "content-type": record.contentType ?? "text/javascript" },
      });
    },
    request: async (path, requestOptions) => {
      requestCalls.push({ path, requestOptions });
      return { ok: true };
    },
    submit: async () => ({ ok: true }),
    navigate: () => {},
    createObjectURL: (blob) => {
      const url = `blob:tau-test-${++objectUrlCounter}`;
      objectUrls.push({ url, blob });
      return url;
    },
    revokeObjectURL: (url) => {
      revokedObjectUrls.push(url);
    },
    importModule: async () => {
      assert.ok(importQueue.length > 0, "missing import namespace for descriptor");
      return importQueue.shift();
    },
  });

  function toVmPlainObject(value) {
    context.__hostValue = value;
    try {
      return vm.runInContext("JSON.parse(JSON.stringify(__hostValue))", context);
    } finally {
      delete context.__hostValue;
    }
  }

  return {
    sdk,
    loadAll: (descriptors) => sdk.loadAll(toVmPlainObject(descriptors)),
    slots: Object.fromEntries(slots.entries()),
    controllers,
    requestCalls,
    fetchCalls,
    objectUrls,
    revokedObjectUrls,
  };
}

async function sha256Integrity(bytes) {
  const digest = await nodeCrypto.subtle.digest("SHA-256", toArrayBuffer(Buffer.from(bytes)));
  return `sha256-${Buffer.from(digest).toString("base64")}`;
}

async function descriptorFromBytes({
  extensionId,
  moduleId,
  bytes,
  sdkVersion = "1.0",
  assetPath,
  integrity,
}) {
  const path = assetPath ?? `/api/extensions/assets/${extensionId}/${moduleId}.js`;
  return {
    asset_url: `https://tau.test${path}`,
    extension_id: extensionId,
    integrity: integrity ?? (await sha256Integrity(bytes)),
    module_id: moduleId,
    sdk_version: sdkVersion,
  };
}

function toPlain(value) {
  return JSON.parse(JSON.stringify(value));
}

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

test("rejects invalid descriptor shape/path/version", async () => {
  const harness = createHarness();

  const version = await descriptorFromBytes({
    extensionId: "extv",
    moduleId: "modv",
    bytes: Buffer.from("ok"),
    sdkVersion: "9.9",
  });
  const path = await descriptorFromBytes({
    extensionId: "extp",
    moduleId: "modp",
    bytes: Buffer.from("ok"),
    assetPath: "/static/not-allowed.js",
  });
  const shape = {
    ...(await descriptorFromBytes({
      extensionId: "exts",
      moduleId: "mods",
      bytes: Buffer.from("ok"),
    })),
    extra: true,
  };

  const result = await harness.loadAll([shape, path, version]);

  assert.equal(result.loaded.length, 0);
  assert.equal(result.errors.length, 3);
  const messages = new Map(result.errors.map((entry) => [entry.module_id, entry.message]));
  assert.match(messages.get("modv"), /unsupported sdk_version/);
  assert.match(messages.get("modp"), /asset_url pathname must start with \/api\/extensions\/assets\//);
  assert.match(messages.get("mods"), /descriptor must contain exact required fields/);
  assert.equal(harness.fetchCalls.length, 0);
});

test("rejects duplicate extension_id/module_id descriptor pairs", async () => {
  const bytes = Buffer.from("duplicate", "utf8");
  const descriptor = await descriptorFromBytes({
    extensionId: "extdup",
    moduleId: "moddup",
    bytes,
  });

  const harness = createHarness({
    assets: new Map([[descriptor.asset_url, { bytes }]]),
  });

  const result = await harness.loadAll([descriptor, { ...descriptor }]);

  assert.deepEqual(toPlain(result.loaded), []);
  assert.equal(result.errors.length, 2);
  for (const error of result.errors) {
    assert.equal(error.extension_id, "extdup");
    assert.equal(error.module_id, "moddup");
    assert.match(error.message, /duplicate extension_id\/module_id pair/);
  }
  assert.equal(harness.fetchCalls.length, 0);
});

test("reports integrity mismatch without importing module", async () => {
  const bytes = Buffer.from("console.log('asset');", "utf8");
  const wrongIntegrity = await sha256Integrity(Buffer.from("different", "utf8"));
  const descriptor = await descriptorFromBytes({
    extensionId: "exti",
    moduleId: "modi",
    bytes,
    integrity: wrongIntegrity,
  });

  const harness = createHarness({
    assets: new Map([[descriptor.asset_url, { bytes }]]),
  });

  const result = await harness.loadAll([descriptor]);

  assert.equal(result.loaded.length, 0);
  assert.equal(result.errors.length, 1);
  assert.match(result.errors[0].message, /asset integrity mismatch/);
  assert.equal(harness.objectUrls.length, 0);
  assert.equal(harness.revokedObjectUrls.length, 0);
});

test("rejects non-JavaScript MIME types for module assets", async () => {
  const bytes = Buffer.from("export default 1;", "utf8");
  const descriptor = await descriptorFromBytes({
    extensionId: "extmime",
    moduleId: "modmime",
    bytes,
  });

  const harness = createHarness({
    assets: new Map([[descriptor.asset_url, { bytes, contentType: "application/json" }]]),
  });

  const result = await harness.loadAll([descriptor]);

  assert.deepEqual(toPlain(result.loaded), []);
  assert.equal(result.errors.length, 1);
  assert.match(result.errors[0].message, /asset content-type must be JavaScript/);
  assert.equal(harness.objectUrls.length, 0);
  assert.equal(harness.revokedObjectUrls.length, 0);
});

test("activates SRI-verified module and binds same-origin /api/ requests", async () => {
  const bytes = Buffer.from("export default 1;", "utf8");
  const descriptor = await descriptorFromBytes({
    extensionId: "extok",
    moduleId: "modok",
    bytes,
  });

  let capturedApi = null;
  const mountCalls = [];

  const harness = createHarness({
    assets: new Map([[descriptor.asset_url, { bytes }]]),
    importQueue: [
      {
        activate(api) {
          capturedApi = api;
          api.mountSlot("sidebar", (container, { signal }) => {
            mountCalls.push({ container, signal });
          });
        },
      },
    ],
  });

  const result = await harness.loadAll([descriptor]);

  assert.deepEqual(toPlain(result.errors), []);
  assert.deepEqual(toPlain(result.loaded), [{ extension_id: "extok", module_id: "modok" }]);
  assert.equal(harness.objectUrls.length, 1);
  assert.equal(harness.revokedObjectUrls.length, 1);
  assert.ok(capturedApi);
  assert.equal(mountCalls.length, 1);

  const sidebar = harness.slots.sidebar;
  assert.equal(sidebar.children.length, 3);
  assert.equal(sidebar.children[0], sidebar.declarativeChild);
  assert.equal(sidebar.children[1], sidebar.preexistingChild);

  const ownedChild = sidebar.children[2];
  assert.equal(mountCalls[0].container, ownedChild);
  assert.equal(mountCalls[0].signal.aborted, false);
  assert.equal(ownedChild.parentNode, sidebar);
  assert.equal(ownedChild.className, "tau-frontend-module-slot");
  assert.equal(ownedChild.getAttribute("data-tau-frontend-slot-owner"), "trusted-module");
  assert.equal(ownedChild.getAttribute("data-extension-id"), "extok");
  assert.equal(ownedChild.getAttribute("data-module-id"), "modok");
  assert.equal(ownedChild.getAttribute("data-slot"), "sidebar");
  assert.equal(sidebar.replaceChildrenCalls, 0);

  await capturedApi.request("/api/sessions?limit=1");
  await capturedApi.request("https://tau.test/api/events?cursor=1");
  assert.deepEqual(
    harness.requestCalls.map((entry) => entry.path),
    ["/api/sessions?limit=1", "/api/events?cursor=1"],
  );

  assert.throws(() => capturedApi.request("/dashboard"), /request path must target same-origin \/api\//);
  assert.throws(
    () => capturedApi.request("https://evil.test/api/sessions"),
    /request path must target same-origin \/api\//,
  );
});

test("loads descriptors deterministically and isolates failures", async () => {
  const bytesA1 = Buffer.from("a1", "utf8");
  const bytesA2 = Buffer.from("a2", "utf8");
  const bytesB1 = Buffer.from("b1", "utf8");

  const descriptorA1 = await descriptorFromBytes({
    extensionId: "exta",
    moduleId: "mod1",
    bytes: bytesA1,
  });
  const descriptorA2 = await descriptorFromBytes({
    extensionId: "exta",
    moduleId: "mod2",
    bytes: bytesA2,
  });
  const descriptorB1 = await descriptorFromBytes({
    extensionId: "extb",
    moduleId: "mod1",
    bytes: bytesB1,
  });

  const activationOrder = [];

  const harness = createHarness({
    assets: new Map([
      [descriptorA1.asset_url, { bytes: bytesA1 }],
      [descriptorA2.asset_url, { bytes: bytesA2 }],
      [descriptorB1.asset_url, { bytes: bytesB1 }],
    ]),
    importQueue: [
      {
        activate() {
          activationOrder.push("exta/mod1");
        },
      },
      {
        activate() {
          activationOrder.push("exta/mod2");
          throw new Error("activate failed");
        },
      },
      {
        activate() {
          activationOrder.push("extb/mod1");
        },
      },
    ],
  });

  const result = await harness.loadAll([descriptorB1, descriptorA2, descriptorA1]);

  assert.deepEqual(activationOrder, ["exta/mod1", "exta/mod2", "extb/mod1"]);
  assert.deepEqual(toPlain(result.loaded), [
    { extension_id: "exta", module_id: "mod1" },
    { extension_id: "extb", module_id: "mod1" },
  ]);
  assert.equal(result.errors.length, 1);
  assert.equal(result.errors[0].extension_id, "exta");
  assert.equal(result.errors[0].module_id, "mod2");
  assert.match(result.errors[0].message, /activate failed/);
});

test("disposeAll aborts mounts, removes owned children, and invokes disposers", async () => {
  const bytes = Buffer.from("dispose-me", "utf8");
  const descriptor = await descriptorFromBytes({
    extensionId: "extd",
    moduleId: "modd",
    bytes,
  });

  const lifecycle = [];
  const mountSignals = [];
  const mountedContainers = {};

  const harness = createHarness({
    assets: new Map([[descriptor.asset_url, { bytes }]]),
    importQueue: [
      {
        activate(api) {
          api.mountSlot("sidebar", (container, { signal }) => {
            mountedContainers.sidebar = container;
            mountSignals.push(signal);
            return () => {
              lifecycle.push("mount-disposer-sidebar");
            };
          });
          api.mountSlot("compose_above", (container, { signal }) => {
            mountedContainers.compose_above = container;
            mountSignals.push(signal);
            return () => {
              lifecycle.push("mount-disposer-compose_above");
            };
          });
          return () => {
            lifecycle.push("module-disposer");
          };
        },
      },
    ],
  });

  await harness.loadAll([descriptor]);

  const sidebar = harness.slots.sidebar;
  const composeAbove = harness.slots.compose_above;
  assert.equal(sidebar.children.length, 3);
  assert.equal(composeAbove.children.length, 3);
  assert.equal(sidebar.children[0], sidebar.declarativeChild);
  assert.equal(sidebar.children[1], sidebar.preexistingChild);
  assert.equal(composeAbove.children[0], composeAbove.declarativeChild);
  assert.equal(composeAbove.children[1], composeAbove.preexistingChild);

  const disposeResult = await harness.sdk.disposeAll();

  assert.deepEqual(toPlain(disposeResult), { errors: [] });
  assert.equal(harness.controllers.length, 2);
  for (const controller of harness.controllers) {
    assert.equal(controller.abortCalls, 1);
    assert.equal(controller.signal.aborted, true);
  }
  for (const signal of mountSignals) {
    assert.equal(signal.aborted, true);
  }

  assert.equal(sidebar.children.length, 2);
  assert.equal(composeAbove.children.length, 2);
  assert.equal(sidebar.children[0], sidebar.declarativeChild);
  assert.equal(sidebar.children[1], sidebar.preexistingChild);
  assert.equal(composeAbove.children[0], composeAbove.declarativeChild);
  assert.equal(composeAbove.children[1], composeAbove.preexistingChild);
  assert.equal(mountedContainers.sidebar.parentNode, null);
  assert.equal(mountedContainers.compose_above.parentNode, null);
  assert.equal(sidebar.replaceChildrenCalls, 0);
  assert.equal(composeAbove.replaceChildrenCalls, 0);

  assert.deepEqual(lifecycle, [
    "mount-disposer-compose_above",
    "mount-disposer-sidebar",
    "module-disposer",
  ]);
});

test("rejects descriptor arrays longer than 64 entries", async () => {
  const harness = createHarness();
  await assert.rejects(
    () => harness.loadAll(Array.from({ length: 65 }, () => ({}))),
    /descriptors exceeds max of 64/,
  );
  assert.equal(harness.fetchCalls.length, 0);
});

let failed = 0;
for (const { name, fn } of tests) {
  try {
    await fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    failed += 1;
    console.error(`not ok - ${name}`);
    console.error(error && error.stack ? error.stack : error);
  }
}

if (failed > 0) {
  console.error(`${failed} test(s) failed`);
  process.exit(1);
}

console.log(`${tests.length} frontend-sdk vm tests passed`);
