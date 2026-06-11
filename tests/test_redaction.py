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
