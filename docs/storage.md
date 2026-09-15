# Storage

Tau's sole live durable store is SQLite. Live sessions, workspaces, aliases, run state, queue state, timeline data, usage records, media metadata, extension state and audit data all live in one database file.

JSONL is **not** the live store any more. In current code it is an interchange format for import/export.

## Live database path

Tau resolves the live database as `TauPaths().home / "tau.sqlite3"`, which in the normal default case is:

```text
~/.tau/tau.sqlite3
```

If `TAU_HOME` is set, Tau uses `$TAU_HOME/tau.sqlite3` instead.

The current CLI does **not** expose `--db-path`. The actual flag in source is `--database`:

- `tau web --database /path/to/tau.sqlite3`
- `tau import-session ... --database /path/to/tau.sqlite3`
- `tau export-session ... --database /path/to/tau.sqlite3`

The default TUI/live manager path is still `TauPaths().home / "tau.sqlite3"`.

## Connection and locking model

On open, `SqliteDatabase`:

1. Acquires a sibling advisory process lock at `tau.sqlite3.lock`.
2. Opens one write connection.
3. Configures SQLite pragmas.
4. Applies pending migrations.
5. Runs an integrity check.
6. Recovers stale `session_runs` rows left as `running`.
7. Starts a serialised writer service and a bounded read-only pool.

The lock is non-blocking. If another Tau process already owns the database writer role, Tau raises `DatabaseLockedError` rather than waiting indefinitely.

Tau also tightens file permissions around the store:

- database directory: `0700`
- database and `-wal` / `-shm` files: `0600`
- lock file: `0600`

## SQLite pragmas actually used

The write connection sets:

- `PRAGMA journal_mode = WAL`
- `PRAGMA foreign_keys = ON`
- `PRAGMA synchronous = NORMAL`
- `PRAGMA busy_timeout = 5000`
- `PRAGMA temp_store = MEMORY`

Each pooled read connection is opened read-only with `mode=ro`, then sets:

- `PRAGMA foreign_keys = ON`
- `PRAGMA busy_timeout = 5000`
- `PRAGMA temp_store = MEMORY`
- `PRAGMA query_only = ON`

## Single writer, pooled readers

Tau uses a strict single-writer model per database instance:

- one write connection per process
- a `SqliteWriter` queue to serialise all mutations
- transactional writes started with `BEGIN IMMEDIATE`
- a default read pool of four read-only connections

That means writes are FIFO within a priority level and happen atomically, while reads can proceed concurrently through the read pool.

## Schema and migrations

Migrations are forward-only and tracked through `schema_migrations` plus `PRAGMA user_version`.

At startup Tau checks the current `user_version`, runs every newer migration in order, records the migration row, sets `user_version`, and commits.

Migrations run inside `BEGIN EXCLUSIVE` / `COMMIT`. If a migration fails, Tau rolls the transaction back and aborts opening the database.

If the database schema version is newer than the code understands, Tau refuses to open it.

The current source ships one live schema migration (`LATEST_SCHEMA_VERSION = 1`).

## JSON columns and `json_valid()`

Structured payloads are stored as `TEXT` columns with SQLite JSON validity checks. Examples include `sessions.metadata_json`, `session_entries.payload_json`, `session_branches.metadata_json`, `session_runs.last_status_json`, `session_runs.error_json`, `queued_messages.content_json`, `chat_deliveries.ancestry_json`, `chat_deliveries.error_json`, `timeline_messages.content_blocks_json`, `usage_records.details_json`, `media_items.metadata_json`, `extension_state.value_json`, and `audit_records.details_json`.

Nullable JSON columns use the nullable form of the check (`column IS NULL OR json_valid(column)`).

## Integrity, recovery and checkpointing

### Integrity check

After migrations, Tau runs:

```sql
PRAGMA quick_check;
```

If SQLite returns anything other than `ok`, Tau raises `DatabaseIntegrityError` and does not continue.

### Recovery on startup

Tau performs one concrete startup recovery step in storage code: any `session_runs` row still marked `running` is updated to `interrupted`, with `updated_at`, `ended_at`, and a structured `error_json` payload recording `runtime_restarted`.

The web service exposes the count as `recovered_run_count`.

### Checkpointing

Tau uses passive WAL checkpointing:

```sql
PRAGMA wal_checkpoint(PASSIVE);
```

It does this on clean close, and the database wrapper also exposes an internal `checkpoint()` method. There is no public `tau checkpoint` CLI command at present.

## Append-only session history

Live transcript history remains append-only at the session-entry level. `SqliteSessionStorage` stores ordered `session_entries` rows, preserves parent/leaf references, and updates the active leaf pointer in `sessions`.

Branching and compaction change the active path; they do not rewrite earlier entry rows.

## JSONL interchange only

JSONL remains supported for moving session history in and out of SQLite:

- `tau import-session <source.jsonl>` imports one Tau JSONL session into SQLite
- `tau export-session <session-id-or-local-address>` exports one SQLite-backed session as Tau JSONL

`tau export-session` only supports `--format jsonl`.

These commands are interchange tooling, not an alternative live storage backend. `SessionInterchange` explicitly validates JSONL before opening the write transaction and then imports the whole session atomically.

## Safe backup, restore and rollback

Use only workflows supported by the current storage model.

### Back up one session

Export JSONL:

```sh
tau export-session <session-id> --output session.jsonl
```

This is best for a single-session archive or transfer, not for a full-database snapshot.

### Back up the whole live store

1. Stop Tau first so it releases `tau.sqlite3.lock` and performs its normal passive checkpoint on close.
2. Then either:
   - use standard SQLite backup tooling, for example `sqlite3 ~/.tau/tau.sqlite3 ".backup '/safe/path/tau.sqlite3'"`; or
   - make a cold filesystem copy of `tau.sqlite3` and, if present, the sibling `tau.sqlite3-wal` and `tau.sqlite3-shm` files together.

Do **not** treat old `~/.tau/sessions/*.jsonl` trees as the live store, and do not copy only the main database file while Tau is still running.

### Restore or roll back

- For a full restore, stop Tau and replace the database from a known-good SQLite backup.
- For session-level rollback, import a previously exported JSONL session into the target database.
- There is no general public `tau rollback` command for arbitrary live-database mutations.

One narrow rollback mechanism does exist in code for legacy bulk imports only: `LegacyMigrationService` emits a `tau-migration-rollback` manifest and can delete only sessions carrying the matching migration marker. That is not the normal live-session workflow.
