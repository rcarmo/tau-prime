import { ApiClient } from "./client";
import type {
  ApprovalRecord, CommandDescriptor, MediaRecord, ModelDescriptor, OnboardingState,
  PlanDocument, QueueItem, RunRecord, SessionRecord, TimelineItem,
} from "./types";

const id = encodeURIComponent;

export class TauApi {
  constructor(readonly client = new ApiClient()) {}

  settings() { return this.client.request<Record<string, unknown>>("/api/settings"); }
  onboarding() { return this.client.request<OnboardingState>("/api/onboarding"); }
  configureOnboarding(input: { provider: string; model: string; credential?: string }) {
    return this.client.request<OnboardingState>("/api/onboarding", { method: "PUT", json: input });
  }
  models() { return this.client.request<ModelDescriptor[]>("/api/models"); }
  commands() { return this.client.request<CommandDescriptor[]>("/api/commands"); }
  sessions() { return this.client.request<SessionRecord[]>("/api/sessions"); }
  session(sessionId: string) { return this.client.request<SessionRecord>(`/api/sessions/${id(sessionId)}`); }
  createSession(input: { title?: string; provider_name: string; model: string }) {
    return this.client.request<SessionRecord>("/api/sessions", { method: "POST", json: input });
  }
  updateSession(sessionId: string, input: Record<string, unknown>) {
    return this.client.request<SessionRecord>(`/api/sessions/${id(sessionId)}`, { method: "PATCH", json: input });
  }
  archiveSession(sessionId: string) {
    return this.client.request<void>(`/api/sessions/${id(sessionId)}`, { method: "DELETE" });
  }
  timeline(sessionId: string) {
    return this.client.request<TimelineItem[]>(`/api/sessions/${id(sessionId)}/timeline`);
  }
  entries(sessionId: string) { return this.client.request<unknown[]>(`/api/sessions/${id(sessionId)}/entries`); }
  messages(sessionId: string) { return this.client.request<unknown[]>(`/api/sessions/${id(sessionId)}/messages`); }
  branches(sessionId: string) { return this.client.request<unknown[]>(`/api/sessions/${id(sessionId)}/branches`); }
  selectBranch(sessionId: string, input: Record<string, unknown>) {
    return this.client.request<unknown>(`/api/sessions/${id(sessionId)}/branches/select`, { method: "POST", json: input });
  }
  context(sessionId: string) { return this.client.request<Record<string, unknown>>(`/api/sessions/${id(sessionId)}/context`); }
  usage(sessionId: string) { return this.client.request<Record<string, unknown>>(`/api/sessions/${id(sessionId)}/usage`); }
  runs(sessionId: string) { return this.client.request<RunRecord[]>(`/api/sessions/${id(sessionId)}/runs`); }
  submitRun(sessionId: string, input: Record<string, unknown>) {
    return this.client.request<RunRecord>(`/api/sessions/${id(sessionId)}/runs`, { method: "POST", json: input });
  }
  runAction(runId: string, action: "cancel" | "abort" | "retry") {
    return this.client.request<RunRecord>(`/api/runs/${id(runId)}/${action}`, { method: "POST" });
  }
  queue(sessionId: string) { return this.client.request<QueueItem[]>(`/api/sessions/${id(sessionId)}/queue`); }
  enqueue(sessionId: string, content: string, kind: QueueItem["kind"]) {
    return this.client.request<QueueItem>(`/api/sessions/${id(sessionId)}/queue`, { method: "POST", json: { content, kind } });
  }
  plan(sessionId: string) { return this.client.request<PlanDocument>(`/api/sessions/${id(sessionId)}/plan`); }
  savePlan(sessionId: string, plan: PlanDocument) {
    return this.client.request<PlanDocument>(`/api/sessions/${id(sessionId)}/plan`, { method: "PUT", json: plan });
  }
  approvals(sessionId: string) { return this.client.request<ApprovalRecord[]>(`/api/sessions/${id(sessionId)}/approvals`); }
  resolveApproval(approvalId: string, resolution: string) {
    return this.client.request<ApprovalRecord>(`/api/approvals/${id(approvalId)}`, { method: "POST", json: { resolution } });
  }
  media() { return this.client.request<MediaRecord[]>("/api/media"); }
  uploadMedia(body: FormData) { return this.client.request<MediaRecord>("/api/media", { method: "POST", body }); }
  deleteMedia(mediaId: string) { return this.client.request<void>(`/api/media/${id(mediaId)}`, { method: "DELETE" }); }
  files(path = "") { return this.client.request<unknown>(`/api/files?path=${encodeURIComponent(path)}`); }
  search(query: string) { return this.client.request<unknown[]>(`/api/search?q=${encodeURIComponent(query)}`); }
  dashboard() { return this.client.request<Record<string, unknown>>("/dashboard"); }
  meters() { return this.client.request<Record<string, unknown>>("/meters"); }
  frontendModules() { return this.client.request<unknown[]>("/api/extensions/frontend-modules"); }
  widget(extensionId: string, widgetId: string) {
    return this.client.request<unknown>(`/api/extensions/widgets/${id(extensionId)}/${id(widgetId)}`);
  }
  widgetAction(extensionId: string, widgetId: string, action: string, input: unknown) {
    return this.client.request<unknown>(`/api/extensions/widgets/${id(extensionId)}/${id(widgetId)}/actions/${id(action)}`, { method: "POST", json: input });
  }
  eventUrl(sessionId: string) { return `/api/events?session_id=${id(sessionId)}`; }
}

export * from "./client";
export * from "./types";
