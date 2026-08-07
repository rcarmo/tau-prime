export type ApiErrorPayload = {
  error?: { code?: string; message?: string; details?: unknown };
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "request_failed",
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type ApiClientOptions = {
  authToken?: () => string | null;
  fetch?: typeof globalThis.fetch;
};

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

export class ApiClient {
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(private readonly options: ApiClientOptions = {}) {
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
  }

  async request<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
    const method = (init.method ?? "GET").toUpperCase();
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (!SAFE_METHODS.has(method)) headers.set("X-Tau-CSRF", "1");
    const token = this.options.authToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    let body = init.body;
    if (init.json !== undefined) {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(init.json);
    }
    const response = await this.fetchImpl(path, {
      ...init,
      body,
      credentials: "same-origin",
      headers,
      method,
    });
    if (response.status === 204) return null as T;
    const isJson = response.headers.get("content-type")?.includes("application/json") ?? false;
    const payload = isJson ? await response.json() : await response.text();
    if (!response.ok) {
      const error = typeof payload === "object" && payload !== null
        ? (payload as ApiErrorPayload).error
        : undefined;
      throw new ApiError(
        error?.message ?? `${response.status} ${response.statusText}`.trim(),
        response.status,
        error?.code,
        error?.details,
      );
    }
    return payload as T;
  }
}
