from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from tau_extensions import (
    ActivationPlan,
    Candidate,
    ContributionRegistry,
    DisposalHandle,
    ExtensionDefinition,
    ExtensionHost,
    ExtensionManifest,
    ExtensionRegistrar,
    ExtensionSource,
    RegistryError,
    ResolutionDecision,
)


class TrackingDisposable:
    def __init__(self, name: str, sink: list[str]) -> None:
        self.name = name
        self.sink = sink
        self.calls = 0

    def dispose(self) -> None:
        self.calls += 1
        self.sink.append(f"dispose:{self.name}")


def _candidate(
    tmp_path: Path,
    extension_id: str,
    *,
    fingerprint: str | None = None,
) -> Candidate:
    manifest = ExtensionManifest.model_validate(
        {
            "schema_version": 1,
            "id": extension_id,
            "name": extension_id,
            "version": "1.0.0",
            "api_version": "^1.0",
            "entrypoint": "demo.extension:setup",
            "permissions": ["views"],
            "dependencies": [],
            "contributions": {},
        }
    )
    return Candidate(
        manifest=manifest,
        path=tmp_path / extension_id.replace(".", "-"),
        source=ExtensionSource.BUILT_IN,
        fingerprint=fingerprint or extension_id,
    )


def _plan(candidates: Sequence[Candidate]) -> ActivationPlan:
    return ActivationPlan(
        ordered_candidates=tuple(candidates),
        decisions=tuple(
            ResolutionDecision(
                candidate=candidate,
                enabled=True,
                code="enabled",
                reason="enabled for test",
            )
            for candidate in candidates
        ),
        diagnostics=(),
    )


def test_contribution_registry_orders_values_and_disposal_is_idempotent() -> None:
    disposed: list[str] = []
    handle = DisposalHandle(lambda: disposed.append("direct"))

    handle.dispose()
    handle.dispose()

    assert disposed == ["direct"]
    assert handle.disposed is True

    registry = ContributionRegistry({"com.example.beta": 1, "com.example.alpha": 0})
    beta_handle = registry.register("com.example.beta", "views", "beta", "beta")
    alpha_handle = registry.register("com.example.alpha", "views", "alpha", "alpha")
    registry.register("com.example.alpha", "views", "late", "late", order=1)

    assert registry.values("views") == ("alpha", "beta", "late")

    alpha_handle.dispose()
    alpha_handle.dispose()
    assert registry.values("views") == ("beta", "late")

    registry.dispose_extension("com.example.alpha")
    registry.dispose_extension("com.example.alpha")
    assert registry.values("views") == ("beta",)

    beta_handle.dispose()
    assert registry.values("views") == ()


@pytest.mark.parametrize(
    ("point", "key", "message"),
    [
        ("", "valid", "point"),
        ("valid", "bad key", "key"),
    ],
)
def test_contribution_registry_rejects_invalid_names(
    point: str,
    key: str,
    message: str,
) -> None:
    registry = ContributionRegistry()

    with pytest.raises(RegistryError, match=message):
        registry.register("com.example.demo", point, key, object())


def test_contribution_registry_rejects_duplicate_point_and_key() -> None:
    registry = ContributionRegistry()
    registry.register("com.example.one", "views", "shared", "first")

    with pytest.raises(RegistryError, match="duplicate contribution"):
        registry.register("com.example.two", "views", "shared", "second")


def test_extension_host_cleans_up_partial_setup_failure(tmp_path: Path) -> None:
    first = _candidate(tmp_path, "com.example.first")
    second = _candidate(tmp_path, "com.example.second")
    events: list[str] = []

    def first_setup(registrar: ExtensionRegistrar) -> list[object]:
        return [
            registrar.contribute("views", "shared", "first"),
            registrar.on("tick", lambda value: events.append(f"first:{value}")),
        ]

    def second_setup(registrar: ExtensionRegistrar) -> None:
        registrar.contribute("views", "temporary", "temp")
        registrar.on("tick", lambda value: events.append(f"second:{value}"))
        registrar.contribute("views", "shared", "duplicate")

    definitions = {
        first.manifest.id: ExtensionDefinition(setup=first_setup),
        second.manifest.id: ExtensionDefinition(setup=second_setup),
    }
    host = ExtensionHost(
        _plan([first, second]),
        lambda candidate: definitions[candidate.manifest.id],
    )

    host.activate_all()
    host.emit("tick", "go")

    assert host.contribution_registry.values("views") == ("first",)
    assert events == ["first:go"]
    assert host.statuses[first.manifest.id] == "active"
    assert host.statuses[second.manifest.id] == "failed"
    assert any(
        diagnostic.extension_id == second.manifest.id
        and diagnostic.phase == "setup"
        and "duplicate contribution" in diagnostic.message
        for diagnostic in host.diagnostics
    )


def test_extension_host_isolates_load_and_activate_failures(tmp_path: Path) -> None:
    bad_load = _candidate(tmp_path, "com.example.bad-load")
    bad_activate = _candidate(tmp_path, "com.example.bad-activate")
    good = _candidate(tmp_path, "com.example.good")
    trace: list[str] = []

    def loader(candidate: Candidate) -> ExtensionDefinition:
        if candidate.manifest.id == bad_load.manifest.id:
            raise RuntimeError("load boom")
        if candidate.manifest.id == bad_activate.manifest.id:
            return ExtensionDefinition(
                setup=lambda registrar: registrar.contribute("views", "activate-temp", "temp"),
                activate=lambda: (_ for _ in ()).throw(RuntimeError("activate boom")),
            )
        return ExtensionDefinition(
            setup=lambda registrar: [
                registrar.contribute("views", "good", "good"),
                registrar.on("ping", lambda: trace.append("good:ping")),
            ],
            activate=lambda: trace.append("good:activate"),
        )

    host = ExtensionHost(_plan([bad_load, bad_activate, good]), loader)

    host.activate_all()
    host.emit("ping")

    assert host.contribution_registry.values("views") == ("good",)
    assert trace == ["good:activate", "good:ping"]
    assert host.statuses[bad_load.manifest.id] == "failed"
    assert host.statuses[bad_activate.manifest.id] == "failed"
    assert host.statuses[good.manifest.id] == "active"
    assert [(diagnostic.extension_id, diagnostic.phase) for diagnostic in host.diagnostics] == [
        (bad_load.manifest.id, "load"),
        (bad_activate.manifest.id, "activate"),
    ]


def test_extension_host_emits_events_deterministically_and_isolates_failures(
    tmp_path: Path,
) -> None:
    alpha = _candidate(tmp_path, "com.example.alpha")
    beta = _candidate(tmp_path, "com.example.beta")
    seen: list[str] = []

    def alpha_setup(registrar: ExtensionRegistrar) -> None:
        registrar.on("tick", lambda value: seen.append(f"alpha:one:{value}"))

        def broken(value: object) -> None:
            seen.append(f"alpha:two:{value}")
            raise RuntimeError("tick boom")

        registrar.on("tick", broken)

    def beta_setup(registrar: ExtensionRegistrar) -> None:
        registrar.on("tick", lambda value: seen.append(f"beta:{value}"))

    host = ExtensionHost(
        _plan([alpha, beta]),
        lambda candidate: ExtensionDefinition(
            setup=alpha_setup if candidate.manifest.id == alpha.manifest.id else beta_setup
        ),
    )

    host.activate_all()
    host.emit("tick", 3)

    assert seen == ["alpha:one:3", "alpha:two:3", "beta:3"]
    assert len(host.diagnostics) == 1
    assert host.diagnostics[0].extension_id == alpha.manifest.id
    assert host.diagnostics[0].phase == "event:tick"
    assert "tick boom" in host.diagnostics[0].message


def test_extension_host_deactivates_in_reverse_order_and_owns_setup_handles(
    tmp_path: Path,
) -> None:
    alpha = _candidate(tmp_path, "com.example.alpha")
    beta = _candidate(tmp_path, "com.example.beta")
    gamma = _candidate(tmp_path, "com.example.gamma")
    trace: list[str] = []
    disposables: dict[str, TrackingDisposable] = {}

    def build_definition(extension_id: str) -> ExtensionDefinition:
        def setup(registrar: ExtensionRegistrar) -> list[object]:
            registrar.contribute("views", extension_id, extension_id)
            registrar.on("activate", lambda: trace.append(f"event:activate:{extension_id}"))
            registrar.on("deactivate", lambda: trace.append(f"event:deactivate:{extension_id}"))
            disposable = TrackingDisposable(extension_id, trace)
            disposables[extension_id] = disposable
            return [
                lambda: trace.append(f"cleanup:{extension_id}"),
                disposable,
            ]

        return ExtensionDefinition(
            setup=setup,
            deactivate=lambda: trace.append(f"hook:deactivate:{extension_id}"),
        )

    definitions = {
        alpha.manifest.id: build_definition(alpha.manifest.id),
        beta.manifest.id: build_definition(beta.manifest.id),
        gamma.manifest.id: build_definition(gamma.manifest.id),
    }
    host = ExtensionHost(
        _plan([alpha, beta, gamma]),
        lambda candidate: definitions[candidate.manifest.id],
    )

    host.activate_all()
    host.deactivate_all()
    host.deactivate_all()

    assert trace == [
        "event:activate:com.example.alpha",
        "event:activate:com.example.beta",
        "event:activate:com.example.gamma",
        "hook:deactivate:com.example.gamma",
        "event:deactivate:com.example.gamma",
        "dispose:com.example.gamma",
        "cleanup:com.example.gamma",
        "hook:deactivate:com.example.beta",
        "event:deactivate:com.example.beta",
        "dispose:com.example.beta",
        "cleanup:com.example.beta",
        "hook:deactivate:com.example.alpha",
        "event:deactivate:com.example.alpha",
        "dispose:com.example.alpha",
        "cleanup:com.example.alpha",
    ]
    assert host.contribution_registry.values("views") == ()
    assert all(disposable.calls == 1 for disposable in disposables.values())
    assert host.active_extension_ids == ()


def test_extension_host_reload_requires_development_mode(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path, "com.example.demo")
    host = ExtensionHost(
        _plan([candidate]),
        lambda _candidate: ExtensionDefinition(),
        development_mode=False,
    )

    host.activate_all()

    assert host.reload(candidate.manifest.id) is False
    assert host.statuses[candidate.manifest.id] == "active"
    assert host.diagnostics[-1].phase == "reload"
    assert "development_mode" in host.diagnostics[-1].message


def test_extension_host_reload_replaces_contributions_and_listeners(tmp_path: Path) -> None:
    old_candidate = _candidate(tmp_path, "com.example.demo", fingerprint="old")
    new_candidate = _candidate(tmp_path, "com.example.demo", fingerprint="new")
    seen: list[str] = []

    def loader(candidate: Candidate) -> ExtensionDefinition:
        label = candidate.fingerprint
        return ExtensionDefinition(
            setup=lambda registrar: [
                registrar.contribute("views", "shared", label),
                registrar.on("tick", lambda: seen.append(label)),
            ]
        )

    host = ExtensionHost(_plan([old_candidate]), loader, development_mode=True)

    host.activate_all()
    host.emit("tick")

    assert host.contribution_registry.values("views") == ("old",)
    assert seen == ["old"]

    assert host.reload(old_candidate.manifest.id, new_candidate) is True

    host.emit("tick")
    assert host.contribution_registry.values("views") == ("new",)
    assert seen == ["old", "new"]
    assert host.statuses[old_candidate.manifest.id] == "active"
    assert host.diagnostics == ()
