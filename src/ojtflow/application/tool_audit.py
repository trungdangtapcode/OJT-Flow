"""Shared audit helpers for assistant and MCP tool execution."""

from __future__ import annotations

import json
from typing import Any

from ojtflow.application.ports import AuditRepository
from ojtflow.core.contracts.audit import AuditRecord
from ojtflow.data_tools.hashing import sha256_text


def append_tool_audit_record(
    repository: AuditRepository | None,
    *,
    action_prefix: str,
    tool_name: str,
    arguments: dict[str, Any],
    output: dict[str, Any],
    owner_user_id: str | None = None,
    request_id: str | None = None,
    assistant_session_id: str | None = None,
    assistant_message_id: str | None = None,
    actor_type: str,
    actor_id: str | None = None,
) -> AuditRecord | None:
    """Append a redacted, correlation-rich tool audit record if storage is configured."""

    if repository is None:
        return None
    workflow_ids = _workflow_ids_from_payload(output)
    workflow_event_refs = _workflow_event_refs_from_payload(output)
    record = AuditRecord(
        owner_user_id=owner_user_id,
        workflow_id=workflow_ids[0] if workflow_ids else None,
        workflow_event_refs=workflow_event_refs,
        assistant_session_id=assistant_session_id,
        assistant_message_id=assistant_message_id,
        request_id=request_id,
        action=f"{action_prefix}.tool.{tool_name}",
        actor_id=actor_id or owner_user_id or actor_type,
        actor_type=actor_type,
        status=_audit_status_from_output(output),
        input_hash=sha256_text(_safe_json(_redacted_arguments(arguments))),
        output_hash=sha256_text(_safe_json(_compact_output_for_audit(output))),
        metadata={
            "action_prefix": action_prefix,
            "tool_name": tool_name,
            "argument_keys": sorted(arguments),
            "workflow_ids": workflow_ids,
            "requires_approval": bool(output.get("requires_approval")),
            "error": output.get("error") if isinstance(output.get("error"), str) else None,
            "data_char_count": _data_char_count(arguments),
        },
    )
    return repository.append(record)


def _redacted_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {key: _redacted_value(key, value) for key, value in arguments.items()}


def _redacted_value(key: str, value: Any) -> Any:
    if isinstance(value, str):
        return {"sha256": sha256_text(value), "char_count": len(value)}
    if isinstance(value, dict):
        return {
            str(child_key): _redacted_value(str(child_key), child)
            for child_key, child in value.items()
        }
    if isinstance(value, list):
        return [_redacted_value(key, child) for child in value]
    return value


def _compact_output_for_audit(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": _audit_status_from_output(output),
        "workflow_ids": _workflow_ids_from_payload(output),
        "workflow_event_refs": _workflow_event_refs_from_payload(output),
        "tool_name": output.get("tool_name"),
        "error": output.get("error"),
    }


def _audit_status_from_output(output: dict[str, Any]) -> str:
    status = output.get("status")
    if isinstance(status, str) and status:
        return status
    if isinstance(output.get("tool_calls"), list):
        statuses = [
            str(call.get("status"))
            for call in output["tool_calls"]
            if isinstance(call, dict) and call.get("status")
        ]
        if any(status == "failed" for status in statuses):
            return "failed"
        if any(status == "requires_approval" for status in statuses):
            return "requires_approval"
    return "completed"


def _workflow_ids_from_payload(value: Any) -> list[str]:
    ids: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            workflow_id = item.get("workflow_id")
            if isinstance(workflow_id, str) and workflow_id.startswith("wf_"):
                ids.append(workflow_id)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return list(dict.fromkeys(ids))


def _workflow_event_refs_from_payload(value: Any) -> list[str]:
    refs: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            event_refs = item.get("audit_event_refs")
            if isinstance(event_refs, list):
                refs.extend(ref for ref in event_refs if isinstance(ref, str))
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return list(dict.fromkeys(refs))


def _data_char_count(arguments: dict[str, Any]) -> int:
    total = 0
    for key, value in arguments.items():
        if key == "data" and isinstance(value, str):
            total += len(value)
        elif isinstance(value, dict):
            total += _data_char_count(value)
    return total


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
