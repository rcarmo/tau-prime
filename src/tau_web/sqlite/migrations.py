"""Ordered SQLite schema migrations for Tau's live runtime store."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    """One immutable, forward-only database migration."""

    version: int
    name: str
    sql: str


MIGRATION_0001 = Migration(
    version=1,
    name="initial_runtime_schema",
    sql=r"""
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

CREATE TABLE workspaces (
    workspace_id TEXT PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
    agent_name TEXT NOT NULL COLLATE NOCASE,
    title TEXT,
    provider_name TEXT NOT NULL,
    model TEXT NOT NULL,
    thinking_level TEXT,
    active_leaf_entry_id TEXT REFERENCES session_entries(entry_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
        CHECK(json_valid(metadata_json))
);

CREATE UNIQUE INDEX sessions_active_agent_name
    ON sessions(agent_name COLLATE NOCASE)
    WHERE archived_at IS NULL;
CREATE INDEX sessions_workspace_updated
    ON sessions(workspace_id, updated_at DESC);

CREATE TABLE session_entries (
    entry_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    parent_entry_id TEXT REFERENCES session_entries(entry_id),
    entry_type TEXT NOT NULL,
    timestamp REAL NOT NULL,
    ordinal INTEGER NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    UNIQUE(session_id, ordinal)
);

CREATE INDEX session_entries_parent
    ON session_entries(session_id, parent_entry_id);
CREATE INDEX session_entries_type
    ON session_entries(session_id, entry_type, ordinal);

CREATE TABLE session_branches (
    branch_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    name TEXT NOT NULL COLLATE NOCASE,
    leaf_entry_id TEXT REFERENCES session_entries(entry_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
        CHECK(json_valid(metadata_json)),
    UNIQUE(session_id, name)
);

CREATE TABLE session_runs (
    run_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    status TEXT NOT NULL
        CHECK(status IN ('pending', 'running', 'completed', 'cancelled', 'failed', 'interrupted')),
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    ended_at TEXT,
    last_event_type TEXT,
    last_status_json TEXT CHECK(last_status_json IS NULL OR json_valid(last_status_json)),
    error_json TEXT CHECK(error_json IS NULL OR json_valid(error_json))
);

CREATE INDEX session_runs_session_started
    ON session_runs(session_id, started_at DESC);
CREATE INDEX session_runs_status
    ON session_runs(status, updated_at);

CREATE TABLE queued_messages (
    queue_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    queue_kind TEXT NOT NULL CHECK(queue_kind IN ('steer', 'follow_up')),
    position INTEGER NOT NULL CHECK(position >= 0),
    content_json TEXT NOT NULL CHECK(json_valid(content_json)),
    source_session_id TEXT REFERENCES sessions(session_id),
    created_at TEXT NOT NULL,
    consumed_at TEXT,
    UNIQUE(session_id, queue_kind, position)
);

CREATE INDEX queued_messages_unconsumed
    ON queued_messages(session_id, queue_kind, position)
    WHERE consumed_at IS NULL;

CREATE TABLE chat_deliveries (
    delivery_id TEXT PRIMARY KEY,
    transport TEXT NOT NULL DEFAULT 'local',
    source_session_id TEXT NOT NULL REFERENCES sessions(session_id),
    target_session_id TEXT REFERENCES sessions(session_id),
    target_address TEXT,
    mode TEXT NOT NULL CHECK(mode IN ('auto', 'queue', 'steer')),
    content TEXT NOT NULL,
    idempotency_key TEXT,
    in_reply_to TEXT REFERENCES chat_deliveries(delivery_id),
    ancestry_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(ancestry_json)),
    hop_count INTEGER NOT NULL DEFAULT 0 CHECK(hop_count >= 0),
    status TEXT NOT NULL
        CHECK(status IN ('pending', 'accepted', 'dispatched', 'completed', 'failed', 'rejected')),
    created_at TEXT NOT NULL,
    accepted_at TEXT,
    completed_at TEXT,
    error_json TEXT CHECK(error_json IS NULL OR json_valid(error_json)),
    CHECK(target_session_id IS NOT NULL OR target_address IS NOT NULL)
);

CREATE UNIQUE INDEX chat_delivery_dedupe
    ON chat_deliveries(transport, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX chat_deliveries_target_status
    ON chat_deliveries(target_session_id, status, created_at);

CREATE TABLE timeline_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id TEXT NOT NULL UNIQUE,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
    entry_id TEXT REFERENCES session_entries(entry_id),
    thread_id INTEGER REFERENCES timeline_messages(message_id),
    role TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    content_blocks_json TEXT
        CHECK(content_blocks_json IS NULL OR json_valid(content_blocks_json)),
    sender_session_id TEXT REFERENCES sessions(session_id),
    delivery_id TEXT REFERENCES chat_deliveries(delivery_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX timeline_messages_session_created
    ON timeline_messages(session_id, created_at, message_id);
CREATE INDEX timeline_messages_entry
    ON timeline_messages(entry_id)
    WHERE entry_id IS NOT NULL;

CREATE TABLE usage_records (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    run_id TEXT REFERENCES session_runs(run_id) ON DELETE SET NULL,
    provider_name TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0 CHECK(input_tokens >= 0),
    output_tokens INTEGER NOT NULL DEFAULT 0 CHECK(output_tokens >= 0),
    cached_input_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cached_input_tokens >= 0),
    cost_microunits INTEGER CHECK(cost_microunits IS NULL OR cost_microunits >= 0),
    details_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(details_json)),
    recorded_at TEXT NOT NULL
);

CREATE INDEX usage_records_session_recorded
    ON usage_records(session_id, recorded_at DESC);

CREATE TABLE session_plans (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    markdown TEXT NOT NULL,
    explanation TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
);

CREATE TABLE media_blobs (
    blob_id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    content BLOB NOT NULL,
    byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
    created_at TEXT NOT NULL
);

CREATE TABLE media_items (
    media_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE SET NULL,
    blob_id TEXT NOT NULL REFERENCES media_blobs(blob_id),
    thumbnail_blob_id TEXT REFERENCES media_blobs(blob_id),
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL,
    width INTEGER CHECK(width IS NULL OR width > 0),
    height INTEGER CHECK(height IS NULL OR height > 0),
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metadata_json)),
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX media_items_session_created
    ON media_items(session_id, created_at DESC);

CREATE TABLE media_references (
    media_id TEXT NOT NULL REFERENCES media_items(media_id) ON DELETE CASCADE,
    reference_type TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(media_id, reference_type, reference_id)
);

CREATE TABLE extension_state (
    extension_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('global', 'workspace', 'session', 'connection')),
    scope_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL CHECK(json_valid(value_json)),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
    updated_at TEXT NOT NULL,
    PRIMARY KEY(extension_id, scope, scope_id, key)
);

CREATE INDEX extension_state_scope
    ON extension_state(scope, scope_id, extension_id);

CREATE TABLE audit_records (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    workspace_id TEXT REFERENCES workspaces(workspace_id),
    session_id TEXT REFERENCES sessions(session_id),
    extension_id TEXT,
    request_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(details_json)),
    created_at TEXT NOT NULL
);

CREATE INDEX audit_records_created
    ON audit_records(created_at DESC, audit_id DESC);
CREATE INDEX audit_records_session
    ON audit_records(session_id, created_at DESC)
    WHERE session_id IS NOT NULL;

CREATE VIRTUAL TABLE search_fts USING fts5(
    entity_type UNINDEXED,
    entity_id UNINDEXED,
    session_id UNINDEXED,
    text,
    tokenize = 'unicode61 remove_diacritics 2'
);
""",
)

MIGRATION_0002 = Migration(
    version=2,
    name="anthropic_cache_write_usage",
    sql=r"""
ALTER TABLE usage_records
    ADD COLUMN cache_write_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_write_tokens >= 0);
ALTER TABLE usage_records
    ADD COLUMN cache_write_1h_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_write_1h_tokens >= 0);
""",
)

MIGRATIONS: tuple[Migration, ...] = (MIGRATION_0001, MIGRATION_0002)
LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version


def pending_migrations(current_version: int) -> tuple[Migration, ...]:
    """Return ordered migrations newer than ``current_version``."""
    if current_version < 0:
        raise ValueError("Schema version must not be negative")
    if current_version > LATEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema {current_version} is newer than supported "
            f"schema {LATEST_SCHEMA_VERSION}"
        )
    return tuple(migration for migration in MIGRATIONS if migration.version > current_version)
