from collections.abc import Sequence
from pathlib import Path

from tau_extensions import (
    ActivationPlan,
    Approval,
    Candidate,
    Dependency,
    ExtensionManifest,
    ExtensionSource,
    TrustPolicy,
    VersionRange,
    resolve_extensions,
)


def _candidate(
    tmp_path: Path,
    extension_id: str,
    *,
    source: ExtensionSource,
    permissions: Sequence[str] = ("views",),
    dependencies: Sequence[Dependency] = (),
    version: str = "1.0.0",
    fingerprint: str = "fingerprint",
) -> Candidate:
    manifest = ExtensionManifest.model_validate(
        {
            "schema_version": 1,
            "id": extension_id,
            "name": extension_id,
            "version": version,
            "api_version": "^1.0",
            "entrypoint": "demo.extension:setup",
            "permissions": list(permissions),
            "dependencies": [
                dependency.model_dump(exclude_none=True) for dependency in dependencies
            ],
            "contributions": {},
        }
    )
    return Candidate(
        manifest=manifest,
        path=tmp_path / extension_id.replace(".", "-"),
        source=source,
        fingerprint=fingerprint,
    )


def _decision_codes(plan: ActivationPlan) -> dict[str, str]:
    return {decision.candidate.manifest.id: decision.code for decision in plan.decisions}


def test_resolve_extensions_applies_trust_defaults(tmp_path: Path) -> None:
    built_in = _candidate(
        tmp_path,
        "com.example.built-in",
        source=ExtensionSource.BUILT_IN,
        permissions=("tools",),
    )
    admin = _candidate(tmp_path, "com.example.admin", source=ExtensionSource.ADMIN)
    workspace = _candidate(tmp_path, "com.example.workspace", source=ExtensionSource.WORKSPACE)

    plan = resolve_extensions(
        [built_in, admin, workspace],
        enabled_ids=(),
        approvals=(),
        policy=TrustPolicy(),
    )

    assert [candidate.manifest.id for candidate in plan.ordered_candidates] == [
        "com.example.built-in"
    ]
    assert _decision_codes(plan) == {
        "com.example.built-in": "builtin_default_enabled",
        "com.example.admin": "not_enabled",
        "com.example.workspace": "not_enabled",
    }
    assert [diagnostic.code for diagnostic in plan.diagnostics] == ["not_enabled", "not_enabled"]


def test_resolve_extensions_enables_admin_and_workspace_candidates_explicitly(
    tmp_path: Path,
) -> None:
    admin = _candidate(
        tmp_path,
        "com.example.admin",
        source=ExtensionSource.ADMIN,
        permissions=("tools",),
    )
    workspace = _candidate(
        tmp_path,
        "com.example.workspace",
        source=ExtensionSource.WORKSPACE,
        permissions=("views", "actions"),
        fingerprint="workspace-v1",
    )

    plan = resolve_extensions(
        [workspace, admin],
        enabled_ids={admin.manifest.id, workspace.manifest.id},
        approvals={Approval(workspace.manifest.id, workspace.fingerprint)},
        policy=TrustPolicy(admin_allowlist={admin.manifest.id}),
    )

    assert [candidate.manifest.id for candidate in plan.ordered_candidates] == [
        "com.example.admin",
        "com.example.workspace",
    ]
    assert _decision_codes(plan) == {
        "com.example.workspace": "explicitly_enabled",
        "com.example.admin": "explicitly_enabled",
    }
    assert plan.diagnostics == ()


def test_resolve_extensions_requires_admin_allowlisting(tmp_path: Path) -> None:
    admin = _candidate(tmp_path, "com.example.admin", source=ExtensionSource.ADMIN)

    plan = resolve_extensions(
        [admin],
        enabled_ids={admin.manifest.id},
        approvals=(),
        policy=TrustPolicy(),
    )

    assert plan.ordered_candidates == ()
    assert _decision_codes(plan) == {"com.example.admin": "admin_not_allowlisted"}
    assert [diagnostic.code for diagnostic in plan.diagnostics] == ["admin_not_allowlisted"]


def test_resolve_extensions_requires_exact_workspace_approval_fingerprint(
    tmp_path: Path,
) -> None:
    approved = _candidate(
        tmp_path,
        "com.example.workspace",
        source=ExtensionSource.WORKSPACE,
        fingerprint="workspace-v1",
    )
    approval = Approval(approved.manifest.id, approved.fingerprint)

    approved_plan = resolve_extensions(
        [approved],
        enabled_ids={approved.manifest.id},
        approvals={approval},
        policy=TrustPolicy(),
    )
    assert _decision_codes(approved_plan) == {"com.example.workspace": "explicitly_enabled"}
    assert approved_plan.diagnostics == ()

    changed = _candidate(
        tmp_path,
        "com.example.workspace",
        source=ExtensionSource.WORKSPACE,
        fingerprint="workspace-v2",
    )
    changed_plan = resolve_extensions(
        [changed],
        enabled_ids={changed.manifest.id},
        approvals={approval},
        policy=TrustPolicy(),
    )

    assert changed_plan.ordered_candidates == ()
    assert _decision_codes(changed_plan) == {"com.example.workspace": "workspace_approval_mismatch"}
    assert [diagnostic.code for diagnostic in changed_plan.diagnostics] == [
        "workspace_approval_mismatch"
    ]


def test_resolve_extensions_denies_permissions_outside_source_allowlist(tmp_path: Path) -> None:
    workspace = _candidate(
        tmp_path,
        "com.example.workspace",
        source=ExtensionSource.WORKSPACE,
        permissions=("tools",),
    )

    plan = resolve_extensions(
        [workspace],
        enabled_ids={workspace.manifest.id},
        approvals={Approval(workspace.manifest.id, workspace.fingerprint)},
        policy=TrustPolicy(),
    )

    assert plan.ordered_candidates == ()
    assert _decision_codes(plan) == {"com.example.workspace": "permission_denied"}
    assert plan.diagnostics[0].message.endswith("extensions: tools")



def test_resolve_extensions_blocks_missing_disabled_and_version_mismatched_dependencies(
    tmp_path: Path,
) -> None:
    missing = _candidate(
        tmp_path,
        "com.example.missing-dependent",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id="com.example.missing"),),
    )
    disabled_dependency = _candidate(
        tmp_path,
        "com.example.disabled-dependency",
        source=ExtensionSource.WORKSPACE,
    )
    disabled = _candidate(
        tmp_path,
        "com.example.disabled-dependent",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id=disabled_dependency.manifest.id),),
    )
    version_dependency = _candidate(
        tmp_path,
        "com.example.version-dependency",
        source=ExtensionSource.BUILT_IN,
        version="1.0.0",
    )
    version = _candidate(
        tmp_path,
        "com.example.version-dependent",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id=version_dependency.manifest.id, version=VersionRange("^2.0")),),
    )

    plan = resolve_extensions(
        [version, missing, disabled, disabled_dependency, version_dependency],
        enabled_ids=(),
        approvals=(),
        policy=TrustPolicy(),
    )

    assert [candidate.manifest.id for candidate in plan.ordered_candidates] == [
        "com.example.version-dependency"
    ]
    assert _decision_codes(plan) == {
        "com.example.version-dependent": "dependency_version_mismatch",
        "com.example.missing-dependent": "missing_dependency",
        "com.example.disabled-dependent": "disabled_dependency",
        "com.example.disabled-dependency": "not_enabled",
        "com.example.version-dependency": "builtin_default_enabled",
    }



def test_resolve_extensions_orders_enabled_candidates_topologically_with_stable_ties(
    tmp_path: Path,
) -> None:
    alpha = _candidate(tmp_path, "com.example.alpha", source=ExtensionSource.BUILT_IN)
    beta = _candidate(tmp_path, "com.example.beta", source=ExtensionSource.BUILT_IN)
    delta = _candidate(
        tmp_path,
        "com.example.delta",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id=alpha.manifest.id),),
    )
    gamma = _candidate(
        tmp_path,
        "com.example.gamma",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id=beta.manifest.id), Dependency(id=alpha.manifest.id)),
    )

    plan = resolve_extensions(
        [gamma, delta, beta, alpha],
        enabled_ids=(),
        approvals=(),
        policy=TrustPolicy(),
    )

    assert [candidate.manifest.id for candidate in plan.ordered_candidates] == [
        "com.example.alpha",
        "com.example.beta",
        "com.example.delta",
        "com.example.gamma",
    ]
    assert plan.diagnostics == ()



def test_resolve_extensions_blocks_cycles_and_transitive_dependents(tmp_path: Path) -> None:
    alpha = _candidate(
        tmp_path,
        "com.example.alpha",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id="com.example.beta"),),
    )
    beta = _candidate(
        tmp_path,
        "com.example.beta",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id="com.example.alpha"),),
    )
    dependent = _candidate(
        tmp_path,
        "com.example.dependent",
        source=ExtensionSource.BUILT_IN,
        dependencies=(Dependency(id="com.example.alpha"),),
    )
    stable = _candidate(tmp_path, "com.example.stable", source=ExtensionSource.BUILT_IN)

    plan = resolve_extensions(
        [dependent, beta, stable, alpha],
        enabled_ids=(),
        approvals=(),
        policy=TrustPolicy(),
    )

    assert [candidate.manifest.id for candidate in plan.ordered_candidates] == [
        "com.example.stable"
    ]
    assert _decision_codes(plan) == {
        "com.example.dependent": "dependency_cycle_dependent",
        "com.example.beta": "dependency_cycle",
        "com.example.stable": "builtin_default_enabled",
        "com.example.alpha": "dependency_cycle",
    }
    assert [(diagnostic.code, diagnostic.id) for diagnostic in plan.diagnostics] == [
        ("dependency_cycle", None),
        ("dependency_cycle_dependent", "com.example.dependent"),
    ]
    assert plan.diagnostics[0].message == (
        "dependency cycle detected: com.example.alpha, com.example.beta"
    )
