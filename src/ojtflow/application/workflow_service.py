"""Workflow orchestration use case."""

from __future__ import annotations

from ojtflow.agents.explanation_agent import ExplanationAgent
from ojtflow.agents.parser_agent import ParserAgent
from ojtflow.agents.safety_agent import SafetyAgent
from ojtflow.agents.transformation_agent import TransformationAgent
from ojtflow.agents.validation_agent import ValidationAgent
from ojtflow.application.ports import (
    DatasetStore,
    EventRepository,
    KnowledgeRepository,
    RetrievalRepository,
    WorkflowRepository,
)
from ojtflow.application.retrieval_service import RetrievalService
from ojtflow.application.tool_registry import tool_specs_json
from ojtflow.core.contracts.data import ParsedData, TransformationOutput, TransformationPlan
from ojtflow.core.contracts.enums import (
    ActorType,
    DataFormat,
    EventType,
    ReviewDecision,
    Severity,
    StepStatus,
    WorkflowStatus,
)
from ojtflow.core.contracts.events import WorkflowEvent
from ojtflow.core.contracts.retrieval import RetrievalPackage, RetrievalQuery, RetrievalSource
from ojtflow.core.contracts.review import HumanReview
from ojtflow.core.contracts.workflow import (
    WorkflowInput,
    WorkflowIntent,
    WorkflowOutput,
    WorkflowState,
    WorkflowStep,
)
from ojtflow.core.errors import NotFoundError, PolicyBlockedError
from ojtflow.data_tools.transform_plan import build_transformation_plan


class WorkflowService:
    """Coordinates the backbone workflow without depending on web or DB frameworks."""

    def __init__(
        self,
        datasets: DatasetStore,
        workflows: WorkflowRepository,
        events: EventRepository,
        knowledge: KnowledgeRepository,
        retrieval: RetrievalRepository,
    ) -> None:
        self.datasets = datasets
        self.workflows = workflows
        self.events = events
        self.knowledge = knowledge
        self.retrieval_service = RetrievalService(retrieval)
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
    ) -> WorkflowState:
        """Start and run a workflow until completion or review pause."""

        workflow = WorkflowState(
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

    def start_workflow_from_file(
        self,
        instruction: str,
        file_bytes: bytes,
        filename: str,
        target_format: DataFormat = DataFormat.JSON,
        schema_id: str | None = "lab_result_v1",
        require_human_review: bool = True,
        prefer_extractor: str = "auto",
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

            extraction = extract_document(file_bytes, safe_filename, prefer=prefer_extractor)
            extracted_text = extraction.text
            extraction_meta = {
                "extractor_used": extraction.extractor_used,
                "source_format": extraction.source_format,
                "filename": extraction.filename,
                "page_count": extraction.page_count,
                "warnings": extraction.warnings,
            }

            dataset = self.datasets.put_text(
                extracted_text,
                workflow_id=workflow.workflow_id,
                source_kind="uploaded_file_extracted_text",
                declared_format=DataFormat.MARKDOWN.value,
                detected_format=DataFormat.MARKDOWN.value,
            )
            workflow.input = WorkflowInput(
                dataset_ref=dataset.storage_ref,
                input_hash=dataset.sha256,
                declared_format=DataFormat.MARKDOWN,
                detected_format=DataFormat.MARKDOWN,
            )
            workflow.handoff_context["source_filename"] = safe_filename
            workflow.handoff_context["extraction"] = extraction_meta
            workflow.handoff_context["extracted_dataset_ref"] = dataset.storage_ref
            self._event(
                workflow,
                ActorType.TOOL,
                "document_extractor",
                EventType.TOOL_COMPLETED,
                f"Extracted {source_format} upload using {extraction.extractor_used}",
                input_refs=[raw_dataset.storage_ref],
                output_refs=[dataset.storage_ref],
                metadata=extraction_meta,
            )
            self._step(
                workflow,
                "document_extraction",
                StepStatus.COMPLETED,
                f"Extracted {source_format} upload using {extraction.extractor_used}",
                output_ref=dataset.storage_ref,
                issue_count=len(extraction.warnings),
            )

            parser_result = self.parser_agent.run(
                text=extracted_text,
                declared_format=DataFormat.MARKDOWN,
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

    def _run_after_parse(
        self,
        workflow: WorkflowState,
        parsed: ParsedData,
        *,
        instruction: str,
        target_format: DataFormat,
        schema_id: str | None,
        require_human_review: bool,
    ) -> WorkflowState:
        """Run retrieval, validation, review gating, and transformation."""

        if workflow.profile is None:
            raise NotFoundError("Workflow is missing a data profile after parsing")

        retrieval_package = self.retrieval_service.search_for_workflow(
            workflow_id=workflow.workflow_id,
            instruction=instruction,
            profile=workflow.profile,
            schema_id=schema_id,
            top_k=5,
        )
        evidence = retrieval_package.evidence
        workflow.retrieved_context = evidence
        workflow.handoff_context["retrieval_trace"] = retrieval_package.trace.model_dump(
            mode="json"
        )
        workflow.handoff_context["retrieval_handoff"] = retrieval_package.handoff_context
        self._event(
            workflow,
            ActorType.AGENT,
            "retrieval_agent",
            EventType.RETRIEVAL_COMPLETED,
            f"Retrieved {len(evidence)} trusted evidence item(s)",
            metadata={
                "source_ids": [item.source_id for item in evidence],
                "strategy": retrieval_package.trace.strategy,
                "warnings": retrieval_package.trace.warnings,
            },
        )
        self._step(
            workflow,
            "retrieval",
            StepStatus.COMPLETED,
            f"Retrieved {len(evidence)} trusted evidence item(s)",
        )

        schema = self.knowledge.get_schema(schema_id)
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

        plan = build_transformation_plan(workflow.validation_report, target_format)
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

        if require_human_review and safety_result.data["requires_review"]:
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
            workflow.touch()
            self.workflows.save(workflow)
            return workflow

        self._complete_transformation(workflow, parsed, target_format, plan)
        self.workflows.save(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> WorkflowState:
        """Fetch a workflow."""

        return self.workflows.get(workflow_id)

    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowState]:
        """List workflows for product UI and audit surfaces."""

        return self.workflows.list(status=status, limit=limit)

    def list_reviews(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowState]:
        """List workflows that have review objects attached."""

        workflows = self.workflows.list(limit=max(limit * 3, limit))
        reviewed = [workflow for workflow in workflows if workflow.review]
        if status:
            reviewed = [
                workflow
                for workflow in reviewed
                if workflow.review and workflow.review.status.value == status
            ]
        return reviewed[:limit]

    def list_schemas(self) -> list[dict]:
        """List trusted schema registry entries."""

        return self.knowledge.list_schemas()

    def search_retrieval(self, query: RetrievalQuery) -> RetrievalPackage:
        """Run direct retrieval search."""

        return self.retrieval_service.search(query)

    def list_retrieval_sources(self) -> list[RetrievalSource]:
        """List available retrieval source inventory."""

        return self.retrieval_service.list_sources()

    def list_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Fetch workflow events."""

        return self.events.list_for_workflow(workflow_id)

    def submit_review(
        self,
        review_id: str,
        decision: ReviewDecision,
        decided_by: str = "user",
        payload: dict | None = None,
    ) -> WorkflowState:
        """Apply a human review decision and resume if approved."""

        workflow = self.workflows.find_by_review_id(review_id)
        if not workflow.review:
            raise NotFoundError(f"Review not found: {review_id}")

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
        if decision == ReviewDecision.CLARIFY:
            workflow.status = WorkflowStatus.NEEDS_HUMAN_REVIEW
            workflow.touch()
            self.workflows.save(workflow)
            return workflow
        if decision not in {ReviewDecision.APPROVE, ReviewDecision.APPROVE_WITH_EDITS}:
            raise PolicyBlockedError(f"Unsupported review decision: {decision}")

        if not workflow.input or not workflow.transformation_plan:
            raise NotFoundError("Workflow is missing input or transformation plan")

        try:
            data = self.datasets.get_text(workflow.input.dataset_ref)
            parser_result = self.parser_agent.run(
                data,
                workflow.input.declared_format,
                workflow.input.dataset_ref,
            )
            parsed: ParsedData = parser_result.data["parsed"]
            target_format = workflow.intent.target_format or DataFormat.JSON
            self._complete_transformation(workflow, parsed, target_format, workflow.transformation_plan)
        except Exception as exc:
            self._fail_workflow(workflow, exc)
        self.workflows.save(workflow)
        return workflow

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

    def _make_review(self, workflow: WorkflowState, plan: TransformationPlan) -> HumanReview:
        actions = [action.model_dump(mode="json") for action in plan.actions]
        return HumanReview(
            workflow_id=workflow.workflow_id,
            trigger="reviewable_transformation_plan",
            question="Approve the proposed data cleaning and conversion actions before execution?",
            proposed_action={"plan_id": plan.plan_id, "actions": actions},
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
        event = WorkflowEvent(
            workflow_id=workflow.workflow_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            severity=severity,
            summary=summary,
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            metadata=metadata or {},
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
