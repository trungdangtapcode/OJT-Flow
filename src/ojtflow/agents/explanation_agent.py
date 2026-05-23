"""Evidence-grounded explanation agent."""

from __future__ import annotations

from ojtflow.agents.base import Agent
from ojtflow.core.contracts.agent import AgentResult
from ojtflow.core.contracts.data import ExplanationReport, TransformationOutput, ValidationReport
from ojtflow.core.contracts.enums import AgentStatus
from ojtflow.core.contracts.evidence import Evidence


class ExplanationAgent(Agent):
    agent_id = "explanation_agent"

    def run(
        self,
        validation_report: ValidationReport,
        transformation_output: TransformationOutput | None,
        evidence: list[Evidence],
    ) -> AgentResult:
        issue_kinds = sorted({issue.kind for issue in validation_report.issues})
        summary = _build_summary(validation_report, transformation_output)
        report = ExplanationReport(
            summary=summary,
            supported_claims=[
                {
                    "claim": ev.claim,
                    "source_id": ev.source_id,
                    "support": "supported",
                }
                for ev in evidence
            ],
            data_quality_flags=issue_kinds,
            uncertainty={
                "schema_confidence": validation_report.schema_confidence,
                "requires_clinician_review": validation_report.requires_review,
            },
            limitations=[
                "No diagnosis, treatment, triage, or medication recommendation was generated",
                "All clinical or healthcare fields require human accountability before operational use",
            ],
        )
        return self.result(
            AgentStatus.SUCCESS,
            "Built evidence-grounded explanation",
            data={"explanation": report},
            evidence=evidence,
        )


def _build_summary(
    validation_report: ValidationReport,
    transformation_output: TransformationOutput | None,
) -> str:
    issue_count = len(validation_report.issues)
    if transformation_output:
        return (
            f"Validated input against {validation_report.schema_id or 'an inferred schema'}, "
            f"found {issue_count} issue(s), and produced {transformation_output.output_format.value} output."
        )
    return (
        f"Validated input against {validation_report.schema_id or 'an inferred schema'} "
        f"and found {issue_count} issue(s)."
    )

