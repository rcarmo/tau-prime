export type SessionRecord = {
  session_id: string;
  title: string;
  provider_name: string;
  model: string;
  thinking_level?: string | null;
  status?: string;
  created_at?: string;
  updated_at?: string;
};

export type ModelDescriptor = { provider_name: string; model: string };
export type OnboardingProvider = {
  name: string;
  models: string[];
  default_model: string;
  credential_name: string | null;
  configured: boolean;
};
export type OnboardingState = {
  configured: boolean;
  default_provider: string;
  default_model: string;
  providers: OnboardingProvider[];
};
export type CommandDescriptor = { name: string; description?: string; source?: string };
export type TimelineItem = {
  id?: string;
  kind: string;
  role?: string;
  content?: unknown;
  created_at?: string;
  [key: string]: unknown;
};
export type RunRecord = {
  run_id: string;
  session_id: string;
  status: string;
  [key: string]: unknown;
};
export type QueueKind = "follow_up" | "steer";
export type QueueItem = {
  queue_id: string;
  session_id: string;
  queue_kind: QueueKind;
  position: number;
  content: unknown;
  source_session_id?: string | null;
  created_at?: string;
  consumed_at?: string | null;
};
export type PlanDocument = { content?: string; markdown?: string; updated_at?: string; [key: string]: unknown };
export type ApprovalRecord = { approval_id: string; status: string; [key: string]: unknown };
export type MediaRecord = { media_id: string; filename?: string; content_type?: string; [key: string]: unknown };
