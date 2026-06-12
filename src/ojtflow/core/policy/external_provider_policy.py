"""External provider policy resolution and enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ojtflow.core.contracts.external_provider import (
    ExternalProviderDecision,
    ExternalProviderPolicy,
    ExternalProviderRule,
    ExternalProviderSurface,
)
from ojtflow.core.contracts.phi import PhiClassification
from ojtflow.core.errors import PolicyBlockedError
from ojtflow.data_tools.phi import classify_text

if TYPE_CHECKING:
    from ojtflow.config import Settings


def external_provider_policy_from_settings(settings: "Settings") -> ExternalProviderPolicy:
    """Build external provider policy from runtime settings."""

    return ExternalProviderPolicy(
        rules=[
            ExternalProviderRule(
                surface="openai_llm",
                enabled=settings.external_openai_llm_enabled,
                allow_phi=settings.external_openai_llm_allow_phi,
                allow_unknown_sensitivity=True,
                reason="Controls OpenAI-compatible LLM planning and synthesis.",
            ),
            ExternalProviderRule(
                surface="openai_vision_ocr",
                enabled=settings.external_openai_ocr_enabled,
                allow_phi=settings.external_openai_ocr_allow_phi,
                allow_unknown_sensitivity=settings.external_openai_ocr_allow_unknown,
                reason="Controls OpenAI-compatible vision OCR image handoff.",
            ),
            ExternalProviderRule(
                surface="openai_embeddings",
                enabled=settings.external_openai_embeddings_enabled,
                allow_phi=settings.external_openai_embeddings_allow_phi,
                allow_unknown_sensitivity=True,
                reason="Controls OpenAI-compatible embedding API calls.",
            ),
            ExternalProviderRule(
                surface="huggingface_embeddings",
                enabled=True,
                allow_phi=True,
                allow_unknown_sensitivity=True,
                reason="Local Hugging Face embeddings do not leave the runtime boundary.",
            ),
            ExternalProviderRule(
                surface="external_medical_search",
                enabled=settings.external_medical_search_enabled,
                allow_phi=settings.external_medical_search_allow_phi,
                allow_unknown_sensitivity=True,
                reason="Controls generated external medical search hints and URLs.",
            ),
        ]
    )


def decide_external_provider_handoff(
    policy: ExternalProviderPolicy,
    *,
    surface: ExternalProviderSurface,
    text: str | None = None,
    contains_phi: bool | None = None,
    metadata: dict[str, str | int | float | bool | None] | None = None,
) -> ExternalProviderDecision:
    """Return the policy decision for an external provider handoff."""

    rule = _rule_for_surface(policy, surface)
    if not rule.enabled:
        return ExternalProviderDecision(
            surface=surface,
            allowed=False,
            reason=f"External provider surface '{surface}' is disabled by policy.",
            metadata=metadata or {},
        )

    phi_classification = _classify_text(text)
    phi_detected = _phi_detected(phi_classification, contains_phi)
    if phi_detected and not rule.allow_phi:
        return ExternalProviderDecision(
            surface=surface,
            allowed=False,
            reason=(
                f"External provider surface '{surface}' cannot receive PHI or "
                "sensitive healthcare data under the active policy."
            ),
            phi_classification=phi_classification,
            metadata=metadata or {},
        )
    if contains_phi is None and text is None and not rule.allow_unknown_sensitivity:
        return ExternalProviderDecision(
            surface=surface,
            allowed=False,
            reason=(
                f"External provider surface '{surface}' cannot receive content "
                "with unknown PHI sensitivity under the active policy."
            ),
            metadata=metadata or {},
        )

    return ExternalProviderDecision(
        surface=surface,
        allowed=True,
        reason=f"External provider surface '{surface}' is allowed by policy.",
        phi_classification=phi_classification,
        metadata=metadata or {},
    )


def require_external_provider_handoff(
    policy: ExternalProviderPolicy,
    *,
    surface: ExternalProviderSurface,
    text: str | None = None,
    contains_phi: bool | None = None,
    metadata: dict[str, str | int | float | bool | None] | None = None,
) -> ExternalProviderDecision:
    """Return an allowed decision or raise a policy error."""

    decision = decide_external_provider_handoff(
        policy,
        surface=surface,
        text=text,
        contains_phi=contains_phi,
        metadata=metadata,
    )
    if not decision.allowed:
        raise PolicyBlockedError(
            decision.reason,
            details={
                "surface": surface,
                "policy_id": policy.policy_id,
                "policy_version": policy.version,
                "phi_classification": (
                    decision.phi_classification.model_dump(mode="json")
                    if decision.phi_classification
                    else None
                ),
                "metadata": decision.metadata,
            },
        )
    return decision


def _rule_for_surface(
    policy: ExternalProviderPolicy,
    surface: ExternalProviderSurface,
) -> ExternalProviderRule:
    for rule in policy.rules:
        if rule.surface == surface:
            return rule
    return ExternalProviderRule(
        surface=surface,
        enabled=False,
        allow_phi=False,
        allow_unknown_sensitivity=False,
        reason="No rule configured for this external provider surface.",
    )


def _classify_text(text: str | None) -> PhiClassification | None:
    if not text:
        return None
    return classify_text(text, target_type="generated_output")


def _phi_detected(
    phi_classification: PhiClassification | None,
    contains_phi: bool | None,
) -> bool:
    if contains_phi is True:
        return True
    return bool(phi_classification and phi_classification.risk_level != "none")
