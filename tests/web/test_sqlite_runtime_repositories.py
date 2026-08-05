from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    DeliveryRepository,
    ExtensionStateRepository,
    MediaCleanupResult,
    MediaRepository,
    QueueRepository,
    RecordNotFoundError,
    RepositoryError,
    RevisionConflictError,
    RunRepository,
    SearchRepository,
    UsageRepository,
)
from tau_web.sqlite.writer import SqliteTransaction

_FUTURE = "9999-12-31T23:59:59+00:00"


async def _seed_sessions(database: SqliteDatabase) -> tuple[str, str]:
    async def seed(transaction: SqliteTransaction) -> None:
        await transaction.execute(
            """
            INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
            VALUES ('workspace', '/workspace', 'now', 'now')
            """
        )
        for session_id, agent_name in (("first", "first"), ("second", "second")):
            await transaction.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, provider_name, model,
                    created_at, updated_at
                ) VALUES (?, 'workspace', ?, 'test', 'model', 'now', 'now')
                """,
                (session_id, agent_name),
            )

    await database.write(seed)
    return "first", "second"


@pytest.mark.anyio
async def test_run_repository_lifecycle_and_retention(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, _ = await _seed_sessions(database)
        runs = RunRepository(database)

        created = await runs.create(first, run_id="run", last_status={"phase": "queued"})
        running = await runs.update_status(
            created.run_id,
            status="running",
            last_event_type="agent_start",
        )
        completed = await runs.update_status(running.run_id, status="completed")

        assert created.status == "pending"
        assert running.last_event_type == "agent_start"
        assert completed.ended_at is not None
        assert await runs.list(session_id=first, statuses=["completed"]) == [completed]
        with pytest.raises(RepositoryError, match="Terminal"):
            await runs.update_status(completed.run_id, status="running")
        assert await runs.purge_terminal_before(_FUTURE) == 1
        assert await runs.get("run") is None


@pytest.mark.anyio
async def test_queue_repository_orders_consumes_and_prunes(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        queue = QueueRepository(database)

        one = await queue.enqueue(
            first,
            queue_kind="follow_up",
            content={"text": "one"},
            source_session_id=second,
        )
        two = await queue.enqueue(first, queue_kind="follow_up", content={"text": "two"})

        assert (one.position, two.position) == (0, 1)
        consumed = await queue.consume_next(first, "follow_up")
        assert consumed is not None and consumed.queue_id == one.queue_id
        assert await queue.list(session_id=first) == [two]
        assert len(await queue.list(session_id=first, include_consumed=True)) == 2
        assert await queue.purge_consumed_before(_FUTURE) == 1


@pytest.mark.anyio
async def test_queue_repository_consume_exact_is_fifo_and_validates_identity(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        queue = QueueRepository(database)

        one = await queue.enqueue(first, queue_kind="follow_up", content={"text": "one"})
        two = await queue.enqueue(first, queue_kind="follow_up", content={"text": "two"})
        other = await queue.enqueue(second, queue_kind="follow_up", content={"text": "other"})

        with pytest.raises(RepositoryError, match="next FIFO row"):
            await queue.consume_exact(two.queue_id, session_id=first, queue_kind="follow_up")
        with pytest.raises(RepositoryError, match="does not belong"):
            await queue.consume_exact(other.queue_id, session_id=first, queue_kind="follow_up")

        consumed = await queue.consume_exact(
            one.queue_id,
            session_id=first,
            queue_kind="follow_up",
        )

        assert consumed.queue_id == one.queue_id
        assert consumed.consumed_at is not None
        assert [record.queue_id for record in await queue.list(session_id=first)] == [two.queue_id]
        with pytest.raises(RepositoryError, match="already been consumed"):
            await queue.consume_exact(one.queue_id, session_id=first, queue_kind="follow_up")


@pytest.mark.anyio
async def test_database_reopen_recovers_run_and_preserves_fifo_queue_and_pending_delivery(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "tau.sqlite3"

    async with SqliteDatabase(database_path) as database:
        first, second = await _seed_sessions(database)
        runs = RunRepository(database)
        queue = QueueRepository(database)
        deliveries = DeliveryRepository(database)

        await runs.create(first, run_id="run", status="running", last_status={"phase": "running"})
        one = await queue.enqueue(first, queue_kind="follow_up", content={"text": "one"})
        two = await queue.enqueue(first, queue_kind="follow_up", content={"text": "two"})
        delivery = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            target_address="@second",
            mode="queue",
            content="pending delivery",
        )

    async with SqliteDatabase(database_path) as database:
        runs = RunRepository(database)
        queue = QueueRepository(database)
        deliveries = DeliveryRepository(database)

        assert database.recovered_run_count == 1

        recovered_run = await runs.get("run")
        assert recovered_run is not None
        assert recovered_run.status == "interrupted"
        assert recovered_run.ended_at is not None
        assert recovered_run.error is not None

        queued = await queue.list(session_id=first, queue_kind="follow_up")
        assert [record.queue_id for record in queued] == [one.queue_id, two.queue_id]

        with pytest.raises(RepositoryError, match="next FIFO row"):
            await queue.consume_exact(two.queue_id, session_id=first, queue_kind="follow_up")

        consumed_one = await queue.consume_exact(
            one.queue_id,
            session_id=first,
            queue_kind="follow_up",
        )
        consumed_two = await queue.consume_exact(
            two.queue_id,
            session_id=first,
            queue_kind="follow_up",
        )

        assert (consumed_one.queue_id, consumed_two.queue_id) == (one.queue_id, two.queue_id)

        pending_delivery = await deliveries.get(delivery.delivery_id)
        assert pending_delivery is not None
        assert pending_delivery.status == "pending"
        assert pending_delivery.accepted_at is None
        assert pending_delivery.completed_at is None
        assert pending_delivery.error is None


@pytest.mark.anyio
async def test_delivery_repository_is_idempotent_and_tracks_receipts(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        deliveries = DeliveryRepository(database)

        parent = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            target_address="@second",
            mode="queue",
            content="hello",
        )
        created = await deliveries.create(
            source_session_id=second,
            target_session_id=first,
            target_address="@first",
            mode="queue",
            content="reply",
            idempotency_key="stable",
            in_reply_to=parent.delivery_id,
            ancestry=[parent.delivery_id],
            hop_count=1,
        )
        duplicate = await deliveries.create(
            source_session_id=second,
            target_session_id=first,
            mode="queue",
            content="ignored",
            idempotency_key="stable",
        )
        completed = await deliveries.update_status(created.delivery_id, status="completed")

        assert duplicate == created
        assert await deliveries.find_by_idempotency("local", "stable") == completed
        assert completed.accepted_at is not None
        assert completed.completed_at is not None
        assert completed.in_reply_to == parent.delivery_id
        assert completed.ancestry == (parent.delivery_id,)
        with pytest.raises(RepositoryError, match="Terminal"):
            await deliveries.update_status(created.delivery_id, status="pending")
        assert await deliveries.purge_terminal_before(_FUTURE) == 1


@pytest.mark.anyio
async def test_delivery_repository_create_validates_reply_lineage_and_source(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        deliveries = DeliveryRepository(database)

        root = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            target_address="@second",
            mode="queue",
            content="hello",
        )
        reply = await deliveries.create(
            source_session_id=second,
            target_session_id=first,
            target_address="@first",
            mode="queue",
            content="reply",
            in_reply_to=root.delivery_id,
            ancestry=[root.delivery_id],
            hop_count=1,
        )

        assert reply.in_reply_to == root.delivery_id
        assert reply.ancestry == (root.delivery_id,)
        assert reply.hop_count == 1

        with pytest.raises(ValueError, match="Reply source session must match"):
            await deliveries.create(
                source_session_id=first,
                target_session_id=second,
                mode="queue",
                content="wrong source",
                in_reply_to=root.delivery_id,
                ancestry=[root.delivery_id],
                hop_count=1,
            )
        with pytest.raises(ValueError, match="Reply ancestry delivery does not exist"):
            await deliveries.create(
                source_session_id=second,
                target_session_id=first,
                mode="queue",
                content="missing ancestor",
                in_reply_to=root.delivery_id,
                ancestry=["missing"],
                hop_count=1,
            )
        with pytest.raises(ValueError, match="Reply ancestry chain is malformed"):
            await deliveries.create(
                source_session_id=first,
                target_session_id=second,
                mode="queue",
                content="malformed chain",
                in_reply_to=reply.delivery_id,
                ancestry=[reply.delivery_id],
                hop_count=1,
            )
        with pytest.raises(ValueError, match="Hop count must equal ancestry length"):
            await deliveries.create(
                source_session_id=second,
                target_session_id=first,
                mode="queue",
                content="wrong hops",
                in_reply_to=root.delivery_id,
                ancestry=[root.delivery_id],
                hop_count=2,
            )


@pytest.mark.anyio
async def test_delivery_repository_find_by_idempotency_validates_and_scopes_transport(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        deliveries = DeliveryRepository(database)

        local = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            target_address="@second",
            mode="queue",
            content="hello",
            idempotency_key="stable",
        )
        remote = await deliveries.create(
            source_session_id=first,
            target_address="xmpp!@second",
            transport="xmpp",
            mode="queue",
            content="remote",
            idempotency_key="stable",
        )

        assert await deliveries.find_by_idempotency(" local ", " stable ") == local
        assert await deliveries.find_by_idempotency("xmpp", "stable") == remote
        assert await deliveries.find_by_idempotency("local", "missing") is None

        with pytest.raises(ValueError, match="Transport must not be empty"):
            await deliveries.find_by_idempotency(" ", "stable")
        with pytest.raises(ValueError, match="Idempotency key must not be empty"):
            await deliveries.find_by_idempotency("local", " ")


@pytest.mark.anyio
async def test_delivery_repository_resolve_target_rules(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, second = await _seed_sessions(database)
        deliveries = DeliveryRepository(database)

        unresolved = await deliveries.create(
            source_session_id=first,
            target_address="@second",
            mode="queue",
            content="needs resolution",
        )
        resolved = await deliveries.resolve_target(unresolved.delivery_id, second)

        assert resolved.target_session_id == second
        assert resolved.target_address == "@second"

        terminal_same_target = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            mode="queue",
            content="done",
            status="completed",
        )
        assert (
            await deliveries.resolve_target(terminal_same_target.delivery_id, second)
            == terminal_same_target
        )

        replacement = await deliveries.create(
            source_session_id=first,
            target_session_id=second,
            mode="queue",
            content="replacement",
        )
        with pytest.raises(RepositoryError, match="already been resolved"):
            await deliveries.resolve_target(replacement.delivery_id, first)

        with pytest.raises(RecordNotFoundError, match="Unknown delivery"):
            await deliveries.resolve_target("missing", second)

        missing_target = await deliveries.create(
            source_session_id=first,
            target_address="@missing",
            mode="queue",
            content="missing target",
        )
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            await deliveries.resolve_target(missing_target.delivery_id, "missing")

        terminal_unresolved = await deliveries.create(
            source_session_id=first,
            target_address="@second",
            mode="queue",
            content="terminal unresolved",
            status="completed",
        )
        with pytest.raises(RepositoryError, match="Terminal"):
            await deliveries.resolve_target(terminal_unresolved.delivery_id, second)


@pytest.mark.anyio
async def test_usage_repository_preserves_details_and_retention(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, _ = await _seed_sessions(database)
        usage = UsageRepository(database)

        recorded = await usage.record(
            first,
            provider_name="provider",
            model="model",
            input_tokens=10,
            output_tokens=4,
            cached_input_tokens=2,
            cost_microunits=25,
            details={"cache": True},
        )

        assert recorded.details == {"cache": True}
        assert await usage.list(session_id=first) == [recorded]
        with pytest.raises(ValueError, match="negative"):
            await usage.record(
                first,
                provider_name="provider",
                model="model",
                input_tokens=-1,
            )
        assert await usage.purge_before(_FUTURE) == 1


@pytest.mark.anyio
async def test_media_repository_deduplicates_and_cleans_unreferenced_blobs(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, _ = await _seed_sessions(database)
        media = MediaRepository(database)

        blob = await media.store_blob(b"same bytes", blob_id="blob")
        duplicate = await media.store_blob(b"same bytes", blob_id="ignored")
        item = await media.create_item(
            blob_id=blob.blob_id,
            session_id=first,
            filename="note.txt",
            media_type="text/plain",
            metadata={"origin": "test"},
        )
        reference = await media.add_reference(item.media_id, "message", "message-1")
        repeated = await media.add_reference(item.media_id, "message", "message-1")

        assert duplicate == blob
        assert repeated == reference
        assert await media.list_references(item.media_id) == [reference]
        assert (await media.mark_deleted(item.media_id)).deleted_at is not None
        assert await media.purge_deleted_before(_FUTURE) == MediaCleanupResult(
            items_deleted=1,
            blobs_deleted=1,
        )
        assert await media.get_blob(blob.blob_id) is None


@pytest.mark.anyio
async def test_extension_state_uses_revisions_and_connection_policy(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_sessions(database)
        state = ExtensionStateRepository(database)

        created = await state.save(
            "extension",
            scope="session",
            scope_id="first",
            key="setting",
            value={"enabled": True},
            expected_revision=None,
        )
        updated = await state.save(
            "extension",
            scope="session",
            scope_id="first",
            key="setting",
            value={"enabled": False},
            expected_revision=created.revision,
        )

        assert updated.revision == 2
        assert await state.get("extension", "session", "first", "setting") == updated
        with pytest.raises(RevisionConflictError):
            await state.save(
                "extension",
                scope="session",
                scope_id="first",
                key="setting",
                value=None,
                expected_revision=1,
            )
        with pytest.raises(RepositoryError, match="connection-scope"):
            await state.list_scope("connection", "browser")
        assert (
            await state.delete(
                "extension",
                scope="session",
                scope_id="first",
                key="setting",
                expected_revision=2,
            )
            == updated
        )

        connection_state = ExtensionStateRepository(
            database,
            allow_persisted_connection_scope=True,
        )
        await connection_state.save(
            "extension",
            scope="connection",
            scope_id="browser",
            key="temporary",
            value=1,
            expected_revision=0,
        )
        assert await connection_state.purge_connection_scope_before(_FUTURE) == 1


@pytest.mark.anyio
async def test_audit_repository_is_append_only_and_prunable(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, _ = await _seed_sessions(database)
        audits = AuditRepository(database)

        record = await audits.append(
            event_type="session.created",
            actor_type="user",
            workspace_id="workspace",
            session_id=first,
            details={"safe": True},
        )

        assert await audits.list(session_id=first) == [record]
        assert await audits.purge_before(_FUTURE) == 1
        assert await audits.list() == []


@pytest.mark.anyio
async def test_search_repository_updates_filters_and_removes_stale_rows(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        first, _ = await _seed_sessions(database)
        search = SearchRepository(database)

        await search.upsert(
            entity_type="message",
            entity_id="one",
            session_id=first,
            text="hello durable world",
        )
        assert [result.entity_id for result in await search.search("durable")] == ["one"]
        assert await search.search("durable", session_id="second") == []

        await search.upsert(
            entity_type="message",
            entity_id="one",
            session_id=first,
            text="replacement text",
        )
        assert await search.search("durable") == []
        assert await search.remove("message", "one") == 1

        await search.upsert(
            entity_type="session",
            entity_id="stale",
            session_id=first,
            text="stale session",
        )

        async def remove_session(transaction: SqliteTransaction) -> None:
            await transaction.execute("DELETE FROM sessions WHERE session_id = ?", (first,))

        await database.write(remove_session)
        assert await search.purge_missing_sessions() == 1
