from datetime import datetime, timezone

import httpx
import pytest

from ojtflow.core.contracts.auth import AuthenticatedSession, SessionRecord, UserRecord
from ojtflow.core.contracts.enums import DataFormat
from ojtflow.data_tools.redaction import build_redaction_preview
from ojtflow.interfaces.api.app import create_app
from ojtflow.interfaces.api.deps import require_authentication


async def _authenticated_dependency() -> AuthenticatedSession:
    now = datetime.now(timezone.utc)
    user = UserRecord(
        user_id="usr_redaction",
        google_sub="google-redaction",
        email="reviewer@example.com",
        email_verified=True,
        display_name="Reviewer",
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_login_at=now,
    )
    return AuthenticatedSession(
        user=user,
        session=SessionRecord(
            session_id="ses_redaction",
            user_id=user.user_id,
            token_hash="hash",
            created_at=now,
            expires_at=now,
            revoked_at=None,
            last_seen_at=now,
        ),
    )


def test_redaction_preview_masks_csv_sensitive_columns_and_regex_values() -> None:
    preview = build_redaction_preview(
        "patient_id,ssn,email,value\nP001,123-45-6789,patient@example.com,7.4\n",
        data_format=DataFormat.CSV,
    )

    assert preview.external_provider_block_recommended is True
    assert "[REDACTED:PATIENT_IDENTIFIER]" in preview.redacted_text
    assert "[REDACTED:SSN]" in preview.redacted_text
    assert "[REDACTED:EMAIL]" in preview.redacted_text
    assert {match.kind for match in preview.matches} >= {
        "patient_identifier",
        "ssn",
        "email",
    }
    assert all("P001" not in match.value_preview for match in preview.matches)


def test_redaction_preview_masks_unstructured_phone_and_email() -> None:
    preview = build_redaction_preview(
        "Call 415-555-1234 or email nurse@example.org before export."
    )

    assert "[REDACTED:PHONE]" in preview.redacted_text
    assert "[REDACTED:EMAIL]" in preview.redacted_text
    assert len(preview.matches) == 2


def test_redaction_preview_can_suppress_phi_values() -> None:
    preview = build_redaction_preview(
        "patient_id,ssn,value\nP001,123-45-6789,7.4\n",
        data_format=DataFormat.CSV,
        action_override="suppress",
    )

    assert preview.redacted_text == "patient_id,ssn,value\n,,7.4"
    assert preview.action_summary == {"suppress": 2}
    assert all(match.action == "suppress" for match in preview.matches)
    assert all(match.replacement == "" for match in preview.matches)


def test_redaction_preview_can_use_deterministic_token_placeholders() -> None:
    preview_a = build_redaction_preview(
        "patient_id,ssn,value\nP001,123-45-6789,7.4\n",
        data_format=DataFormat.CSV,
        action_override="tokenize_placeholder",
    )
    preview_b = build_redaction_preview(
        "patient_id,ssn,value\nP001,123-45-6789,7.4\n",
        data_format=DataFormat.CSV,
        action_override="tokenize_placeholder",
    )

    assert "[TOKEN:PATIENT_IDENTIFIER:" in preview_a.redacted_text
    assert "[TOKEN:SSN:" in preview_a.redacted_text
    assert preview_a.redacted_text == preview_b.redacted_text
    assert preview_a.action_summary == {"tokenize_placeholder": 2}
    assert all(match.token for match in preview_a.matches)


def test_redaction_preview_marks_review_gated_reveal_without_exposing_raw_values() -> None:
    preview = build_redaction_preview(
        "patient_id,diagnosis,value\nP001,diabetes,7.4\n",
        data_format=DataFormat.CSV,
        action_override="review_gated_reveal",
    )

    assert "[REVIEW_REQUIRED:PATIENT_IDENTIFIER]" in preview.redacted_text
    assert "[REVIEW_REQUIRED:CLINICAL_CONTEXT]" in preview.redacted_text
    assert "P001" not in preview.redacted_text
    assert "diabetes" not in preview.redacted_text
    assert preview.requires_review is True
    assert preview.reveal_required is True
    assert all(match.status == "requires_review" for match in preview.matches)


def test_redaction_preview_can_reveal_after_internal_review_approval() -> None:
    preview = build_redaction_preview(
        "patient_id,diagnosis,value\nP001,diabetes,7.4\n",
        data_format=DataFormat.CSV,
        action_override="review_gated_reveal",
        reveal_approved=True,
    )

    assert preview.redacted_text == "patient_id,diagnosis,value\nP001,diabetes,7.4"
    assert preview.requires_review is False
    assert preview.reveal_required is False
    assert preview.reveal_approved is True
    assert all(match.status == "revealed" for match in preview.matches)


@pytest.mark.asyncio
async def test_redaction_preview_endpoint_returns_public_envelope() -> None:
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/parse/redaction-preview",
            json={
                "data": "patient_id,ssn\nP001,123-45-6789\n",
                "input_format": "csv",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["external_provider_block_recommended"] is True
    assert "[REDACTED:SSN]" in body["data"]["redacted_text"]


@pytest.mark.asyncio
async def test_redaction_preview_endpoint_accepts_action_override() -> None:
    app = create_app()
    app.dependency_overrides[require_authentication] = _authenticated_dependency
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/parse/redaction-preview",
            json={
                "data": "patient_id,ssn\nP001,123-45-6789\n",
                "input_format": "csv",
                "redaction_action": "tokenize_placeholder",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["action_summary"] == {"tokenize_placeholder": 2}
    assert "[TOKEN:SSN:" in body["data"]["redacted_text"]
