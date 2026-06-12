"""Application service for evidence retrieval."""

from __future__ import annotations

from collections.abc import Sequence
import json
from hashlib import sha256
from typing import Any

from ojtflow.application.graph_conflict_service import GraphConflictService
from ojtflow.application.graph_ner_service import GraphNERService
from ojtflow.application.ports import RetrievalRepository
from ojtflow.application.retrieval_answer_service import RetrievalAnswerSynthesizer
from ojtflow.core.contracts.data import DataProfile
from ojtflow.core.contracts.external_provider import (
    ExternalProviderDecision,
    ExternalProviderPolicy,
)
from ojtflow.core.contracts.retrieval import (
    RetrievalIndexManifest,
    RetrievalIntegrityReport,
    RetrievalPlan,
    RetrievalPlanCoverageSummary,
    RetrievalPlanTaskSummary,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalQueryAnalysis,
    RetrievalQueryDiagnostic,
    RetrievalSource,
)
from ojtflow.core.policy.external_provider_policy import decide_external_provider_handoff


class RetrievalService:
    """Builds retrieval queries and delegates ranking to replaceable adapters."""

    def __init__(
        self,
        repository: RetrievalRepository,
        graph_ner: GraphNERService | None = None,
        graph_conflicts: GraphConflictService | None = None,
        answer_synthesizer: RetrievalAnswerSynthesizer | None = None,
        rule_packs: Sequence[dict[str, Any]] | None = None,
        external_provider_policy: ExternalProviderPolicy | None = None,
    ) -> None:
        self.repository = repository
        self.graph_ner = graph_ner or GraphNERService()
        self.graph_conflicts = graph_conflicts or GraphConflictService()
        self.answer_synthesizer = answer_synthesizer or RetrievalAnswerSynthesizer()
        self.rule_packs = [dict(pack) for pack in rule_packs or ()]
        self.external_provider_policy = external_provider_policy

    def search(self, query: RetrievalQuery) -> RetrievalPackage:
        """Run direct retrieval."""

        package = self.repository.search(query)
        package = self._attach_search_metadata(package, query)
        package = self._attach_rule_pack_metadata(package)
        package = self._apply_external_search_policy(package, query)
        package = self.graph_ner.augment_package(package, query)
        package = self.graph_conflicts.augment_package(package, query)
        return self.answer_synthesizer.augment_package(package, query)

    def plan(self, query: RetrievalQuery) -> RetrievalPlan:
        """Build a plan-only retrieval analysis without ranking evidence."""

        plan = self.repository.plan(query)
        request = _search_request_payload(query)
        plan = self._apply_external_search_policy_to_plan(plan, query)
        return plan.model_copy(
            update={
                "search_signature": _search_request_signature(request),
            }
        )

    def list_sources(self) -> list[RetrievalSource]:
        """List configured retrieval sources."""

        return self.repository.list_sources()

    def reindex(self, *, include_seeded: bool = True, include_corpus: bool = True) -> dict:
        """Refresh retrieval index from configured trusted sources."""

        return self.repository.reindex(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def index_manifest(self) -> RetrievalIndexManifest:
        """Return operational metadata for the active retrieval index."""

        return self.repository.index_manifest()

    def integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport:
        """Check whether indexed retrieval knowledge matches trusted sources."""

        return self.repository.integrity_report(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def search_for_workflow(
        self,
        *,
        workflow_id: str,
        instruction: str,
        profile: DataProfile,
        schema_id: str | None,
        resource_type: str | None = None,
        query_terms: list[str] | None = None,
        top_k: int = 5,
    ) -> RetrievalPackage:
        """Build workflow-aware retrieval context from instruction and profile."""

        field_names = [field.name for field in profile.fields]
        query_parts = [
            instruction,
            f"fields: {', '.join(field_names)}" if field_names else "",
            f"schema: {schema_id}" if schema_id else "",
            f"format: {profile.format.value}",
            f"FHIR resource: {resource_type}" if resource_type else "",
            " ".join(query_terms or []),
        ]
        query = RetrievalQuery(
            query=" ".join(part for part in query_parts if part),
            workflow_id=workflow_id,
            fields=field_names,
            schema_id=schema_id,
            detected_format=profile.format.value,
            resource_type=resource_type,
            top_k=top_k,
            filters={"trust_level": "approved"},
        )
        return self.search(query)

    def _attach_rule_pack_metadata(self, package: RetrievalPackage) -> RetrievalPackage:
        if not self.rule_packs:
            return package
        handoff_context = {
            **package.handoff_context,
            "retrieval_rule_packs": self.rule_packs,
        }
        return package.model_copy(update={"handoff_context": handoff_context})

    def _apply_external_search_policy(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        decision = self._external_search_decision(query)
        if decision is None:
            return package

        handoff_context = {
            **package.handoff_context,
            "external_provider_policy": {
                "external_medical_search": decision.model_dump(mode="json")
            },
        }
        if not decision.allowed:
            handoff_context = _suppress_external_search_handoff(
                handoff_context,
                decision=decision,
            )
            trace = package.trace.model_copy(
                update={
                    "safety_flags": [
                        *package.trace.safety_flags,
                        "external_medical_search_policy_blocked",
                    ],
                    "warnings": [*package.trace.warnings, decision.reason],
                }
            )
            return package.model_copy(
                update={"handoff_context": handoff_context, "trace": trace}
            )

        return package.model_copy(update={"handoff_context": handoff_context})

    def _apply_external_search_policy_to_plan(
        self,
        plan: RetrievalPlan,
        query: RetrievalQuery,
    ) -> RetrievalPlan:
        decision = self._external_search_decision(query)
        if decision is None or decision.allowed:
            return plan

        analysis = _suppress_external_search_analysis(
            plan.query_analysis,
            decision=decision,
        )
        blocked_count = sum(
            1
            for task in plan.query_analysis.retrieval_tasks
            if task.target == "external_medical_index"
        )
        summary = (
            f"{plan.summary} External medical search hints were suppressed by policy."
        )
        return plan.model_copy(
            update={
                "query_analysis": analysis,
                "coverage_summary": _suppressed_external_search_coverage_summary(
                    plan.coverage_summary,
                    analysis,
                    decision=decision,
                ),
                "task_summary": _suppressed_external_search_task_summary(
                    analysis,
                    blocked_count=blocked_count,
                ),
                "summary": summary,
            }
        )

    def _external_search_decision(
        self,
        query: RetrievalQuery,
    ) -> ExternalProviderDecision | None:
        if self.external_provider_policy is None:
            return None
        request = _search_request_payload(query)
        return decide_external_provider_handoff(
            self.external_provider_policy,
            surface="external_medical_search",
            text=json.dumps(request, sort_keys=True, ensure_ascii=False),
            metadata={
                "workflow_id": query.workflow_id,
                "schema_id": query.schema_id,
                "field_count": len(query.fields),
                "top_k": query.top_k,
            },
        )

    def _attach_search_metadata(
        self,
        package: RetrievalPackage,
        query: RetrievalQuery,
    ) -> RetrievalPackage:
        request = _search_request_payload(query)
        handoff_context = {
            **package.handoff_context,
            "search_request": request,
            "search_signature": _search_request_signature(request),
        }
        return package.model_copy(update={"handoff_context": handoff_context})


def _search_request_payload(query: RetrievalQuery) -> dict[str, Any]:
    return {
        "query": query.query,
        "workflow_id": query.workflow_id,
        "fields": list(query.fields),
        "schema_id": query.schema_id,
        "detected_format": query.detected_format,
        "resource_type": query.resource_type,
        "top_k": query.top_k,
        "filters": dict(query.filters),
    }


def _search_request_signature(request: dict[str, Any]) -> str:
    encoded = json.dumps(
        request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"


def _suppress_external_search_handoff(
    handoff_context: dict[str, Any],
    *,
    decision: ExternalProviderDecision,
) -> dict[str, Any]:
    query_analysis = handoff_context.get("query_analysis")
    if isinstance(query_analysis, dict):
        tasks = query_analysis.get("retrieval_tasks")
        query_analysis = {
            **query_analysis,
            "search_hints": [],
            "retrieval_tasks": [
                task
                for task in tasks
                if not (
                    isinstance(task, dict)
                    and task.get("target") == "external_medical_index"
                )
            ]
            if isinstance(tasks, list)
            else [],
            "external_search_suppressed": True,
            "external_search_policy_reason": decision.reason,
        }
        handoff_context = {**handoff_context, "query_analysis": query_analysis}
    return handoff_context


def _suppress_external_search_analysis(
    analysis: RetrievalQueryAnalysis,
    *,
    decision: ExternalProviderDecision,
) -> RetrievalQueryAnalysis:
    diagnostics = [
        *analysis.diagnostics,
        RetrievalQueryDiagnostic(
            code="external_medical_search_policy_blocked",
            severity="warning",
            message=decision.reason,
            suggested_action=(
                "Use local trusted corpus retrieval or ask an administrator to update "
                "external-provider policy for this workspace."
            ),
            metadata=decision.model_dump(mode="json"),
        ),
    ]
    return analysis.model_copy(
        update={
            "search_hints": [],
            "retrieval_tasks": [
                task
                for task in analysis.retrieval_tasks
                if task.target != "external_medical_index"
            ],
            "diagnostics": diagnostics,
        }
    )


def _suppressed_external_search_coverage_summary(
    current: RetrievalPlanCoverageSummary,
    analysis: RetrievalQueryAnalysis,
    *,
    decision: ExternalProviderDecision,
) -> RetrievalPlanCoverageSummary:
    local_tasks = [
        task for task in analysis.retrieval_tasks if task.target == "local_corpus"
    ]
    required_local_count = sum(1 for task in local_tasks if task.required)
    warnings = [*current.warnings, decision.reason]
    return RetrievalPlanCoverageSummary(
        ready=bool(local_tasks),
        local_task_count=len(local_tasks),
        required_local_task_count=required_local_count,
        external_task_count=0,
        standard_count=current.standard_count,
        filter_count=current.filter_count,
        standards=current.standards,
        warnings=warnings,
        next_action=(
            "Run required local corpus search tasks; external medical follow-ups "
            "are suppressed by policy."
        ),
        summary=(
            "Plan is ready for local evidence search with "
            f"{required_local_count} required local task(s); external follow-ups "
            "are suppressed by policy."
        ),
    )


def _suppressed_external_search_task_summary(
    analysis: RetrievalQueryAnalysis,
    *,
    blocked_count: int,
) -> RetrievalPlanTaskSummary:
    local_tasks = [
        task for task in analysis.retrieval_tasks if task.target == "local_corpus"
    ]
    required_local_count = sum(1 for task in local_tasks if task.required)
    return RetrievalPlanTaskSummary(
        total_task_count=len(analysis.retrieval_tasks),
        runnable_local_count=len(local_tasks),
        required_runnable_local_count=required_local_count,
        external_open_count=0,
        external_copy_count=0,
        manual_followup_count=0,
        blocked_task_count=blocked_count,
        primary_action=(
            "Run required local corpus search tasks; external medical follow-ups "
            "are suppressed by policy."
        ),
        summary=(
            f"{len(local_tasks)} local runnable task(s), 0 external/manual "
            f"follow-up(s), and {blocked_count} blocked task(s)."
        ),
    )
