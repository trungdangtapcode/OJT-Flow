from ojtflow.core.contracts.enums import EvidenceSourceType
from ojtflow.core.contracts.workflow import WorkflowState


def test_workflow_state_accepts_advanced_retrieval_evidence_source_types() -> None:
    workflow = WorkflowState.model_validate(
        {
            "workflow_id": "wf_retrieval_compat",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "status": "completed",
            "schema_version": "workflow_state.v0",
            "user_instruction": "validate healthcare data",
            "intent": {},
            "retrieved_context": [
                {
                    "evidence_id": "ev_rxnorm",
                    "source_type": "terminology_system",
                    "source_id": "rxnorm",
                    "claim": "RxNorm is a medication terminology source.",
                    "locator": {"system": "RxNorm"},
                    "trust_level": "approved",
                },
                {
                    "evidence_id": "ev_fhir",
                    "source_type": "healthcare_standard",
                    "source_id": "hl7-fhir",
                    "claim": "FHIR is a healthcare interoperability standard.",
                    "locator": {"standard": "FHIR"},
                    "trust_level": "approved",
                },
            ],
        }
    )

    assert workflow.retrieved_context[0].source_type == EvidenceSourceType.TERMINOLOGY_SYSTEM
    assert workflow.retrieved_context[1].source_type == EvidenceSourceType.HEALTHCARE_STANDARD
