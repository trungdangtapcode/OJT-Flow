"""Use cases for PHI-safe Assistant preference memory."""

from __future__ import annotations

import re
from typing import Any, Literal

from ojtflow.application.ports import AssistantMemoryRepository
from ojtflow.core.contracts.assistant import (
    AssistantMemoryPolicy,
    AssistantMemoryPreference,
    AssistantMemoryPreferenceDefinition,
    AssistantMemorySnapshot,
    AssistantMemoryValue,
)
from ojtflow.core.errors import OJTFlowError
from ojtflow.core.time import utc_now


class AssistantMemoryService:
    """Persist and expose safe operational preferences for Assistant planning."""

    def __init__(
        self,
        repository: AssistantMemoryRepository,
        *,
        policy: AssistantMemoryPolicy,
    ) -> None:
        self.repository = repository
        self.policy = policy
        self._definitions = {preference.key: preference for preference in policy.preferences}
        self._rejected_value_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in policy.rejected_value_patterns
        ]

    def memory_policy(self) -> AssistantMemoryPolicy:
        return self.policy

    def snapshot(self, *, owner_user_id: str) -> AssistantMemorySnapshot:
        preferences = self.repository.list_preferences(owner_user_id=owner_user_id)
        allowed_preferences = [
            preference
            for preference in preferences
            if preference.key in self._definitions
            and preference.policy_version == self.policy.version
        ]
        allowed_preferences.sort(key=lambda preference: preference.key)
        return AssistantMemorySnapshot(
            policy_version=self.policy.version,
            preferences=allowed_preferences,
            context={preference.key: preference.value for preference in allowed_preferences},
        )

    def upsert_preference(
        self,
        *,
        owner_user_id: str,
        key: str,
        value: Any,
        source: Literal["user", "system", "admin"] = "user",
    ) -> AssistantMemoryPreference:
        clean_key = _clean_key(key)
        definition = self._definition(clean_key)
        clean_value = self._validated_value(definition=definition, value=value)
        existing = {
            preference.key: preference
            for preference in self.repository.list_preferences(owner_user_id=owner_user_id)
        }.get(clean_key)
        now = utc_now().isoformat()
        preference = AssistantMemoryPreference(
            owner_user_id=owner_user_id,
            key=clean_key,
            value=clean_value,
            category=definition.category,
            source=source,
            policy_version=self.policy.version,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        return self.repository.upsert_preference(preference=preference)

    def delete_preference(self, *, owner_user_id: str, key: str) -> None:
        clean_key = _clean_key(key)
        self._definition(clean_key)
        self.repository.delete_preference(owner_user_id=owner_user_id, key=clean_key)

    def assistant_context(self, *, owner_user_id: str) -> dict[str, Any]:
        snapshot = self.snapshot(owner_user_id=owner_user_id)
        if not snapshot.context:
            return {}
        return {
            "assistant_memory": {
                "policy_version": snapshot.policy_version,
                "preferences": snapshot.context,
                "safety": "operational_preferences_only_no_phi_no_uploaded_content",
            }
        }

    def _definition(self, key: str) -> AssistantMemoryPreferenceDefinition:
        if any(term.casefold() in key.casefold() for term in self.policy.rejected_key_terms):
            raise OJTFlowError(f"Assistant memory key is not allowed: {key}")
        definition = self._definitions.get(key)
        if not definition:
            raise OJTFlowError(f"Assistant memory key is not configured: {key}")
        return definition

    def _validated_value(
        self,
        *,
        definition: AssistantMemoryPreferenceDefinition,
        value: Any,
    ) -> AssistantMemoryValue:
        if definition.value_type == "boolean":
            if not isinstance(value, bool):
                raise OJTFlowError(f"{definition.key} must be a boolean preference.")
            return value
        if definition.value_type == "number":
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise OJTFlowError(f"{definition.key} must be a numeric preference.")
            return value
        if definition.value_type == "enum":
            clean_value = _clean_string_value(value)
            allowed = {str(item) for item in definition.allowed_values}
            if clean_value not in allowed:
                allowed_text = ", ".join(sorted(allowed))
                raise OJTFlowError(
                    f"{definition.key} must be one of the configured values: {allowed_text}"
                )
            self._reject_sensitive_value(clean_value)
            return clean_value
        clean_value = _clean_string_value(value)
        if len(clean_value) > definition.max_length:
            raise OJTFlowError(
                f"{definition.key} is too long for Assistant memory "
                f"({len(clean_value)} > {definition.max_length})."
            )
        self._reject_sensitive_value(clean_value)
        return clean_value

    def _reject_sensitive_value(self, value: str) -> None:
        for pattern in self._rejected_value_patterns:
            if pattern.search(value):
                raise OJTFlowError(
                    "Assistant memory only stores operational preferences; "
                    "sensitive, clinical, uploaded, or raw data-like values are rejected."
                )


def merge_assistant_memory_context(
    context: dict[str, Any],
    memory_context: dict[str, Any],
) -> dict[str, Any]:
    """Merge memory without letting caller-provided context spoof stored memory."""

    merged = dict(context)
    merged.pop("assistant_memory", None)
    merged.update(memory_context)
    return merged


def _clean_key(key: str) -> str:
    clean = key.strip()
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,80}", clean):
        raise OJTFlowError(f"Assistant memory key is invalid: {key}")
    return clean


def _clean_string_value(value: Any) -> str:
    if not isinstance(value, str):
        raise OJTFlowError("Assistant memory preference value must be a string.")
    clean = " ".join(value.strip().split())
    if not clean:
        raise OJTFlowError("Assistant memory preference value cannot be empty.")
    return clean
