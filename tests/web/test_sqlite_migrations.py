from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.migrations import LATEST_SCHEMA_VERSION, MIGRATIONS, pending_migrations
from tau_web.sqlite.writer import SqliteTransaction


@pytest.fixture
def database() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    for migration in MIGRATIONS:
        connection.executescript(migration.sql)
        connection.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
            (migration.version, migration.name, "2026-08-04T00:00:00Z"),
        )
    yield connection
    connection.close()


def _insert_workspace_and_session(
    database: sqlite3.Connection, *, session_id: str = "session-1", agent_name: str = "default"
) -> None:
    database.execute(
        """
        INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
        VALUES ('workspace-1', '/workspace', 'now', 'now')
        """
    )
    database.execute(
        """
        INSERT INTO sessions(
            session_id, workspace_id, agent_name, provider_name, model, created_at, updated_at
        ) VALUES (?, 'workspace-1', ?, 'test', 'test-model', 'now', 'now')
        """,
        (session_id, agent_name),
    )


def test_migration_versions_are_strictly_ordered() -> None:
    versions = [migration.version for migration in MIGRATIONS]

    assert versions == list(range(1, LATEST_SCHEMA_VERSION + 1))
    assert len({migration.name for migration in MIGRATIONS}) == len(MIGRATIONS)
    assert pending_migrations(0) == MIGRATIONS
    assert pending_migrations(LATEST_SCHEMA_VERSION) == ()


def test_pending_migrations_rejects_unsupported_versions() -> None:
    with pytest.raises(ValueError, match="negative"):
        pending_migrations(-1)
    with pytest.raises(RuntimeError, match="newer"):
        pending_migrations(LATEST_SCHEMA_VERSION + 1)


def test_initial_schema_contains_all_runtime_entities(database: sqlite3.Connection) -> None:
    objects = {
        (row[0], row[1])
        for row in database.execute(
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        )
    }

    expected_tables = {
        "schema_migrations",
        "workspaces",
        "sessions",
        "session_entries",
        "session_branches",
        "session_runs",
        "queued_messages",
        "chat_deliveries",
        "timeline_messages",
        "usage_records",
        "session_plans",
        "media_blobs",
        "media_items",
        "media_references",
        "extension_state",
        "audit_records",
    }
    assert {("table", name) for name in expected_tables} <= objects
    assert ("table", "search_fts") in objects


def test_structured_json_columns_require_json_valid_checks(
    database: sqlite3.Connection,
) -> None:
    table_sql = {
        str(row[0]): str(row[1])
        for row in database.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL"
        )
    }

    json_columns: list[tuple[str, str]] = []
    for table_name in table_sql:
        pragma_name = table_name.replace("'", "''")
        rows = database.execute(f"PRAGMA table_info('{pragma_name}')")
        json_columns.extend(
            (table_name, str(row[1])) for row in rows if str(row[1]).endswith("_json")
        )

    assert json_columns
    for table_name, column_name in json_columns:
        pattern = (
            rf"\b{re.escape(column_name)}\b[^,]*CHECK\("
            rf"(?:{re.escape(column_name)}\s+IS\s+NULL\s+OR\s+)?"
            rf"json_valid\({re.escape(column_name)}\)\)"
        )
        assert re.search(pattern, table_sql[table_name], flags=re.IGNORECASE | re.DOTALL), (
            f"{table_name}.{column_name} must enforce json_valid()"
        )


def test_active_session_aliases_are_case_insensitively_unique(
    database: sqlite3.Connection,
) -> None:
    _insert_workspace_and_session(database, agent_name="Review")

    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO sessions(
                session_id, workspace_id, agent_name, provider_name, model,
                created_at, updated_at
            ) VALUES ('session-2', 'workspace-1', 'review', 'test', 'model', 'now', 'now')
            """
        )

    database.execute("UPDATE sessions SET archived_at = 'now' WHERE session_id = 'session-1'")
    database.execute(
        """
        INSERT INTO sessions(
            session_id, workspace_id, agent_name, provider_name, model, created_at, updated_at
        ) VALUES ('session-2', 'workspace-1', 'review', 'test', 'model', 'now', 'now')
        """
    )


def test_entries_preserve_append_order_and_branch_edges(database: sqlite3.Connection) -> None:
    _insert_workspace_and_session(database)
    database.execute(
        """
        INSERT INTO session_entries(
            entry_id, session_id, parent_entry_id, entry_type, timestamp, ordinal, payload_json
        ) VALUES ('entry-1', 'session-1', NULL, 'session_info', 1.0, 0, '{}')
        """
    )
    database.execute(
        """
        INSERT INTO session_entries(
            entry_id, session_id, parent_entry_id, entry_type, timestamp, ordinal, payload_json
        ) VALUES ('entry-2', 'session-1', 'entry-1', 'message', 2.0, 1, '{}')
        """
    )
    database.execute(
        """
        INSERT INTO session_branches(
            branch_id, session_id, name, leaf_entry_id, created_at, updated_at
        ) VALUES ('branch-1', 'session-1', 'main', 'entry-2', 'now', 'now')
        """
    )
    database.execute(
        "UPDATE sessions SET active_leaf_entry_id = 'entry-2' WHERE session_id = 'session-1'"
    )

    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO session_entries(
                entry_id, session_id, entry_type, timestamp, ordinal, payload_json
            ) VALUES ('entry-3', 'session-1', 'message', 3.0, 1, '{}')
            """
        )


def test_queue_delivery_and_extension_constraints(database: sqlite3.Connection) -> None:
    _insert_workspace_and_session(database)

    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO queued_messages(
                queue_id, session_id, queue_kind, position, content_json, created_at
            ) VALUES ('queue-1', 'session-1', 'later', 0, '{}', 'now')
            """
        )

    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO extension_state(
                extension_id, scope, scope_id, key, value_json, updated_at
            ) VALUES ('test', 'invalid', 'x', 'key', '{}', 'now')
            """
        )

    database.execute(
        """
        INSERT INTO chat_deliveries(
            delivery_id, source_session_id, target_session_id, mode, content,
            idempotency_key, status, created_at
        ) VALUES ('delivery-1', 'session-1', 'session-1', 'queue', 'hello',
                  'same-key', 'accepted', 'now')
        """
    )
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO chat_deliveries(
                delivery_id, source_session_id, target_session_id, mode, content,
                idempotency_key, status, created_at
            ) VALUES ('delivery-2', 'session-1', 'session-1', 'queue', 'again',
                      'same-key', 'accepted', 'now')
            """
        )


def test_foreign_keys_reject_orphan_entries(database: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO session_entries(
                entry_id, session_id, entry_type, timestamp, ordinal, payload_json
            ) VALUES ('entry-1', 'missing', 'message', 1.0, 0, '{}')
            """
        )


@pytest.mark.anyio
async def test_fresh_database_reopen_is_migration_idempotent_without_prior_release(
    tmp_path: Path,
) -> None:
    assert len(MIGRATIONS) == 1
    assert LATEST_SCHEMA_VERSION == 1

    database_path = tmp_path / "tau.sqlite3"
    async with SqliteDatabase(database_path) as database:
        async def seed_runtime_rows(tx: SqliteTransaction) -> None:
            await tx.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES ('workspace-1', '/workspace', 'now', 'now')
                """
            )
            await tx.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, provider_name, model,
                    created_at, updated_at
                ) VALUES ('session-1', 'workspace-1', 'default', 'test', 'model', 'now', 'now')
                """
            )
            await tx.execute(
                """
                INSERT INTO session_entries(
                    entry_id, session_id, parent_entry_id, entry_type,
                    timestamp, ordinal, payload_json
                ) VALUES ('entry-1', 'session-1', NULL, 'message', 1.0, 0, '{"seed":true}')
                """
            )

        await database.write(seed_runtime_rows)

    async with SqliteDatabase(database_path) as database:
        async def inspect(reader: SqliteReader) -> None:
            version_row = await reader.fetch_one("PRAGMA user_version")
            assert version_row is not None
            assert int(version_row[0]) == LATEST_SCHEMA_VERSION

            migration_row = await reader.fetch_one(
                """
                SELECT count(*), count(DISTINCT version), count(DISTINCT name)
                FROM schema_migrations
                """
            )
            assert migration_row is not None
            migration_count, unique_versions, unique_names = (int(value) for value in migration_row)
            assert migration_count == len(MIGRATIONS)
            assert unique_versions == migration_count
            assert unique_names == migration_count

            workspace_row = await reader.fetch_one(
                "SELECT root_path FROM workspaces WHERE workspace_id = 'workspace-1'"
            )
            session_row = await reader.fetch_one(
                "SELECT workspace_id FROM sessions WHERE session_id = 'session-1'"
            )
            entry_row = await reader.fetch_one(
                "SELECT payload_json FROM session_entries WHERE entry_id = 'entry-1'"
            )
            assert workspace_row is not None
            assert str(workspace_row[0]) == "/workspace"
            assert session_row is not None
            assert str(session_row[0]) == "workspace-1"
            assert entry_row is not None
            assert str(entry_row[0]) == '{"seed":true}'

            assert await reader.fetch_all("PRAGMA foreign_key_check") == []
            integrity_rows = await reader.fetch_all("PRAGMA integrity_check")
            assert [str(row[0]) for row in integrity_rows] == ["ok"]

        await database.read(inspect)
