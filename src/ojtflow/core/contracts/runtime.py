"""Runtime diagnostics contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ojtflow.core.contracts.base import ContractModel
from ojtflow.core.ids import new_id
from ojtflow.core.time import utc_now


MigrationStatus = Literal[
    "applied",
    "pending",
    "checksum_mismatch",
    "unknown_applied",
]

MigrationDiagnosticsStatus = Literal["ok", "warning", "error", "not_required"]


class MigrationDiagnosticItem(ContractModel):
    """Single migration row or manifest entry for operator diagnostics."""

    version: str
    name: str
    checksum: str | None = None
    status: MigrationStatus
    applied_at: str | None = None
    duration_ms: int | None = None
    failure_reason: str | None = None


class MigrationDiagnostics(ContractModel):
    """Sanitized migration manifest and database status."""

    status: MigrationDiagnosticsStatus
    storage_backend: str
    required: bool = False
    postgres_configured: bool = False
    dependency_available: bool = True
    connection_ok: bool | None = None
    table_exists: bool = False
    manifest_count: int = 0
    applied_count: int = 0
    pending_count: int = 0
    unknown_applied_count: int = 0
    checksum_mismatch_count: int = 0
    latest_available_version: str | None = None
    latest_applied_version: str | None = None
    bootstrap_code: str | None = None
    bootstrap_summary: str = ""
    migrations: list[MigrationDiagnosticItem] = Field(default_factory=list)


RuntimeSettingSurface = Literal["retrieval", "assistant", "rollback"]


class RuntimeSettingChange(ContractModel):
    """Single runtime setting mutation in a history entry."""

    key: str
    old_value_present: bool = False
    old_value: Any = None
    new_value_present: bool = True
    new_value: Any = None


class RuntimeSettingHistoryEntry(ContractModel):
    """Append-only runtime setting history entry."""

    change_id: str = Field(default_factory=lambda: new_id("rsh"))
    changed_at: str = Field(default_factory=lambda: utc_now().isoformat())
    surface: RuntimeSettingSurface
    actor_id: str
    actor_email: str | None = None
    reason: str
    rollback_of: str | None = None
    changes: list[RuntimeSettingChange] = Field(default_factory=list)
