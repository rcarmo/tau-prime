from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import create_app
from tau_web.baseline_extensions.meters import HostMetersSampler
from tau_web.config import WebConfig


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _write_proc_snapshot(
    proc_root: Path,
    *,
    stat: str,
    meminfo: str,
    status: str,
) -> None:
    (proc_root / "self").mkdir(parents=True, exist_ok=True)
    (proc_root / "stat").write_text(stat, encoding="utf-8")
    (proc_root / "meminfo").write_text(meminfo, encoding="utf-8")
    (proc_root / "self" / "status").write_text(status, encoding="utf-8")


@pytest.mark.anyio
async def test_meters_route_returns_initial_cached_snapshot(web_config: WebConfig) -> None:
    client = TestClient(TestServer(create_app(web_config)))
    await client.start_server()
    try:
        async with client.get("/meters") as response:
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            payload = await response.json()
    finally:
        await client.close()

    assert set(payload) == {
        "cpu_percent",
        "ram_percent",
        "swap_percent",
        "cpu_series",
        "ram_series",
        "swap_series",
        "process_rss_bytes",
        "process_rss_series_bytes",
        "sample_interval_ms",
        "platform",
    }
    assert payload["sample_interval_ms"] == 2_000
    assert len(payload["cpu_series"]) == 1
    assert len(payload["process_rss_series_bytes"]) == 1


@pytest.mark.anyio
async def test_host_meters_sampler_reads_proc_and_computes_cpu_deltas(tmp_path: Path) -> None:
    proc_root = tmp_path / "proc"
    _write_proc_snapshot(
        proc_root,
        stat="cpu  100 0 100 800 0 0 0 0 0 0\n",
        meminfo=(
            "MemTotal:        1000 kB\n"
            "MemAvailable:     250 kB\n"
            "SwapTotal:       1000 kB\n"
            "SwapFree:         500 kB\n"
        ),
        status="VmRSS:\t42 kB\n",
    )
    sampler = HostMetersSampler(proc_root=proc_root, platform="linux-test")

    first = await sampler.sample_once()

    assert first.cpu_percent is None
    assert first.ram_percent == 75.0
    assert first.swap_percent == 50.0
    assert first.process_rss_bytes == 42 * 1_024
    assert first.cpu_series == (None,)
    assert first.ram_series == (75.0,)
    assert first.swap_series == (50.0,)
    assert first.process_rss_series_bytes == (42 * 1_024,)
    assert first.sample_interval_ms == 2_000
    assert first.platform == "linux-test"

    _write_proc_snapshot(
        proc_root,
        stat="cpu  200 0 200 1300 0 0 0 0 0 0\n",
        meminfo=(
            "MemTotal:        1000 kB\n"
            "MemAvailable:     250 kB\n"
            "SwapTotal:       1000 kB\n"
            "SwapFree:         500 kB\n"
        ),
        status="VmRSS:\t84 kB\n",
    )

    second = await sampler.sample_once()

    assert second.cpu_percent == pytest.approx((200.0 / 700.0) * 100.0)
    assert second.ram_percent == 75.0
    assert second.swap_percent == 50.0
    assert second.process_rss_bytes == 84 * 1_024
    assert second.cpu_series == (None, pytest.approx((200.0 / 700.0) * 100.0))
    assert second.ram_series == (75.0, 75.0)
    assert second.swap_series == (50.0, 50.0)
    assert second.process_rss_series_bytes == (42 * 1_024, 84 * 1_024)


@pytest.mark.anyio
async def test_host_meters_sampler_bounds_series_and_uses_memfree_fallback(tmp_path: Path) -> None:
    proc_root = tmp_path / "proc"
    sampler = HostMetersSampler(proc_root=proc_root, max_points=3)

    for index in range(5):
        _write_proc_snapshot(
            proc_root,
            stat=(
                f"cpu  {100 + (100 * index)} 0 {100 + (100 * index)} {800 + (100 * index)} "
                "0 0 0 0 0 0\n"
            ),
            meminfo=(
                "MemTotal:        1000 kB\n"
                "MemFree:          100 kB\n"
                "Buffers:           50 kB\n"
                "Cached:           150 kB\n"
                "SwapTotal:          0 kB\n"
                "SwapFree:           0 kB\n"
            ),
            status=f"VmRSS:\t{index + 1} kB\n",
        )
        snapshot = await sampler.sample_once()

    assert snapshot.cpu_series == pytest.approx((200.0 / 300.0 * 100.0,) * 3)
    assert snapshot.ram_series == (70.0, 70.0, 70.0)
    assert snapshot.swap_series == (0.0, 0.0, 0.0)
    assert snapshot.process_rss_series_bytes == (3 * 1_024, 4 * 1_024, 5 * 1_024)
    assert len(snapshot.cpu_series) == 3
    assert len(snapshot.process_rss_series_bytes) == 3


class _FakePsutil:
    @staticmethod
    def cpu_percent(*, interval: float | None = None) -> float:
        assert interval is None
        return 120.0

    @staticmethod
    def virtual_memory() -> Any:
        return SimpleNamespace(percent=-1.0)

    @staticmethod
    def swap_memory() -> Any:
        return SimpleNamespace(percent=12.5)

    @staticmethod
    def Process() -> Any:
        return SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=2_048))


@pytest.mark.anyio
async def test_host_meters_sampler_uses_psutil_fallback_when_proc_is_unavailable(
    tmp_path: Path,
) -> None:
    sampler = HostMetersSampler(
        proc_root=tmp_path / "missing-proc",
        psutil_provider=lambda: _FakePsutil(),
    )

    snapshot = await sampler.sample_once()

    assert snapshot.cpu_percent == 100.0
    assert snapshot.ram_percent == 0.0
    assert snapshot.swap_percent == 12.5
    assert snapshot.process_rss_bytes == 2_048
    assert snapshot.cpu_series == (100.0,)
    assert snapshot.process_rss_series_bytes == (2_048,)


@pytest.mark.anyio
async def test_host_meters_sampler_survives_non_proc_sampling_failures(tmp_path: Path) -> None:
    sampler = HostMetersSampler(
        proc_root=tmp_path / "missing-proc",
        psutil_provider=lambda: None,
        loadavg_getter=lambda: (_ for _ in ()).throw(OSError("no loadavg")),
        resource_rss_getter=lambda: (_ for _ in ()).throw(RuntimeError("no rss")),
    )

    snapshot = await sampler.sample_once()

    assert snapshot.cpu_percent is None
    assert snapshot.ram_percent is None
    assert snapshot.swap_percent is None
    assert snapshot.process_rss_bytes is None
    assert snapshot.cpu_series == (None,)
    assert snapshot.ram_series == (None,)
    assert snapshot.swap_series == (None,)
    assert snapshot.process_rss_series_bytes == (None,)
