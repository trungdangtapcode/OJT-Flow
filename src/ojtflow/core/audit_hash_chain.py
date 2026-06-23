"""Rule-based hash-chain helpers for generic audit records."""

from __future__ import annotations

import hashlib
import json

from ojtflow.core.contracts.audit import AuditRecord

AUDIT_HASH_ALGORITHM = "sha256"
AUDIT_CHAIN_SCOPE_PREFIX = "owner_user"


def audit_chain_scope(record: AuditRecord) -> str:
    """Return the independent chain scope for an audit record."""

    owner = record.owner_user_id or "system"
    return f"{AUDIT_CHAIN_SCOPE_PREFIX}:{owner}"


def link_audit_record(
    record: AuditRecord,
    previous_record: AuditRecord | None,
) -> AuditRecord:
    """Return a copy of an audit record linked to the previous scoped record."""

    sequence = 1
    previous_hash: str | None = None
    if previous_record is not None and previous_record.record_hash:
        sequence = (previous_record.chain_sequence or 0) + 1
        previous_hash = previous_record.record_hash

    linked = record.model_copy(
        update={
            "chain_scope": audit_chain_scope(record),
            "chain_sequence": sequence,
            "previous_record_hash": previous_hash,
            "record_hash": None,
            "hash_algorithm": AUDIT_HASH_ALGORITHM,
            "chain_status": "linked",
        }
    )
    return linked.model_copy(update={"record_hash": audit_record_hash(linked)})


def audit_record_hash(record: AuditRecord) -> str:
    """Hash the canonical audit payload excluding its own record_hash field."""

    payload = record.model_dump(mode="json", exclude={"record_hash"})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
