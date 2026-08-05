"""Host-wide baseline meters sampler for Tau Web."""

from __future__ import annotations

import asyncio
import os
import sys
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, cast

from tau_agent.types import JSONObject
from tau_web.events import build_invalidation_envelope
from tau_web.sse import GLOBAL_EVENT_SESSION_ID, EventBroker

DEFAULT_SAMPLE_INTERVAL_MS = 2_000
DEFAULT_SERIES_POINTS = 30
METERS_EVENT_TYPE = "tau.meters.updated"


@dataclass(frozen=True, slots=True)
class MeterSnapshot:
    cpu_percent: float | None
    ram_percent: float | None
    swap_percent: float | None
    cpu_series: tuple[float | None, ...]
    ram_series: tuple[float | None, ...]
    swap_series: tuple[float | None, ...]
    process_rss_bytes: int | None
    process_rss_series_bytes: tuple[int | None, ...]
    sample_interval_ms: int
    platform: str

    def to_payload(self) -> JSONObject:
        return cast(
            JSONObject,
            {
                "cpu_percent": self.cpu_percent,
                "ram_percent": self.ram_percent,
                "swap_percent": self.swap_percent,
                "cpu_series": list(self.cpu_series),
                "ram_series": list(self.ram_series),
                "swap_series": list(self.swap_series),
                "process_rss_bytes": self.process_rss_bytes,
                "process_rss_series_bytes": list(self.process_rss_series_bytes),
                "sample_interval_ms": self.sample_interval_ms,
                "platform": self.platform,
            },
        )


@dataclass(frozen=True, slots=True)
class _MeterSample:
    cpu_percent: float | None
    ram_percent: float | None
    swap_percent: float | None
    process_rss_bytes: int | None


@dataclass(frozen=True, slots=True)
class _ProcCpuTimes:
    total_ticks: int
    idle_ticks: int


@dataclass(frozen=True, slots=True)
class _ProcMemInfo:
    mem_total_bytes: int | None
    mem_available_bytes: int | None
    mem_free_bytes: int | None
    buffers_bytes: int | None
    cached_bytes: int | None
    swap_total_bytes: int | None
    swap_free_bytes: int | None


class HostMetersSampler:
    """Cache and publish one shared host metrics snapshot for all browsers."""

    def __init__(
        self,
        *,
        broker: EventBroker | None = None,
        sample_interval_ms: int = DEFAULT_SAMPLE_INTERVAL_MS,
        max_points: int = DEFAULT_SERIES_POINTS,
        proc_root: Path = Path("/proc"),
        proc_reader: Callable[[Path], str] | None = None,
        psutil_provider: Callable[[], Any | None] | None = None,
        loadavg_getter: Callable[[], tuple[float, float, float]] | None = None,
        cpu_count_getter: Callable[[], int | None] = os.cpu_count,
        resource_rss_getter: Callable[[], int | None] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        platform: str | None = None,
        collector: Callable[[], _MeterSample] | None = None,
    ) -> None:
        if sample_interval_ms <= 0:
            raise ValueError("sample_interval_ms must be positive")
        if max_points < 1:
            raise ValueError("max_points must be at least 1")

        self._broker = broker
        self._sample_interval_ms = sample_interval_ms
        self._max_points = max_points
        self._proc_root = proc_root
        self._proc_reader = proc_reader or _default_proc_reader
        self._psutil_provider = psutil_provider or _default_psutil_provider
        self._loadavg_getter = (
            loadavg_getter if loadavg_getter is not None else getattr(os, "getloadavg", None)
        )
        self._cpu_count_getter = cpu_count_getter
        self._resource_rss_getter = resource_rss_getter or (
            lambda: _default_resource_rss_bytes(self._platform)
        )
        self._sleep = sleep
        self._platform = platform or sys.platform
        self._collector = collector
        self._cpu_times: _ProcCpuTimes | None = None
        self._cpu_series: deque[float | None] = deque(maxlen=max_points)
        self._ram_series: deque[float | None] = deque(maxlen=max_points)
        self._swap_series: deque[float | None] = deque(maxlen=max_points)
        self._rss_series: deque[int | None] = deque(maxlen=max_points)
        self._task: asyncio.Task[None] | None = None
        self._snapshot = MeterSnapshot(
            cpu_percent=None,
            ram_percent=None,
            swap_percent=None,
            cpu_series=(),
            ram_series=(),
            swap_series=(),
            process_rss_bytes=None,
            process_rss_series_bytes=(),
            sample_interval_ms=sample_interval_ms,
            platform=self._platform,
        )

    @property
    def snapshot(self) -> MeterSnapshot:
        return self._snapshot

    async def open(self) -> None:
        if self._task is not None:
            return
        await self.sample_once()
        self._task = asyncio.create_task(self._run(), name="tau-web-meters")

    async def close(self) -> None:
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def sample_once(self, *, publish: bool = False) -> MeterSnapshot:
        try:
            sample = self._collect_sample()
        except Exception:
            sample = _MeterSample(
                cpu_percent=None,
                ram_percent=None,
                swap_percent=None,
                process_rss_bytes=None,
            )

        snapshot = self._record_sample(sample)
        self._snapshot = snapshot
        if publish and self._broker is not None:
            await self._publish(snapshot)
        return snapshot

    def _collect_sample(self) -> _MeterSample:
        if self._collector is not None:
            return self._collector()
        if self._proc_root.is_dir():
            return self._collect_proc_sample()
        return self._collect_fallback_sample()

    def _collect_proc_sample(self) -> _MeterSample:
        return _MeterSample(
            cpu_percent=_suppress_sampling_error(self._sample_proc_cpu_percent),
            ram_percent=_suppress_sampling_error(self._sample_proc_ram_percent),
            swap_percent=_suppress_sampling_error(self._sample_proc_swap_percent),
            process_rss_bytes=_suppress_sampling_error(self._sample_proc_rss_bytes),
        )

    def _collect_fallback_sample(self) -> _MeterSample:
        psutil = _suppress_sampling_error(self._psutil_provider)
        cpu_percent: float | None = None
        ram_percent: float | None = None
        swap_percent: float | None = None
        process_rss_bytes: int | None = None

        if psutil is not None:
            cpu_percent = _suppress_sampling_error(lambda: _psutil_cpu_percent(psutil))
            ram_percent = _suppress_sampling_error(lambda: _psutil_virtual_memory_percent(psutil))
            swap_percent = _suppress_sampling_error(lambda: _psutil_swap_percent(psutil))
            process_rss_bytes = _suppress_sampling_error(lambda: _psutil_process_rss_bytes(psutil))

        if cpu_percent is None and self._loadavg_getter is not None:
            cpu_percent = _suppress_sampling_error(self._sample_loadavg_cpu_percent)
        if process_rss_bytes is None:
            process_rss_bytes = _suppress_sampling_error(self._resource_rss_getter)

        return _MeterSample(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            swap_percent=swap_percent,
            process_rss_bytes=process_rss_bytes,
        )

    def _sample_proc_cpu_percent(self) -> float | None:
        current = _parse_proc_cpu_times(self._proc_reader(self._proc_root / "stat"))
        previous = self._cpu_times
        self._cpu_times = current
        if previous is None:
            return None
        total_delta = current.total_ticks - previous.total_ticks
        idle_delta = current.idle_ticks - previous.idle_ticks
        if total_delta <= 0 or idle_delta < 0:
            return None
        busy_delta = max(total_delta - idle_delta, 0)
        return _normalize_percent(busy_delta * 100.0 / total_delta)

    def _sample_proc_ram_percent(self) -> float | None:
        return _ram_percent(_parse_proc_meminfo(self._proc_reader(self._proc_root / "meminfo")))

    def _sample_proc_swap_percent(self) -> float | None:
        return _swap_percent(_parse_proc_meminfo(self._proc_reader(self._proc_root / "meminfo")))

    def _sample_proc_rss_bytes(self) -> int | None:
        return _normalize_bytes(
            _parse_proc_status_rss_bytes(self._proc_reader(self._proc_root / "self" / "status"))
        )

    def _sample_loadavg_cpu_percent(self) -> float | None:
        if self._loadavg_getter is None:
            return None
        cpu_count = self._cpu_count_getter()
        if cpu_count is None or cpu_count <= 0:
            return None
        load1, _, _ = self._loadavg_getter()
        return _normalize_percent((load1 / cpu_count) * 100.0)

    def _record_sample(self, sample: _MeterSample) -> MeterSnapshot:
        cpu_percent = _normalize_percent(sample.cpu_percent)
        ram_percent = _normalize_percent(sample.ram_percent)
        swap_percent = _normalize_percent(sample.swap_percent)
        process_rss_bytes = _normalize_bytes(sample.process_rss_bytes)
        self._cpu_series.append(cpu_percent)
        self._ram_series.append(ram_percent)
        self._swap_series.append(swap_percent)
        self._rss_series.append(process_rss_bytes)
        return MeterSnapshot(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            swap_percent=swap_percent,
            cpu_series=tuple(self._cpu_series),
            ram_series=tuple(self._ram_series),
            swap_series=tuple(self._swap_series),
            process_rss_bytes=process_rss_bytes,
            process_rss_series_bytes=tuple(self._rss_series),
            sample_interval_ms=self._sample_interval_ms,
            platform=self._platform,
        )

    async def _publish(self, snapshot: MeterSnapshot) -> None:
        assert self._broker is not None
        try:
            await self._broker.publish(
                build_invalidation_envelope(
                    event_type=METERS_EVENT_TYPE,
                    session_id=GLOBAL_EVENT_SESSION_ID,
                    payload=snapshot.to_payload(),
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return

    async def _run(self) -> None:
        while True:
            await self._sleep(self._sample_interval_ms / 1_000.0)
            await self.sample_once(publish=True)


def _default_proc_reader(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _default_psutil_provider() -> Any | None:
    try:
        import psutil  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        return None
    return psutil


def _default_resource_rss_bytes(platform: str) -> int | None:
    try:
        import resource
    except ModuleNotFoundError:
        return None

    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = getattr(usage, "ru_maxrss", None)
    if isinstance(rss, bool) or not isinstance(rss, int | float):
        return None
    value = int(rss)
    if value < 0:
        return None
    if platform.startswith("darwin"):
        return value
    return value * 1_024


def _parse_proc_cpu_times(text: str) -> _ProcCpuTimes:
    for line in text.splitlines():
        if not line.startswith("cpu "):
            continue
        parts = line.split()
        if len(parts) < 5:
            break
        values = [int(part) for part in parts[1:9]]
        while len(values) < 8:
            values.append(0)
        idle_ticks = values[3] + values[4]
        total_ticks = sum(values[:8])
        return _ProcCpuTimes(total_ticks=total_ticks, idle_ticks=idle_ticks)
    raise ValueError("/proc/stat does not contain a usable aggregate cpu line")


def _parse_proc_meminfo(text: str) -> _ProcMemInfo:
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, separator, remainder = line.partition(":")
        if not separator:
            continue
        tokens = remainder.strip().split()
        if not tokens:
            continue
        raw_value = int(tokens[0])
        unit = tokens[1] if len(tokens) > 1 else "kB"
        multiplier = 1_024 if unit == "kB" else 1
        values[key] = raw_value * multiplier
    return _ProcMemInfo(
        mem_total_bytes=values.get("MemTotal"),
        mem_available_bytes=values.get("MemAvailable"),
        mem_free_bytes=values.get("MemFree"),
        buffers_bytes=values.get("Buffers"),
        cached_bytes=values.get("Cached"),
        swap_total_bytes=values.get("SwapTotal"),
        swap_free_bytes=values.get("SwapFree"),
    )


def _parse_proc_status_rss_bytes(text: str) -> int | None:
    for line in text.splitlines():
        if not line.startswith("VmRSS:"):
            continue
        tokens = line.split()
        if len(tokens) < 2:
            return None
        value = int(tokens[1])
        unit = tokens[2] if len(tokens) > 2 else "kB"
        if unit == "kB":
            return value * 1_024
        return value
    return None


def _ram_percent(meminfo: _ProcMemInfo) -> float | None:
    total = meminfo.mem_total_bytes
    if total is None or total <= 0:
        return None
    available = meminfo.mem_available_bytes
    if available is None:
        fallback_components = (
            meminfo.mem_free_bytes,
            meminfo.buffers_bytes,
            meminfo.cached_bytes,
        )
        if any(component is None for component in fallback_components):
            return None
        available = sum(cast(tuple[int, int, int], fallback_components))
    used = total - available
    return _normalize_percent((used / total) * 100.0)


def _swap_percent(meminfo: _ProcMemInfo) -> float | None:
    total = meminfo.swap_total_bytes
    free = meminfo.swap_free_bytes
    if total is None or total < 0:
        return None
    if total == 0:
        return 0.0
    if free is None:
        return None
    used = total - free
    return _normalize_percent((used / total) * 100.0)


def _psutil_cpu_percent(psutil: Any) -> float | None:
    return _normalize_percent(psutil.cpu_percent(interval=None))


def _psutil_virtual_memory_percent(psutil: Any) -> float | None:
    return _normalize_percent(getattr(psutil.virtual_memory(), "percent", None))


def _psutil_swap_percent(psutil: Any) -> float | None:
    return _normalize_percent(getattr(psutil.swap_memory(), "percent", None))


def _psutil_process_rss_bytes(psutil: Any) -> int | None:
    return _normalize_bytes(psutil.Process().memory_info().rss)


def _normalize_percent(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    percent = float(value)
    if not isfinite(percent):
        return None
    return min(100.0, max(0.0, percent))


def _normalize_bytes(value: object) -> int | None:
    if value is None or isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if not isfinite(float(value)):
        return None
    normalized = int(value)
    if normalized < 0:
        return None
    return normalized


def _suppress_sampling_error[T](callback: Callable[[], T]) -> T | None:
    try:
        return callback()
    except Exception:
        return None


__all__ = [
    "DEFAULT_SAMPLE_INTERVAL_MS",
    "DEFAULT_SERIES_POINTS",
    "HostMetersSampler",
    "METERS_EVENT_TYPE",
    "MeterSnapshot",
]
