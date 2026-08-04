"""Portable lifecycle and contribution runtime for Tau extensions."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Protocol, TypeGuard, runtime_checkable

from tau_extensions.discovery import Candidate
from tau_extensions.resolution import ActivationPlan

DiagnosticSeverity = Literal["info", "warning", "error"]
EventCallback = Callable[..., None]

_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_UNKNOWN_ACTIVATION_RANK = 1_000_000_000


@dataclass(frozen=True, slots=True)
class RuntimeDiagnostic:
    """Immutable runtime diagnostic for one extension lifecycle phase."""

    extension_id: str
    phase: str
    message: str
    severity: DiagnosticSeverity


class RegistryError(ValueError):
    """Stable error raised for invalid or conflicting contributions."""


@runtime_checkable
class Disposable(Protocol):
    """Minimal disposable protocol used by setup-owned resources."""

    def dispose(self) -> None:
        """Release the owned resource."""


class DisposalHandle:
    """Idempotent disposable handle."""

    __slots__ = ("_disposer", "_disposed")

    def __init__(self, disposer: Callable[[], None] | None = None) -> None:
        self._disposer = disposer
        self._disposed = False

    @property
    def disposed(self) -> bool:
        """Return whether this handle has already been disposed."""
        return self._disposed

    def dispose(self) -> None:
        """Dispose the underlying resource at most once."""
        if self._disposed:
            return
        self._disposed = True
        if self._disposer is not None:
            self._disposer()


@dataclass(frozen=True, slots=True)
class Contribution:
    """Immutable contribution registered by one activated extension."""

    extension_id: str
    point: str
    key: str
    value: object
    order: int
    registration_index: int


class ContributionRegistry:
    """Registry for deterministic extension contributions."""

    def __init__(self, activation_ranks: Mapping[str, int] | None = None) -> None:
        self._activation_ranks = dict(activation_ranks or {})
        self._by_point: dict[str, dict[str, Contribution]] = defaultdict(dict)
        self._keys_by_extension: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self._next_registration_index = 0

    def set_activation_rank(self, extension_id: str, rank: int) -> None:
        """Set or update the activation rank used for contribution ordering."""
        self._activation_ranks[extension_id] = rank

    def register(
        self,
        extension_id: str,
        point: str,
        key: str,
        value: object,
        *,
        order: int = 0,
    ) -> DisposalHandle:
        """Register one contribution and return its disposal handle."""
        extension_name = _validate_name("extension_id", extension_id)
        point_name = _validate_name("point", point)
        key_name = _validate_name("key", key)
        if not isinstance(order, int):
            raise RegistryError("order must be an int")

        point_entries = self._by_point[point_name]
        if key_name in point_entries:
            existing = point_entries[key_name]
            raise RegistryError(
                "duplicate contribution for "
                f"{point_name!r}/{key_name!r} already registered by {existing.extension_id}"
            )

        contribution = Contribution(
            extension_id=extension_name,
            point=point_name,
            key=key_name,
            value=value,
            order=order,
            registration_index=self._next_registration_index,
        )
        self._next_registration_index += 1
        point_entries[key_name] = contribution
        self._keys_by_extension[extension_name].add((point_name, key_name))
        return DisposalHandle(lambda: self._remove(extension_name, point_name, key_name))

    def contributions(self, point: str) -> tuple[Contribution, ...]:
        """Return deterministic contribution entries for one point."""
        point_name = _validate_name("point", point)
        point_entries = self._by_point.get(point_name)
        if not point_entries:
            return ()
        return tuple(sorted(point_entries.values(), key=self._sort_key))

    def values(self, point: str) -> tuple[object, ...]:
        """Return contribution values for one point in deterministic order."""
        return tuple(contribution.value for contribution in self.contributions(point))

    def dispose_extension(self, extension_id: str) -> None:
        """Dispose every contribution owned by one extension."""
        extension_name = _validate_name("extension_id", extension_id)
        for point_name, key_name in sorted(self._keys_by_extension.get(extension_name, ())):
            self._remove(extension_name, point_name, key_name)

    def _remove(self, extension_id: str, point: str, key: str) -> None:
        point_entries = self._by_point.get(point)
        if point_entries is not None:
            point_entries.pop(key, None)
            if not point_entries:
                self._by_point.pop(point, None)

        extension_keys = self._keys_by_extension.get(extension_id)
        if extension_keys is None:
            return
        extension_keys.discard((point, key))
        if not extension_keys:
            self._keys_by_extension.pop(extension_id, None)

    def _sort_key(self, contribution: Contribution) -> tuple[int, int, int, str]:
        return (
            contribution.order,
            self._activation_ranks.get(contribution.extension_id, _UNKNOWN_ACTIVATION_RANK),
            contribution.registration_index,
            contribution.key,
        )


class ExtensionRegistrar:
    """Registrar passed to extension setup for contributions and event listeners."""

    def __init__(self, host: ExtensionHost, extension_id: str, activation_rank: int) -> None:
        self._host = host
        self._extension_id = extension_id
        self._activation_rank = activation_rank

    def contribute(
        self,
        point: str,
        key: str,
        value: object,
        *,
        order: int = 0,
    ) -> DisposalHandle:
        """Register one contribution owned by the current extension."""
        return self._host.contribution_registry.register(
            self._extension_id,
            point,
            key,
            value,
            order=order,
        )

    def on(self, event: str, callback: EventCallback) -> DisposalHandle:
        """Register one event listener owned by the current extension."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        return self._host._register_event_listener(
            self._extension_id,
            self._activation_rank,
            event,
            callback,
        )


@dataclass(frozen=True, slots=True)
class ExtensionDefinition:
    """Portable extension definition loaded for one candidate."""

    setup: Callable[[ExtensionRegistrar], object] | None = None
    activate: Callable[[], None] | None = None
    deactivate: Callable[[], None] | None = None


@dataclass(frozen=True, slots=True)
class _EventSubscription:
    extension_id: str
    event: str
    callback: EventCallback
    activation_rank: int
    registration_index: int


@dataclass(slots=True)
class _ExtensionState:
    candidate: Candidate
    definition: ExtensionDefinition
    activation_rank: int
    owned_handles: list[Disposable]
    active: bool = False


class ExtensionHost:
    """Activate, dispatch, deactivate, and reload extension definitions."""

    def __init__(
        self,
        plan: ActivationPlan,
        loader: Callable[[Candidate], ExtensionDefinition],
        *,
        development_mode: bool = False,
    ) -> None:
        self._plan = plan
        self._loader = loader
        self._development_mode = development_mode
        self._candidate_by_id = {
            decision.candidate.manifest.id: decision.candidate for decision in plan.decisions
        }
        self._activation_ranks = {
            candidate.manifest.id: index for index, candidate in enumerate(plan.ordered_candidates)
        }
        self._states: dict[str, _ExtensionState] = {}
        self._diagnostics: list[RuntimeDiagnostic] = []
        self._statuses: dict[str, str] = {}
        self._subscriptions_by_event: dict[str, dict[int, _EventSubscription]] = defaultdict(dict)
        self._subscriptions_by_index: dict[int, _EventSubscription] = {}
        self._subscription_indices_by_extension: dict[str, set[int]] = defaultdict(set)
        self._next_event_registration_index = 0
        self._contribution_registry = ContributionRegistry(self._activation_ranks)

        if plan.decisions:
            for decision in plan.decisions:
                self._statuses[decision.candidate.manifest.id] = (
                    "pending" if decision.enabled else "blocked"
                )
        else:
            for candidate in plan.ordered_candidates:
                self._statuses[candidate.manifest.id] = "pending"

    @property
    def contribution_registry(self) -> ContributionRegistry:
        """Return the shared contribution registry."""
        return self._contribution_registry

    @property
    def diagnostics(self) -> tuple[RuntimeDiagnostic, ...]:
        """Return collected runtime diagnostics."""
        return tuple(self._diagnostics)

    @property
    def statuses(self) -> Mapping[str, str]:
        """Return current extension statuses."""
        return MappingProxyType(self._statuses)

    @property
    def active_extension_ids(self) -> tuple[str, ...]:
        """Return active extension ids in activation order."""
        active_states = sorted(
            (
                state
                for state in self._states.values()
                if state.active and self._statuses.get(state.candidate.manifest.id) == "active"
            ),
            key=lambda state: (state.activation_rank, state.candidate.manifest.id),
        )
        return tuple(state.candidate.manifest.id for state in active_states)

    def activate_all(self) -> None:
        """Activate every enabled candidate in plan order."""
        for candidate in self._plan.ordered_candidates:
            extension_id = candidate.manifest.id
            if self._statuses.get(extension_id) == "active":
                continue
            self._activate_candidate(candidate)

    def emit(self, event: str, *args: object) -> None:
        """Emit one event to all active listeners in deterministic order."""
        event_name = _validate_name("event", event)
        subscriptions = self._subscriptions_by_event.get(event_name)
        if not subscriptions:
            return
        ordered = sorted(
            subscriptions.values(),
            key=lambda subscription: (
                subscription.activation_rank,
                subscription.registration_index,
                subscription.extension_id,
            ),
        )
        for subscription in ordered:
            try:
                subscription.callback(*args)
            except Exception as exc:  # noqa: BLE001 - extension isolation boundary
                self._record_diagnostic(
                    subscription.extension_id,
                    f"event:{event_name}",
                    _format_exception(exc),
                )

    def deactivate_all(self) -> None:
        """Deactivate every active extension in reverse activation order."""
        for extension_id in reversed(self.active_extension_ids):
            self._dispose_extension(extension_id, run_deactivate=True)

    def reload(self, extension_id: str, new_candidate: Candidate | None = None) -> bool:
        """Reload one extension in development mode."""
        extension_name = _validate_name("extension_id", extension_id)
        if not self._development_mode:
            self._record_diagnostic(
                extension_name,
                "reload",
                "reload requires development_mode=True",
            )
            return False

        candidate = (
            self._candidate_by_id.get(extension_name)
            if new_candidate is None
            else new_candidate
        )
        if candidate is None:
            self._record_diagnostic(extension_name, "reload", "unknown extension id")
            return False
        if candidate.manifest.id != extension_name:
            self._record_diagnostic(
                extension_name,
                "reload",
                "new candidate id must match the reloaded extension id",
            )
            return False
        if extension_name not in self._activation_ranks:
            self._record_diagnostic(
                extension_name,
                "reload",
                "extension is not part of the active activation plan",
            )
            return False

        self._dispose_extension(extension_name, run_deactivate=True)
        self._candidate_by_id[extension_name] = candidate
        self._statuses[extension_name] = "pending"
        return self._activate_candidate(candidate)

    def _activate_candidate(self, candidate: Candidate) -> bool:
        extension_id = candidate.manifest.id
        activation_rank = self._activation_ranks.get(extension_id)
        if activation_rank is None:
            self._record_diagnostic(
                extension_id,
                "activate",
                "candidate is not part of the current activation plan",
            )
            self._statuses[extension_id] = "failed"
            return False

        self._contribution_registry.set_activation_rank(extension_id, activation_rank)
        self._statuses[extension_id] = "pending"

        try:
            definition = self._loader(candidate)
        except Exception as exc:  # noqa: BLE001 - extension isolation boundary
            self._statuses[extension_id] = "failed"
            self._record_diagnostic(extension_id, "load", _format_exception(exc))
            return False

        if not isinstance(definition, ExtensionDefinition):
            self._statuses[extension_id] = "failed"
            self._record_diagnostic(
                extension_id,
                "load",
                "loader must return an ExtensionDefinition",
            )
            return False

        state = _ExtensionState(
            candidate=candidate,
            definition=definition,
            activation_rank=activation_rank,
            owned_handles=[],
        )
        self._states[extension_id] = state
        registrar = ExtensionRegistrar(self, extension_id, activation_rank)

        try:
            if definition.setup is not None:
                if not callable(definition.setup):
                    raise TypeError("setup must be callable")
                state.owned_handles.extend(_normalize_owned_handles(definition.setup(registrar)))
        except Exception as exc:  # noqa: BLE001 - extension isolation boundary
            self._statuses[extension_id] = "failed"
            self._record_diagnostic(extension_id, "setup", _format_exception(exc))
            self._dispose_extension(
                extension_id,
                run_deactivate=False,
                final_status="failed",
            )
            return False

        try:
            if definition.activate is not None:
                if not callable(definition.activate):
                    raise TypeError("activate must be callable")
                definition.activate()
        except Exception as exc:  # noqa: BLE001 - extension isolation boundary
            self._statuses[extension_id] = "failed"
            self._record_diagnostic(extension_id, "activate", _format_exception(exc))
            self._dispose_extension(
                extension_id,
                run_deactivate=False,
                final_status="failed",
            )
            return False

        state.active = True
        self._statuses[extension_id] = "active"
        self._emit_extension_event(extension_id, "activate")
        return True

    def _register_event_listener(
        self,
        extension_id: str,
        activation_rank: int,
        event: str,
        callback: EventCallback,
    ) -> DisposalHandle:
        event_name = _validate_name("event", event)
        registration_index = self._next_event_registration_index
        self._next_event_registration_index += 1
        subscription = _EventSubscription(
            extension_id=extension_id,
            event=event_name,
            callback=callback,
            activation_rank=activation_rank,
            registration_index=registration_index,
        )
        self._subscriptions_by_event[event_name][registration_index] = subscription
        self._subscriptions_by_index[registration_index] = subscription
        self._subscription_indices_by_extension[extension_id].add(registration_index)
        return DisposalHandle(lambda: self._remove_event_listener(registration_index))

    def _remove_event_listener(self, registration_index: int) -> None:
        subscription = self._subscriptions_by_index.pop(registration_index, None)
        if subscription is None:
            return

        event_subscriptions = self._subscriptions_by_event.get(subscription.event)
        if event_subscriptions is not None:
            event_subscriptions.pop(registration_index, None)
            if not event_subscriptions:
                self._subscriptions_by_event.pop(subscription.event, None)

        extension_subscriptions = self._subscription_indices_by_extension.get(
            subscription.extension_id
        )
        if extension_subscriptions is None:
            return
        extension_subscriptions.discard(registration_index)
        if not extension_subscriptions:
            self._subscription_indices_by_extension.pop(subscription.extension_id, None)

    def _emit_extension_event(self, extension_id: str, event: str) -> None:
        subscriptions = self._subscriptions_by_event.get(event)
        if not subscriptions:
            return
        ordered = sorted(
            (
                subscription
                for subscription in subscriptions.values()
                if subscription.extension_id == extension_id
            ),
            key=lambda subscription: (subscription.registration_index, subscription.extension_id),
        )
        for subscription in ordered:
            try:
                subscription.callback()
            except Exception as exc:  # noqa: BLE001 - extension isolation boundary
                self._record_diagnostic(extension_id, f"event:{event}", _format_exception(exc))

    def _dispose_extension(
        self,
        extension_id: str,
        *,
        run_deactivate: bool,
        final_status: str = "inactive",
    ) -> None:
        state = self._states.get(extension_id)
        if state is None:
            self._statuses[extension_id] = final_status
            return

        if run_deactivate and state.active:
            try:
                if state.definition.deactivate is not None:
                    if not callable(state.definition.deactivate):
                        raise TypeError("deactivate must be callable")
                    state.definition.deactivate()
            except Exception as exc:  # noqa: BLE001 - extension isolation boundary
                self._record_diagnostic(extension_id, "deactivate", _format_exception(exc))
            self._emit_extension_event(extension_id, "deactivate")

        self._dispose_owned_handles(extension_id, state.owned_handles)
        self._dispose_event_listeners(extension_id)
        self._contribution_registry.dispose_extension(extension_id)
        state.active = False
        self._states.pop(extension_id, None)
        self._statuses[extension_id] = final_status

    def _dispose_owned_handles(self, extension_id: str, handles: Sequence[Disposable]) -> None:
        for handle in reversed(handles):
            try:
                handle.dispose()
            except Exception as exc:  # noqa: BLE001 - extension isolation boundary
                self._record_diagnostic(extension_id, "dispose", _format_exception(exc))

    def _dispose_event_listeners(self, extension_id: str) -> None:
        registration_indices = self._subscription_indices_by_extension.get(extension_id, ())
        for registration_index in sorted(registration_indices):
            self._remove_event_listener(registration_index)

    def _record_diagnostic(
        self,
        extension_id: str,
        phase: str,
        message: str,
        *,
        severity: DiagnosticSeverity = "error",
    ) -> None:
        self._diagnostics.append(
            RuntimeDiagnostic(
                extension_id=extension_id,
                phase=phase,
                message=message,
                severity=severity,
            )
        )


def _format_exception(exc: Exception) -> str:
    detail = str(exc)
    if detail:
        return f"{exc.__class__.__name__}: {detail}"
    return exc.__class__.__name__


def _is_disposable(value: object) -> TypeGuard[Disposable]:
    return isinstance(value, Disposable)


def _normalize_owned_handles(value: object) -> tuple[Disposable, ...]:
    if value is None:
        return ()
    if _is_disposable(value):
        return (value,)
    if callable(value):
        return (DisposalHandle(value),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        handles: list[Disposable] = []
        for item in value:
            handles.extend(_normalize_owned_handles(item))
        return tuple(handles)
    raise TypeError("setup must return a disposable, callable, or sequence of handles")


def _validate_name(kind: str, value: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"{kind} must be a string")
    if not _NAME_RE.fullmatch(value):
        raise RegistryError(f"{kind} must match {_NAME_RE.pattern!r}")
    return value


__all__ = [
    "Contribution",
    "ContributionRegistry",
    "Disposable",
    "DisposalHandle",
    "ExtensionDefinition",
    "ExtensionHost",
    "ExtensionRegistrar",
    "RegistryError",
    "RuntimeDiagnostic",
]
