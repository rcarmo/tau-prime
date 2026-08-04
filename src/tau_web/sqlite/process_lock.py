"""Cross-process ownership lock for a Tau SQLite database."""

from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path
from typing import IO


class DatabaseLockedError(RuntimeError):
    """Raised when another Tau process owns the database writer role."""


class DatabaseProcessLock:
    """Hold a non-blocking advisory lock beside one database file."""

    def __init__(self, database_path: Path) -> None:
        self.path = database_path.with_name(f"{database_path.name}.lock")
        self._file: IO[str] | None = None

    @property
    def acquired(self) -> bool:
        return self._file is not None

    def acquire(self) -> None:
        if self._file is not None:
            return
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        file = self.path.open("a+", encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
            _lock_file(file)
            file.seek(0)
            file.truncate()
            file.write(f"pid={os.getpid()}\n")
            file.flush()
        except Exception:
            file.close()
            raise
        self._file = file

    def release(self) -> None:
        file = self._file
        if file is None:
            return
        self._file = None
        try:
            _unlock_file(file)
        finally:
            file.close()

    def __enter__(self) -> DatabaseProcessLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def _lock_file(file: IO[str]) -> None:
    if os.name == "nt":
        import msvcrt

        file.seek(0)
        if not file.read(1):
            file.seek(0)
            file.write("\0")
            file.flush()
        file.seek(0)
        try:
            msvcrt.locking(  # type: ignore[attr-defined]
                file.fileno(), msvcrt.LK_NBLCK, 1  # type: ignore[attr-defined]
            )
        except OSError as exc:
            raise DatabaseLockedError("Tau database is already open by another process") from exc
        return

    import fcntl

    try:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        raise DatabaseLockedError("Tau database is already open by another process") from exc


def _unlock_file(file: IO[str]) -> None:
    if os.name == "nt":
        import msvcrt

        file.seek(0)
        with suppress(OSError):
            msvcrt.locking(  # type: ignore[attr-defined]
                file.fileno(), msvcrt.LK_UNLCK, 1  # type: ignore[attr-defined]
            )
        return

    import fcntl

    fcntl.flock(file.fileno(), fcntl.LOCK_UN)
