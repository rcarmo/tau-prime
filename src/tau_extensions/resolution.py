"""Portable extension resolution helpers for Tau."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from heapq import heappop, heappush
from types import MappingProxyType
from typing import cast

from tau_extensions.discovery import Candidate, Diagnostic, ExtensionSource
from tau_extensions.manifest import Dependency, Permission

_ALL_PERMISSIONS = cast(
    frozenset[Permission],
    frozenset(
        {
            "storage",
            "background_tasks",
            "assets",
            "commands",
            "tools",
            "routes",
            "events",
            "views",
            "actions",
        }
    ),
)
_DEFAULT_WORKSPACE_PERMISSIONS = cast(
    frozenset[Permission],
    frozenset({"views", "actions", "events", "commands"}),
)
_DEFAULT_PERMISSION_ALLOWLISTS = MappingProxyType(
    {
        ExtensionSource.BUILT_IN: _ALL_PERMISSIONS,
        ExtensionSource.ADMIN: _ALL_PERMISSIONS,
        ExtensionSource.WORKSPACE: _DEFAULT_WORKSPACE_PERMISSIONS,
    }
)


@dataclass(frozen=True, slots=True)
class Approval:
    """Immutable approval for one workspace extension fingerprint."""

    extension_id: str
    fingerprint: str


@dataclass(frozen=True, slots=True, init=False)
class TrustPolicy:
    """Immutable source trust policy for extension activation."""

    admin_allowlist: frozenset[str]
    permission_allowlists: Mapping[ExtensionSource, frozenset[Permission]]

    def __init__(
        self,
        *,
        admin_allowlist: Iterable[str] = (),
        permission_allowlists: Mapping[ExtensionSource, Iterable[Permission]] | None = None,
    ) -> None:
        object.__setattr__(self, "admin_allowlist", frozenset(admin_allowlist))
        merged = dict(_DEFAULT_PERMISSION_ALLOWLISTS)
        if permission_allowlists is not None:
            for source, permissions in permission_allowlists.items():
                merged[source] = frozenset(permissions)
        object.__setattr__(self, "permission_allowlists", MappingProxyType(merged))

    def permissions_for(self, source: ExtensionSource) -> frozenset[Permission]:
        """Return the allowed manifest permissions for one source bucket."""
        return self.permission_allowlists[source]


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    """Final activation decision for one discovered extension candidate."""

    candidate: Candidate
    enabled: bool
    code: str
    reason: str


@dataclass(frozen=True, slots=True)
class ActivationPlan:
    """Resolved activation order, decisions, and diagnostics."""

    ordered_candidates: tuple[Candidate, ...]
    decisions: tuple[ResolutionDecision, ...]
    diagnostics: tuple[Diagnostic, ...]


def resolve_extensions(
    candidates: Sequence[Candidate],
    enabled_ids: Iterable[str],
    approvals: Iterable[Approval],
    policy: TrustPolicy | None = None,
) -> ActivationPlan:
    """Resolve candidate activation under trust and dependency rules."""

    trust_policy = TrustPolicy() if policy is None else policy
    candidate_list = tuple(candidates)
    candidate_by_id: dict[str, Candidate] = {}
    for candidate in candidate_list:
        extension_id = candidate.manifest.id
        if extension_id in candidate_by_id:
            raise ValueError(f"candidates must have unique ids: {extension_id}")
        candidate_by_id[extension_id] = candidate

    enabled_set = frozenset(enabled_ids)
    approval_set = frozenset(approvals)
    approvals_by_id: dict[str, frozenset[str]] = defaultdict(frozenset)
    if approval_set:
        grouped_approvals: dict[str, set[str]] = defaultdict(set)
        for approval in approval_set:
            grouped_approvals[approval.extension_id].add(approval.fingerprint)
        approvals_by_id = {
            extension_id: frozenset(fingerprints)
            for extension_id, fingerprints in grouped_approvals.items()
        }

    decisions_by_id: dict[str, ResolutionDecision] = {}
    diagnostics: list[Diagnostic] = []
    active_ids: set[str] = set()
    for candidate in candidate_list:
        decision = _initial_decision(
            candidate,
            enabled_ids=enabled_set,
            approvals=approval_set,
            approvals_by_id=approvals_by_id,
            policy=trust_policy,
        )
        decisions_by_id[candidate.manifest.id] = decision
        if decision.enabled:
            active_ids.add(candidate.manifest.id)
        else:
            diagnostics.append(_decision_diagnostic(decision))

    while True:
        disabled_ids: list[str] = []
        for extension_id in sorted(active_ids):
            candidate = candidate_by_id[extension_id]
            problem = _dependency_problem(
                candidate,
                active_ids=active_ids,
                candidate_by_id=candidate_by_id,
            )
            if problem is None:
                continue
            code, reason = problem
            decision = ResolutionDecision(
                candidate=candidate,
                enabled=False,
                code=code,
                reason=reason,
            )
            decisions_by_id[extension_id] = decision
            diagnostics.append(_decision_diagnostic(decision))
            disabled_ids.append(extension_id)
        if not disabled_ids:
            break
        active_ids.difference_update(disabled_ids)

    active_graph = {
        extension_id: tuple(
            dependency.id
            for dependency in _sorted_dependencies(candidate_by_id[extension_id])
            if dependency.id in active_ids
        )
        for extension_id in sorted(active_ids)
    }
    cycles = _find_cycles(active_graph)
    if cycles:
        dependent_cycles = _collect_cycle_dependents(active_graph, cycles)
        cycle_members = {member for cycle in cycles for member in cycle}

        for cycle in cycles:
            cycle_text = ", ".join(cycle)
            diagnostics.append(
                Diagnostic(
                    code="dependency_cycle",
                    message=f"dependency cycle detected: {cycle_text}",
                )
            )
            for extension_id in cycle:
                candidate = candidate_by_id[extension_id]
                decisions_by_id[extension_id] = ResolutionDecision(
                    candidate=candidate,
                    enabled=False,
                    code="dependency_cycle",
                    reason=f"dependency cycle detected: {cycle_text}",
                )
        for extension_id in sorted(dependent_cycles):
            if extension_id in cycle_members:
                continue
            cycle = dependent_cycles[extension_id]
            cycle_text = ", ".join(cycle)
            candidate = candidate_by_id[extension_id]
            decision = ResolutionDecision(
                candidate=candidate,
                enabled=False,
                code="dependency_cycle_dependent",
                reason=f"depends on blocked dependency cycle: {cycle_text}",
            )
            decisions_by_id[extension_id] = decision
            diagnostics.append(_decision_diagnostic(decision))

        blocked_ids = cycle_members | set(dependent_cycles)
        active_ids.difference_update(blocked_ids)
        active_graph = {
            extension_id: tuple(
                dependency_id
                for dependency_id in dependencies
                if dependency_id in active_ids
            )
            for extension_id, dependencies in active_graph.items()
            if extension_id in active_ids
        }

    ordered_ids = _topological_order(active_graph)
    ordered_candidates = tuple(candidate_by_id[extension_id] for extension_id in ordered_ids)
    decisions = tuple(
        decisions_by_id[candidate.manifest.id]
        for candidate in candidate_list
    )
    return ActivationPlan(
        ordered_candidates=ordered_candidates,
        decisions=decisions,
        diagnostics=tuple(diagnostics),
    )


def _initial_decision(
    candidate: Candidate,
    *,
    enabled_ids: frozenset[str],
    approvals: frozenset[Approval],
    approvals_by_id: Mapping[str, frozenset[str]],
    policy: TrustPolicy,
) -> ResolutionDecision:
    extension_id = candidate.manifest.id
    if candidate.source is ExtensionSource.BUILT_IN:
        enabled = True
        code = "builtin_default_enabled"
        reason = "built-in extension is enabled by default"
    elif extension_id not in enabled_ids:
        enabled = False
        code = "not_enabled"
        reason = "extension is not explicitly enabled"
    else:
        enabled = True
        code = "explicitly_enabled"
        reason = "extension is explicitly enabled"

    if not enabled:
        return ResolutionDecision(candidate=candidate, enabled=False, code=code, reason=reason)

    if candidate.source is ExtensionSource.ADMIN and extension_id not in policy.admin_allowlist:
        return ResolutionDecision(
            candidate=candidate,
            enabled=False,
            code="admin_not_allowlisted",
            reason="admin extension is not in the admin allowlist",
        )

    if candidate.source is ExtensionSource.WORKSPACE:
        approval = Approval(extension_id=extension_id, fingerprint=candidate.fingerprint)
        if approval not in approvals:
            if extension_id in approvals_by_id:
                return ResolutionDecision(
                    candidate=candidate,
                    enabled=False,
                    code="workspace_approval_mismatch",
                    reason="workspace extension fingerprint does not match its recorded approval",
                )
            return ResolutionDecision(
                candidate=candidate,
                enabled=False,
                code="workspace_approval_required",
                reason="workspace extension requires approval for its current fingerprint",
            )

    denied_permissions = sorted(
        candidate.manifest.permissions - policy.permissions_for(candidate.source)
    )
    if denied_permissions:
        denied_text = ", ".join(denied_permissions)
        return ResolutionDecision(
            candidate=candidate,
            enabled=False,
            code="permission_denied",
            reason=(
                f"requested permissions are not allowed for {candidate.source.value} "
                f"extensions: {denied_text}"
            ),
        )

    return ResolutionDecision(candidate=candidate, enabled=True, code=code, reason=reason)


def _dependency_problem(
    candidate: Candidate,
    *,
    active_ids: set[str],
    candidate_by_id: Mapping[str, Candidate],
) -> tuple[str, str] | None:
    for dependency in _sorted_dependencies(candidate):
        dependency_candidate = candidate_by_id.get(dependency.id)
        if dependency_candidate is None:
            return ("missing_dependency", f"missing dependency: {dependency.id}")
        if dependency.id not in active_ids:
            return ("disabled_dependency", f"dependency is not enabled: {dependency.id}")
        if dependency.version is not None and not dependency.version.contains(
            dependency_candidate.manifest.version
        ):
            return (
                "dependency_version_mismatch",
                (
                    f"dependency version mismatch for {dependency.id}: "
                    f"requires {dependency.version}, found {dependency_candidate.manifest.version}"
                ),
            )
    return None


def _sorted_dependencies(candidate: Candidate) -> tuple[Dependency, ...]:
    return tuple(sorted(candidate.manifest.dependencies, key=lambda dependency: dependency.id))


def _find_cycles(graph: Mapping[str, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    cycles: list[tuple[str, ...]] = []

    def strongconnect(node: str) -> None:
        nonlocal index

        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for dependency_id in graph[node]:
            if dependency_id not in indices:
                strongconnect(dependency_id)
                lowlinks[node] = min(lowlinks[node], lowlinks[dependency_id])
            elif dependency_id in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[dependency_id])

        if lowlinks[node] != indices[node]:
            return

        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            cycles.append(tuple(sorted(component)))

    for node in sorted(graph):
        if node not in indices:
            strongconnect(node)

    cycles.sort()
    return tuple(cycles)


def _collect_cycle_dependents(
    graph: Mapping[str, tuple[str, ...]],
    cycles: tuple[tuple[str, ...], ...],
) -> dict[str, tuple[str, ...]]:
    reverse_graph: dict[str, list[str]] = defaultdict(list)
    for extension_id, dependencies in graph.items():
        for dependency_id in dependencies:
            reverse_graph[dependency_id].append(extension_id)
    for dependents in reverse_graph.values():
        dependents.sort()

    cycle_members = {member for cycle in cycles for member in cycle}
    blocked_by_cycle: dict[str, tuple[str, ...]] = {}
    for cycle in cycles:
        queue: deque[str] = deque(cycle)
        seen = set(cycle)
        while queue:
            extension_id = queue.popleft()
            for dependent_id in reverse_graph.get(extension_id, []):
                if dependent_id in seen:
                    continue
                seen.add(dependent_id)
                if dependent_id not in cycle_members and dependent_id not in blocked_by_cycle:
                    blocked_by_cycle[dependent_id] = cycle
                queue.append(dependent_id)
    return blocked_by_cycle


def _topological_order(graph: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    indegree = {extension_id: len(dependencies) for extension_id, dependencies in graph.items()}
    reverse_graph: dict[str, list[str]] = defaultdict(list)
    for extension_id, dependencies in graph.items():
        for dependency_id in dependencies:
            reverse_graph[dependency_id].append(extension_id)
    for dependents in reverse_graph.values():
        dependents.sort()

    ready: list[str] = []
    for extension_id, degree in indegree.items():
        if degree == 0:
            heappush(ready, extension_id)

    ordered: list[str] = []
    while ready:
        extension_id = heappop(ready)
        ordered.append(extension_id)
        for dependent_id in reverse_graph.get(extension_id, []):
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                heappush(ready, dependent_id)

    if len(ordered) != len(graph):
        raise RuntimeError("topological ordering requires an acyclic graph")
    return tuple(ordered)


def _decision_diagnostic(decision: ResolutionDecision) -> Diagnostic:
    return Diagnostic(
        code=decision.code,
        message=decision.reason,
        path=decision.candidate.manifest_path,
        id=decision.candidate.manifest.id,
    )


__all__ = [
    "ActivationPlan",
    "Approval",
    "ResolutionDecision",
    "TrustPolicy",
    "resolve_extensions",
]
