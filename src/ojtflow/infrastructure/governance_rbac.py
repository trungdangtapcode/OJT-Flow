"""Load data-driven RBAC role policy."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.governance import RbacPolicy


DEFAULT_RBAC_POLICY_PATH = Path("governance/rbac_roles.json")


def load_rbac_policy(knowledge_root: Path) -> RbacPolicy:
    """Load and validate the workspace RBAC role catalog."""

    path = knowledge_root / DEFAULT_RBAC_POLICY_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid RBAC policy at {path}: expected object")
    policy = RbacPolicy.model_validate(raw)
    _validate_unique_permissions(policy, path=path)
    _validate_unique_roles(policy, path=path)
    _validate_role_permissions(policy, path=path)
    return policy


def _validate_unique_permissions(policy: RbacPolicy, *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for permission in policy.permissions:
        if permission.permission_scope in seen:
            duplicates.add(permission.permission_scope)
        seen.add(permission.permission_scope)
    if duplicates:
        raise ValueError(
            f"Invalid RBAC policy at {path}: duplicate permission_scope "
            + ", ".join(sorted(duplicates))
        )


def _validate_unique_roles(policy: RbacPolicy, *, path: Path) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for role in policy.roles:
        if role.role_key in seen:
            duplicates.add(role.role_key)
        seen.add(role.role_key)
    if duplicates:
        raise ValueError(
            f"Invalid RBAC policy at {path}: duplicate role_key "
            + ", ".join(sorted(duplicates))
        )


def _validate_role_permissions(policy: RbacPolicy, *, path: Path) -> None:
    permission_scopes = {permission.permission_scope for permission in policy.permissions}
    unknown: dict[str, list[str]] = {}
    for role in policy.roles:
        missing = [
            permission_scope
            for permission_scope in role.permission_scopes
            if permission_scope not in permission_scopes
        ]
        if missing:
            unknown[role.role_key] = missing
    if unknown:
        rendered = "; ".join(
            f"{role_key}: {', '.join(scopes)}"
            for role_key, scopes in sorted(unknown.items())
        )
        raise ValueError(f"Invalid RBAC policy at {path}: unknown permission scopes {rendered}")
