"""Versioned PHI classification policy.

The default policy tracks the HIPAA Safe Harbor identifier families at a
contract level without claiming full de-identification. It is intentionally
high-recall and configurable through the policy model.
"""

from __future__ import annotations

from ojtflow.core.contracts.phi import (
    PhiClassificationPolicy,
    PhiFieldRule,
    PhiPatternRule,
)


DEFAULT_PHI_CLASSIFICATION_POLICY = PhiClassificationPolicy(
    policy_id="hipaa_safe_harbor_high_recall_v0",
    version="2026-06-11",
    field_rules=[
        PhiFieldRule(
            rule_id="direct_patient_identifier_fields",
            tokens=[
                "patient",
                "patient_id",
                "subject_id",
                "person_id",
                "mrn",
                "medical_record",
                "member_id",
                "record_number",
            ],
            category="direct_identifier",
            kind="patient_identifier",
            reason="Field name matches a patient or medical-record identifier policy.",
        ),
        PhiFieldRule(
            rule_id="ssn_fields",
            tokens=["ssn", "social_security"],
            category="direct_identifier",
            kind="ssn",
            reason="Field name matches a Social Security number identifier policy.",
            confidence=0.92,
        ),
        PhiFieldRule(
            rule_id="name_fields",
            tokens=["patient_name", "person_name", "full_name", "first_name", "last_name"],
            category="direct_identifier",
            kind="name",
            reason="Field name matches a person-name identifier policy.",
        ),
        PhiFieldRule(
            rule_id="email_fields",
            tokens=["email"],
            category="contact",
            kind="email",
            reason="Field name matches an email identifier policy.",
        ),
        PhiFieldRule(
            rule_id="phone_fields",
            tokens=["phone", "telephone"],
            category="contact",
            kind="phone",
            reason="Field name matches a phone identifier policy.",
        ),
        PhiFieldRule(
            rule_id="fax_fields",
            tokens=["fax"],
            category="contact",
            kind="fax",
            reason="Field name matches a fax identifier policy.",
        ),
        PhiFieldRule(
            rule_id="address_fields",
            tokens=["address", "zip_code"],
            category="contact",
            kind="address",
            reason="Field name matches an address identifier policy.",
        ),
        PhiFieldRule(
            rule_id="payment_identifier_fields",
            tokens=["insurance", "health_plan", "beneficiary", "account_number"],
            category="direct_identifier",
            kind="payer_identifier",
            reason="Field name matches a health-plan or account identifier policy.",
        ),
        PhiFieldRule(
            rule_id="date_demographic_fields",
            tokens=["dob", "date_of_birth", "birth_date", "admission_date", "discharge_date"],
            category="demographic",
            kind="date_related_to_individual",
            reason="Field name matches a date or demographic identifier policy.",
            confidence=0.8,
        ),
        PhiFieldRule(
            rule_id="clinical_context_fields",
            tokens=["diagnosis", "condition", "medication", "medical_history", "procedure"],
            category="clinical_context",
            kind="clinical_context",
            reason="Field name matches a clinical-context policy that can be PHI when tied to an individual.",
            confidence=0.78,
        ),
        PhiFieldRule(
            rule_id="free_text_sensitive_fields",
            tokens=["note", "comment", "narrative", "free_text"],
            category="free_text_sensitive",
            kind="free_text_sensitive",
            reason="Free-text field may contain patient identifiers or clinical details.",
            confidence=0.72,
        ),
    ],
    pattern_rules=[
        PhiPatternRule(
            rule_id="ssn_value_pattern",
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",
            category="direct_identifier",
            kind="ssn",
            reason="SSN-like value detected.",
            confidence=0.94,
        ),
        PhiPatternRule(
            rule_id="email_value_pattern",
            pattern=r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            category="contact",
            kind="email",
            reason="Email address detected.",
            confidence=0.92,
        ),
        PhiPatternRule(
            rule_id="phone_value_pattern",
            pattern=(
                r"(?<!\d)(?:\+?1[\s.-]?)?"
                r"(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
            ),
            category="contact",
            kind="phone",
            reason="Phone-like value detected.",
            confidence=0.88,
        ),
        PhiPatternRule(
            rule_id="ip_address_value_pattern",
            pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            category="direct_identifier",
            kind="ip_address",
            reason="IP-address-like value detected.",
            confidence=0.74,
        ),
        PhiPatternRule(
            rule_id="url_value_pattern",
            pattern=r"\bhttps?://[^\s,;]+",
            category="direct_identifier",
            kind="url",
            reason="URL-like value detected.",
            confidence=0.72,
        ),
    ],
    high_risk_categories=["direct_identifier"],
    medium_risk_categories=["contact", "clinical_context", "demographic"],
    review_risk_levels=["low", "medium", "high"],
    external_provider_block_risk_levels=["medium", "high"],
)


def default_phi_policy() -> PhiClassificationPolicy:
    """Return the active built-in PHI classification policy."""

    return DEFAULT_PHI_CLASSIFICATION_POLICY


def match_phi_field_rule(
    field_name: str,
    *,
    policy: PhiClassificationPolicy | None = None,
) -> PhiFieldRule | None:
    """Return the first field rule matching the field name."""

    active_policy = policy or default_phi_policy()
    normalized = normalize_policy_text(field_name)
    for rule in active_policy.field_rules:
        if any(normalize_policy_text(token) in normalized for token in rule.tokens):
            return rule
    return None


def matches_phi_field_policy(
    field_name: str,
    *,
    policy: PhiClassificationPolicy | None = None,
) -> bool:
    """Return whether a field name matches the PHI policy."""

    return match_phi_field_rule(field_name, policy=policy) is not None


def normalize_policy_text(value: str) -> str:
    """Normalize user/config field names for policy matching."""

    return value.lower().replace("-", "_").replace(" ", "_")
