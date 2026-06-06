import json
import re
from pathlib import Path

from fastapi.routing import APIRoute

from ojtflow.interfaces.api.app import create_app


REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = REPO_ROOT / "frontend" / "src" / "features"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
FRONTEND_E2E = REPO_ROOT / "frontend" / "e2e"
IMPORT_RE = re.compile(r"""from\s+["']([^"']+)["']""")
FETCH_RE = re.compile(r"\bfetch\s*\(")
BROWSER_STORAGE_RE = re.compile(r"\b(localStorage|sessionStorage|document\.cookie)\b")
FULL_PAGE_RELOAD_RE = re.compile(r"\b(?:window\.)?location\.reload\s*\(")
PLAYWRIGHT_CONTEXT_POST_RE = re.compile(r"context\.request\.post\s*\(")
CLEANUP_SCRIPT = REPO_ROOT / "frontend" / "scripts" / "cleanup-e2e-artifacts.mjs"
LOCAL_CLEANUP_SCRIPT = (
    REPO_ROOT / "frontend" / "scripts" / "cleanup-e2e-local-artifacts.mjs"
)
PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
RELEASE_CHECK = REPO_ROOT / "scripts" / "release-check.sh"
AUTH_PROVIDER = REPO_ROOT / "frontend" / "src" / "app" / "auth.tsx"
APP_PROVIDERS = REPO_ROOT / "frontend" / "src" / "app" / "providers.tsx"
ERROR_BOUNDARY = REPO_ROOT / "frontend" / "src" / "app" / "error-boundary.tsx"
API_MODULE = REPO_ROOT / "frontend" / "src" / "api.ts"
APP_SHELL = REPO_ROOT / "frontend" / "src" / "components" / "layout" / "app-shell.tsx"
FRONTEND_TYPES = REPO_ROOT / "frontend" / "src" / "types.ts"
WORKFLOW_DETAIL = (
    REPO_ROOT / "frontend" / "src" / "features" / "workflows" / "workflow-detail.tsx"
)
WORKFLOW_DETAIL_SPLIT_FILES = [
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-chrome.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-review.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "workflows"
    / "workflow-detail-sections.tsx",
]
WORKBENCH_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-page.tsx"
)
GUIDE_PANEL = REPO_ROOT / "frontend" / "src" / "components" / "ui" / "guide-panel.tsx"
RETRIEVAL_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "retrieval" / "retrieval-page.tsx"
)
SETTINGS_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "settings" / "settings-page.tsx"
)
ASSISTANT_PAGE = (
    REPO_ROOT / "frontend" / "src" / "features" / "assistant" / "assistant-page.tsx"
)
HELP_PAGE = REPO_ROOT / "frontend" / "src" / "features" / "help" / "help-page.tsx"
WORKBENCH_SPLIT_FILES = [
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-controls.tsx",
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-examples.ts",
    REPO_ROOT / "frontend" / "src" / "features" / "workbench" / "workbench-utils.ts",
]
FRONTEND_API_CALL_RE = re.compile(
    r"\b(?P<fn>request|fetchApi)(?:<[^>]+>)?\(\s*(?P<quote>[`\"])(?P<path>[^`\"]*/[^`\"]*)(?P=quote)"
)


def _frontend_source_files() -> list[Path]:
    return sorted(path for path in FRONTEND_SRC.rglob("*") if path.suffix in {".ts", ".tsx"})


def test_frontend_features_do_not_import_other_features() -> None:
    violations: list[str] = []

    for source_file in sorted(
        path for path in FEATURES_DIR.rglob("*") if path.suffix in {".ts", ".tsx"}
    ):
        current_feature = source_file.relative_to(FEATURES_DIR).parts[0]
        text = source_file.read_text(encoding="utf-8")
        for specifier in IMPORT_RE.findall(text):
            if not specifier.startswith("."):
                continue

            imported_path = (source_file.parent / specifier).resolve()
            try:
                relative_import = imported_path.relative_to(FEATURES_DIR)
            except ValueError:
                continue

            imported_feature = relative_import.parts[0]
            if imported_feature != current_feature:
                violations.append(
                    f"{source_file.relative_to(REPO_ROOT)} imports {specifier!r} from feature {imported_feature!r}",
                )

    assert violations == []


def test_frontend_network_calls_stay_behind_api_boundary() -> None:
    violations: list[str] = []
    allowed_fetch_file = FRONTEND_SRC / "api.ts"

    for source_file in _frontend_source_files():
        if source_file == allowed_fetch_file:
            continue

        text = source_file.read_text(encoding="utf-8")
        if FETCH_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} calls fetch outside src/api.ts",
            )

    assert violations == []


def test_frontend_features_use_server_state_boundary() -> None:
    violations: list[str] = []

    for source_file in sorted(
        path for path in FEATURES_DIR.rglob("*") if path.suffix in {".ts", ".tsx"}
    ):
        text = source_file.read_text(encoding="utf-8")
        for specifier in IMPORT_RE.findall(text):
            if specifier.endswith("/api") or specifier in {"../../api", "../api"}:
                violations.append(
                    f"{source_file.relative_to(REPO_ROOT)} imports API module directly",
                )

    assert violations == []


def test_workflow_detail_shell_stays_split_by_responsibility() -> None:
    workflow_detail = WORKFLOW_DETAIL.read_text(encoding="utf-8")

    assert len(workflow_detail.splitlines()) <= 240
    assert "useWorkflowQuery" in workflow_detail
    assert "useWorkflowEventsQuery" in workflow_detail
    assert "useReviewDecisionMutation" in workflow_detail
    assert "useWorkflowOutputQuery" not in workflow_detail
    assert "navigator.clipboard" not in workflow_detail
    assert "toast." not in workflow_detail
    assert "<Table" not in workflow_detail
    for split_file in WORKFLOW_DETAIL_SPLIT_FILES:
        assert split_file.exists()

    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    for split_file in [WORKFLOW_DETAIL, *WORKFLOW_DETAIL_SPLIT_FILES]:
        assert split_file.name in frontend_architecture


def test_workbench_shell_stays_split_by_responsibility() -> None:
    workbench_page = WORKBENCH_PAGE.read_text(encoding="utf-8")

    assert len(workbench_page.splitlines()) <= 430
    assert "useCreateWorkflowMutation" in workbench_page
    assert "useUploadWorkflowMutation" in workbench_page
    assert "inputExamples" in workbench_page
    assert "const sampleCsv" not in workbench_page
    assert "function validateUploadFile" not in workbench_page
    assert "function WorkbenchControlPlane" not in workbench_page
    for split_file in WORKBENCH_SPLIT_FILES:
        assert split_file.exists()

    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    for split_file in [WORKBENCH_PAGE, *WORKBENCH_SPLIT_FILES]:
        assert split_file.name in frontend_architecture


def test_retrieval_page_surfaces_runtime_ranking_stack() -> None:
    retrieval_page = RETRIEVAL_PAGE.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "rankingStackFromPackage" in retrieval_page
    assert "diversityFromPackage" in retrieval_page
    assert "scoreComponentsFromHit" in retrieval_page
    assert "ScoreExplanation" in retrieval_page
    assert "Score explanation" in retrieval_page
    assert "QualitySignalList" in retrieval_page
    assert "QualitySignalMetadataDetails" in retrieval_page
    assert "SectionHelpText" in retrieval_page
    assert "Quality signals explain why the evidence package" in retrieval_page
    assert "Signal details" in retrieval_page
    assert "qualitySignalMetadataDetails" in retrieval_page
    assert "Retrieval quality" in retrieval_page
    assert "Safety-sensitive context detected" in retrieval_page
    assert "Backend warnings about search coverage" in retrieval_page
    assert "quality_signals" in retrieval_page
    assert "quality_summary" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "Readiness" in retrieval_page
    assert "qualitySummaryTone" in retrieval_page
    assert "qualitySignalBadgeVariant" in retrieval_page
    assert "queryVariantsFromTrace" in retrieval_page
    assert "QueryVariantList" in retrieval_page
    assert "Query rewrites" in retrieval_page
    assert "Query rewrites are backend-generated search variants" in retrieval_page
    assert "query_variant_details" in retrieval_page
    assert "QueryProfileCard" in retrieval_page
    assert "queryProfileValue" in retrieval_page
    assert "query_profile" in retrieval_page
    assert "QueryAspectPlan" in retrieval_page
    assert "queryAspectsValue" in retrieval_page
    assert "query_aspects" in retrieval_page
    assert "Search aspect plan" in retrieval_page
    assert "Query diagnostics explain parser" in retrieval_page
    assert "SearchHintMetadata" in retrieval_page
    assert "Route details" in retrieval_page
    assert "Parameter examples" in retrieval_page
    assert "Lineage follow-up" in retrieval_page
    assert "Endpoint scope" in retrieval_page
    assert "Selected terminology terms" in retrieval_page
    assert "Selected unit candidates" in retrieval_page
    assert "selected_terms" in retrieval_page
    assert "selected_unit_candidates" in retrieval_page
    assert "capability_warning" in retrieval_page
    assert "searchHintParameterExamples" in retrieval_page
    assert "searchHintLineageFollowup" in retrieval_page
    assert "metadata?: Record<string, unknown>" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "RunComparisonQueryAspects" in retrieval_page
    assert "queryAspectComparisonBetweenRuns" in retrieval_page
    assert "queryAspectComparison" in retrieval_page
    assert "Search aspects" in retrieval_page
    assert "queryAspectFilterEntries" in retrieval_page
    assert "Suggested by search aspect" in retrieval_page
    assert "entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`" in retrieval_page
    assert "RunComparisonCoverage" in retrieval_page
    assert "coverageComparisonBetweenRuns" in retrieval_page
    assert "coverageComparison" in retrieval_page
    assert "coverage_diagnostics_changed" in retrieval_page
    assert "QueryAspectMatchExplanation" in retrieval_page
    assert "queryAspectMatchesFromHit" in retrieval_page
    assert "Aspect support" in retrieval_page
    assert "ConceptMatchExplanation" in retrieval_page
    assert "conceptMatchesFromHit" in retrieval_page
    assert "Concept grounding" in retrieval_page
    assert "concept_grounding_requirements" in retrieval_page
    assert "HitEvidenceAuditStrip" in retrieval_page
    assert "Evidence support summary" in retrieval_page
    assert "EvidenceSupportSummary" in retrieval_page
    assert "support_summary: evidenceSupportSummary(hit, provenanceEntries)" in retrieval_page
    assert "EvidenceSupportMatrixCard" in retrieval_page
    assert "EvidenceSupportMobileField" in retrieval_page
    assert "md:hidden" in retrieval_page
    assert "hidden overflow-auto rounded-md border border-border bg-card md:block" in retrieval_page
    assert "EvidenceUseGuidancePanel" in retrieval_page
    assert "Evidence interpretation guidance" in retrieval_page
    assert "Evidence interpretation help" in retrieval_page
    assert "EvidenceUsabilitySummaryPanel" in retrieval_page
    assert "Evidence usability summary" in retrieval_page
    assert "Usability summary" in retrieval_page
    assert "evidenceUsabilitySummary" in retrieval_page
    assert "usability_summary: evidenceUsabilitySummary" in retrieval_page
    assert "evidenceUseGuidance" in retrieval_page
    assert "evidenceUseGuidanceReasons" in retrieval_page
    assert "Use with provenance check" in retrieval_page
    assert "Review before relying on it" in retrieval_page
    assert "Weak evidence support" in retrieval_page
    assert "missing medical grounding" in retrieval_page
    assert "judged ${judgmentLabel(judgment.value)}" in retrieval_page
    assert "matched_term_count" in retrieval_page
    assert "ranking_signal_count" in retrieval_page
    assert "EvidenceProvenanceSummary" in retrieval_page
    assert "Evidence provenance" in retrieval_page
    assert "provenanceEntriesFromEvidence" in retrieval_page
    assert "provenanceHrefForLocator" in retrieval_page
    assert "https://pubmed.ncbi.nlm.nih.gov" in retrieval_page
    assert "https://doi.org" in retrieval_page
    assert "Copy evidence" in retrieval_page
    assert "Copy evidence JSON" in retrieval_page
    assert "Evidence JSON report help" in retrieval_page
    assert "useCopyFeedback" in retrieval_page
    assert "markCopied" in retrieval_page
    assert "clearCopied" in retrieval_page
    assert "Copied" in retrieval_page
    assert "evidenceReportFromHit" in retrieval_page
    assert "retrieval_evidence_hit" in retrieval_page
    assert "RunComparisonConceptGrounding" in retrieval_page
    assert "conceptGroundingComparisonBetweenRuns" in retrieval_page
    assert "conceptGroundingComparison" in retrieval_page
    assert "concept_grounding_changed" in retrieval_page
    assert "serverSearchSignatureFromPackage" in retrieval_page
    assert "Search signature" in retrieval_page
    assert "search_signature: comparison.activeSummary.serverSignature" in retrieval_page
    assert "qualityPolicyFromPackage" in retrieval_page
    assert "Quality policy" in retrieval_page
    assert "query_profiles" in retrieval_page
    assert "queryProfileSummaryFromPackage" in retrieval_page
    assert "queryProfile: queryProfileSummaryFromPackage(packageData)" in retrieval_page
    assert "Profile: {run.summary.queryProfile.label}" in retrieval_page
    assert "SearchRunEvidenceSummary" in retrieval_page
    assert "searchRunRemediationSummary" in retrieval_page
    assert "searchRunScopeLabels" in retrieval_page
    assert "Run scope" in retrieval_page
    assert "Run remediation:" in retrieval_page
    assert "SearchAnswerCard" in retrieval_page
    assert "Search answer" in retrieval_page
    assert "EvidenceInterpretationPanel" in retrieval_page
    assert "Evidence interpretation" in retrieval_page
    assert "Why the top result matched" in retrieval_page
    assert "evidenceInterpretationSummary" in retrieval_page
    assert "InterpretationCard" in retrieval_page
    assert "packageData.interpretation" in retrieval_page
    assert "RetrievalInterpretation" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "StandardSearchPlanPanel" in retrieval_page
    assert "Healthcare search plan" in retrieval_page
    assert "Backend-selected playbook for the next standards-aware search" in retrieval_page
    assert "StandardSearchMatchReasons" in retrieval_page
    assert "Matched by" in retrieval_page
    assert "matched_fields" in retrieval_page
    assert "matched_query_aspects" in retrieval_page
    assert "retrievalStandardSearchPlanReport" in retrieval_page
    assert "standard_search_plan" in retrieval_page
    assert "RetrievalStandardSearchPlan" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "searchAnswerReportFromPackage" in retrieval_page
    assert "retrieval_search_answer" in retrieval_page
    assert "medicalSearchHintReport" in retrieval_page
    assert "medical_search_hints" in retrieval_page
    assert "route_details" in retrieval_page
    assert "retrievalDiversityReport" in retrieval_page
    assert "diversity: retrievalDiversityReport(packageData)" in retrieval_page
    assert "retrievalInterpretationReport" in retrieval_page
    assert "Copy answer JSON" in retrieval_page
    assert "This is an evidence retrieval summary for workflow operations" in retrieval_page
    assert "it is not clinical advice" in retrieval_page
    assert "remediationSummary: string | null" in retrieval_page
    assert "packageData.remediation_summary" in retrieval_page
    assert "handoff_context.remediation_summary" in retrieval_page
    assert "Top action" in retrieval_page
    assert "qualitySummary: packageData.quality_summary ?? null" in retrieval_page
    assert "qualitySummaryFingerprint" in retrieval_page
    assert "qualitySummaryChanged" in retrieval_page
    assert "quality_score: comparison.qualityScoreDelta" in retrieval_page
    assert "searchRunQualityBadgeVariant" in retrieval_page
    assert "RunComparisonQueryProfile" in retrieval_page
    assert "QueryProfileSummaryCard" in retrieval_page
    assert "RunComparisonQualitySignals" in retrieval_page
    assert "QualitySignalChangeList" in retrieval_page
    assert "qualitySignalComparisonBetweenRuns" in retrieval_page
    assert "qualitySignalSummariesFromRun" in retrieval_page
    assert "qualitySignalComparison" in retrieval_page
    assert "Quality signals" in retrieval_page
    assert "RunComparisonFacetCoverage" in retrieval_page
    assert "FacetValueChange" in retrieval_page
    assert "facetComparisonsBetweenRuns" in retrieval_page
    assert "facetValuesFromRun" in retrieval_page
    assert "facetComparisons" in retrieval_page
    assert "Facet coverage" in retrieval_page
    assert "queryProfilesChanged" in retrieval_page
    assert "queryProfileChanged" in retrieval_page
    assert "profile changed" in retrieval_page
    assert "retrievalMode" in retrieval_page
    assert "suggestedFilters" in retrieval_page
    assert "queryProfileFilterEntries" in retrieval_page
    assert "appliedFilterMatches" in retrieval_page
    assert "appliedFilters={trace.filters_applied}" in retrieval_page
    assert "entry.applied" in retrieval_page
    assert "Suggested by query profile" in retrieval_page
    assert "entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`" in retrieval_page
    assert "RerankBadge" in retrieval_page
    assert "DiversityBadge" in retrieval_page
    assert "Fusion agreement" in retrieval_page
    assert "fusionDiagnosticsFromPackage" in retrieval_page
    assert "fusion_diagnostics" in retrieval_page
    assert "Whether lexical and vector retrieval agree" in retrieval_page
    assert "lexical/vector top overlap" in (
        REPO_ROOT / "docs/retrieval_module_v0.md"
    ).read_text(encoding="utf-8")
    assert "framework_managed_fusion" in (
        REPO_ROOT / "docs/retrieval_module_v0.md"
    ).read_text(encoding="utf-8")
    assert "RetrievalPackage.diversity" in (
        REPO_ROOT / "docs/retrieval_module_v0.md"
    ).read_text(encoding="utf-8")
    assert "trace.fusion_diagnostics" in (
        REPO_ROOT / "docs/api_contract_v0.md"
    ).read_text(encoding="utf-8")
    assert "evaluation_readiness" in (
        REPO_ROOT / "docs/api_contract_v0.md"
    ).read_text(encoding="utf-8")
    assert "DiversitySelectionExplanation" in retrieval_page
    assert "SourceDiversityPanel" in retrieval_page
    assert "Source diversity" in retrieval_page
    assert "Selected-hit rationale" in retrieval_page
    assert "DiversityMetricCard" in retrieval_page
    assert "RunComparisonSourceDiversity" in retrieval_page
    assert "Source diversity comparison" in retrieval_page
    assert "RunComparisonOperatorSummary" in retrieval_page
    assert "Comparison operator summary" in retrieval_page
    assert "comparisonOperatorSummary" in retrieval_page
    assert "operator_summary: comparisonOperatorSummary(comparison, recommendedActions)" in retrieval_page
    assert "Review focus" in retrieval_page
    assert "sourceDiversityComparisonBetweenRuns" in retrieval_page
    assert "sourceDiversityComparison" in retrieval_page
    assert "source_diversity_regressed" in retrieval_page
    assert "source_diversity_improved" in retrieval_page
    assert "source_diversity: {" in retrieval_page
    assert "selected_source_delta" in retrieval_page
    assert "duplicate_selected_source_delta" in retrieval_page
    assert "selected_hits: diversity.selectedHits.map" in retrieval_page
    assert "diversitySelectionByEvidenceId" in retrieval_page
    assert "selected_hits" in retrieval_page
    assert "Diversity selection" in retrieval_page
    assert "packageData.diversity ?? packageData.handoff_context.diversity" in retrieval_page
    assert "packageData.handoff_context.reranker" in retrieval_page
    assert "packageData.handoff_context.diversity" in retrieval_page
    assert "runtime?.rerank?.enabled" in retrieval_page
    assert "rankingBoostSignalsFromHit" in retrieval_page
    assert "ranking_boosts" in retrieval_page
    assert "ranking_boost_rules" in retrieval_page
    assert "Ranking boost rule applied." in retrieval_page
    assert "Ranking signals" in retrieval_page
    assert "applyFilterSuggestion" in retrieval_page
    assert "applySearchFilter" in retrieval_page
    assert "clearSearchFilter" in retrieval_page
    assert "clearAllSearchFilters" in retrieval_page
    assert "ActiveFilterBar" in retrieval_page
    assert "activeFilterEntries" in retrieval_page
    assert "Active filters" in retrieval_page
    assert "lastSearchSignature" in retrieval_page
    assert "currentSearchSignature" in retrieval_page
    assert "submittedSearchSignature" in retrieval_page
    assert "currentSearchSignature !== submittedSearchSignature" in retrieval_page
    assert "isSearchResultStale" in retrieval_page
    assert "retrievalPayloadFromForm" in retrieval_page
    assert "retrievalSearchSignature" in retrieval_page
    assert "Search settings changed" in retrieval_page
    assert "pending changes" in retrieval_page
    assert "submittedSearchPayload" in retrieval_page
    assert "SubmittedSearchSummary" in retrieval_page
    assert "Submitted search" in retrieval_page
    assert "SearchRunHistory" in retrieval_page
    assert "Search runs" in retrieval_page
    assert "searchRuns" in retrieval_page
    assert "createSearchRun" in retrieval_page
    assert "restoreSearchRun" in retrieval_page
    assert "retrievalRunSummary" in retrieval_page
    assert "SearchRunComparison" in retrieval_page
    assert "Run comparison" in retrieval_page
    assert "Run comparison help" in retrieval_page
    assert "Baseline is the older comparison run" in retrieval_page
    assert "warning deltas, quality changes, and rank movement" in retrieval_page
    assert "Baseline query" in retrieval_page
    assert "RunComparisonAtAGlance" in retrieval_page
    assert "Comparison at a glance" in retrieval_page
    assert "readinessGlanceLabel" in retrieval_page
    assert "baselineSummary.qualitySummary?.status" in retrieval_page
    assert "activeSummary.qualitySummary?.status" in retrieval_page
    assert "Action priority" in retrieval_page
    assert "Evidence overlap" in retrieval_page
    assert "label=\"Top source\"" in retrieval_page
    assert "comparison.topSourceChanged ? \"changed\" : \"stable\"" in retrieval_page
    assert "RunComparisonDiagnosis" in retrieval_page
    assert "Comparison diagnosis" in retrieval_page
    assert "RunComparisonRecommendedActions" in retrieval_page
    assert "Recommended actions" in retrieval_page
    assert "const recommendedActions = React.useMemo" in retrieval_page
    assert "actions={recommendedActions}" in retrieval_page
    assert "comparisonReportFromComparison(comparison, judgments, recommendedActions)" in retrieval_page
    assert "RetrievalComparisonRecommendedAction" in retrieval_page
    assert "comparisonRecommendedActionSummary" in retrieval_page
    assert "recommended_action_summary: comparisonRecommendedActionSummary" in retrieval_page
    assert "highest_priority" in retrieval_page
    assert "source_count" in retrieval_page
    assert "source_counts" in retrieval_page
    assert "actionSummary.sources.map" in retrieval_page
    assert "actionSummary.source_counts[source]" in retrieval_page
    assert "priority: comparison.activeSummary.qualitySummary?.status === \"blocked\" ? 1 : 2" in retrieval_page
    assert "left.priority - right.priority" in retrieval_page
    assert "comparisonDiagnosisFromComparison" in retrieval_page
    assert "diagnosis: comparison.diagnosis" in retrieval_page
    assert "compareSearchRuns" in retrieval_page
    assert "comparisonRunForActive" in retrieval_page
    assert "comparisonBaselineRunId" in retrieval_page
    assert "Set baseline" in retrieval_page
    assert "as comparison baseline" in retrieval_page
    assert "GitCompareArrows" in retrieval_page
    assert "addedEvidenceIds" in retrieval_page
    assert "retainedEvidenceIds" in retrieval_page
    assert "RunComparisonRankChanges" in retrieval_page
    assert "Rank movement" in retrieval_page
    assert "Rank movement help" in retrieval_page
    assert "Stable rank means retained evidence kept the same ordering" in retrieval_page
    assert "Use rank movement to debug relevance tuning" in retrieval_page
    assert "rankChangesBetweenRuns" in retrieval_page
    assert "rankDelta" in retrieval_page
    assert "Copy comparison JSON" in retrieval_page
    assert "Copy retrieval comparison report" in retrieval_page
    assert "Comparison JSON report help" in retrieval_page
    assert "comparisonReportFromComparison" in retrieval_page
    assert "comparisonReportSummary" in retrieval_page
    assert "summary: comparisonReportSummary(comparison, judgments)" in retrieval_page
    assert "remediationSummary ??" in retrieval_page
    assert "remediation: {" in retrieval_page
    assert "before: comparison.topSourceBefore" in retrieval_page
    assert "after: comparison.topSourceAfter" in retrieval_page
    assert "comparisonReportRecommendedActions" in retrieval_page
    assert "recommended_actions: recommendedActions" in retrieval_page
    assert "changed_dimensions" in retrieval_page
    assert "judgment_count: judgments.length" in retrieval_page
    assert "retrieval_run_comparison" in retrieval_page
    assert "RunComparisonMetrics" in retrieval_page
    assert "Overlap shows shared evidence" in retrieval_page
    assert "churn shows how much the result set changed" in retrieval_page
    assert "mean rank delta shows ordering instability" in retrieval_page
    assert "RunComparisonRulePacks" in retrieval_page
    assert "rulePackChangesBetweenRuns" in retrieval_page
    assert "rulePackFingerprint" in retrieval_page
    assert "rulePackChanged" in retrieval_page
    assert "rule_packs" in retrieval_page
    assert "retrievalRulePacksFromPackage" in retrieval_page
    assert "configured" in retrieval_page
    assert "content_hash" in retrieval_page
    assert "Search comparison metrics" in retrieval_page
    assert "comparisonMetrics" in retrieval_page
    assert "overlapRatio" in retrieval_page
    assert "churnRate" in retrieval_page
    assert "meanAbsoluteRankDelta" in retrieval_page
    assert "RelevanceJudgmentControl" in retrieval_page
    assert "Relevance judgment" in retrieval_page
    assert "Relevance judgment help" in retrieval_page
    assert "Use relevant for direct support" in retrieval_page
    assert "relevanceJudgments" in retrieval_page
    assert "useRetrievalJudgmentsQuery" in retrieval_page
    assert "useRetrievalJudgmentMutation" in retrieval_page
    assert "useRetrievalJudgmentSummaryQuery" in retrieval_page
    assert "useRetrievalJudgmentEvaluationQuery" in retrieval_page
    assert "useDeleteRetrievalJudgmentMutation" in retrieval_page
    assert "relevanceJudgmentFromPersisted" in retrieval_page
    assert "/retrieval/judgments" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "/retrieval/judgments/summary" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "/retrieval/judgments/evaluate" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "judgmentsForComparison" in retrieval_page
    assert "RelevanceJudgmentSummary" in retrieval_page
    assert "Judgment metrics" in retrieval_page
    assert "Judgment metrics help" in retrieval_page
    assert "Precision@k and nDCG@k become meaningful" in retrieval_page
    assert "relevanceJudgmentMetrics" in retrieval_page
    assert "relevanceJudgmentRating" in retrieval_page
    assert "judgmentsForRunHits" in retrieval_page
    assert "discountedCumulativeGain" in retrieval_page
    assert "Precision@k" in retrieval_page
    assert "nDCG@k" in retrieval_page
    assert "Server MAP@k" in retrieval_page
    assert "Server HitRate@k" in retrieval_page
    assert "Server MRR@k" in retrieval_page
    assert "Server nDCG@k" in retrieval_page
    assert "Evaluation recommendations" in retrieval_page
    assert "EvidenceReadinessPanel" in retrieval_page
    assert "Evidence readiness" in retrieval_page
    assert "readinessInterpretation" in retrieval_page
    assert "Blocked for governed use" in retrieval_page
    assert "Needs human review" in retrieval_page
    assert "Ready for evidence review" in retrieval_page
    assert "Readiness score unavailable" in retrieval_page
    assert "RetrievalSearchCockpit" in retrieval_page
    assert "Search cockpit" in retrieval_page
    assert "SearchReadinessChecklist" in retrieval_page
    assert "Search readiness checklist" in retrieval_page
    assert "searchReadinessChecklist" in retrieval_page
    assert "readiness_checklist: readinessChecklist" in retrieval_page
    assert "Source spread" in retrieval_page
    assert "Governance" in retrieval_page
    assert "Query transformation" in retrieval_page
    assert "Next best action" in retrieval_page
    assert "hybridStackValue" in retrieval_page
    assert "Copy cockpit" in retrieval_page
    assert "Copy cockpit JSON" in retrieval_page
    assert "Cockpit JSON report help" in retrieval_page
    assert "retrievalCockpitReportFromPackage" in retrieval_page
    assert "retrievalCockpitEvidenceHitReports" in retrieval_page
    assert "evidence_hits" in retrieval_page
    assert 'report_type: "retrieval_cockpit"' in retrieval_page
    assert "interpretation: retrievalInterpretationReport(packageData)" in retrieval_page
    assert "RecommendedActionsPanel" in retrieval_page
    assert "Corrective actions" in retrieval_page
    assert "packageData.recommended_actions ?? []" in retrieval_page
    assert "recommendedActionFilter" in retrieval_page
    assert "recommendedActionSourceLabel" in retrieval_page
    assert "corrective_rule_source" in retrieval_page
    assert "query diagnostic" in retrieval_page
    assert 'action.action_type === "broaden_query"' in retrieval_page
    assert "correctiveActionSummaryFromPackage" in retrieval_page
    assert "packageData.recommended_action_summary" in retrieval_page
    assert "correctiveActionSummary: CorrectiveActionSummary" in retrieval_page
    assert "recommendedActionTypeCounts" in retrieval_page
    assert "CorrectiveActionTypeCountChips" in retrieval_page
    assert "correctiveActionTypeCountEntries" in retrieval_page
    assert "counts={run.summary.correctiveActionSummary.actionTypeCounts}" in retrieval_page
    assert "action_type_counts" in retrieval_page
    assert "broaden_query_count" in retrieval_page
    assert "actionTypeCounts" in retrieval_page
    assert "broadenQueryCount" in retrieval_page
    assert "Top action:" in retrieval_page
    assert "missing_required_evidence_buckets" in retrieval_page
    assert "qualitySummaryBadgeVariant" in retrieval_page
    assert "bucketSuggestedFilter" in retrieval_page
    assert "onApplyBucketFilter" in retrieval_page
    assert "bucket.suggested_filter" in retrieval_page
    assert "EvidencePackBuckets" in retrieval_page
    assert "Evidence pack" in retrieval_page
    assert "packageData.evidence_buckets ?? []" in retrieval_page
    assert "missingRequiredCount" in retrieval_page
    assert "required gap" in retrieval_page
    assert "EvidenceSupportMatrix" in retrieval_page
    assert "Evidence support matrix" in retrieval_page
    assert "Evidence support matrix help" in retrieval_page
    assert "Weak rows need inspection before use" in retrieval_page
    assert "evidenceSupportMatrixRows" in retrieval_page
    assert "HitMatchExplanationPanel" in retrieval_page
    assert "Why this matched" in retrieval_page
    assert "hitMatchExplanation" in retrieval_page
    assert "match_explanation" in retrieval_page
    assert "match_explanation?: Record<string, unknown>" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "backendExplanation" in retrieval_page
    assert "aspectIds" in retrieval_page
    assert "bucketIds" in retrieval_page
    assert "conceptIds" in retrieval_page
    assert "provenanceFields" in retrieval_page
    assert "rankingSignalRuleIds" in retrieval_page
    assert "topScoreComponent" in retrieval_page
    assert "evidenceReportFromHit(" in retrieval_page
    assert "judgment," in retrieval_page
    assert "Top driver" in retrieval_page
    assert "Evidence pack" in retrieval_page
    assert "evidenceBucketLabelsByEvidenceId" in retrieval_page
    assert "evidenceSupportStatus" in retrieval_page
    assert '"source_id"' in retrieval_page
    assert "SourceScopePicker" in retrieval_page
    assert "Exact source scope" in retrieval_page
    assert "Exact source scope help" in retrieval_page
    assert "Search is constrained to one exact source" in retrieval_page
    assert "applied exact source" in retrieval_page
    assert "onUseSource" in retrieval_page
    assert "Use source" in retrieval_page
    assert "payload.filters?.source_id" in retrieval_page
    assert "source_id?: string | null" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "persisted judgment state" in frontend_architecture
    assert "it must not create hidden clinical claims" in frontend_architecture
    assert "matrix must explain how to interpret weak rows" in frontend_architecture
    assert "RetrievalEvidenceBucket" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "evidence_buckets?: RetrievalEvidenceBucket[]" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "suggested_filter: Record<string, string>" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "RetrievalRecommendedAction" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "recommended_actions?: RetrievalRecommendedAction[]" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "metadata: Record<string, unknown>" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "recommended_action_summary?: RetrievalRecommendedActionSummary | null" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "remediation_summary?: string | null" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "action_type_counts: Record<string, number>" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "RetrievalStrategyRecommendation" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "strategy_recommendations?: RetrievalStrategyRecommendation[]" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "StrategyRecommendationsPanel" in retrieval_page
    assert "StrategyRecommendationCard" in retrieval_page
    assert "Strategy recommendations" in retrieval_page
    assert "suggestedFilterAction(recommendation.suggested_filters)" in retrieval_page
    assert "strategy_recommendations: (packageData.strategy_recommendations ?? [])" in retrieval_page
    assert "Copy eval" in retrieval_page
    assert "Copy evaluation JSON" in retrieval_page
    assert "Copy retrieval judgment evaluation report" in retrieval_page
    assert "Judgment evaluation JSON report help" in retrieval_page
    assert "EvaluationReadinessPanel" in retrieval_page
    assert "Judgment evaluation readiness" in retrieval_page
    assert "Judgment readiness help" in retrieval_page
    assert "evaluation_readiness: evaluation.evaluation_readiness" in retrieval_page
    assert "evaluationReadinessVariant" in retrieval_page
    assert "evaluationReadinessClass" in retrieval_page
    assert "evaluationReportFromJudgmentSummary" in retrieval_page
    assert "retrieval_judgment_evaluation" in retrieval_page
    assert "correctiveActionReportContext" in retrieval_page
    assert "corrective_actions: correctiveActions" in retrieval_page
    assert "package_top_actions" in retrieval_page
    assert "runSummary.remediationSummary ?? searchRunRemediationSummary(runSummary)" in retrieval_page
    assert "retrievalRulePacksFromPackage" in retrieval_page
    assert "retrieval_rule_packs" in retrieval_page
    assert "content_hash" in retrieval_page
    assert "retrieval_rule_packs?: RuntimeRetrievalRulePack[]" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "recommendations" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "persistedJudgmentEvaluation" in retrieval_page
    assert "average_precision_at_k" in retrieval_page
    assert "hit_rate_at_k" in retrieval_page
    assert "mrr_at_k" in retrieval_page
    assert "judgmentCoverage" in retrieval_page
    assert "judgedPrecision" in retrieval_page
    assert "not_relevant" in retrieval_page
    assert "judgment-aware metrics" in frontend_architecture
    assert "labels are for the" in frontend_architecture
    assert "share of hits judged" in frontend_architecture
    assert "evaluation_readiness" in frontend_architecture
    assert "low confidence" in frontend_architecture
    assert "/retrieval/judgments" in frontend_architecture
    assert "/retrieval/judgments/summary" in frontend_architecture
    assert "/retrieval/judgments/evaluate" in frontend_architecture
    assert "stored label" in retrieval_page
    assert "clinical evidence pack" in frontend_architecture
    assert "operator interpretation of the" in frontend_architecture
    assert "translate support signals into operator action" in frontend_architecture
    assert "recommended_action_summary.action_type_counts" in frontend_architecture
    assert "compact action-type chips" in frontend_architecture
    assert "Run remediation" in frontend_architecture
    assert "same derived summary should be included in copied cockpit" in frontend_architecture
    assert "comparison JSON reports as `remediation_summary`" in frontend_architecture
    assert "When the backend action is `broaden_query`" in frontend_architecture
    assert "derived from a package `quality_signal` or a `query_diagnostic`" in frontend_architecture
    assert "strong evidence can be used with provenance check" in frontend_architecture
    assert "partial evidence" in frontend_architecture
    assert "weak evidence" in frontend_architecture
    assert "retrieval cockpit" in frontend_architecture
    assert "copyable `retrieval_cockpit` JSON report" in frontend_architecture
    assert "QueryHealthPanel" in retrieval_page
    assert "Query health" in retrieval_page
    assert "Query health help" in retrieval_page
    assert "queryHealthItems" in retrieval_page
    assert "queryDiagnosticHealthItems" in retrieval_page
    assert "DiagnosticMetadataChips" in retrieval_page
    assert "metadata: recordValue(item.metadata)" in retrieval_page
    assert "metadata: diagnostic.metadata" in retrieval_page
    assert "active_metadata_filters" in retrieval_page
    assert "suggested_standards" in retrieval_page
    assert "diagnostic_${diagnostic.code}" in retrieval_page
    assert "Filter over-constraint" in retrieval_page
    assert "overconstrained_metadata_filters" in retrieval_page
    assert "diagnostic_overconstrained_metadata_filters" in retrieval_page
    assert "Clear source scope" in retrieval_page
    assert "Broaden search" in retrieval_page
    assert "onClearAllFilters" in retrieval_page
    assert "onClearFilter" in retrieval_page
    assert "queryHealthBadgeVariant" in retrieval_page
    assert "queryHealthOverallLabel" in retrieval_page
    assert "Query specificity" in retrieval_page
    assert "Clinical context" in retrieval_page
    assert "Search scope" in retrieval_page
    assert "Result coverage" in retrieval_page
    assert "Safety signals" in retrieval_page
    assert "query_health: queryHealth" in retrieval_page
    assert "query-health checklist" in frontend_architecture
    assert "query specificity, clinical context, search" in frontend_architecture
    assert "over-constrained by exact source scope" in frontend_architecture
    assert "query_analysis.diagnostics[]" in frontend_architecture
    assert "structured diagnostic metadata" in frontend_architecture
    assert "active metadata filter names" in frontend_architecture
    assert "overconstrained_metadata_filters" in frontend_architecture
    assert "clear exact source scope" in frontend_architecture
    assert "clear all metadata filters" in frontend_architecture
    assert "query_health[]" in frontend_architecture
    assert "Report copy" in frontend_architecture
    assert "export JSON" in frontend_architecture
    assert "Trace sections must also explain" in frontend_architecture
    assert "safety flags mark untrusted or sensitive query context" in frontend_architecture
    assert "compact `evidence_hits`" in frontend_architecture
    assert "stable bucket IDs" in frontend_architecture
    assert "backend-owned `match_explanation`" in (REPO_ROOT / "docs/retrieval_module_v0.md").read_text(
        encoding="utf-8"
    )
    assert "isJudgmentSyncing" in retrieval_page
    assert "restoreSubmittedSearch" in retrieval_page
    assert "onRestoreSubmittedSearch" in retrieval_page
    assert "Restore submitted search" in retrieval_page
    assert "displayed request" in retrieval_page
    assert "useRetrievalPresetsQuery" in retrieval_page
    assert "SearchPresetStrip" in retrieval_page
    assert "activePresetId" in retrieval_page
    assert "Loading retrieval presets" in retrieval_page
    assert "data-driven" in retrieval_page
    assert "useRetrievalSearchOptionsQuery" in retrieval_page
    assert "formatOptions" in retrieval_page
    assert "mergeSearchOptions" in retrieval_page
    assert "categoryFilter" in retrieval_page
    assert "presetSearch" in retrieval_page
    assert "presetMatchesSearch" in retrieval_page
    assert "Filter retrieval presets" in retrieval_page
    assert "Preset categories" in retrieval_page
    assert "sourceSearch" in retrieval_page
    assert "sourceTypeFilter" in retrieval_page
    assert "sourceMatchesInventoryFilters" in retrieval_page
    assert "Filter trusted sources" in retrieval_page
    assert "Source inventory filters" in retrieval_page
    assert "SourceInventoryReadinessPanel" in retrieval_page
    assert "Source inventory readiness" in retrieval_page
    assert "Source readiness" in retrieval_page
    assert "Source readiness help" in retrieval_page
    assert "sourceInventoryReadiness" in retrieval_page
    assert "sourceInventoryReadinessMessage" in retrieval_page
    assert "filtered inventory" in retrieval_page
    assert "all shown sources have chunks" in retrieval_page
    assert "No trusted sources are loaded" in retrieval_page
    assert "Trusted sources help" in retrieval_page
    assert "Inventory filters only inspect available sources" in retrieval_page
    assert '<option value="csv">CSV</option>' not in retrieval_page
    assert '<option value="fhir_like">FHIR-like</option>' not in retrieval_page
    assert "defaultQuery" not in retrieval_page
    assert "activeFacetFiltersFromPayload" in retrieval_page
    assert "onApplyFacet" in retrieval_page
    assert "aria-pressed={applied}" in retrieval_page
    assert "supportedSuggestionFilterFields" in retrieval_page
    assert "onApplyFilterSuggestion" in retrieval_page
    assert "coverageSuggestedFilter" in retrieval_page
    assert "coverageSuggestedAction" in retrieval_page
    assert "CoverageItemList" in retrieval_page
    assert "Aspect coverage" in retrieval_page
    assert "coverage?.query_aspects" in retrieval_page
    assert "suggested_filter" in retrieval_page
    assert "onApplyCoverageFilter" in retrieval_page
    assert "Copy medical search hint" in retrieval_page
    assert "Open medical search hint" in retrieval_page
    assert "launchable hint" in retrieval_page
    assert "copyTextToClipboard" in retrieval_page
    assert "Embedding and rerank provider state" in frontend_architecture
    assert "per-hit ranking boost signals" in frontend_architecture
    assert "source coverage" in frontend_architecture
    assert "explicit operator apply" in frontend_architecture
    assert "actionable refinements" in frontend_architecture
    assert "removable chips" in frontend_architecture
    assert "pending changes" in frontend_architecture
    assert "submitted request summary" in frontend_architecture
    assert "compare recent search packages" in frontend_architecture
    assert "select a baseline run" in frontend_architecture
    assert "rank movement" in frontend_architecture
    assert "baseline is the older selected run" in frontend_architecture
    assert "rank movement is not clinical evidence" in frontend_architecture
    assert "distinguish broad result replacement from rank-order instability" in frontend_architecture
    assert "copyable JSON report" in frontend_architecture
    assert "overlap and churn metrics" in frontend_architecture
    assert "explicit relevance judgments" in frontend_architecture
    assert "restore the query builder" in frontend_architecture
    assert "copyable and launchable" in frontend_architecture
    assert "/retrieval/presets" in frontend_architecture
    assert "/retrieval/search-options" in frontend_architecture
    assert "trusted knowledge data" in frontend_architecture
    assert "Preset category filters" in frontend_architecture
    assert "trusted source inventory" in frontend_architecture
    assert "searchable and filterable" in frontend_architecture
    assert "source readiness before filters" in frontend_architecture
    assert "visible/total source count" in frontend_architecture
    assert "empty-source warnings" in frontend_architecture
    assert "reindexing problems visible" in frontend_architecture


def test_settings_page_exposes_reloadable_assistant_runtime() -> None:
    settings_page = SETTINGS_PAGE.read_text(encoding="utf-8")
    server_state = (FRONTEND_SRC / "lib" / "server-state.ts").read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "AssistantSettingsForm" in settings_page
    assert "useRuntimeAssistantSettingsMutation" in settings_page
    assert "runtimeAssistantPayloadFromForm" in settings_page
    assert "OpenAI key configured" in settings_page
    assert "updateRuntimeAssistantSettings" in server_state
    assert '"/runtime/assistant-settings"' in api_module
    assert "Assistant runtime" in frontend_architecture


def test_settings_page_surfaces_retrieval_rule_pack_inventory() -> None:
    settings_page = SETTINGS_PAGE.read_text(encoding="utf-8")
    types_module = (FRONTEND_SRC / "types.ts").read_text(encoding="utf-8")
    api_contract = (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(
        encoding="utf-8"
    )
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "RetrievalRulePackInventory" in settings_page
    assert "ReadinessRulePackDetails" in settings_page
    assert "retrievalRulePacksFromDetails" in settings_page
    assert "shortRulePackHash" in settings_page
    assert "retrieval_rule_packs" in settings_page
    assert "Rule pack readiness" in settings_page
    assert "Retrieval rule packs" in settings_page
    assert "runtime?.retrieval?.rule_packs" in settings_page
    assert "RuntimeRetrievalRulePack" in types_module
    assert "rule_packs?: RuntimeRetrievalRulePack[]" in types_module
    assert "content_hash?: string | null" in types_module
    assert "version?: string | null" in types_module
    assert "retrieval.rule_packs[]" in api_contract
    assert "OJT_QUERY_DIAGNOSTIC_RULES_PATH" in api_contract
    assert "OJT_CORRECTIVE_ACTION_RULES_PATH" in api_contract
    assert "OJT_STANDARD_SEARCH_PLAYBOOK_RULES_PATH" in api_contract
    assert "OJT_EVIDENCE_BUCKET_RULES_PATH" in api_contract
    assert "sanitized pack name" in frontend_architecture
    assert "0 favors source novelty; 1 favors raw relevance" in settings_page
    assert "disabled={!form.diversityEnabled}" in settings_page
    assert "Disable it only when strict score order is required" in settings_page
    assert "Retrieval source-diversity controls" in frontend_architecture


def test_assistant_ui_surfaces_tool_layer() -> None:
    assistant_page = ASSISTANT_PAGE.read_text(encoding="utf-8")
    app_shell = APP_SHELL.read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")
    server_state = (FRONTEND_SRC / "lib" / "server-state.ts").read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert 'to="/assistant"' in app_shell
    assert "Open assistant" in app_shell
    assert "AssistantToolSpec" in assistant_page
    assert "ToolCatalogPanel" in assistant_page
    assert "Assistant tool catalog" in assistant_page
    assert "AI Assistant" in assistant_page
    assert "Advanced context" in assistant_page
    assert "LiveToolTimeline" in assistant_page
    assert "Live tool calls" in assistant_page
    assert "ConversationTurn" in assistant_page
    assert "streamed_answer" in assistant_page
    assert "AssistantEvidenceMatchStrip" in assistant_page
    assert "assistantEvidenceMatchExplanation" in assistant_page
    assert "matchSupportBadgeVariant" in assistant_page
    assert "item.match_explanation" in assistant_page
    assert "AssistantStandardSearchPlan" in assistant_page
    assert "Standards plan" in assistant_page
    assert "AssistantStandardSearchMatchReasons" in assistant_page
    assert "Matched by" in assistant_page
    assert "matched_fields" in assistant_page
    assert "AssistantMedicalSearchHints" in assistant_page
    assert "Medical search hints" in assistant_page
    assert "AssistantSourceDiversity" in assistant_page
    assert "toolDiversitySummary" in assistant_page
    assert "diversitySummaryValue" in assistant_page
    assert "Evidence spread after final retrieval selection" in assistant_page
    assert "_compact_retrieval_diversity" in (
        REPO_ROOT / "src/ojtflow/application/assistant_service.py"
    ).read_text(encoding="utf-8")
    assert "toolSearchHints" in assistant_page
    assert "selected_unit_candidates" in assistant_page
    assert "scope_endpoints" in assistant_page
    assert "ExternalLink" in assistant_page
    assert "Clipboard" in assistant_page
    assert "copyTextToClipboard" in assistant_page
    assert "Copied" in assistant_page
    assert 'rel="noopener noreferrer"' in assistant_page
    assert "toolStandardSearchPlan" in assistant_page
    assert "standardSearchPlanValue" in assistant_page
    assert "RetrievalStandardSearchPlan" in assistant_page
    assert "AssistantSessionSidebar" in assistant_page
    assert "createAssistantChatSession" in assistant_page
    assert "sessionWithAppendedTranscriptItem" in assistant_page
    assert "New chat" in assistant_page
    assert "transcriptEndRef" in assistant_page
    assert 'scrollIntoView({ block: "end" })' in assistant_page
    assert "lg:h-[calc(100dvh-6rem)]" in assistant_page
    assert "ChatGPT-style chat sessions" in frontend_architecture
    assert "contained app-viewport chat" in frontend_architecture
    assert "auto-follow the active" in frontend_architecture
    assert "AbortController" in assistant_page
    assert "cancelActiveStream" in assistant_page
    assert "Stop" in assistant_page
    assert "useAssistantChatStreamMutation" in assistant_page
    assert "useAssistantExamplesQuery" in assistant_page
    assert "useExtractFileTextMutation" in assistant_page
    assert "AttachmentPreview" in assistant_page
    assert "fileFromClipboard" in assistant_page
    assert "assistantContextWithAttachment" in assistant_page
    assert "Paste an image" in assistant_page
    assert "Attach" in assistant_page
    assert "ChatEmptyState" in assistant_page
    assert "No starter tasks are configured." in assistant_page
    assert "Message" in assistant_page
    assert "Send" in assistant_page
    assert "answer {response.synthesis_mode}" in assistant_page
    assert "synthesis_mode" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "match_explanation?: Record<string, unknown>" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "AssistantStreamEvent" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'type: "stream_opened"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'type: "planning_progress"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'type: "planning_step"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'type: "planning_delta"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "chronologicalTimelineItems" in assistant_page
    assert "AssistantTextStreamPreview" in assistant_page
    assert "ToolTimelineCard" in assistant_page
    assert "formatPlannerStreamText" in assistant_page
    assert "PlannerStreamPreview" in assistant_page
    assert "Planner stream" in assistant_page
    assert "Planning ${event.elapsed_seconds}s" in assistant_page
    assert "PlanReadyPreview" in assistant_page
    assert "Validated plan" in assistant_page
    assert "planningStartedDetail" in assistant_page
    assert "Tools available:" in assistant_page
    assert "Max tool calls:" in assistant_page
    assert 'type: "error"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "useAssistantToolsQuery" in assistant_page
    assert "listAssistantExamples" in api_module
    assert '"/assistant/examples"' in api_module
    assert "assistantExamples" in server_state
    assert "streamAssistantChat" in api_module
    assert "extractFileText" in api_module
    assert "/parse/extract" in api_module
    assert "/assistant/chat/stream" in api_module
    assert "signal?: AbortSignal" in api_module
    assert "Assistant evidence summary cards must render compact retrieval" in frontend_architecture
    assert "governed source scope" in (REPO_ROOT / "docs/assistant_mcp_agent.md").read_text(
        encoding="utf-8"
    )
    assert "exact `source_id`" in (REPO_ROOT / "docs/api_contract_v0.md").read_text(
        encoding="utf-8"
    )
    assert "useAssistantChatStreamMutation" in server_state
    assert "useExtractFileTextMutation" in server_state
    assert "listAssistantTools" in api_module
    assert '"/assistant/tools"' in api_module
    assert "assistantTools" in server_state
    assert "server allowlisted assistant/MCP tools" in frontend_architecture


def test_help_center_surfaces_user_guidance() -> None:
    app = (FRONTEND_SRC / "App.tsx").read_text(encoding="utf-8")
    app_shell = APP_SHELL.read_text(encoding="utf-8")
    assistant_page = ASSISTANT_PAGE.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    help_page = HELP_PAGE.read_text(encoding="utf-8")
    guide_panel = GUIDE_PANEL.read_text(encoding="utf-8")
    retrieval_page = RETRIEVAL_PAGE.read_text(encoding="utf-8")
    reviews_page = (
        REPO_ROOT / "frontend" / "src" / "features" / "reviews" / "reviews-page.tsx"
    ).read_text(encoding="utf-8")
    schemas_page = (
        REPO_ROOT / "frontend" / "src" / "features" / "schemas" / "schemas-page.tsx"
    ).read_text(encoding="utf-8")
    workflows_page = (
        REPO_ROOT / "frontend" / "src" / "features" / "workflows" / "workflows-page.tsx"
    ).read_text(encoding="utf-8")
    workbench_page = WORKBENCH_PAGE.read_text(encoding="utf-8")
    help_tooltip = (FRONTEND_SRC / "components" / "ui" / "help-tooltip.tsx").read_text(
        encoding="utf-8"
    )

    assert "HelpPage" in app
    assert 'path: "/help"' in app
    assert 'path: "/help/tutorials"' in app
    assert 'path: "/help/manual"' in app
    assert 'label: "Help"' in app_shell
    assert "HelpTooltip" in help_tooltip
    assert "group-focus-within/help:block" in help_tooltip
    assert "GuidePanel" in guide_panel
    assert "GuideGrid" in guide_panel
    assert "GuideChecklist" in guide_panel
    assert "Help Center" in help_page
    assert "User Manual" in help_page
    assert "What Should I Do?" in help_page
    assert "I have a file and I do not know the format" in help_page
    assert "I do not trust an explanation yet" in help_page
    assert "First Run Checklist" in help_page
    assert "Status And Output Manual" in help_page
    assert "Needs human review" in help_page
    assert "Who Should Start Where" in help_page
    assert "Operations user" in help_page
    assert "Data steward" in help_page
    assert "Evidence reviewer" in help_page
    assert "Administrator" in help_page
    assert "Quick Start" in help_page
    assert "How To Read Output" in help_page
    assert "Audit events" in help_page
    assert "Input Format Guide" in help_page
    assert "CSV" in help_page
    assert "JSON / YAML" in help_page
    assert "FHIR-like JSON" in help_page
    assert "PDF / DOCX / Image" in help_page
    assert "Retrieval Search Manual" in help_page
    assert "Hybrid search" in help_page
    assert "Reranking" in help_page
    assert "Exact source scope" in help_page
    assert "Query rewrites" in help_page
    assert "Exported JSON reports" in help_page
    assert "RetrievalManualItem" in help_page
    assert "Manual And Glossary" in help_page
    assert "Issue And Warning Manual" in help_page
    assert "Missing field" in help_page
    assert "Missing unit" in help_page
    assert "Possible PHI" in help_page
    assert "Weak evidence" in help_page
    assert "Prompt-injection pattern" in help_page
    assert "Safety Rules" in help_page
    assert "Validate a lab CSV" in help_page
    assert "Search medical evidence" in help_page
    assert "Upload a document" in help_page
    assert "AssistantInlineGuide" in assistant_page
    assert "How to use Assistant" in assistant_page
    assert "RetrievalInlineGuide" in retrieval_page
    assert "How to read Retrieval" in retrieval_page
    assert "RetrievalFirstRunGuide" in retrieval_page
    assert "NoResultRemediationPanel" in retrieval_page
    assert "Retrieval query help" in retrieval_page
    assert "Retrieval fields help" in retrieval_page
    assert "Schema filter help" in retrieval_page
    assert "Top K help" in retrieval_page
    assert "Format filter help" in retrieval_page
    assert "Resource filter help" in retrieval_page
    assert "Clinical domain help" in retrieval_page
    assert "Standard filter help" in retrieval_page
    assert "Trust filter help" in retrieval_page
    assert "Source type filter help" in retrieval_page
    assert "explain missing units for lab_result_v1" in retrieval_page
    assert "date, patient_id, lab_name, value, unit" in retrieval_page
    assert "Start with a concrete healthcare data question" in retrieval_page
    assert "first search guide" in retrieval_page
    assert "Good starter questions" in retrieval_page
    assert "No matching evidence returned" in retrieval_page
    assert "Loosen scope" in retrieval_page
    assert "Clear all filters" in retrieval_page
    assert "Clear exact source scope and rerun search" in retrieval_page
    assert "Check source inventory" in retrieval_page
    assert "firstSupportedRecommendedAction" in retrieval_page
    assert "direct controls to clear exact source scope" in frontend_architecture
    assert "Search presets help" in retrieval_page
    assert "Source inventory filters help" in retrieval_page
    assert "Execute write actions help" in assistant_page
    assert "Optional context JSON help" in assistant_page
    assert "Tool catalog help" in assistant_page
    assert "How to create a workflow" in workbench_page
    assert "Workflow instruction help" in workbench_page
    assert "Source data help" in workbench_page
    assert "Upload file help" in workbench_page
    assert "Extractor help" in workbench_page
    assert "How to read workflow operations" in workflows_page
    assert "Workflow queue help" in workflows_page
    assert "Workflow sort help" in workflows_page
    assert "How to handle a review gate" in reviews_page
    assert "Pending decisions help" in reviews_page
    assert "Review sort help" in reviews_page
    assert "How to use schema profiles" in schemas_page
    assert "Schema registry search help" in schemas_page
    assert "Required fields help" in schemas_page
    assert "The backend route chosen for this query" in retrieval_page
    assert "The retrieval stack combines lexical search" in retrieval_page
    assert "How many independent sources survived source-diversity selection" in retrieval_page
    assert "Concepts and query aspects detected from the search" in retrieval_page
    assert "Strategy recommendations help" in retrieval_page
    assert "Open full manual" in assistant_page
    assert "Open full manual" in retrieval_page
    assert "operator guidance as first-class routes" in frontend_architecture
    assert "/help/tutorials" in frontend_architecture
    assert "/help/manual" in frontend_architecture
    assert "retrieval search manual" in frontend_architecture
    assert "keyboard-focusable tooltips" in frontend_architecture
    assert "Query-builder controls must explain" in frontend_architecture
    assert "must guide first-time users before a search runs" in frontend_architecture
    assert "completed search returns zero ranked hits" in frontend_architecture
    assert "exact source scope can over-constrain evidence" in frontend_architecture
    assert "controls must explain that the search is constrained to one source" in frontend_architecture
    assert "clear it before judging corpus-wide" in frontend_architecture


def test_frontend_browser_storage_is_not_used_for_auth_or_state() -> None:
    violations: list[str] = []

    for source_file in _frontend_source_files():
        text = source_file.read_text(encoding="utf-8")
        if BROWSER_STORAGE_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} uses browser storage/cookie APIs directly",
            )

    assert violations == []


def test_frontend_does_not_use_full_page_reload_for_server_state_refresh() -> None:
    violations: list[str] = []

    for source_file in _frontend_source_files():
        text = source_file.read_text(encoding="utf-8")
        if FULL_PAGE_RELOAD_RE.search(text):
            violations.append(
                f"{source_file.relative_to(REPO_ROOT)} uses full-page reload",
            )

    assert violations == []


def test_auth_provider_clears_server_state_cache_on_session_loss() -> None:
    auth_provider = AUTH_PROVIDER.read_text(encoding="utf-8")

    assert "useQueryClient" in auth_provider
    assert "AUTH_SESSION_EXPIRED_EVENT" in auth_provider
    assert "window.addEventListener(AUTH_SESSION_EXPIRED_EVENT" in auth_provider
    assert "queryClient.clear()" in auth_provider
    assert "err.status === 401" in auth_provider
    assert auth_provider.count("expireSession()") >= 2
    assert "logoutCurrentSession()" in auth_provider


def test_server_state_retries_do_not_repeat_unauthorized_requests() -> None:
    providers = APP_PROVIDERS.read_text(encoding="utf-8")

    assert "ApiRequestError" in providers
    assert "error.status === 401" in providers
    assert "return false" in providers
    assert "failureCount < 1" in providers


def test_frontend_has_app_level_error_boundary_without_page_reload() -> None:
    providers = APP_PROVIDERS.read_text(encoding="utf-8")
    error_boundary = ERROR_BOUNDARY.read_text(encoding="utf-8")

    assert "AppErrorBoundary" in providers
    assert "<AppErrorBoundary>" in providers
    assert "static getDerivedStateFromError" in error_boundary
    assert "Application error" in error_boundary
    assert "Reset view" in error_boundary
    assert "location.reload" not in error_boundary
    assert "window.location" not in error_boundary


def test_frontend_auth_callback_contract_does_not_model_bearer_token() -> None:
    frontend_types = FRONTEND_TYPES.read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")

    auth_login_start = frontend_types.index("export type AuthLoginResponse")
    auth_session_start = frontend_types.index("export type AuthSessionResponse")
    auth_login_type = frontend_types[auth_login_start:auth_session_start]

    assert "access_token" not in auth_login_type
    assert "token_type" not in auth_login_type
    assert "include_token" not in api_module


def test_frontend_api_wraps_malformed_json_as_structured_errors() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "response.json()" not in api_module
    assert "await response.text()" in api_module
    assert "JSON.parse(body)" in api_module
    assert "normalizeEnvelope(JSON.parse(body)" in api_module
    assert "isApiEnvelope" in api_module
    assert "API response envelope is invalid." in api_module
    assert "API returned malformed JSON." in api_module
    assert "parse_error" in api_module


def test_frontend_api_wraps_network_failures_as_structured_errors() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "async function fetchApi" in api_module
    assert "return await fetch(input, init)" in api_module
    assert 'code: "network_error"' in api_module
    assert "status: 0" in api_module
    assert "API request could not reach the server." in api_module
    assert "fetchApi(`${API_BASE_URL}${path}`" in api_module
    assert "fetchApi(`${rootPrefix}/health`" in api_module
    assert "fetchApi(`${API_BASE_URL}/parse/upload/workflow`" in api_module


def test_frontend_api_sets_json_content_type_only_for_body_requests() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")

    assert "headers: requestHeaders(init)" in api_module
    assert "function requestHeaders(init?: RequestInit): Headers" in api_module
    assert "new Headers(init?.headers)" in api_module
    assert "init?.body !== undefined" in api_module
    assert "!(init.body instanceof FormData)" in api_module
    assert 'headers.set("Content-Type", "application/json")' in api_module
    assert '"Content-Type": "application/json"' not in api_module


def test_frontend_api_calls_match_backend_route_surface() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")
    frontend_calls = _frontend_api_calls(api_module)

    backend_calls = {
        (method, route.path)
        for route in create_app().routes
        if isinstance(route, APIRoute)
        for method in route.methods or set()
        if method not in {"HEAD", "OPTIONS"}
    }

    assert frontend_calls
    assert frontend_calls - backend_calls == set()


def test_frontend_api_encodes_dynamic_path_segments() -> None:
    api_module = API_MODULE.read_text(encoding="utf-8")
    raw_dynamic_segments = [
        r"/\$\{workflowId\}",
        r"/\$\{reviewId\}",
        r"/\$\{judgmentId\}",
    ]

    assert "function pathSegment(value: string): string" in api_module
    assert "encodeURIComponent(value)" in api_module
    for pattern in raw_dynamic_segments:
        assert re.search(pattern, api_module) is None
    assert "${pathSegment(workflowId)}" in api_module
    assert "${pathSegment(reviewId)}" in api_module
    assert "${pathSegment(judgmentId)}" in api_module


def test_app_shell_storage_badge_uses_runtime_config_contract() -> None:
    app_shell = APP_SHELL.read_text(encoding="utf-8")

    assert "useRuntimeConfigQuery" in app_shell
    assert "runtimeConfig.storage_backend" in app_shell
    assert "runtimeConfig.persistent_storage" in app_shell
    assert "Persistent storage" not in app_shell


def _normalize_frontend_api_path(raw_path: str) -> str | None:
    path = raw_path
    if path.startswith("${API_BASE_URL}"):
        path = path.removeprefix("${API_BASE_URL}")
        if path.startswith("/"):
            path = f"/api/v1{path}"
    elif path.startswith("${rootPrefix}"):
        path = path.removeprefix("${rootPrefix}")
    elif path.startswith("/api/v1"):
        return path
    elif path.startswith("/"):
        path = f"/api/v1{path}"
    else:
        return None

    path = path.split("${query", 1)[0]
    path = path.replace("${workflowId}", "{workflow_id}")
    path = path.replace("${pathSegment(workflowId)}", "{workflow_id}")
    path = path.replace("${reviewId}", "{review_id}")
    path = path.replace("${pathSegment(reviewId)}", "{review_id}")
    path = path.replace("${pathSegment(judgmentId)}", "{judgment_id}")
    if path == "/api/v1/health":
        return "/health"
    return path


def _frontend_api_calls(api_module: str) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for match in FRONTEND_API_CALL_RE.finditer(api_module):
        path = _normalize_frontend_api_path(match.group("path"))
        if path is None or path == "/api/v1":
            continue
        call_source = _balanced_call_source(api_module, match.start())
        method_match = re.search(r"method:\s*[\"']([A-Z]+)[\"']", call_source)
        method = method_match.group(1) if method_match else "GET"
        calls.add((method, path))
    return calls


def _balanced_call_source(source: str, start: int) -> str:
    opening = source.find("(", start)
    if opening == -1:
        return source[start:]

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    return source[start:]


def test_e2e_cleanup_script_emits_parseable_json_summary() -> None:
    script = CLEANUP_SCRIPT.read_text(encoding="utf-8")

    assert "import json" in script
    assert "json.dumps(" in script
    assert "sort_keys=True" in script
    assert "deleted_workflows" in script
    assert "deleted_datasets" in script
    assert "deleted_events" in script
    assert "deleted_reviews" in script
    assert "deleted_evidence" in script
    assert "deleted_dataset_files" in script
    assert "deleted_auth_sessions" in script
    assert "deleted_auth_users" in script
    assert 'PLAYWRIGHT_GOOGLE_SUB_LIKE = "playwright-%"' in script
    assert 'PLAYWRIGHT_INSTRUCTION_LIKE = "Playwright E2E:%"' in script
    assert "left join ojtflow.users" in script
    assert "state_json->>'user_instruction'" in script
    assert "state_json->>'instruction'" in script
    assert "collect_file_refs" in script
    assert "input_refs, output_refs, event_json" in script
    assert "path.resolve().relative_to(data_root)" in script
    assert "ojtflow.workflow_events" in script
    assert "ojtflow.reviews" in script
    assert "ojtflow.evidence" in script
    assert "delete from ojtflow.sessions" in script
    assert "print({" not in script


def test_release_residue_assertion_matches_cleanup_workflow_markers() -> None:
    cleanup_script = CLEANUP_SCRIPT.read_text(encoding="utf-8")
    release_check = RELEASE_CHECK.read_text(encoding="utf-8")
    required_markers = [
        "u.google_sub like",
        "state_json->>'user_instruction'",
        "state_json->>'instruction'",
        "Playwright E2E:%",
    ]

    for marker in required_markers:
        assert marker in cleanup_script
        assert marker in release_check


def test_e2e_local_cleanup_is_success_only_and_limited_to_reports() -> None:
    package_json = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    local_cleanup = LOCAL_CLEANUP_SCRIPT.read_text(encoding="utf-8")
    release_check = RELEASE_CHECK.read_text(encoding="utf-8")

    assert package_json["scripts"]["e2e:cleanup:local"] == (
        "node scripts/cleanup-e2e-local-artifacts.mjs"
    )
    assert 'const artifactDirs = ["test-results", "playwright-report"];' in local_cleanup
    assert "rmSync(artifactPath, { force: true, recursive: true })" in local_cleanup
    assert "repoRoot" not in local_cleanup
    assert "docker" not in local_cleanup

    failure_exit_index = release_check.index('exit "${e2e_status}"')
    local_cleanup_index = release_check.index('npm run e2e:cleanup:local')
    residue_assertion_index = release_check.index('run_step "E2E residue assertion"')

    assert residue_assertion_index < failure_exit_index < local_cleanup_index


def test_playwright_cookie_authenticated_posts_send_origin_header() -> None:
    violations: list[str] = []

    for source_file in sorted(path for path in FRONTEND_E2E.rglob("*.ts") if path.is_file()):
        source = source_file.read_text(encoding="utf-8")
        for match in PLAYWRIGHT_CONTEXT_POST_RE.finditer(source):
            call_source = _balanced_call_source(source, match.start())
            if "headers:" not in call_source or "Origin:" not in call_source:
                violations.append(str(source_file.relative_to(REPO_ROOT)))

    assert violations == []
