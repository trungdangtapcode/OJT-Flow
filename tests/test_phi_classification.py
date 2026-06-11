from ojtflow.application.assistant_session_service import AssistantSessionService
from ojtflow.core.contracts.enums import DataFormat, EvidenceSourceType, TrustLevel
from ojtflow.data_tools.convert import convert_data
from ojtflow.data_tools.parse import parse_data
from ojtflow.data_tools.profile import profile_data
from ojtflow.data_tools.redaction import build_redaction_preview
from ojtflow.data_tools.validate import validate_against_schema
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk, evidence_from_chunk
from ojtflow.infrastructure.storage.in_memory import InMemoryAssistantSessionRepository


def test_dataset_profile_validation_and_generated_output_carry_phi_classification() -> None:
    parsed = parse_data(
        "patient_id,ssn,diagnosis,value\nP001,123-45-6789,diabetes,7.4\n",
        DataFormat.CSV,
        source_ref="memory://phi.csv",
    )
    profile = profile_data(parsed)
    report = validate_against_schema(parsed, profile, schema=None)
    _output_text, output = convert_data(parsed, DataFormat.JSON)

    assert profile.phi_classification is not None
    assert profile.phi_classification.target_type == "row"
    assert profile.phi_classification.risk_level == "high"
    assert {finding.kind for finding in profile.phi_classification.findings} >= {
        "patient_identifier",
        "ssn",
        "clinical_context",
    }
    assert report.phi_classification.risk_level == "high"
    assert output.phi_classification.risk_level == "high"
    assert output.phi_classification.target_type == "generated_output"


def test_phi_policy_does_not_flag_operational_lab_name_field() -> None:
    parsed = parse_data(
        "lab_name,value,unit\nHbA1c,7.4,%\n",
        DataFormat.CSV,
        source_ref="memory://lab.csv",
    )
    profile = profile_data(parsed)

    lab_name = next(field for field in profile.fields if field.name == "lab_name")
    assert lab_name.possible_phi is False
    assert profile.phi_classification.risk_level == "none"


def test_redaction_preview_uses_phi_policy_classification() -> None:
    preview = build_redaction_preview(
        "patient_id,ssn,email,value\nP001,123-45-6789,patient@example.com,7.4\n",
        data_format=DataFormat.CSV,
    )

    assert preview.phi_classification is not None
    assert preview.phi_classification.risk_level == "high"
    assert preview.external_provider_block_recommended is True
    assert "[REDACTED:PATIENT_IDENTIFIER]" in preview.redacted_text
    assert "[REDACTED:SSN]" in preview.redacted_text
    assert "[REDACTED:EMAIL]" in preview.redacted_text


def test_assistant_chat_message_phi_classification_persists_in_payload() -> None:
    service = AssistantSessionService(InMemoryAssistantSessionRepository())
    session = service.create_session(owner_user_id="usr_phi")

    message = service.append_message(
        owner_user_id="usr_phi",
        session_id=session.session_id,
        role="user",
        content="Profile this CSV.",
        payload={
            "context": {
                "data": "patient_id,ssn,value\nP001,123-45-6789,7.4\n",
                "input_format": "csv",
            }
        },
    )
    detail = service.get_session(owner_user_id="usr_phi", session_id=session.session_id)
    persisted = detail.messages[0]

    assert message.phi_classification is not None
    assert message.phi_classification.target_type == "chat_message"
    assert message.phi_classification.risk_level == "high"
    assert persisted.phi_classification.risk_level == "high"
    assert persisted.payload["phi_classification"]["risk_level"] == "high"


def test_retrieval_chunk_evidence_locator_includes_phi_classification() -> None:
    chunk = KnowledgeChunk(
        chunk_id="chunk_phi",
        source_id="source:phi_policy",
        source_type=EvidenceSourceType.HEALTHCARE_STANDARD,
        title="Privacy policy",
        content="Contact privacy@example.org before exporting patient data.",
        trust_level=TrustLevel.APPROVED,
    )

    evidence = evidence_from_chunk(chunk, confidence=0.87)

    classification = evidence.locator["phi_classification"]
    assert classification["target_type"] == "chunk"
    assert classification["risk_level"] == "medium"
    assert classification["source_ref"] == "source:phi_policy"
