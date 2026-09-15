(function () {
  'use strict';

  var VERSION = '1.0';
  var MAX_MODULES = 64;
  var MAX_ASSET_BYTES = 1024 * 1024;
  var SAFE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
  var REQUIRED_FIELDS = ['asset_url', 'extension_id', 'integrity', 'module_id', 'sdk_version'];
  var ALLOWED_SLOTS = Object.freeze({
    dashboard: true,
    timeline_before: true,
    timeline_after: true,
    sidebar: true,
    compose_above: true,
    compose_below: true,
  });
  var ALLOWED_ASSET_MEDIA_TYPES = Object.freeze({
    'application/javascript': true,
    'text/javascript': true,
    'application/ecmascript': true,
    'text/ecmascript': true,
  });

  var state = {
    configured: false,
    adapters: null,
    activeModules: [],
  };

  function isFunction(value) {
    return typeof value === 'function';
  }

  function errorMessage(err) {
    return err && err.message ? String(err.message) : String(err);
  }

  function fail(message) {
    throw new Error(message);
  }

  function ensureConfigured() {
    if (!state.configured) fail('tauFrontendSDK.configure(adapters) must be called first');
  }

  function constantTimeEqual(a, b) {
    var max = a.length > b.length ? a.length : b.length;
    var diff = a.length ^ b.length;
    for (var i = 0; i < max; i += 1) diff |= (a[i] || 0) ^ (b[i] || 0);
    return diff === 0;
  }

  function base64ToBytes(base64) {
    var binary = atob(base64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }

  function getIds(raw) {
    return {
      extension_id: raw && typeof raw.extension_id === 'string' ? raw.extension_id : '',
      module_id: raw && typeof raw.module_id === 'string' ? raw.module_id : '',
    };
  }

  function isPlainObject(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    return Object.getPrototypeOf(value) === Object.prototype;
  }

  function mediaTypeFromContentType(contentType) {
    var raw = String(contentType || '');
    var separatorIndex = raw.indexOf(';');
    var mediaType = separatorIndex >= 0 ? raw.slice(0, separatorIndex) : raw;
    return mediaType.trim().toLowerCase();
  }

  function parsedContentLength(contentLength) {
    var value = String(contentLength || '').trim();
    if (!value || !/^[0-9]+$/.test(value)) return null;
    var parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 0) return null;
    return parsed;
  }

  function descriptorKey(descriptor) {
    return descriptor.extension_id + '\n' + descriptor.module_id;
  }

  function validateDescriptor(raw) {
    if (!isPlainObject(raw)) fail('descriptor must be a plain object');

    var keys = Object.keys(raw).sort();
    if (keys.length !== REQUIRED_FIELDS.length) fail('descriptor must contain exact required fields');
    for (var i = 0; i < REQUIRED_FIELDS.length; i += 1) {
      if (keys[i] !== REQUIRED_FIELDS[i]) fail('descriptor must contain exact required fields');
    }

    var extensionId = raw.extension_id;
    var moduleId = raw.module_id;
    var sdkVersion = raw.sdk_version;
    var integrity = raw.integrity;
    var assetUrl = raw.asset_url;

    if (typeof extensionId !== 'string' || !SAFE_ID_RE.test(extensionId)) fail('invalid extension_id');
    if (typeof moduleId !== 'string' || !SAFE_ID_RE.test(moduleId)) fail('invalid module_id');
    if (sdkVersion !== VERSION) fail('unsupported sdk_version');

    if (typeof integrity !== 'string') fail('invalid integrity');
    var sriMatch = /^sha256-([A-Za-z0-9+/]{43}=)$/.exec(integrity);
    if (!sriMatch) fail('integrity must be sha256-base64');
    var digest = base64ToBytes(sriMatch[1]);
    if (digest.length !== 32) fail('integrity digest must be SHA-256');

    if (typeof assetUrl !== 'string') fail('invalid asset_url');
    var resolved = new URL(assetUrl, window.location.href);
    if (resolved.origin !== window.location.origin) fail('asset_url must be same-origin');
    if (!resolved.pathname.startsWith('/api/extensions/assets/')) {
      fail('asset_url pathname must start with /api/extensions/assets/');
    }

    return {
      extension_id: extensionId,
      module_id: moduleId,
      sdk_version: sdkVersion,
      integrity: integrity,
      asset_url: resolved.href,
      digest: digest,
    };
  }

  function createModuleApi(record) {
    function request(path, options) {
      var resolved = new URL(String(path), window.location.href);
      if (resolved.origin !== window.location.origin || !resolved.pathname.startsWith('/api/')) {
        fail('request path must target same-origin /api/');
      }
      return state.adapters.request(resolved.pathname + resolved.search, options);
    }

    function mountSlot(slot, mount) {
      if (!ALLOWED_SLOTS[slot]) fail('unsupported slot: ' + slot);
      if (!isFunction(mount)) fail('mount must be a function');

      var slotContainer = document.querySelector('[data-extension-slot="' + slot + '"]');
      if (!slotContainer) fail('slot not found: ' + slot);

      var ownedContainer = document.createElement('div');
      ownedContainer.className = 'tau-frontend-module-slot';
      ownedContainer.setAttribute('data-tau-frontend-slot-owner', 'trusted-module');
      ownedContainer.setAttribute('data-extension-id', record.extension_id);
      ownedContainer.setAttribute('data-module-id', record.module_id);
      ownedContainer.setAttribute('data-slot', slot);
      slotContainer.appendChild(ownedContainer);

      var controller = new AbortController();
      var mountRecord = { controller: controller, container: ownedContainer, disposer: null };
      record.mounts.push(mountRecord);

      try {
        var maybeDisposer = mount(ownedContainer, Object.freeze({ signal: controller.signal }));
        if (isFunction(maybeDisposer)) mountRecord.disposer = maybeDisposer;
        return maybeDisposer;
      } catch (err) {
        record.mounts.pop();
        try {
          controller.abort();
        } catch (_) {}
        try {
          ownedContainer.remove();
        } catch (_) {}
        throw err;
      }
    }

    return Object.freeze({
      version: VERSION,
      extensionId: record.extension_id,
      moduleId: record.module_id,
      request: request,
      submit: state.adapters.submit,
      navigate: state.adapters.navigate,
      mountSlot: mountSlot,
    });
  }

  async function disposeModule(record) {
    var messages = [];

    var mounts = record.mounts.slice().reverse();
    record.mounts.length = 0;
    for (var i = 0; i < mounts.length; i += 1) {
      var mount = mounts[i];
      try {
        mount.controller.abort();
      } catch (err) {
        messages.push('mount abort failed: ' + errorMessage(err));
      }
      try {
        if (isFunction(mount.disposer)) await mount.disposer();
      } catch (err) {
        messages.push('mount disposer failed: ' + errorMessage(err));
      }
      try {
        mount.container.remove();
      } catch (err) {
        messages.push('mount remove failed: ' + errorMessage(err));
      }
    }

    try {
      if (isFunction(record.disposer)) await record.disposer();
    } catch (err) {
      messages.push('module disposer failed: ' + errorMessage(err));
    }

    return messages;
  }

  async function loadDescriptor(descriptor) {
    var response = await state.adapters.fetchAsset(descriptor.asset_url);
    if (!response || !isFunction(response.arrayBuffer) || typeof response.ok !== 'boolean') {
      fail('fetchAsset must return a Response');
    }
    if (!response.ok) fail('asset fetch failed: ' + response.status);

    var contentType = response.headers && isFunction(response.headers.get)
      ? String(response.headers.get('content-type') || '')
      : '';
    var mediaType = mediaTypeFromContentType(contentType);
    if (!ALLOWED_ASSET_MEDIA_TYPES[mediaType]) {
      fail('asset content-type must be JavaScript');
    }

    var contentLength = response.headers && isFunction(response.headers.get)
      ? parsedContentLength(response.headers.get('content-length'))
      : null;
    if (contentLength !== null && contentLength > MAX_ASSET_BYTES) {
      fail('asset exceeds 1 MiB');
    }

    var bytes = await response.arrayBuffer();
    if (bytes.byteLength > MAX_ASSET_BYTES) fail('asset exceeds 1 MiB');

    var actualDigest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
    if (!constantTimeEqual(actualDigest, descriptor.digest)) fail('asset integrity mismatch');

    var moduleUrl = state.adapters.createObjectURL(new Blob([bytes], { type: 'text/javascript' }));
    var moduleNamespace;
    try {
      // Same-origin extension code is trusted and runs with full page privileges (not sandboxed).
      moduleNamespace = await state.adapters.importModule(moduleUrl);
    } finally {
      try {
        state.adapters.revokeObjectURL(moduleUrl);
      } catch (_) {}
    }

    var activate = isFunction(moduleNamespace && moduleNamespace.activate)
      ? moduleNamespace.activate
      : (isFunction(moduleNamespace && moduleNamespace.default) ? moduleNamespace.default : null);
    if (!activate) fail('module must export activate or default function');

    var record = {
      extension_id: descriptor.extension_id,
      module_id: descriptor.module_id,
      mounts: [],
      disposer: null,
    };

    try {
      var maybeDisposer = await activate(createModuleApi(record));
      if (isFunction(maybeDisposer)) record.disposer = maybeDisposer;
      state.activeModules.push(record);
    } catch (err) {
      var cleanupErrors = await disposeModule(record);
      if (cleanupErrors.length) {
        fail(errorMessage(err) + '; cleanup: ' + cleanupErrors.join('; '));
      }
      throw err;
    }
  }

  function configure(adapters) {
    if (state.configured) fail('configure() can only be called once');
    if (!adapters || typeof adapters !== 'object') fail('adapters must be an object');

    var required = ['fetchAsset', 'request', 'submit', 'navigate'];
    for (var i = 0; i < required.length; i += 1) {
      if (!isFunction(adapters[required[i]])) fail('missing adapter: ' + required[i]);
    }

    if ('importModule' in adapters && !isFunction(adapters.importModule)) fail('invalid adapter: importModule');
    if ('createObjectURL' in adapters && !isFunction(adapters.createObjectURL)) fail('invalid adapter: createObjectURL');
    if ('revokeObjectURL' in adapters && !isFunction(adapters.revokeObjectURL)) fail('invalid adapter: revokeObjectURL');

    state.adapters = Object.freeze({
      fetchAsset: adapters.fetchAsset,
      request: adapters.request,
      submit: adapters.submit,
      navigate: adapters.navigate,
      importModule: adapters.importModule || function (url) { return import(url); },
      createObjectURL: adapters.createObjectURL || function (blob) { return URL.createObjectURL(blob); },
      revokeObjectURL: adapters.revokeObjectURL || function (url) { URL.revokeObjectURL(url); },
    });

    state.configured = true;
  }

  async function loadAll(descriptors) {
    ensureConfigured();
    if (!Array.isArray(descriptors)) fail('descriptors must be an array');
    if (descriptors.length > MAX_MODULES) fail('descriptors exceeds max of 64');

    var loaded = [];
    var errors = [];
    var ordered = descriptors.slice().sort(function (a, b) {
      var aExt = a && typeof a.extension_id === 'string' ? a.extension_id : '';
      var bExt = b && typeof b.extension_id === 'string' ? b.extension_id : '';
      if (aExt !== bExt) return aExt < bExt ? -1 : 1;
      var aMod = a && typeof a.module_id === 'string' ? a.module_id : '';
      var bMod = b && typeof b.module_id === 'string' ? b.module_id : '';
      if (aMod === bMod) return 0;
      return aMod < bMod ? -1 : 1;
    });

    var validDescriptors = [];
    var keyCounts = Object.create(null);

    for (var i = 0; i < ordered.length; i += 1) {
      var raw = ordered[i];
      var ids = getIds(raw);
      try {
        var descriptor = validateDescriptor(raw);
        validDescriptors.push({ descriptor: descriptor, ids: ids });
        var key = descriptorKey(descriptor);
        keyCounts[key] = (keyCounts[key] || 0) + 1;
      } catch (err) {
        errors.push({
          extension_id: ids.extension_id,
          module_id: ids.module_id,
          message: errorMessage(err),
        });
      }
    }

    var duplicateKeys = Object.create(null);
    for (var key in keyCounts) {
      if (Object.prototype.hasOwnProperty.call(keyCounts, key) && keyCounts[key] > 1) {
        duplicateKeys[key] = true;
      }
    }

    for (var j = 0; j < validDescriptors.length; j += 1) {
      var entry = validDescriptors[j];
      var entryDescriptor = entry.descriptor;
      if (duplicateKeys[descriptorKey(entryDescriptor)]) {
        errors.push({
          extension_id: entryDescriptor.extension_id,
          module_id: entryDescriptor.module_id,
          message: 'duplicate extension_id/module_id pair',
        });
        continue;
      }

      try {
        await loadDescriptor(entryDescriptor);
        loaded.push({
          extension_id: entryDescriptor.extension_id,
          module_id: entryDescriptor.module_id,
        });
      } catch (err) {
        errors.push({
          extension_id: entry.ids.extension_id,
          module_id: entry.ids.module_id,
          message: errorMessage(err),
        });
      }
    }

    return { loaded: loaded, errors: errors };
  }

  async function disposeAll() {
    ensureConfigured();

    var errors = [];
    var active = state.activeModules.slice().reverse();
    state.activeModules.length = 0;

    for (var i = 0; i < active.length; i += 1) {
      var record = active[i];
      var messages = await disposeModule(record);
      for (var j = 0; j < messages.length; j += 1) {
        errors.push({
          extension_id: record.extension_id,
          module_id: record.module_id,
          message: messages[j],
        });
      }
    }

    return { errors: errors };
  }

  window.tauFrontendSDK = Object.freeze({
    version: VERSION,
    configure: configure,
    loadAll: loadAll,
    disposeAll: disposeAll,
  });
})();
