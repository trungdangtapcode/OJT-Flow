"""Workflow orchestration use case."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from ojtflow.agents.explanation_agent import ExplanationAgent
from ojtflow.agents.parser_agent import ParserAgent
from ojtflow.agents.safety_agent import SafetyAgent
from ojtflow.agents.transformation_agent import TransformationAgent
from ojtflow.agents.validation_agent import ValidationAgent
from ojtflow.application.ports import (
    DatasetStore,
    EventRepository,
    GraphRepository,
    KnowledgeRepository,
    RetrievalRepository,
    WorkflowRepository,
)
from ojtflow.application.graph_service import GraphService
from ojtflow.application.retrieval_service import RetrievalService
from ojtflow.application.tool_registry import tool_specs_json
from ojtflow.clinical.package_builder import build_clinical_package
from ojtflow.core.contracts.data import (
    ParsedData,
    TransformationAction,
    TransformationOutput,
    TransformationPlan,
)
from ojtflow.core.contracts.enums import (
    ActorType,
    DataFormat,
    EventType,
    ReviewDecision,
    ReviewStatus,
    Severity,
    StepStatus,
    WorkflowStatus,
)
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.external_provider import ExternalProviderPolicy
from ojtflow.core.contracts.graph import (
    GraphContextRecord,
    GraphExport,
    GraphExportFormat,
    GraphNeighborhood,
    GraphNeighborhoodQuery,
)
from ojtflow.core.contracts.retrieval import (
    RetrievalIntegrityReport,
    RetrievalPlan,
    RetrievalPackage,
    RetrievalQuery,
    RetrievalSource,
)
from ojtflow.core.contracts.review import HumanReview
from ojtflow.core.contracts.summary import WorkflowStats, WorkflowSummaryPage
from ojtflow.core.contracts.workflow import (
    WorkflowFailure,
    WorkflowInput,
    WorkflowIntent,
    WorkflowOutput,
    WorkflowOutputArtifact,
    WorkflowState,
    WorkflowStep,
)
from ojtflow.core.errors import (
    ArtifactIntegrityError,
    NotFoundError,
    OJTFlowError,
    PolicyBlockedError,
    ToolExecutionError,
    UnsupportedUploadError,
    UploadTooLargeError,
)
from ojtflow.core.text import format_count
from ojtflow.data_tools.hashing import sha256_text
from ojtflow.data_tools.transform_plan import build_transformation_plan
from ojtflow.fhir.profile import profile_fhir_like


SUPPORTED_REVIEW_EDIT_ACTIONS = {
    "normalize_date",
    "preserve_missing_as_null",
    "preserve_missing_unit_as_null",
    "mask_sensitive_field_for_explanation",
}


class WorkflowService:
    """Coordinates the backbone workflow without depending on web or DB frameworks."""

    def __init__(
        self,
        datasets: DatasetStore,
        workflows: WorkflowRepository,
        events: EventRepository,
        knowledge: KnowledgeRepository,
        retrieval: RetrievalRepository,
        graph_repository: GraphRepository | None = None,
        retrieval_rule_packs: Sequence[dict[str, Any]] | None = None,
        external_provider_policy: ExternalProviderPolicy | None = None,
    ) -> None:
        self.datasets = datasets
        self.workflows = workflows
        self.events = events
        self.knowledge = knowledge
        self.graph_service = GraphService(graph_repository) if graph_repository else None
        self.retrieval_service = RetrievalService(
            retrieval,
            rule_packs=retrieval_rule_packs,
            external_provider_policy=external_provider_policy,
        )
        self.parser_agent = ParserAgent()
        self.validation_agent = ValidationAgent()
        self.safety_agent = SafetyAgent()
        self.transformation_agent = TransformationAgent()
        self.explanation_agent = ExplanationAgent()

    def start_workflow(
        self,
        instruction: str,
        data: str,
        declared_format: DataFormat | None = None,
        target_format: DataFormat = DataFormat.JSON,
        schema_id: str | None = "lab_result_v1",
        require_human_review: bool = True,
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        """Start and run a workflow until completion or review pause."""

        workflow = WorkflowState(
            owner_user_id=owner_user_id,
            user_instruction=instruction,
            intent=WorkflowIntent(
                target_format=target_format,
                requires_explanation=True,
                options={
                    "schema_id": schema_id,
                    "require_human_review": require_human_review,
                },
            ),
            status=WorkflowStatus.RUNNING,
        )
        if request_id:
            workflow.handoff_context["request_id"] = request_id
        workflow.handoff_context["tool_specs"] = tool_specs_json()
        self.workflows.save(workflow)
        dataset = self.datasets.put_text(
            data,
            workflow_id=workflow.workflow_id,
            declared_format=declared_format.value if declared_format else None,
        )
        workflow.input = WorkflowInput(
            dataset_ref=dataset.storage_ref,
            input_hash=dataset.sha256,
            declared_format=declared_format,
        )
        self._event(
            workflow,
            ActorType.SYSTEM,
            "workflow_service",
            EventType.WORKFLOW_CREATED,
            "Workflow created",
            output_refs=[dataset.storage_ref],
        )
        self._step(workflow, "workflow_created", StepStatus.COMPLETED, "Workflow created")

        try:
            parser_result = self.parser_agent.run(data, declared_format, dataset.storage_ref)
            parsed: ParsedData = parser_result.data["parsed"]
            workflow.input.detected_format = parsed.format
            workflow.profile = parser_result.data["profile"]
            self._event(
                workflow,
                ActorType.AGENT,
                self.parser_agent.agent_id,
                EventType.AGENT_COMPLETED,
                parser_result.summary,
                metadata={"confidence": parser_result.confidence},
            )
            self._step(
                workflow,
                "parser",
                StepStatus.COMPLETED,
                parser_result.summary,
                issue_count=len(parser_result.issues),
            )

            return self._run_after_parse(
                workflow,
                parsed,
                instruction=instruction,
                target_format=target_format,
                schema_id=schema_id,
                require_human_review=require_human_review,
            )
        except Exception as exc:
            self._fail_workflow(workflow, exc)
            self.workflows.save(workflow)
            return workflow

    def create_mapping_draft(
        self,
        *,
        instruction: str,
        data: str,
        declared_format: DataFormat | None = None,
        target_format: DataFormat = DataFormat.JSON,
        schema_id: str | None = "lab_result_v1",
        mapping_goal: str | None = None,
        source_fields: list[str] | None = None,
        target_fields: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        """Create a review-gated transform plan without executing conversion."""

        clean_instruction = instruction.strip()
        if not clean_instruction:
            raise PolicyBlockedError("Mapping draft instruction is required.")
        workflow = WorkflowState(
            owner_user_id=owner_user_id,
            user_instruction=clean_instruction,
            intent=WorkflowIntent(
                task_type="mapping_draft",
                target_format=target_format,
                requires_explanation=False,
                options={
                    "schema_id": schema_id,
                    "source": "assistant",
                    "draft_only": True,
                    "mapping_goal": mapping_goal,
                    "source_fields": source_fields or [],
                    "target_fields": target_fields or [],
                },
            ),
            status=WorkflowStatus.RUNNING,
            risk_flags=["mapping_draft", "review_gated_transformation"],
        )
        if request_id:
            workflow.handoff_context["request_id"] = request_id
        workflow.handoff_context["tool_specs"] = tool_specs_json()
        self.workflows.save(workflow)
        dataset = self.datasets.put_text(
            data,
            workflow_id=workflow.workflow_id,
            declared_format=declared_format.value if declared_format else None,
        )
        workflow.input = WorkflowInput(
            dataset_ref=dataset.storage_ref,
            input_hash=dataset.sha256,
            declared_format=declared_format,
        )
        self._event(
            workflow,
            ActorType.SYSTEM,
            "workflow_service",
            EventType.WORKFLOW_CREATED,
            "Mapping draft workflow created",
            output_refs=[dataset.storage_ref],
        )
        self._step(
            workflow,
            "workflow_created",
            StepStatus.COMPLETED,
            "Mapping draft workflow created",
            output_ref=dataset.storage_ref,
        )
        try:
            parser_result = self.parser_agent.run(data, declared_format, dataset.storage_ref)
            parsed: ParsedData = parser_result.data["parsed"]
            workflow.input.detected_format = parsed.format
            workflow.profile = parser_result.data["profile"]
            self._event(
                workflow,
                ActorType.AGENT,
                self.parser_agent.agent_id,
                EventType.AGENT_COMPLETED,
                parser_result.summary,
                metadata={"confidence": parser_result.confidence},
            )
            self._step(
                workflow,
                "parser",
                StepStatus.COMPLETED,
                parser_result.summary,
                issue_count=len(parser_result.issues),
            )
            return self._run_after_parse(
                workflow,
                parsed,
                instruction=clean_instruction,
                target_format=target_format,
                schema_id=schema_id,
                require_human_review=True,
                draft_review={
                    "mapping_goal": mapping_goal,
                    "source_fields": source_fields or [],
                    "target_fields": target_fields or [],
                    "evidence_ids": evidence_ids or [],
                },
            )
        except Exception as exc:
            self._fail_workflow(workflow, exc)
            self.workflows.save(workflow)
            return workflow

    def start_workflow_from_file(
        self,
        instruction: str,
        file_bytes: bytes,
        filename: str,
        target_format: DataFormat = DataFormat.JSON,
        schema_id: str | None = "lab_result_v1",
        require_human_review: bool = True,
        prefer_extractor: str = "auto",
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        """Start a workflow from a raw document file (PDF, DOCX, image, …).

        The raw upload is preserved as an immutable artifact. Extracted text is
        stored as a derived text dataset so submit_review() can re-parse safely
        after approval.
        """
        from ojtflow.data_tools.extract import (
            extract_document,
            sanitize_upload_filename,
            source_format_for_filename,
            validate_extractor_choice,
        )

        safe_filename = sanitize_upload_filename(filename)
        prefer_extractor = validate_extractor_choice(prefer_extractor)
        source_format = source_format_for_filename(safe_filename)
        raw_format = DataFormat(source_format) if source_format in {item.value for item in DataFormat} else DataFormat.UNKNOWN

        workflow = WorkflowState(
            owner_user_id=owner_user_id,
            user_instruction=instruction,
            intent=WorkflowIntent(
                target_format=target_format,
                requires_explanation=True,
                options={
                    "schema_id": schema_id,
                    "require_human_review": require_human_review,
                    "source_filename": safe_filename,
                    "prefer_extractor": prefer_extractor,
                    "source_format": source_format,
                },
            ),
            status=WorkflowStatus.RUNNING,
        )
        if request_id:
            workflow.handoff_context["request_id"] = request_id
        workflow.handoff_context["tool_specs"] = tool_specs_json()
        self.workflows.save(workflow)

        try:
            raw_dataset = self.datasets.put_bytes(
                file_bytes,
                workflow_id=workflow.workflow_id,
                source_kind="uploaded_file_raw",
                filename=safe_filename,
                declared_format=source_format,
                detected_format=source_format,
            )
            workflow.input = WorkflowInput(
                dataset_ref=raw_dataset.storage_ref,
                input_hash=raw_dataset.sha256,
                declared_format=raw_format,
                detected_format=raw_format,
            )
            workflow.handoff_context["raw_upload"] = {
                "filename": safe_filename,
                "source_format": source_format,
                "dataset_ref": raw_dataset.storage_ref,
                "sha256": raw_dataset.sha256,
                "byte_size": raw_dataset.byte_size,
            }
            self._event(
                workflow,
                ActorType.SYSTEM,
                "workflow_service",
                EventType.WORKFLOW_CREATED,
                f"Workflow created from uploaded file '{safe_filename}'",
                input_refs=[raw_dataset.storage_ref],
            )
            self._step(
                workflow,
                "workflow_created",
                StepStatus.COMPLETED,
                f"Uploaded file: {safe_filename}",
                output_ref=raw_dataset.storage_ref,
            )

            direct_format = _direct_upload_data_format(source_format)
            if direct_format:
                try:
                    extracted_text = file_bytes.decode("utf-8-sig")
                except UnicodeDecodeError as exc:
                    raise ToolExecutionError(
                        f"Uploaded {source_format} file must be UTF-8 encoded."
                    ) from exc
                extraction_meta = {
                    "extractor_used": "direct_text_upload",
                    "source_format": source_format,
                    "filename": safe_filename,
                    "page_count": None,
                    "warnings": [],
                }
                parsed_declared_format = direct_format
            else:
                extraction = extract_document(file_bytes, safe_filename, prefer=prefer_extractor)
                extracted_text = extraction.text
                extraction_meta = {
                    "extractor_used": extraction.extractor_used,
                    "source_format": extraction.source_format,
                    "filename": extraction.filename,
                    "page_count": extraction.page_count,
                    "warnings": extraction.warnings,
                }
                parsed_declared_format = DataFormat.MARKDOWN

            dataset = self.datasets.put_text(
                extracted_text,
                workflow_id=workflow.workflow_id,
                source_kind="uploaded_file_extracted_text",
                declared_format=parsed_declared_format.value,
                detected_format=parsed_declared_format.value,
            )
            workflow.input = WorkflowInput(
                dataset_ref=dataset.storage_ref,
                input_hash=dataset.sha256,
                declared_format=parsed_declared_format,
                detected_format=parsed_declared_format,
            )
            workflow.handoff_context["source_filename"] = safe_filename
            workflow.handoff_context["extraction"] = extraction_meta
            workflow.handoff_context["extracted_dataset_ref"] = dataset.storage_ref
            extractor_used = str(extraction_meta.get("extractor_used", "unknown"))
            extraction_warnings = extraction_meta.get("warnings") or []
            self._event(
                workflow,
                ActorType.TOOL,
                "document_extractor",
                EventType.TOOL_COMPLETED,
                f"Extracted {source_format} upload using {extractor_used}",
                input_refs=[raw_dataset.storage_ref],
                output_refs=[dataset.storage_ref],
                metadata=extraction_meta,
            )
            self._step(
                workflow,
                "document_extraction",
                StepStatus.COMPLETED,
                f"Extracted {source_format} upload using {extractor_used}",
                output_ref=dataset.storage_ref,
                issue_count=len(extraction_warnings),
            )

            parser_result = self.parser_agent.run(
                text=extracted_text,
                declared_format=parsed_declared_format,
                source_ref=dataset.storage_ref,
            )
            parsed: ParsedData = parser_result.data["parsed"]
            workflow.input.detected_format = parsed.format
            workflow.profile = parser_result.data["profile"]
            self._event(
                workflow,
                ActorType.AGENT,
                self.parser_agent.agent_id,
                EventType.AGENT_COMPLETED,
                parser_result.summary,
                metadata={
                    "confidence": parser_result.confidence,
                    "extractor": extraction_meta.get("extractor_used"),
                    "source_format": extraction_meta.get("source_format"),
                },
            )
            self._step(
                workflow,
                "parser",
                StepStatus.COMPLETED,
                parser_result.summary,
                issue_count=len(parser_result.issues),
            )

            return self._run_after_parse(
                workflow,
                parsed,
                instruction=instruction,
                target_format=target_format,
                schema_id=schema_id,
                require_human_review=require_human_review,
            )
        except Exception as exc:
            self._fail_workflow(workflow, exc)
            self.workflows.save(workflow)
            return workflow

    def validate_data(
        self,
        data: str,
        declared_format: DataFormat | None = None,
        schema_id: str | None = "lab_result_v1",
    ) -> dict:
        """Parse and validate data without creating a persisted workflow."""

        parser_result = self.parser_agent.run(
            text=data,
            declared_format=declared_format,
            source_ref="inline://validate",
        )
        parsed: ParsedData = parser_result.data["parsed"]
        profile = parser_result.data["profile"]
        schema = self._load_requested_schema(schema_id)
        validation_result = self.validation_agent.run(parsed, profile, schema)
        return {
            "status": "success",
            "detected_format": parsed.format,
            "profile": profile.model_dump(mode="json"),
            "validation_report": validation_result.data["validation_report"].model_dump(mode="json"),
        }

    def convert_data(
        self,
        data: str,
        declared_format: DataFormat | None = None,
        target_format: DataFormat = DataFormat.JSON,
    ) -> dict:
        """Parse and convert data without creating a persisted workflow."""

        parser_result = self.parser_agent.run(
            text=data,
            declared_format=declared_format,
            source_ref="inline://convert",
        )
        parsed: ParsedData = parser_result.data["parsed"]
        profile = parser_result.data["profile"]
        transformation_result = self.transformation_agent.run(
            parsed,
            target_format,
            plan=None,
        )
        output_text = transformation_result.data["output_text"]
        output = transformation_result.data["transformation_output"]
        metadata = output.model_dump(mode="json")
        metadata["source_format"] = parsed.format.value
        metadata["target_format"] = output.output_format.value
        metadata["source_row_count"] = profile.row_count
        metadata["target_row_count"] = output.diff_summary.get("target_row_count")
        metadata["output_hash"] = output.output_hash
        metadata["lossy"] = bool(output.warnings)
        metadata["actions_applied"] = output.diff_summary.get("actions_applied", [])
        return {
            "status": "success",
            "detected_format": parsed.format,
            "output_format": output.output_format,
            "output": output_text,
            "metadata": metadata,
        }

    def _run_after_parse(
        self,
        workflow: WorkflowState,
        parsed: ParsedData,
        *,
        instruction: str,
        target_format: DataFormat,
        schema_id: str | None,
        require_human_review: bool,
        draft_review: dict[str, Any] | None = None,
    ) -> WorkflowState:
        """Run retrieval, validation, review gating, and transformation."""

        if workflow.profile is None:
            raise NotFoundError("Workflow is missing a data profile after parsing")

        schema = self._load_requested_schema(
            schema_id,
            workflow_id=workflow.workflow_id,
        )
        fhir_context = self._profile_fhir_context(workflow, parsed)

        retrieval_package = self.retrieval_service.search_for_workflow(
            workflow_id=workflow.workflow_id,
            instruction=instruction,
            profile=workflow.profile,
            schema_id=schema_id,
            resource_type=fhir_context["resource_type"],
            query_terms=fhir_context["query_terms"],
            top_k=5,
        )
        retrieval_package.trace.request_id = _workflow_request_id(workflow)
        retrieval_package = self._persist_graph_context(
            retrieval_package,
            owner_user_id=workflow.owner_user_id,
            workflow_id=workflow.workflow_id,
        )
        evidence = retrieval_package.evidence
        workflow.retrieved_context = [*fhir_context["evidence"], *evidence]
        workflow.handoff_context["retrieval_trace"] = retrieval_package.trace.model_dump(
            mode="json"
        )
        workflow.handoff_context["retrieval_handoff"] = retrieval_package.handoff_context
        self._event(
            workflow,
            ActorType.AGENT,
            "retrieval_agent",
            EventType.RETRIEVAL_COMPLETED,
            f"Retrieved {format_count(len(evidence), 'trusted evidence item')}",
            metadata={
                "source_ids": [item.source_id for item in evidence],
                "strategy": retrieval_package.trace.strategy,
                "safety_flags": retrieval_package.trace.safety_flags,
                "warnings": retrieval_package.trace.warnings,
            },
        )
        self._step(
            workflow,
            "retrieval",
            StepStatus.COMPLETED,
            f"Retrieved {format_count(len(workflow.retrieved_context), 'trusted evidence item')}",
        )

        validation_result = self.validation_agent.run(parsed, workflow.profile, schema)
        workflow.validation_report = validation_result.data["validation_report"]
        workflow.schema_profile = {
            "schema_id": schema.get("$id") if schema else None,
            "schema_confidence": workflow.validation_report.schema_confidence,
        }
        self._event(
            workflow,
            ActorType.AGENT,
            self.validation_agent.agent_id,
            EventType.VALIDATION_COMPLETED,
            validation_result.summary,
            metadata={"severity_summary": workflow.validation_report.severity_summary},
        )
        self._step(
            workflow,
            "validation",
            StepStatus.COMPLETED,
            validation_result.summary,
            issue_count=len(workflow.validation_report.issues),
        )
        self._refresh_clinical_package(
            workflow,
            parsed,
            schema_id=schema_id,
        )

        plan = build_transformation_plan(workflow.validation_report, target_format)
        if draft_review is not None:
            plan.requires_review = True
        workflow.transformation_plan = plan
        safety_result = self.safety_agent.run(workflow.validation_report, plan)
        self._event(
            workflow,
            ActorType.AGENT,
            self.safety_agent.agent_id,
            EventType.AGENT_COMPLETED,
            safety_result.summary,
            severity=Severity.WARNING if safety_result.data["requires_review"] else Severity.INFO,
        )
        self._step(
            workflow,
            "safety_review_gate",
            StepStatus.COMPLETED,
            safety_result.summary,
            issue_count=len(safety_result.issues),
        )

        if (
            draft_review is None
            and require_human_review
            and safety_result.data["requires_review"]
        ):
            workflow.review = self._make_review(workflow, plan)
            workflow.status = WorkflowStatus.NEEDS_HUMAN_REVIEW
            self._event(
                workflow,
                ActorType.AGENT,
                "review_agent",
                EventType.REVIEW_REQUESTED,
                workflow.review.question,
                severity=Severity.WARNING,
                metadata={"review_id": workflow.review.review_id},
            )
            self._step(
                workflow,
                "human_review",
                StepStatus.PENDING,
                workflow.review.question,
                issue_count=len(workflow.validation_report.issues),
            )
            self._refresh_clinical_package(
                workflow,
                parsed,
                schema_id=schema_id,
            )
            workflow.touch()
            self.workflows.save(workflow)
            return workflow

        if draft_review is not None:
            workflow.review = self._make_mapping_draft_review(
                workflow,
                plan,
                draft_review,
            )
            workflow.status = WorkflowStatus.NEEDS_HUMAN_REVIEW
            self._event(
                workflow,
                ActorType.AGENT,
                "review_agent",
                EventType.REVIEW_REQUESTED,
                workflow.review.question,
                severity=Severity.WARNING,
                metadata={
                    "review_id": workflow.review.review_id,
                    "trigger": workflow.review.trigger,
                },
            )
            self._step(
                workflow,
                "human_review",
                StepStatus.PENDING,
                workflow.review.question,
                issue_count=len(workflow.validation_report.issues),
            )
            self._refresh_clinical_package(
                workflow,
                parsed,
                schema_id=schema_id,
            )
            workflow.touch()
            self.workflows.save(workflow)
            return workflow

        self._complete_transformation(workflow, parsed, target_format, plan)
        self.workflows.save(workflow)
        return workflow

    def create_review_task(
        self,
        *,
        question: str,
        proposed_action: dict[str, Any] | None = None,
        data: str | None = None,
        declared_format: DataFormat | None = None,
        schema_id: str | None = "lab_result_v1",
        source_context: dict[str, Any] | None = None,
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> WorkflowState:
        """Create a durable human-review task without executing a transformation."""

        clean_question = question.strip()
        if not clean_question:
            raise PolicyBlockedError("Review task question is required.")
        workflow = WorkflowState(
            owner_user_id=owner_user_id,
            user_instruction=f"Review task: {clean_question}",
            intent=WorkflowIntent(
                task_type="manual_review_task",
                target_format=DataFormat.JSON,
                requires_explanation=False,
                options={
                    "schema_id": schema_id,
                    "source": "assistant",
                    "review_task": True,
                },
            ),
            status=WorkflowStatus.NEEDS_HUMAN_REVIEW,
            handoff_context={
                "source_context": dict(source_context or {}),
                "tool_specs": tool_specs_json(),
            },
            risk_flags=["manual_review_task"],
        )
        if request_id:
            workflow.handoff_context["request_id"] = request_id
        self.workflows.save(workflow)
        output_refs: list[str] = []
        if data and data.strip():
            dataset = self.datasets.put_text(
                data,
                workflow_id=workflow.workflow_id,
                declared_format=declared_format.value if declared_format else None,
            )
            workflow.input = WorkflowInput(
                dataset_ref=dataset.storage_ref,
                input_hash=dataset.sha256,
                declared_format=declared_format,
            )
            output_refs.append(dataset.storage_ref)
        self._event(
            workflow,
            ActorType.SYSTEM,
            "workflow_service",
            EventType.WORKFLOW_CREATED,
            "Manual review task workflow created",
            output_refs=output_refs,
        )
        self._step(
            workflow,
            "workflow_created",
            StepStatus.COMPLETED,
            "Manual review task workflow created",
            output_ref=output_refs[0] if output_refs else None,
        )
        workflow.review = HumanReview(
            workflow_id=workflow.workflow_id,
            trigger="manual_assistant_review_task",
            question=clean_question,
            proposed_action={
                "review_task_type": "assistant_escalation",
                "schema_id": schema_id,
                **(proposed_action or {}),
            },
            allowed_decisions=[
                ReviewDecision.APPROVE,
                ReviewDecision.REJECT,
                ReviewDecision.CLARIFY,
                ReviewDecision.CANCEL,
            ],
        )
        self._event(
            workflow,
            ActorType.AGENT,
            "assistant",
            EventType.REVIEW_REQUESTED,
            clean_question,
            severity=Severity.WARNING,
            metadata={
                "review_id": workflow.review.review_id,
                "trigger": workflow.review.trigger,
            },
        )
        self._step(workflow, "human_review", StepStatus.PENDING, clean_question)
        workflow.touch()
        self.workflows.save(workflow)
        return workflow

    def _profile_fhir_context(
        self,
        workflow: WorkflowState,
        parsed: ParsedData,
    ) -> dict:
        """Attach lightweight FHIR-like profile context when JSON input carries resources."""

        empty = {"evidence": [], "resource_type": None, "query_terms": []}
        if parsed.format != DataFormat.JSON or not isinstance(parsed.content, dict):
            return empty
        if not (
            parsed.content.get("resourceType")
            or (
                parsed.content.get("resourceType") == "Bundle"
                and isinstance(parsed.content.get("entry"), list)
            )
        ):
            return empty

        profile_result = profile_fhir_like(json.dumps(parsed.content))
        profile = profile_result["profile"]
        evidence = profile_result["evidence"]
        profile_payload = profile.model_dump(mode="json")
        workflow.handoff_context["fhir_profile"] = profile_payload
        workflow.handoff_context["fhir_handoff"] = profile.handoff_context
        resource_type = _primary_fhir_resource_type(profile_payload)
        query_terms = list(profile.handoff_context.get("rag_query_terms", []))
        self._event(
            workflow,
            ActorType.AGENT,
            "fhir_agent",
            EventType.AGENT_COMPLETED,
            f"Profiled FHIR-like input with {format_count(len(profile.resource_counts), 'resource type')}",
            severity=Severity.WARNING if profile.issues else Severity.INFO,
            metadata={
                "resource_type": resource_type,
                "resource_counts": profile_payload.get("resource_counts", {}),
                "issues": profile_payload.get("issues", []),
            },
        )
        self._step(
            workflow,
            "fhir_profile",
            StepStatus.COMPLETED,
            f"Profiled FHIR-like input: {', '.join(query_terms) or 'resource detected'}",
            issue_count=len(profile.issues),
        )
        return {"evidence": evidence, "resource_type": resource_type, "query_terms": query_terms}

    def get_workflow(
        self,
        workflow_id: str,
        owner_user_id: str | None = None,
    ) -> WorkflowState:
        """Fetch a workflow."""

        workflow = self.workflows.get(workflow_id)
        self._assert_workflow_owner(workflow, owner_user_id)
        return workflow

    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]:
        """List workflows for product UI and audit surfaces."""

        return self.workflows.list(
            status=status,
            limit=limit,
            owner_user_id=owner_user_id,
        )

    def list_workflow_summaries(
        self,
        status: WorkflowStatus | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "updated_at",
        direction: str = "desc",
        owner_user_id: str | None = None,
    ) -> WorkflowSummaryPage:
        """List paginated workflow summaries for enterprise tables."""

        return self.workflows.list_summary(
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            reviews_only=False,
            review_status=None,
            owner_user_id=owner_user_id,
        )

    def list_review_summaries(
        self,
        status: str | None = "pending",
        q: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "updated_at",
        direction: str = "desc",
        owner_user_id: str | None = None,
    ) -> WorkflowSummaryPage:
        """List paginated review-backed workflow summaries."""

        page_result = self.workflows.list_summary(
            status=None,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            reviews_only=True,
            review_status=status,
            owner_user_id=owner_user_id,
        )
        return page_result

    def workflow_stats(self, owner_user_id: str | None = None) -> WorkflowStats:
        """Return aggregate workflow stats for command center surfaces."""

        return self.workflows.stats(owner_user_id=owner_user_id)

    def list_reviews(
        self,
        status: str | None = None,
        limit: int = 50,
        owner_user_id: str | None = None,
    ) -> list[WorkflowState]:
        """List workflows that have review objects attached."""

        if limit <= 0:
            return []

        review_status = None if status in {None, "all"} else status
        page_size = min(limit, 100)
        page = 1
        reviewed: list[WorkflowState] = []

        while len(reviewed) < limit:
            page_result = self.workflows.list_summary(
                page=page,
                page_size=page_size,
                sort="updated_at",
                direction="desc",
                reviews_only=True,
                review_status=review_status,
                owner_user_id=owner_user_id,
            )
            if not page_result.items:
                break

            for item in page_result.items:
                workflow = self.workflows.get(item.workflow_id)
                self._assert_workflow_owner(workflow, owner_user_id)
                if not workflow.review:
                    continue
                if review_status and workflow.review.status.value != review_status:
                    continue
                reviewed.append(workflow)
                if len(reviewed) >= limit:
                    break

            if page * page_size >= page_result.total:
                break
            page += 1

        return reviewed

    def list_schemas(self) -> list[dict]:
        """List trusted schema registry entries."""

        return self.knowledge.list_schemas()

    def search_retrieval(
        self,
        query: RetrievalQuery,
        owner_user_id: str | None = None,
        request_id: str | None = None,
    ) -> RetrievalPackage:
        """Run direct retrieval search."""

        if query.workflow_id:
            workflow = self.workflows.get(query.workflow_id)
            self._assert_workflow_owner(workflow, owner_user_id)
        self._load_requested_schema(query.schema_id, workflow_id=query.workflow_id)
        package = self.retrieval_service.search(query)
        package.trace.request_id = request_id
        package = self._persist_graph_context(
            package,
            owner_user_id=owner_user_id,
            workflow_id=query.workflow_id,
        )
        return package

    def plan_retrieval(
        self,
        query: RetrievalQuery,
        owner_user_id: str | None = None,
    ) -> RetrievalPlan:
        """Build direct retrieval plan without ranking evidence."""

        if query.workflow_id:
            workflow = self.workflows.get(query.workflow_id)
            self._assert_workflow_owner(workflow, owner_user_id)
        self._load_requested_schema(query.schema_id, workflow_id=query.workflow_id)
        return self.retrieval_service.plan(query)

    def list_retrieval_sources(self) -> list[RetrievalSource]:
        """List available retrieval source inventory."""

        return self.retrieval_service.list_sources()

    def list_graph_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[GraphContextRecord]:
        if self.graph_service is None:
            return []
        return self.graph_service.list_contexts(
            owner_user_id=owner_user_id,
            workflow_id=workflow_id,
            limit=limit,
        )

    def export_graph_contexts(
        self,
        *,
        owner_user_id: str | None,
        workflow_id: str | None = None,
        limit: int = 100,
        export_format: GraphExportFormat = "jsonl",
    ) -> GraphExport:
        if self.graph_service is None:
            from ojtflow.core.time import utc_now

            return GraphExport(
                format=export_format,
                content_type="application/x-ndjson",
                graph_count=0,
                node_count=0,
                edge_count=0,
                triple_count=0,
                generated_at=utc_now().isoformat(),
                content="",
            )
        return self.graph_service.export_contexts(
            owner_user_id=owner_user_id,
            workflow_id=workflow_id,
            limit=limit,
            export_format=export_format,
        )

    def graph_neighborhood(
        self,
        *,
        owner_user_id: str | None,
        query: GraphNeighborhoodQuery,
    ) -> GraphNeighborhood:
        if self.graph_service is None:
            from ojtflow.core.time import utc_now

            return GraphNeighborhood(
                query=query,
                graph_count=0,
                node_count=0,
                edge_count=0,
                triple_count=0,
                warnings=["Graph persistence is not configured."],
                generated_at=utc_now().isoformat(),
            )
        return self.graph_service.neighborhood(
            owner_user_id=owner_user_id,
            query=query,
        )

    def reindex_retrieval(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = True,
    ) -> dict:
        """Refresh retrieval index from configured trusted sources."""

        return self.retrieval_service.reindex(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def retrieval_integrity_report(
        self,
        *,
        include_seeded: bool = True,
        include_corpus: bool = False,
    ) -> RetrievalIntegrityReport:
        """Check retrieval index consistency against trusted knowledge sources."""

        return self.retrieval_service.integrity_report(
            include_seeded=include_seeded,
            include_corpus=include_corpus,
        )

    def _persist_graph_context(
        self,
        package: RetrievalPackage,
        *,
        owner_user_id: str | None,
        workflow_id: str | None,
    ) -> RetrievalPackage:
        if self.graph_service is None:
            return package
        request = package.handoff_context.get("search_request")
        if not isinstance(request, dict):
            return package
        query_payload = {**request, "workflow_id": workflow_id or request.get("workflow_id")}
        try:
            query = RetrievalQuery.model_validate(query_payload)
        except Exception:
            return package
        return self.graph_service.persist_retrieval_package(
            package,
            query,
            owner_user_id=owner_user_id,
        )

    def _load_requested_schema(
        self,
        schema_id: str | None,
        *,
        workflow_id: str | None = None,
    ) -> dict | None:
        """Load an explicitly requested schema.

        Missing named schemas must fail rather than downgrade validation.
        """

        if not schema_id:
            return None
        schema = self.knowledge.get_schema(schema_id)
        if schema is None:
            raise NotFoundError(
                f"Requested schema profile not found: {schema_id}",
                workflow_id=workflow_id,
                details={
                    "schema_id": schema_id,
                    "resolution": (
                        "Use a schema_id returned by GET /api/v1/schemas, "
                        "or set schema_id to null for explicit no-schema validation."
                    ),
                },
            )
        return schema

    def list_events(
        self,
        workflow_id: str,
        owner_user_id: str | None = None,
    ) -> list[WorkflowEvent]:
        """Fetch workflow events."""

        workflow = self.workflows.get(workflow_id)
        self._assert_workflow_owner(workflow, owner_user_id)
        return self.events.list_for_workflow(workflow_id)

    def get_workflow_output(
        self,
        workflow_id: str,
        owner_user_id: str | None = None,
    ) -> WorkflowOutputArtifact:
        """Return the generated output artifact for a workflow.

        The caller provides only a workflow ID. The storage ref is resolved from
        persisted workflow state so clients cannot read arbitrary local files.
        """

        workflow = self.workflows.get(workflow_id)
        self._assert_workflow_owner(workflow, owner_user_id)
        output = workflow.output.transformation if workflow.output else None
        if not output or not output.output_ref:
            raise NotFoundError(
                f"Workflow output not generated: {workflow_id}",
                workflow_id=workflow_id,
            )
        content = self._read_verified_text_artifact(
            storage_ref=output.output_ref,
            expected_hash=output.output_hash,
            workflow_id=workflow.workflow_id,
            artifact_label="output",
        )
        return WorkflowOutputArtifact(
            workflow_id=workflow.workflow_id,
            output_format=output.output_format,
            output_hash=output.output_hash,
            byte_size=len(content.encode("utf-8")),
            content=content,
            warnings=output.warnings,
            diff_summary=output.diff_summary,
        )

    def submit_review(
        self,
        review_id: str,
        decision: ReviewDecision,
        decided_by: str,
        payload: dict | None = None,
        owner_user_id: str | None = None,
    ) -> WorkflowState:
        """Apply a human review decision and resume if approved."""

        if not decided_by.strip():
            raise PolicyBlockedError("Review decision requires an explicit reviewer identity.")

        workflow = self.workflows.find_by_review_id(review_id)
        self._assert_workflow_owner(workflow, owner_user_id)
        if not workflow.review:
            raise NotFoundError(f"Review not found: {review_id}")
        if workflow.review.status != ReviewStatus.PENDING:
            raise PolicyBlockedError(
                f"Review is already decided: {review_id}",
                workflow_id=workflow.workflow_id,
                details={
                    "review_id": review_id,
                    "review_status": workflow.review.status.value,
                },
            )
        if decision not in workflow.review.allowed_decisions:
            raise PolicyBlockedError(
                f"Review decision is not allowed: {decision.value}",
                workflow_id=workflow.workflow_id,
                details={
                    "review_id": review_id,
                    "decision": decision.value,
                    "allowed_decisions": [
                        allowed.value for allowed in workflow.review.allowed_decisions
                    ],
                },
            )

        if decision == ReviewDecision.CLARIFY:
            workflow.review.request_clarification(requested_by=decided_by, payload=payload)
            workflow.status = WorkflowStatus.NEEDS_HUMAN_REVIEW
            workflow.touch()
            self._event(
                workflow,
                ActorType.USER,
                decided_by,
                EventType.REVIEW_DECIDED,
                f"Clarification requested for review: {review_id}",
                metadata={"review_id": review_id, "decision": decision.value},
            )
            self.workflows.save(workflow)
            return workflow

        plan_for_execution = workflow.transformation_plan
        if decision == ReviewDecision.APPROVE_WITH_EDITS:
            if not workflow.transformation_plan:
                raise NotFoundError(
                    "Workflow is missing transformation plan",
                    workflow_id=workflow.workflow_id,
                )
            plan_for_execution = _edited_plan_from_review_payload(
                payload=payload,
                current_plan=workflow.transformation_plan,
                workflow_id=workflow.workflow_id,
                review_id=review_id,
            )
            workflow.transformation_plan = plan_for_execution

        workflow.review.apply_decision(decision, decided_by=decided_by, payload=payload)
        self._complete_pending_step(
            workflow,
            "human_review",
            f"Review decision recorded: {decision.value}",
            StepStatus.COMPLETED if decision in {ReviewDecision.APPROVE, ReviewDecision.APPROVE_WITH_EDITS} else StepStatus.SKIPPED,
        )
        self._event(
            workflow,
            ActorType.USER,
            decided_by,
            EventType.REVIEW_DECIDED,
            f"Review decision recorded: {decision.value}",
            metadata={"review_id": review_id, "decision": decision.value},
        )

        if decision in {ReviewDecision.REJECT, ReviewDecision.CANCEL}:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.touch()
            self.workflows.save(workflow)
            return workflow
        if decision not in {ReviewDecision.APPROVE, ReviewDecision.APPROVE_WITH_EDITS}:
            raise PolicyBlockedError(f"Unsupported review decision: {decision}")

        if not workflow.input or not plan_for_execution:
            raise NotFoundError("Workflow is missing input or transformation plan")

        try:
            data = self._read_verified_text_artifact(
                storage_ref=workflow.input.dataset_ref,
                expected_hash=workflow.input.input_hash,
                workflow_id=workflow.workflow_id,
                artifact_label="input",
            )
            parser_result = self.parser_agent.run(
                data,
                workflow.input.declared_format,
                workflow.input.dataset_ref,
            )
            parsed: ParsedData = parser_result.data["parsed"]
            target_format = workflow.intent.target_format or DataFormat.JSON
            self._complete_transformation(workflow, parsed, target_format, plan_for_execution)
        except ArtifactIntegrityError as exc:
            self._fail_workflow(workflow, exc)
            self.workflows.save(workflow)
            raise
        except Exception as exc:
            self._fail_workflow(workflow, exc)
        self.workflows.save(workflow)
        return workflow

    def _read_verified_text_artifact(
        self,
        storage_ref: str,
        expected_hash: str | None,
        workflow_id: str,
        artifact_label: str,
    ) -> str:
        content = self.datasets.get_text(storage_ref)
        content_hash = sha256_text(content)
        if expected_hash and content_hash != expected_hash:
            raise ArtifactIntegrityError(
                f"Workflow {artifact_label} artifact failed integrity verification: {workflow_id}",
                workflow_id=workflow_id,
                details={"artifact": artifact_label},
            )
        return content

    def _complete_transformation(
        self,
        workflow: WorkflowState,
        parsed: ParsedData,
        target_format: DataFormat,
        plan: TransformationPlan | None,
    ) -> None:
        transform_result = self.transformation_agent.run(parsed, target_format, plan)
        output_text: str = transform_result.data["output_text"]
        transformation_output: TransformationOutput = transform_result.data["transformation_output"]
        output_record = self.datasets.put_text(
            output_text,
            workflow_id=workflow.workflow_id,
            source_kind="generated",
            declared_format=target_format.value,
            detected_format=target_format.value,
        )
        transformation_output.output_ref = output_record.storage_ref
        transformation_output.output_hash = output_record.sha256
        workflow.output = WorkflowOutput(
            transformation=transformation_output,
            validation_report_id=workflow.validation_report.report_id if workflow.validation_report else None,
        )
        self._event(
            workflow,
            ActorType.AGENT,
            self.transformation_agent.agent_id,
            EventType.TRANSFORMATION_COMPLETED,
            transform_result.summary,
            output_refs=[output_record.storage_ref],
            metadata=transformation_output.diff_summary,
        )
        self._step(
            workflow,
            "transformation",
            StepStatus.COMPLETED,
            transform_result.summary,
            output_ref=output_record.storage_ref,
        )

        if workflow.validation_report:
            explanation_result = self.explanation_agent.run(
                workflow.validation_report,
                transformation_output,
                workflow.retrieved_context,
            )
            workflow.explanation = explanation_result.data["explanation"]
            workflow.output.explanation_id = workflow.explanation.explanation_id
            self._event(
                workflow,
                ActorType.AGENT,
                self.explanation_agent.agent_id,
                EventType.EXPLANATION_COMPLETED,
                explanation_result.summary,
                metadata={"explanation_id": workflow.explanation.explanation_id},
            )
            self._step(
                workflow,
                "explanation",
                StepStatus.COMPLETED,
                explanation_result.summary,
                issue_count=len(workflow.explanation.unsupported_claims),
            )

        workflow.status = WorkflowStatus.COMPLETED
        workflow.touch()
        self._event(
            workflow,
            ActorType.SYSTEM,
            "workflow_service",
            EventType.WORKFLOW_COMPLETED,
            "Workflow completed",
            output_refs=[output_record.storage_ref],
        )
        self._step(
            workflow,
            "workflow_completed",
            StepStatus.COMPLETED,
            "Workflow completed",
            output_ref=output_record.storage_ref,
        )
        self._refresh_clinical_package(
            workflow,
            parsed,
            schema_id=workflow.intent.options.get("schema_id"),
            output_ref=output_record.storage_ref,
        )

    def _refresh_clinical_package(
        self,
        workflow: WorkflowState,
        parsed: ParsedData,
        *,
        schema_id: str | None,
        output_ref: str | None = None,
    ) -> None:
        package = build_clinical_package(
            workflow=workflow,
            parsed=parsed,
            schema_id=schema_id,
            output_ref=output_ref,
        )
        if package is None:
            return
        workflow.clinical_package = package
        workflow.handoff_context["clinical_package"] = {
            "package_id": package.package_id,
            "schema_version": package.schema_version,
            "resource_types": package.handoff_context.get("resource_types", []),
            "resource_count": package.handoff_context.get("resource_count", 0),
            "operation_outcome_issue_count": package.handoff_context.get(
                "operation_outcome_issue_count",
                0,
            ),
            "fhir_compliance": package.handoff_context.get("fhir_compliance"),
        }

    def _make_review(self, workflow: WorkflowState, plan: TransformationPlan) -> HumanReview:
        actions = [action.model_dump(mode="json") for action in plan.actions]
        return HumanReview(
            workflow_id=workflow.workflow_id,
            trigger="reviewable_transformation_plan",
            question="Approve the proposed data cleaning and conversion actions before execution?",
            proposed_action={"plan_id": plan.plan_id, "actions": actions},
        )

    def _make_mapping_draft_review(
        self,
        workflow: WorkflowState,
        plan: TransformationPlan,
        draft_review: dict[str, Any],
    ) -> HumanReview:
        actions = [action.model_dump(mode="json") for action in plan.actions]
        return HumanReview(
            workflow_id=workflow.workflow_id,
            trigger="mapping_draft_transform_plan",
            question="Review the drafted mapping and transformation plan before execution.",
            proposed_action={
                "draft_type": "assistant_mapping_draft",
                "plan_id": plan.plan_id,
                "target_format": plan.target_format.value,
                "actions": actions,
                "mapping_goal": draft_review.get("mapping_goal"),
                "source_fields": draft_review.get("source_fields") or [],
                "target_fields": draft_review.get("target_fields") or [],
                "evidence_ids": draft_review.get("evidence_ids") or [],
            },
        )

    def _event(
        self,
        workflow: WorkflowState,
        actor_type: ActorType,
        actor_id: str,
        event_type: EventType,
        summary: str,
        severity: Severity = Severity.INFO,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        metadata: dict | None = None,
    ) -> None:
        event_metadata = dict(metadata or {})
        request_id = _workflow_request_id(workflow)
        if request_id:
            event_metadata.setdefault("request_id", request_id)
        event = WorkflowEvent(
            workflow_id=workflow.workflow_id,
            request_id=request_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            severity=severity,
            summary=summary,
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            metadata=event_metadata,
        )
        self.events.append(event)
        workflow.audit_event_refs.append(event.event_id)

    def _step(
        self,
        workflow: WorkflowState,
        name: str,
        status: StepStatus,
        summary: str,
        output_ref: str | None = None,
        issue_count: int = 0,
    ) -> None:
        completed_at = None if status in {StepStatus.PENDING, StepStatus.RUNNING} else workflow.updated_at
        workflow.steps.append(
            WorkflowStep(
                name=name,
                status=status.value,
                summary=summary,
                completed_at=completed_at,
                output_ref=output_ref,
                issue_count=issue_count,
            )
        )

    def _complete_pending_step(
        self,
        workflow: WorkflowState,
        name: str,
        summary: str,
        status: StepStatus,
    ) -> None:
        for step in reversed(workflow.steps):
            if step.name == name and step.status == StepStatus.PENDING.value:
                step.status = status.value
                step.summary = summary
                step.completed_at = workflow.updated_at
                return
        self._step(workflow, name, status, summary)

    def _fail_workflow(self, workflow: WorkflowState, exc: Exception) -> None:
        workflow.status = WorkflowStatus.FAILED
        workflow.risk_flags.append(type(exc).__name__)
        workflow.failure = WorkflowFailure(
            code=_failure_code(exc),
            message=str(exc),
            error_type=type(exc).__name__,
            details=exc.details if isinstance(exc, OJTFlowError) else {},
        )
        workflow.touch()
        self._event(
            workflow,
            ActorType.SYSTEM,
            "workflow_service",
            EventType.WORKFLOW_FAILED,
            str(exc),
            severity=Severity.ERROR,
            metadata={"error_type": type(exc).__name__},
        )
        self._step(
            workflow,
            "workflow_failed",
            StepStatus.FAILED,
            str(exc),
            issue_count=1,
        )

    @staticmethod
    def _assert_workflow_owner(
        workflow: WorkflowState,
        owner_user_id: str | None,
    ) -> None:
        if owner_user_id is not None and workflow.owner_user_id != owner_user_id:
            raise NotFoundError(f"Workflow not found: {workflow.workflow_id}")


def _failure_code(exc: Exception) -> str:
    if isinstance(exc, ArtifactIntegrityError):
        return "artifact_integrity_error"
    if isinstance(exc, NotFoundError):
        return "not_found"
    if isinstance(exc, PolicyBlockedError):
        return "policy_blocked"
    if isinstance(exc, UploadTooLargeError):
        return "upload_too_large"
    if isinstance(exc, UnsupportedUploadError):
        return "unsupported_upload"
    if isinstance(exc, ToolExecutionError):
        return "tool_execution_error"
    if isinstance(exc, OJTFlowError):
        return "ojtflow_error"
    return "workflow_failed"


def _workflow_request_id(workflow: WorkflowState) -> str | None:
    value = workflow.handoff_context.get("request_id")
    return value if isinstance(value, str) and value else None


def _direct_upload_data_format(source_format: str) -> DataFormat | None:
    """Return a parser format for uploads that do not need document extraction."""

    return {
        "csv": DataFormat.CSV,
        "json": DataFormat.JSON,
        "yaml": DataFormat.YAML,
        "markdown": DataFormat.MARKDOWN,
        "text": DataFormat.MARKDOWN,
    }.get(source_format)


def _edited_plan_from_review_payload(
    *,
    payload: dict | None,
    current_plan: TransformationPlan,
    workflow_id: str,
    review_id: str,
) -> TransformationPlan:
    if not isinstance(payload, dict) or not payload:
        raise PolicyBlockedError(
            "approve_with_edits requires explicit edited transformation actions.",
            workflow_id=workflow_id,
            details={"review_id": review_id, "required": "payload.actions"},
        )

    plan_payload = payload.get("transformation_plan", payload)
    if not isinstance(plan_payload, dict):
        raise PolicyBlockedError(
            "approve_with_edits transformation_plan payload must be an object.",
            workflow_id=workflow_id,
            details={"review_id": review_id},
        )

    target_format = plan_payload.get("target_format")
    if target_format and target_format != current_plan.target_format.value:
        raise PolicyBlockedError(
            "approve_with_edits cannot change the workflow target format.",
            workflow_id=workflow_id,
            details={
                "review_id": review_id,
                "target_format": target_format,
                "expected_target_format": current_plan.target_format.value,
            },
        )

    raw_actions = plan_payload.get("actions")
    if not isinstance(raw_actions, list) or not raw_actions:
        raise PolicyBlockedError(
            "approve_with_edits requires at least one edited transformation action.",
            workflow_id=workflow_id,
            details={"review_id": review_id, "required": "payload.actions"},
        )

    actions: list[TransformationAction] = []
    for index, raw_action in enumerate(raw_actions):
        if not isinstance(raw_action, dict):
            raise PolicyBlockedError(
                "approve_with_edits actions must be objects.",
                workflow_id=workflow_id,
                details={"review_id": review_id, "action_index": index},
            )
        try:
            action = TransformationAction.model_validate(raw_action)
        except ValueError as exc:
            raise PolicyBlockedError(
                "approve_with_edits action payload is invalid.",
                workflow_id=workflow_id,
                details={
                    "review_id": review_id,
                    "action_index": index,
                    "validation_error": str(exc),
                },
            ) from exc
        if action.action not in SUPPORTED_REVIEW_EDIT_ACTIONS:
            raise PolicyBlockedError(
                "approve_with_edits action is not supported by the deterministic transformer.",
                workflow_id=workflow_id,
                details={
                    "review_id": review_id,
                    "action_index": index,
                    "action": action.action,
                    "supported_actions": sorted(SUPPORTED_REVIEW_EDIT_ACTIONS),
                },
            )
        actions.append(action)

    return TransformationPlan(
        plan_id=current_plan.plan_id,
        target_format=current_plan.target_format,
        actions=actions,
        requires_review=any(action.requires_review for action in actions),
    )


def _primary_fhir_resource_type(profile_payload: dict) -> str | None:
    resource_type = profile_payload.get("resource_type")
    if resource_type and resource_type != "Bundle":
        return str(resource_type)
    resource_counts = profile_payload.get("resource_counts")
    if isinstance(resource_counts, dict) and resource_counts:
        non_bundle = sorted(key for key in resource_counts if key != "Bundle")
        if non_bundle:
            return str(non_bundle[0])
        return str(sorted(resource_counts)[0])
    return str(resource_type) if resource_type else None
