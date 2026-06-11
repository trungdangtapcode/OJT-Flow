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
RETRIEVAL_SPLIT_FILES = [
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "active-filter-bar.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "concept-candidate-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-empty-state.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-item-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-item-row.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "coverage-diagnostics-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "corrective-action-type-count-chips.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-highlight-utils.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-pack-buckets.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-provenance-summary.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-provenance-snippet.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-provenance-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "highlighted-text.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "snippet-block.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-interpretation-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-interpretation-guidance.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-readiness-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-readiness-missing-buckets.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "evidence-support-matrix.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "filter-suggestion-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-hint-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "first-run-guide.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "graph-counter.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "hit-card-evidence-section.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "hit-card-score-section.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "hit-card-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "judgment-evaluation-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "judgment-evaluation-outcome-badges.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "judgment-evaluation-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "use-judgment-evaluation-report-copy.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "metric-primitives.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-action-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-format.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-loosen-scope-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-remediation-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-remediation-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-remediation-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-quality-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "no-result-suggestion-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "quality-signal-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-hit-card-copy-report.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-form-session.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "retrieval-form-state-builders.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-run-session.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-plan-session.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-plan-filter-action.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-workspace-search-actions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-judgment-actions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-judgment-hydration.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-judgment-queries.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-judgment-session.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-search-actions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-active-filter-bar.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-panel-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-submit-button.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-fields.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-builder-notices.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-page-chrome.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-query-column.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-results-column.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-page-controller.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "hooks"
    / "use-retrieval-page-workspace.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-page-props.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-page-prop-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-page-chrome-props.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-page-query-column-props.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-page-results-column-props.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-inline-guide.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "recommended-actions-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "recommended-action-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "recommended-action-broaden-controls.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "recommended-actions-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "recommended-actions-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "recommended-actions-panel-model.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-variant-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-diagnostic-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-analysis-block.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-analysis-block-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-analysis-token-sections.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-aspect-plan.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-profile-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-hint-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "ranked-evidence-triage-fact.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "ranked-evidence-triage-facts.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "ranked-evidence-triage-guidance.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "ranked-evidence-triage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "ranked-evidence-triage-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "relevance-judgment-control.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-runtime-status.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-trace-content.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-trace-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-trace-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-trace-panel-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-trace-unavailable.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-summary-strip.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "run-comparison-detail-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "run-comparison-summary-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "result-facets.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-inventory-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "use-source-inventory-panel-state.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-inventory-filter-controls.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-inventory-readiness-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-diversity-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-diversity-panel-view.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-metadata-badges.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-empty-state.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-option-row.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-picker-format.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "use-source-scope-picker-state.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-picker.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-picker-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-selected-summary.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "source-scope-status-notice.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "hit-evidence-audit-strip.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "hit-explanation-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "strategy-standard-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "standard-search-governance-notes.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "standard-search-match-reasons.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "standard-search-plan-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "standard-search-plan-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "standard-search-step-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "submitted-search-filter-chips.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "submitted-search-metadata-chips.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "submitted-search-summary.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "submitted-search-summary-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "token-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "trace-fact.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-overview-section.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-judgment-section.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-evidence-section.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-section-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-results-hit-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-answer-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "use-search-answer-card-state.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-health-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-readiness-checklist.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "cockpit-metric-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "query-health-status.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-panel-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-insights.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-metric-grid.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-query-transformation.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-cockpit-next-best-action.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-aspect-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-detail-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-filter-suggestion-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-hint-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-rewrite-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-summary-panels.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-task-group-toolbar.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-task-group-count-view.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-task-remaining.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-task-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview-content.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview-empty.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-plan-preview-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-preset-strip.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-preset-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-preset-category-filter.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-preset-header.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-preset-filter.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-filter-active.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-filter-format.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-filter-suggestions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-filter-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-query-analysis-coercion.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-query-analysis-profile-values.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-query-analysis-task-values.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-comparison-node.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-evidence-summary.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-evidence-summary-view.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-panel.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-panel-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-row.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-row-actions.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-row-summary.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-format.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "search-run-history-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "use-search-run-comparison-view.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "section-help-text.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-review-path-action-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-review-path-check-card.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-review-path-check-list.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-review-path-format.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "components"
    / "retrieval-review-path.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "corrective-actions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "evidence-interpretation.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "evidence-interpretation-status.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "evidence-interpretation-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "evidence-interpretation-values.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "evidence-interpretation-view-model.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-report.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-interpretation.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-hints.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-status.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-view-model.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-answer-warnings.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-history-model.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-labels.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-presentation.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-presentation-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-quality.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "search-run-remediation.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-concepts.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-coverage.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-dimensions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-facets.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-profiles.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-run-comparison-quality-signals.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-path.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-actions.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-checklist.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-guidance.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-path-builder.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-support.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-types.ts",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "retrieval"
    / "model"
    / "retrieval-review-warnings.ts",
]
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


def test_feature_routes_are_lazy_loaded() -> None:
    app = (FRONTEND_SRC / "App.tsx").read_text(encoding="utf-8")
    app_shell = APP_SHELL.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert "lazy" in app
    assert "Suspense" in app
    assert "RouteSuspense" in app
    assert 'import("./features/retrieval/retrieval-page")' in app
    assert 'import("./features/assistant/assistant-page")' in app
    assert 'import("./features/workflows/workflows-page")' in app
    assert 'from "./features/retrieval/retrieval-page"' not in app
    assert 'from "./features/assistant/assistant-page"' not in app
    assert 'from "./features/workflows/workflows-page"' not in app
    assert 'preload="intent"' in app_shell
    assert "Feature routes are lazy-loaded" in frontend_architecture
    assert 'preload="intent"' in frontend_architecture


def test_retrieval_page_surfaces_runtime_ranking_stack() -> None:
    retrieval_page = RETRIEVAL_PAGE.read_text(encoding="utf-8")
    retrieval_page_controller_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-page-controller.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_workspace_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-page-workspace.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_workspace_types_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-page-workspace-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_workspace_search_submit_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-workspace-search-submit.ts"
    ).read_text(encoding="utf-8")
    retrieval_workspace_clear_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-workspace-clear-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_workspace_view_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-workspace-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_workspace_search_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-workspace-search-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_chrome_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-chrome-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_query_column_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-query-column-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_query_builder_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-query-builder-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_search_plan_preview_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-search-plan-preview-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_search_run_history_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-search-run-history-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_results_column_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-results-column-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_search_results_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-search-results-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_page_trace_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-page-trace-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_results_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_content = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-content.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_content_props = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-content-props.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_results_panel_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-panel-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_results_overview_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-overview-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_judgment_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-judgment-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_evidence_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-evidence-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_hit_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-hit-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_hit_card_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-hit-card-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_no_result_remediation = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-no-result-remediation.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-results-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-search-cockpit.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_section_stack = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-section-stack.tsx"
    ).read_text(encoding="utf-8")
    server_state = (FRONTEND_SRC / "lib" / "server-state.ts").read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")
    types_module = FRONTEND_TYPES.read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    api_contract = (REPO_ROOT / "docs" / "api_contract_v0.md").read_text(encoding="utf-8")
    retrieval_evidence_interpretation = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-interpretation-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-interpretation-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-readiness-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-readiness-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_interpretation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-readiness-interpretation-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_shell_class = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-readiness-shell-class.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_missing_buckets = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-readiness-missing-buckets.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_pack_buckets = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-pack-buckets.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_provenance_snippet = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-provenance-snippet.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_provenance_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-provenance-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_snippet_block = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "snippet-block.tsx"
    ).read_text(encoding="utf-8")
    retrieval_highlighted_text = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "highlighted-text.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_highlight_utils = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-highlight-utils.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_matrix = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-matrix.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_matrix_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-matrix-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_matrix_card_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-matrix-card-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_signal_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-signal-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_mobile_field = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-mobile-field.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_matrix_table = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-matrix-table.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_matrix_table_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-matrix-table-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_coverage_diagnostics_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "coverage-diagnostics-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_coverage_diagnostics_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "coverage-diagnostics-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_coverage_diagnostics_item_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "coverage-diagnostics-item-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_coverage_diagnostics_item_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "coverage-diagnostics-item-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_concept_candidate_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "concept-candidate-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_filter_suggestion_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "filter-suggestion-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_corrective_action_chips = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "corrective-action-type-count-chips.tsx"
    ).read_text(encoding="utf-8")
    retrieval_corrective_action_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "corrective-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_status_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_cards_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-cards.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_top_match_card_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-top-match-card.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_coverage_card_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-coverage-card.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_next_action_card_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-next-action-card.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-interpretation-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-readiness-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-readiness-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_interpretation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-readiness-interpretation.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-readiness-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_readiness_format_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "evidence-readiness-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_evidence_audit_strip = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-evidence-audit-strip.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_evidence_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-card-evidence-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-card-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_score_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-card-score-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-card-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "hit-card-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_report_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "hit-card-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_ranking_signals = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-ranking-signals.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_matched_terms = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-matched-terms.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_locator_details = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-locator-details.tsx"
    ).read_text(encoding="utf-8")
    retrieval_copy_feedback = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "copy-feedback.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_card_copy_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-hit-card-copy-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_hit_explanation_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-explanation-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_score_explanation = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-score-explanation.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_diversity_selection = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-diversity-selection.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_concept_grounding = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-concept-grounding.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_query_aspect_support = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-query-aspect-support.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_interpretation_guidance = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-interpretation-guidance.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_use_guidance_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-use-guidance-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_usability_summary_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-usability-summary-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_match_explanation_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-match-explanation-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_hit_match_explanation_metric = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "hit-match-explanation-metric.tsx"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_status = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "evidence-support-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_relevance_judgment_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "relevance-judgment-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_runtime_status = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-runtime-status.tsx"
    ).read_text(encoding="utf-8")
    retrieval_runtime_status_strip = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "runtime-status-strip.tsx"
    ).read_text(encoding="utf-8")
    retrieval_runtime_status_fact = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "runtime-status-fact.tsx"
    ).read_text(encoding="utf-8")
    retrieval_runtime_graph_status = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "runtime-graph-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_graph_handoff_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "graph-handoff-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_panel_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-panel-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_summary_metrics = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-summary-metrics.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_source_checks = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-source-checks.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_source_check_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-source-check-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_integrity_warnings = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "integrity-warnings.tsx"
    ).read_text(encoding="utf-8")
    retrieval_trace_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-trace-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_trace_content = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-trace-content.tsx"
    ).read_text(encoding="utf-8")
    retrieval_trace_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-trace-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_trace_panel_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-trace-panel-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata_values = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata_details = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata-details.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata_section_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata-section-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_endpoint_scope_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-endpoint-scope-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_parameter_examples_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-parameter-examples-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_lineage_followup_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-lineage-followup-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_selected_candidates_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-selected-candidates-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_metadata_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-metadata-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_ranked_evidence_triage = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "ranked-evidence-triage.tsx"
    ).read_text(encoding="utf-8")
    retrieval_ranked_evidence_triage_facts = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "ranked-evidence-triage-facts.tsx"
    ).read_text(encoding="utf-8")
    retrieval_ranked_evidence_triage_guidance = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "ranked-evidence-triage-guidance.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_variant_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-variant-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_variant_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-variant-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_diagnostic_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-diagnostic-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_diagnostic_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-diagnostic-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_diagnostic_metadata = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-diagnostic-metadata.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_diagnostic_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-diagnostic-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_block = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-analysis-block.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_block_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-analysis-block-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_counter = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-analysis-counter.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-analysis-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_token_sections = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-analysis-token-sections.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_plan = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-plan.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_plan_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-plan-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_filter_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-filter-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_filter_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-filter-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_filter_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-filter-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_aspect_plan_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-aspect-plan-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_profile_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-profile-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_profile_filter_actions = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-profile-filter-actions.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_profile_rule_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-profile-rule-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_profile_card_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-profile-card-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_hint_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-hint-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-answer-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_card_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-search-answer-card-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-answer-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_metrics = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-answer-metrics.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_warning_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-answer-warning-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-answer-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_health_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-health-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_health_item_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-health-item-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_readiness_checklist = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-readiness-checklist.tsx"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_metric_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "cockpit-metric-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_health_status = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-health-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-search-cockpit.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_section_stack = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-section-stack.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_copy_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-copy-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_status_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-status-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_status_badge_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-status-badge-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_insights = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-insights.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_metric_grid = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-metric-grid.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_metric_grid = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-metric-grid.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_metric_grid = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-metric-grid.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_query_transformation = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-query-transformation.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_next_best_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-next-best-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_apply_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-apply-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_broaden_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-broaden-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_evidence_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-evidence-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_evidence_summary_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-evidence-summary-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_row_actions = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-row-actions.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_row_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-row-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_row_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-row-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_row_details = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-row-details.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-history-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_node = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-node.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_view_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-search-run-comparison-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_active_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-comparison-active.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_group = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-group.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_group_toolbar = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-group-toolbar.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_group_count_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-group-count-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_remaining = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-remaining.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_badge_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-badge-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_action_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-action-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_filter_chips = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-filter-chips.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_actions = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-actions.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_content = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-content.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_summary_stack = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-summary-stack.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_detail_stack = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-detail-stack.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_notices = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-notices.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_empty = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-empty.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_copy_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-copy-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_component_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_route_decision_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-route-decision-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_suggested_filters_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-suggested-filters-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_panel_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-search-plan-preview-panel-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_panel_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-panel-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_report = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-preview-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_preview_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-plan-preview-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_detail_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-detail-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_aspect_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-aspect-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_filter_suggestion_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-filter-suggestion-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_hint_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-hint-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_rewrite_preview = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-rewrite-preview.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_summary_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-summary-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_coverage_summary_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-coverage-summary-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_summary_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-summary-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_run_order = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-run-order.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_summary_actions = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-task-summary-actions.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_summary_actions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-plan-task-summary-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_risk_signals_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-plan-risk-signals-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_strip = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-strip.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_category_filter = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-category-filter.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_strip_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-search-preset-strip-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_filter_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-preset-filter.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_picker = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-scope-picker.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_picker_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-scope-picker-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_picker_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-source-scope-picker-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_option_row = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-scope-option-row.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_status_notice = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-scope-status-notice.tsx"
    ).read_text(encoding="utf-8")
    retrieval_active_filter_bar = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "active-filter-bar.tsx"
    ).read_text(encoding="utf-8")
    retrieval_submitted_search_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "submitted-search-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_submitted_search_filter_chips = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "submitted-search-filter-chips.tsx"
    ).read_text(encoding="utf-8")
    retrieval_submitted_search_metadata_chips = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "submitted-search-metadata-chips.tsx"
    ).read_text(encoding="utf-8")
    retrieval_submitted_search_summary_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "submitted-search-summary-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_inline_guide = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-inline-guide.tsx"
    ).read_text(encoding="utf-8")
    retrieval_page_chrome = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-page-chrome.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_column = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-query-column.tsx"
    ).read_text(encoding="utf-8")
    retrieval_results_column = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-results-column.tsx"
    ).read_text(encoding="utf-8")
    retrieval_summary_strip = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-summary-strip.tsx"
    ).read_text(encoding="utf-8")
    retrieval_section_help_text = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "section-help-text.tsx"
    ).read_text(encoding="utf-8")
    retrieval_token_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "token-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_trace_fact = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "trace-fact.tsx"
    ).read_text(encoding="utf-8")
    retrieval_graph_counter = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "graph-counter.tsx"
    ).read_text(encoding="utf-8")
    retrieval_metric_primitives = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "metric-primitives.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_remediation_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-remediation-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_loosen_scope_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-loosen-scope-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_quality_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-quality-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_remediation_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-remediation-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_suggestion_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-suggestion-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_detail_stack = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-detail-stack.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_help = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-help.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_copy_action = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-copy-action.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_copy_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-judgment-evaluation-report-copy.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_metrics = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-metrics.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_readiness = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-readiness.tsx"
    ).read_text(encoding="utf-8")
    retrieval_judgment_evaluation_recommendations = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "judgment-evaluation-recommendations.tsx"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_list_item = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-list-item.tsx"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_metadata = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-metadata.ts"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_metadata_sections = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-metadata-sections.ts"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_metadata_values = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-metadata-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_metadata_details = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-metadata-details.tsx"
    ).read_text(encoding="utf-8")
    retrieval_quality_signal_variants = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "quality-signal-variants.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_form_content = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-form-content.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_active_filter_bar = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-active-filter-bar.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_submit_button = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-submit-button.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_column = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-query-column.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_text_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-text-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_schema_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-schema-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_top_k_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-top-k-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_format_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-format-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_resource_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-resource-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_select = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-select.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_text_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-text-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_schema_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-schema-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_top_k_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-top-k-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_format_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-format-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_resource_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-resource-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_select = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-select.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_notices = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-notices.tsx"
    ).read_text(encoding="utf-8")
    retrieval_page_chrome = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-page-chrome.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_panel_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "use-source-inventory-panel-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_source_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-source-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filter_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-filter-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filter_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-filter-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_filter_chip_group = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-filter-chip-group.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_filter_chip_class = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-filter-chip-class.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filter_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-filter-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_readiness_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-readiness-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_standard_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-standard-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_plan_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-plan-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_governance_notes = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-governance-notes.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_match_reasons = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-match-reasons.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_plan_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-plan-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_step_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-step-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_standard_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-standard-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendations_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendations-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendation-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_diversity_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-diversity-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_diversity_panel_view = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-diversity-panel-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_diversity_rationale = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-diversity-rationale.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_diversity_metric_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-diversity-metric-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_source_diversity = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-source-diversity.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_list_delta = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-list-delta.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_summary_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-summary-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_summary_metrics = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-summary-metrics.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_at_a_glance = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-at-a-glance.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_metrics = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-metrics.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_delta_metric = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-delta-metric.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_summary_narrative = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-summary-narrative.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_operator_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-operator-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_diagnosis = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-diagnosis.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_recommended_actions = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-recommended-actions.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_detail_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-detail-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_query_detail_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-query-detail-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_query_profile = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-query-profile.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_concept_grounding = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-concept-grounding.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_query_aspects = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-query-aspects.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_quality_detail_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-quality-detail-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_coverage_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-coverage-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_coverage_status_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-coverage-status-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_coverage_summary_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-coverage-summary-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_coverage_key = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-coverage-key.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_quality_signals_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-quality-signals-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_facet_coverage_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-facet-coverage-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rank_rule_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-rank-rule-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rank_changes = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-rank-changes.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_evidence_change = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-evidence-change.tsx"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rule_packs = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "run-comparison-rule-packs.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_help = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-help.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_top_source = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-top-source.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_summary_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-summary-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_detail_section = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-detail-section.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_status_badges = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-status-badges.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_baseline = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-baseline.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_run_comparison_metric_grid = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-run-comparison-metric-grid.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_standard_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-standard-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendations_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendations-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendation-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_plan_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-plan-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_governance_notes = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-governance-notes.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_match_reasons = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-match-reasons.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_plan_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-plan-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_standard_search_step_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "standard-search-step-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_standard_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-standard-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendations_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendations-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendation-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_report_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_interpretation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-interpretation.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_hints_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-hints.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_status_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_answer_warnings_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-answer-warnings.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_presentation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-presentation.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_history_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-history-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_labels_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-labels.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_quality_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-quality.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_run_remediation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-run-remediation.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_view_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-view-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_quality_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-quality-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_view_derivations_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-view-derivations.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_runtime_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-runtime.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_ranking_runtime_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-ranking-runtime.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_runtime_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-runtime.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_diversity_runtime_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-diversity-runtime.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_evidence_counts_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-evidence-counts.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_signals_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-signals.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_filter_signals_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-filter-signals.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_recommended_action_filter_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-recommended-action-filter.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_diagnostics_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-diagnostics.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_items_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-items.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_item_builders_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-item-builders.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_item_policy_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-item-policy.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_item_status_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-item-status.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_item_descriptions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-item-descriptions.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_signals_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-signals.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_query_health_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-query-health-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_cockpit_readiness_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-cockpit-readiness.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_rules_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-rules.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_profile_rules_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-profile-rules.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_quality_rules_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-quality-rules.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_source_rules_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-source-rules.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_stability_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-stability.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_diagnosis_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-diagnosis-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommendation_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommendation-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_summary_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-summary-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_judgment_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-judgment-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_actions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_actions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_policy_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-policy.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_configuration_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-configuration.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_evidence_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-evidence.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_judgments_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-judgments.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_quality_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-quality.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_stable_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-stable.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_recommended_action_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-recommended-action-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_operator_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-operator-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_action_format_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-action-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_sections_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-sections.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_run_sections_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-run-sections.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_deltas_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-deltas.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_evidence_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-evidence.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_source_diversity_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-source-diversity.ts"
    ).read_text(encoding="utf-8")
    retrieval_comparison_report_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-comparison-report-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_payload_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-search-payload.ts"
    ).read_text(encoding="utf-8")
    retrieval_planned_task_payload_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-planned-task-payload.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_stack_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-stack.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_coercion_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-coercion.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_profile_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-profile-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_profile_value_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-profile-value.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_aspect_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-aspect-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_concept_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-concept-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_filter_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-filter-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_diagnostic_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-diagnostic-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_hint_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-hint-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_task_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-task-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_coverage_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan-coverage-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_task_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan-task-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_risk_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan-risk.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_plan_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-plan-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_analysis_variants_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-query-analysis-variants.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_stack_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-stack.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_ranking_stack_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-ranking-stack.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_ranking_extraction_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-ranking-extraction.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_ranking_labels_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-ranking-labels.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_fusion_diagnostics_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-fusion-diagnostics.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_diversity_stack_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-diversity-stack.ts"
    ).read_text(encoding="utf-8")
    retrieval_runtime_quality_policy_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-runtime-quality-policy.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_diversity_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-diversity-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_quality_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-quality-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_summary_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-summary-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_dimensions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-dimensions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_concept_grounding_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-concept-grounding.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_coverage_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-coverage.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_query_aspects_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-query-aspects.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_query_profile_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-query-profile.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_rule_packs_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-rule-packs.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_actions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_builder_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-builder.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_dimension_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-dimension-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_core_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-core-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_run_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-run-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_metric_input_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-metric-input.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_dimensions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-dimensions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_evidence_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-evidence.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_concepts_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-concepts.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_coverage_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-coverage.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_facets_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-facets.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_profiles_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-profiles.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_quality_signals_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-quality-signals.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_quality_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-quality-summary.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_metrics_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-metrics.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_aggregate_metrics_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-aggregate-metrics.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_source_diversity_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-source-diversity.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rank_changes_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-rank-changes.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rule_packs_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-rule-packs.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_core_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-core-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_change_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-change-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_facet_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-facet-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_metric_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-metric-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rank_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-rank-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_comparison_rule_pack_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-run-comparison-rule-pack-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_plan_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-plan.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_standard_plan_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-standard-plan.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_query_analysis_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-query-analysis.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_ranking_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-ranking.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_readiness_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-readiness.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_retrieval_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-retrieval.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_rule_packs_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-rule-packs.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_cockpit_strategy_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-cockpit-strategy.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_diversity_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-diversity.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_evidence_hits_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-evidence-hits.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_medical_hints_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-medical-hints.ts"
    ).read_text(encoding="utf-8")
    retrieval_report_interpretation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-report-interpretation.ts"
    ).read_text(encoding="utf-8")
    retrieval_format_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_trace_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-trace-view-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_integrity_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-integrity-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_integrity_session_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-integrity-session.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_options_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-search-options-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_session_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-form-session.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_payload_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-form-payload-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-form-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_field_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-form-field-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_state_builders_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-form-state-builders.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_defaults_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-form-defaults.ts"
    ).read_text(encoding="utf-8")
    retrieval_form_derived_state_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-form-derived-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_controls_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-filter-controls.ts"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_draft_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-query-builder-draft-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-session.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-session-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-session-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_search_action_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-search-action.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_search_executor_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-search-executor.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_completion_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-session-completion.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_history_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-history-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_active_run_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-active-retrieval-run-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_history_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-session-history.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_record_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-session-record.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_transitions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-session-transitions.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_validation_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-run-session-validation.ts"
    ).read_text(encoding="utf-8")
    retrieval_run_session_types_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-run-session-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_plan_session_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-plan-session.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_session_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-judgment-session.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-judgment-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_action_state_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-judgment-action-state.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_hydration_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-judgment-hydration.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_queries_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-judgment-queries.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-search-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_planned_task_action_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-planned-task-action.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_search_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-filter-search-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_plan_filter_action_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-plan-filter-action.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_search_action_policy_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-filter-search-action-policy.ts"
    ).read_text(encoding="utf-8")
    retrieval_metadata_filter_search_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-metadata-filter-search-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_scope_search_actions_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "use-retrieval-source-scope-search-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_action_types_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-search-action-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_notice_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-search-plan-notice.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_task_controls_hook = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "hooks"
        / "retrieval-search-task-controls.ts"
    ).read_text(encoding="utf-8")
    retrieval_summary_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-summary-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_active_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-active.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_format_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_suggestions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-suggestions.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_entry_suggestions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-entry-suggestions.ts"
    ).read_text(encoding="utf-8")
    retrieval_filter_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-filter-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-inventory-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filters_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-inventory-filters.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_readiness_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-inventory-readiness.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-inventory-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-source-inventory-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_actions_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-actions.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_payload_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-payload.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_labels_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-labels.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_mapping_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-mapping.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_metrics_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-metrics.ts"
    ).read_text(encoding="utf-8")
    retrieval_judgment_report_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-judgment-report.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_implementation = "\n".join(
        (
            REPO_ROOT
            / "frontend"
            / "src"
            / "features"
            / "retrieval"
            / "model"
            / path
        ).read_text(encoding="utf-8")
        for path in (
            "retrieval-evidence-corrective-actions-report.ts",
            "retrieval-evidence-provenance.ts",
            "retrieval-evidence-report.ts",
            "retrieval-evidence-hit-signals.ts",
            "retrieval-evidence-match-explanation-backend.ts",
            "retrieval-evidence-match-explanation-fallback.ts",
            "retrieval-evidence-match-explanation.ts",
            "retrieval-evidence-score-components.ts",
            "retrieval-evidence-signals.ts",
            "retrieval-evidence-signal-extraction.ts",
            "retrieval-evidence-support.ts",
            "retrieval-evidence-support-hit.ts",
            "retrieval-evidence-support-matrix.ts",
            "retrieval-evidence-support-summary.ts",
            "retrieval-evidence-usability-summary.ts",
            "retrieval-evidence-use-guidance.ts",
            "retrieval-evidence-use-guidance-action.ts",
            "retrieval-evidence-use-guidance-reasons.ts",
            "retrieval-evidence-match-types.ts",
            "retrieval-evidence-matrix-types.ts",
            "retrieval-evidence-provenance-types.ts",
            "retrieval-evidence-signal-types.ts",
            "retrieval-evidence-support-types.ts",
            "retrieval-evidence-types.ts",
            "retrieval-evidence-utils.ts",
        )
    )
    retrieval_evidence_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_signal_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-signal-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_matrix_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-matrix-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_support_types_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-support-types.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_score_components_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-score-components.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_signal_extraction_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-signal-extraction.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_hit_signals_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-hit-signals.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_explanation_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-explanation.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_explanation_values_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-explanation-values.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_explanation_backend_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-explanation-backend.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_explanation_fallback_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-explanation-fallback.ts"
    ).read_text(encoding="utf-8")
    retrieval_evidence_match_explanation_merge_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-evidence-match-explanation-merge.ts"
    ).read_text(encoding="utf-8")
    assert 'export * from "./retrieval-evidence-signals";' in retrieval_evidence_model
    assert 'export * from "./retrieval-evidence-support";' in retrieval_evidence_model
    assert 'export * from "./retrieval-evidence-match-types";' in retrieval_evidence_types_model
    assert 'export * from "./retrieval-evidence-matrix-types";' in retrieval_evidence_types_model
    assert 'export * from "./retrieval-evidence-provenance-types";' in retrieval_evidence_types_model
    assert 'export * from "./retrieval-evidence-signal-types";' in retrieval_evidence_types_model
    assert 'export * from "./retrieval-evidence-support-types";' in retrieval_evidence_types_model
    assert "type EvidenceHitSignals" in retrieval_evidence_signal_types_model
    assert "type EvidenceHitMatchExplanation" in retrieval_evidence_match_types_model
    assert "type EvidenceSupportMatrixRow" in retrieval_evidence_matrix_types_model
    assert "type EvidenceSupportStatus" in retrieval_evidence_support_types_model
    retrieval_search_plan_tasks_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-plan-tasks.ts"
    ).read_text(encoding="utf-8")
    retrieval_search_plan_task_group_view_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "search-plan-task-group-view.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_path = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-review-path.tsx"
    ).read_text(encoding="utf-8")
    retrieval_review_path_action_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-review-path-action-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_review_path_check_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-review-path-check-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_review_path_check_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-review-path-check-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_review_path_format = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-review-path-format.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-review-path.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_checklist_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-review-checklist.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_guidance_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-review-guidance.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_path_builder_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-review-path-builder.ts"
    ).read_text(encoding="utf-8")
    retrieval_review_warnings_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "retrieval-review-warnings.ts"
    ).read_text(encoding="utf-8")
    retrieval_recommended_actions_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-actions-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_action_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-action-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_action_card_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-action-card-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_action_filter_summary = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-action-filter-summary.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_action_broaden_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-action-broaden-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_actions_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "recommended-actions-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_recommended_actions_panel_model = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "model"
        / "recommended-actions-panel-model.ts"
    ).read_text(encoding="utf-8")
    retrieval_result_facets = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "result-facets.tsx"
    ).read_text(encoding="utf-8")
    retrieval_result_facet_bucket_button = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "result-facet-bucket-button.tsx"
    ).read_text(encoding="utf-8")
    retrieval_result_facet_sections = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "result-facet-sections.ts"
    ).read_text(encoding="utf-8")
    retrieval_result_facet_types = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "result-facet-types.ts"
    ).read_text(encoding="utf-8")

    assert "retrievalRuntimeStatusStripView" not in retrieval_page
    assert "retrievalRuntimeStatusStripView" in retrieval_page_results_column_props
    assert "retrievalPageSearchResultsProps" in retrieval_page_results_column_props
    assert "function retrievalPageSearchResultsProps" in retrieval_page_search_results_props
    assert "retrievalPageTraceProps" in retrieval_page_results_column_props
    assert "function retrievalPageTraceProps" in retrieval_page_trace_props
    assert "setHitJudgment" not in retrieval_page_results_column_props
    assert "setHitJudgment" in retrieval_page_search_results_props
    assert "rankingStackFromPackage" in retrieval_summary_model
    assert "retrieval-format" not in retrieval_page
    assert "retrieval-format" not in retrieval_page_query_column_props
    assert "retrieval-format" in retrieval_page_search_plan_preview_props
    assert "function formatClaim" not in retrieval_page
    assert "function formatClaim" in retrieval_format_model
    assert "function formatConfidence" in retrieval_format_model
    assert "function formatScore" in retrieval_format_model
    assert "function formatCount" in retrieval_format_model
    assert "function formatNullablePercent" in retrieval_format_model
    assert "function formatShortSignature" in retrieval_format_model
    assert "function rankingStackFromPackage" not in retrieval_page
    assert "rankingStackFromPackage" in retrieval_runtime_stack_model
    assert "function rankingStackFromPackage" in retrieval_runtime_ranking_extraction_model
    assert "diversityFromPackage" in retrieval_summary_model
    assert "scoreComponentsFromHit" not in retrieval_page
    assert "function scoreComponentsFromHit" in retrieval_evidence_score_components_model
    assert "function scoreComponentsFromHit" not in retrieval_evidence_model
    assert "evidenceSupportSummaryForHit" in retrieval_evidence_implementation
    assert "supportStatusBadgeVariant" in retrieval_evidence_implementation
    assert "evidenceSignalsFromHit" not in retrieval_page
    assert "SearchResults" in retrieval_results_column
    assert "./search-results-panel" in retrieval_results_column
    assert "components/search-results-panel" not in retrieval_page
    assert "SearchResultsHeader" in retrieval_search_results_panel
    assert "SearchResultsContent" in retrieval_search_results_panel
    assert "type SearchResultsProps" in retrieval_search_results_panel_types
    assert "SearchResultsProps" in retrieval_search_results_panel
    assert "searchResultsContentProps" in retrieval_search_results_panel
    assert "function searchResultsContentProps" in retrieval_search_results_content_props
    assert "type SearchResultsContentProps" in retrieval_search_results_content_props
    assert "hitsProps: {" not in retrieval_search_results_panel
    assert "hitsProps: {" in retrieval_search_results_content_props
    assert "SearchResultsHitList" in retrieval_search_results_content
    assert "EmptySearchResults" in retrieval_search_results_panel
    assert "./search-results-header" in retrieval_search_results_panel
    assert "./search-results-content" in retrieval_search_results_panel
    assert "./search-results-hit-list" in retrieval_search_results_content
    assert "SearchResultsOverviewSection" in retrieval_search_results_content
    assert "SearchResultsJudgmentSection" in retrieval_search_results_content
    assert "SearchResultsEvidenceSection" in retrieval_search_results_content
    assert "./search-results-overview-section" in retrieval_search_results_content
    assert "./search-results-judgment-section" in retrieval_search_results_content
    assert "./search-results-evidence-section" in retrieval_search_results_content
    assert "searchResultsViewModel" in retrieval_search_results_panel
    assert "function searchResultsViewModel" in retrieval_search_results_view_model
    assert "activeFacetFiltersFromPayload" not in retrieval_search_results_panel
    assert "activeFacetFiltersFromPayload" in retrieval_search_results_view_model
    assert "retrievalCockpitReportFromPackage" not in retrieval_search_results_panel
    assert "retrievalCockpitReportFromPackage" in retrieval_search_results_view_model
    assert "HitCard" not in retrieval_search_results_panel
    assert "SearchResultsHitCardList" in retrieval_search_results_hit_list
    assert './hit-card"' not in retrieval_search_results_hit_list
    assert "HitCard" in retrieval_search_results_hit_card_list
    assert "./hit-card" in retrieval_search_results_hit_card_list
    assert "function HitCard" not in retrieval_page
    assert "type HitCardProps" in retrieval_hit_card_types
    assert "}: HitCardProps)" in retrieval_hit_card
    assert "recommendedActions: RetrievalRecommendedAction[]" not in retrieval_hit_card
    assert "HitCardScoreSection" in retrieval_hit_card
    assert "./hit-card-score-section" in retrieval_hit_card
    assert "ScoreExplanation" in retrieval_hit_card_score_section
    assert "./hit-explanation-panels" in retrieval_hit_card_score_section
    assert "function ScoreExplanation" not in retrieval_page
    assert "ScoreExplanation" in retrieval_hit_explanation_panels
    assert "./hit-score-explanation" in retrieval_hit_explanation_panels
    assert "Score explanation" in retrieval_hit_score_explanation
    assert "qualitySignalBadgeVariant" not in retrieval_search_results_panel
    assert "qualitySignalBadgeVariant" in retrieval_search_results_judgment_section
    assert "./quality-signal-list" in retrieval_search_results_judgment_section
    assert "function QualitySignalList" not in retrieval_page
    assert "QualitySignalListItem" in retrieval_quality_signal_list
    assert "QualitySignalMetadataDetails" in retrieval_quality_signal_list_item
    assert "function qualitySignalMetadataDetails" in retrieval_quality_signal_metadata
    assert "conceptMetadataValues" in retrieval_quality_signal_metadata
    assert "function conceptMetadataValues" in retrieval_quality_signal_metadata_sections
    assert "function provenanceIssueMetadataValues" in retrieval_quality_signal_metadata_sections
    assert "function suggestedFilterMetadataValues" in retrieval_quality_signal_metadata_sections
    assert "function recordValue" in retrieval_quality_signal_metadata_values
    assert "function stringArrayValue" in retrieval_quality_signal_metadata_values
    assert "Quality signals explain why the evidence package" in retrieval_quality_signal_list
    assert "leading-5 text-muted-foreground" in retrieval_section_help_text
    assert "bg-amber-100 text-amber-900" in retrieval_token_list
    assert "RetrievalResultsColumn" in retrieval_page
    assert "components/retrieval-results-column" in retrieval_page
    assert "RetrievalTracePanel" in retrieval_results_column
    assert "./retrieval-trace-panel" in retrieval_results_column
    assert "components/retrieval-trace-panel" not in retrieval_page
    assert "function RetrievalTracePanel" not in retrieval_page
    assert "RetrievalTraceHeader" in retrieval_trace_panel
    assert "RetrievalTraceContent" in retrieval_trace_panel
    assert "RetrievalTraceUnavailable" in retrieval_trace_panel
    assert "TraceFact" in retrieval_trace_content
    assert "./trace-fact" in retrieval_trace_content
    assert "function TraceFact" not in retrieval_page
    assert "grid-cols-[7rem_minmax(0,1fr)]" in retrieval_trace_fact
    assert "GraphCounter" in retrieval_graph_handoff_panel
    assert "./graph-counter" in retrieval_graph_handoff_panel
    assert "function GraphCounter" not in retrieval_page
    assert "tabular-nums" in retrieval_graph_counter
    assert "IntegrityMetric" in retrieval_integrity_summary_metrics
    assert "IntegrityFact" in retrieval_integrity_source_check_row
    assert "SourceReadinessMetric" in retrieval_source_inventory_readiness_panel
    assert "./metric-primitives" in retrieval_integrity_summary_metrics
    assert "./metric-primitives" in retrieval_integrity_source_check_row
    assert "function IntegrityMetric" not in retrieval_page
    assert "function IntegrityFact" not in retrieval_page
    assert "function SourceReadinessMetric" not in retrieval_page
    assert "function metricToneClass" in retrieval_metric_primitives
    assert "bg-card/80 px-3 py-2" in retrieval_metric_primitives
    assert "Quality signals explain why the evidence package" in retrieval_quality_signal_list
    assert "Signal details" in retrieval_quality_signal_metadata_details
    assert "qualitySignalMetadataDetails" in retrieval_quality_signal_metadata_details
    assert "Retrieval quality" in retrieval_quality_signal_list
    assert "Retrieval trace help" in retrieval_trace_header
    assert "Safety-sensitive context detected" in retrieval_trace_content
    assert "Backend warnings about search coverage" in retrieval_trace_content
    assert "RetrievalTracePanelView" in retrieval_trace_panel_types
    assert "quality_signals" in retrieval_trace_view_model
    assert "quality_summary" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "RetrievalPageChrome" in retrieval_page
    assert "components/retrieval-page-chrome" in retrieval_page
    assert "RetrievalQueryColumn" in retrieval_page
    assert "components/retrieval-query-column" in retrieval_page
    assert "RetrievalSummaryStrip" not in retrieval_page
    assert "RetrievalSummaryStrip" in retrieval_page_chrome
    assert "./retrieval-summary-strip" in retrieval_page_chrome
    assert "retrievalSummaryStripView" in retrieval_summary_model
    assert "RetrievalSummaryStripViewModel" in retrieval_summary_model
    assert "function RetrievalSummary(" not in retrieval_page
    assert "PageHeader" not in retrieval_page
    assert "PageHeader" in retrieval_page_chrome
    assert "Readiness" in retrieval_summary_strip
    assert "Reranker" in retrieval_summary_strip
    assert 'export * from "./search-run-history-model";' in retrieval_search_run_presentation_model
    assert 'export * from "./search-run-labels";' in retrieval_search_run_presentation_model
    assert 'export * from "./search-run-quality";' in retrieval_search_run_presentation_model
    assert 'export * from "./search-run-remediation";' in retrieval_search_run_presentation_model
    assert "qualitySummaryTone" in retrieval_search_run_quality_model
    assert "qualitySignalBadgeVariant" not in retrieval_page
    assert "qualitySignalBadgeVariant" in retrieval_search_results_judgment_section
    assert "function qualitySignalBadgeVariant" in retrieval_quality_signal_variants
    assert "function qualitySignalBadgeVariant" not in retrieval_quality_signal_list_item
    assert "queryVariantsFromTrace" in retrieval_trace_view_model
    assert "retrievalTracePanelView" in retrieval_trace_view_model
    assert "function retrievalTracePanelView" not in retrieval_page
    assert "function queryAnalysisBlockView" in retrieval_trace_view_model
    assert "function queryAnalysisBlockView" not in retrieval_page
    assert "function queryVariantsFromTrace" not in retrieval_page
    assert "function queryVariantsFromTrace" in retrieval_query_analysis_variants_model
    assert "QueryVariantList" in retrieval_trace_content
    assert "./query-variant-list" in retrieval_trace_content
    assert "function QueryVariantList" not in retrieval_page
    assert "Query rewrites" in retrieval_query_variant_list
    assert "Query rewrites are backend-generated search variants" in retrieval_query_variant_list
    assert "QueryVariantRow" in retrieval_query_variant_list
    assert "Copy query rewrite" in retrieval_query_variant_row
    assert "humanize(variant.source)" in retrieval_query_variant_row
    assert "copyTextToClipboard" in retrieval_query_variant_list
    assert "./copy-feedback" in retrieval_query_variant_list
    assert "copyTextToClipboard" not in retrieval_query_variant_row
    assert "document.execCommand" not in retrieval_query_variant_list
    assert "document.execCommand" in retrieval_copy_feedback
    assert "function useCopyFeedback" in retrieval_copy_feedback
    assert "query_variant_details" not in retrieval_query_analysis_model
    assert "query_variant_details" in retrieval_query_analysis_stack_model
    assert "query_variant_details" in retrieval_query_analysis_variants_model
    assert "SearchPlanPreviewPanel" in retrieval_query_column
    assert "./search-plan-preview-panel" in retrieval_query_column
    assert "components/search-plan-preview-panel" not in retrieval_page
    assert "SearchPlanPreview" in retrieval_search_plan_preview_panel
    assert "./search-plan-preview" in retrieval_search_plan_preview_panel
    assert "function SearchPlanPreview" not in retrieval_page
    assert "SearchPlanPreviewContent" in retrieval_search_plan_preview
    assert "SearchPlanPreviewEmpty" in retrieval_search_plan_preview
    assert "SearchPlanPreviewHeader" in retrieval_search_plan_preview
    assert "Search plan" in retrieval_search_plan_preview_header
    assert "SearchPlanCopyAction" in retrieval_search_plan_preview_header
    assert "Copy search plan JSON" in retrieval_search_plan_copy_action
    assert "Copy plan" in retrieval_search_plan_copy_action
    assert "No search plan yet" in retrieval_search_plan_preview_empty
    assert "type SearchPlanPreviewProps" in retrieval_search_plan_preview_component_types
    assert "SearchPlanPreviewView" in retrieval_search_plan_preview_types_model
    assert "SearchPlanPreviewView" in retrieval_search_plan_preview_panel_view
    assert "SearchPlanRouteDecisionPanel" not in retrieval_search_plan_preview
    assert "SearchPlanRouteDecisionPanel" not in retrieval_search_plan_preview_content
    assert "SearchPlanRouteDecisionPanel" in retrieval_search_plan_preview_summary_stack
    assert "useRetrievalPageController" in retrieval_page
    assert "useRetrievalPlanSession" not in retrieval_page
    assert "useRetrievalPlanSession" in retrieval_page_workspace_hook
    assert "type UseRetrievalPageWorkspaceArgs" in retrieval_page_workspace_types_hook
    assert "type SearchMutationState" in retrieval_page_workspace_types_hook
    assert "UseRetrievalPageWorkspaceArgs" in retrieval_page_workspace_hook
    assert "SearchMutationState" not in retrieval_page_workspace_hook
    assert "onApplyFilterSuggestion" in retrieval_page_trace_props
    assert "applyPlanFilterSuggestion" not in retrieval_page_query_column_props
    assert "applyPlanFilterSuggestion" in retrieval_page_search_plan_preview_props
    assert "applyFilterControl" in retrieval_page_workspace_hook
    assert "planControlNotice" not in retrieval_page_query_column_props
    assert "planControlNotice" in retrieval_page_query_builder_props
    assert "Plan filter applied" in retrieval_query_builder_notices
    assert "SearchPlanPreviewSummaryStack" in retrieval_search_plan_preview_content
    assert "SearchPlanPreviewDetailStack" in retrieval_search_plan_preview_content
    assert "SearchPlanSuggestedFiltersPanel" in retrieval_search_plan_preview_detail_stack
    assert "SearchPlanFilterSuggestionPreview" in retrieval_search_plan_suggested_filters_panel
    assert "./search-plan-detail-panels" in retrieval_search_plan_suggested_filters_panel
    assert "function SearchPlanFilterSuggestionPreview" not in retrieval_page
    assert 'export * from "./search-plan-filter-suggestion-preview";' in retrieval_search_plan_detail_panels
    assert 'export * from "./search-plan-detail-types";' in retrieval_search_plan_detail_panels
    assert "Apply" in retrieval_search_plan_filter_suggestion_preview
    assert "SearchPlanAspectPreview" in retrieval_search_plan_preview_detail_stack
    assert "function SearchPlanAspectPreview" not in retrieval_page
    assert "Search aspects" in retrieval_search_plan_aspect_preview
    assert "SearchPlanRewritePreview" in retrieval_search_plan_preview_detail_stack
    assert "function SearchPlanRewritePreview" not in retrieval_page
    assert "Query rewrites" in retrieval_search_plan_rewrite_preview
    assert "SearchPlanHintPreview" in retrieval_search_plan_preview_detail_stack
    assert "function SearchPlanHintPreview" not in retrieval_page
    assert "Medical search hints" in retrieval_search_plan_hint_preview
    assert "useRetrievalPlanSession" in retrieval_page_workspace_hook
    assert "use-retrieval-plan-session" in retrieval_page_workspace_hook
    assert "function useRetrievalPlanSession" in retrieval_plan_session_hook
    assert "useRetrievalPlanQuery" in retrieval_plan_session_hook
    assert "planPayload" in retrieval_plan_session_hook
    assert "packageDataForPlanPreview: isSearchResultStale ? undefined : packageData" in retrieval_plan_session_hook
    assert "currentPlanData" in retrieval_plan_session_hook
    assert "queryAnalysisFromPlan" not in retrieval_page
    assert "useSearchPlanPreviewPanelView" in retrieval_search_plan_preview_panel
    assert "searchPlanPreviewView" not in retrieval_search_plan_preview_panel
    assert "searchPlanPreviewView" in retrieval_search_plan_preview_panel_hook
    assert "function searchPlanPreviewView" in retrieval_search_plan_preview_panel_view
    assert "queryAnalysisFromPlan" in retrieval_search_plan_preview_panel_view
    assert "function queryAnalysisFromPlan" not in retrieval_page
    assert "function queryAnalysisFromPlan" in retrieval_query_analysis_model
    assert "function queryAnalysisStackFromRecord" in retrieval_query_analysis_stack_model
    assert "queryAnalysisStackFromRecord" in retrieval_query_analysis_model
    assert "searchPlanPreviewReportText" not in retrieval_search_plan_preview_panel
    assert "searchPlanPreviewReportText" in retrieval_search_plan_preview_panel_hook
    assert "function searchPlanPreviewReportText" in retrieval_search_plan_preview_report
    assert "retrievalSearchPlanPreviewReport" in retrieval_search_plan_preview_report
    assert "function retrievalSearchPlanPreviewReport" not in retrieval_page
    assert "function retrievalSearchPlanPreviewReport" in retrieval_report_plan_model
    assert "retrieval_search_plan_preview" in retrieval_report_plan_model
    assert "SearchPlanTaskPreview" in retrieval_search_plan_preview_detail_stack
    assert "./search-plan-task-preview" in retrieval_search_plan_preview_detail_stack
    assert "function SearchPlanTaskPreview" not in retrieval_page
    assert "SearchPlanTaskGroup" in retrieval_search_plan_task_preview
    assert "Execution tasks" in retrieval_search_plan_task_preview
    assert "Local OJTFlow searches" in retrieval_search_plan_task_preview
    assert "External follow-ups" in retrieval_search_plan_task_preview
    assert "SearchPlanTaskRow" in retrieval_search_plan_task_group
    assert "SearchPlanTaskGroupToolbar" in retrieval_search_plan_task_group
    assert "./search-plan-task-group-toolbar" in retrieval_search_plan_task_group
    assert "SearchPlanTaskRemaining" in retrieval_search_plan_task_group
    assert "./search-plan-task-remaining" in retrieval_search_plan_task_group
    assert "Show remaining" not in retrieval_search_plan_task_group
    assert "Show remaining" in retrieval_search_plan_task_remaining
    assert "remainingTasks" in retrieval_search_plan_task_group
    assert "remainingTasks" in retrieval_search_plan_task_group_view_model
    assert "ChevronDown" not in retrieval_search_plan_task_group
    assert "ChevronDown" in retrieval_search_plan_task_remaining
    assert "group-open:rotate-180" in retrieval_search_plan_task_remaining
    assert "requiredTaskCount" in retrieval_search_plan_task_group
    assert "optionalTaskCount" in retrieval_search_plan_task_group
    assert "orderedSearchPlanTasks" not in retrieval_search_plan_task_group
    assert "orderedSearchPlanTasks" in retrieval_search_plan_task_group_view_model
    assert "visibleTasks" in retrieval_search_plan_task_group_view_model
    assert "requiredTaskCount" in retrieval_search_plan_task_group_view_model
    assert "optionalTaskCount" in retrieval_search_plan_task_group_view_model
    assert 'formatCount(requiredTaskCount, "required task")' not in retrieval_search_plan_task_group
    assert 'formatCount(requiredTaskCount, "required task")' not in retrieval_search_plan_task_group_toolbar
    assert 'formatCount(requiredTaskCount, "required task")' in retrieval_search_plan_task_group_count_view
    assert 'formatCount(optionalTaskCount, "optional task")' not in retrieval_search_plan_task_group_toolbar
    assert 'formatCount(optionalTaskCount, "optional task")' in retrieval_search_plan_task_group_count_view
    assert "requiredTaskCountView" in retrieval_search_plan_task_group_toolbar
    assert "optionalTaskCountView" in retrieval_search_plan_task_group_toolbar
    assert "taskGroupCountGuidance" in retrieval_search_plan_task_group_toolbar
    assert "./search-plan-task-group-count-view" in retrieval_search_plan_task_group
    assert "copyGroupQueries" not in retrieval_search_plan_task_group
    assert "copyGroupQueries" in retrieval_search_plan_task_group_toolbar
    assert "retrievalTaskClipboardText" in retrieval_search_plan_tasks_model
    assert "target: ${humanize(task.target)}" in retrieval_search_plan_tasks_model
    assert "action: ${humanize(task.action_type)}" in retrieval_search_plan_tasks_model
    assert "task-group:" in retrieval_search_plan_task_group
    assert "Copy group queries" in retrieval_search_plan_task_group_toolbar
    assert "Copied group" in retrieval_search_plan_task_group_toolbar
    assert "Prioritize required tasks before optional follow-ups" not in retrieval_search_plan_task_group_toolbar
    assert "Prioritize required tasks before optional follow-ups" in retrieval_search_plan_task_group_count_view
    assert "No local OJTFlow search task was generated" in retrieval_search_plan_task_preview
    assert "No external medical-index follow-up was generated" in retrieval_search_plan_task_preview
    assert "Run order" in retrieval_search_plan_run_order
    assert "SearchPlanTaskBadges" in retrieval_search_plan_task_row
    assert "SearchPlanTaskActionSummary" in retrieval_search_plan_task_row
    assert "SearchPlanTaskFilterChips" in retrieval_search_plan_task_row
    assert "SearchPlanTaskActions" in retrieval_search_plan_task_row
    assert "searchPlanTaskTargetBadgeView" in retrieval_search_plan_task_badges
    assert "searchPlanTaskRequirementBadgeView" in retrieval_search_plan_task_badges
    assert "local corpus" not in retrieval_search_plan_task_badges
    assert "local corpus" in retrieval_search_plan_task_badge_view
    assert "medical index" not in retrieval_search_plan_task_badges
    assert "medical index" in retrieval_search_plan_task_badge_view
    assert "What happens" in retrieval_search_plan_task_action_summary
    assert "retrievalTaskActionDescription" in retrieval_search_plan_tasks_model
    assert "Runs in OJTFlow" in retrieval_search_plan_tasks_model
    assert "Opens external source" in retrieval_search_plan_tasks_model
    assert "Copies external query" in retrieval_search_plan_tasks_model
    assert "Run task" in retrieval_search_plan_task_actions
    assert "suggested_filters" in retrieval_search_plan_task_filter_chips
    assert "SearchPlanTaskRow" in retrieval_search_plan_task_group
    assert "retrievalTaskExternalUrl" in retrieval_search_plan_tasks_model
    assert 'export * from "./retrieval-query-analysis-coercion";' in retrieval_query_analysis_values_model
    assert 'export * from "./retrieval-query-analysis-profile-values";' in retrieval_query_analysis_values_model
    assert 'export * from "./retrieval-query-analysis-task-values";' in retrieval_query_analysis_values_model
    assert "retrievalTaskActionTypeValue" in retrieval_query_analysis_task_values_model
    assert "Open follow-up" in retrieval_search_plan_task_actions
    assert "syntax only" in retrieval_search_plan_task_actions
    assert "Copy query" in retrieval_search_plan_task_actions
    assert "task-query:" in retrieval_search_plan_task_row
    assert "useRetrievalSearchActions" not in retrieval_page
    assert "useRetrievalSearchActions" not in retrieval_page_workspace_hook
    assert "useRetrievalWorkspaceSearchActions" in retrieval_page_workspace_hook
    assert "use-retrieval-workspace-search-actions" in retrieval_page_workspace_hook
    assert "useRetrievalSearchActions" in retrieval_workspace_search_actions_hook
    assert "isSupportedFilterField" in retrieval_workspace_search_actions_hook
    assert "isSupportedFilterField" not in retrieval_page_workspace_hook
    assert "function useRetrievalSearchActions" in retrieval_search_actions_hook
    assert "useRetrievalFilterSearchActions" in retrieval_search_actions_hook
    assert "function useRetrievalFilterSearchActions" in retrieval_filter_search_actions_hook
    assert "useRetrievalMetadataFilterSearchActions" in retrieval_filter_search_actions_hook
    assert "useRetrievalSourceScopeSearchActions" in retrieval_filter_search_actions_hook
    assert (
        "function useRetrievalMetadataFilterSearchActions"
        in retrieval_metadata_filter_search_actions_hook
    )
    assert (
        "function useRetrievalSourceScopeSearchActions"
        in retrieval_source_scope_search_actions_hook
    )
    assert "useRetrievalPlannedTaskAction" in retrieval_search_actions_hook
    assert "function useRetrievalPlannedTaskAction" in retrieval_planned_task_action_hook
    assert "plannedTaskSearchOverrides" not in retrieval_search_actions_hook
    assert "plannedTaskSearchOverrides" in retrieval_planned_task_action_hook
    assert "function plannedTaskSearchOverrides" not in retrieval_page
    assert "function plannedTaskSearchOverrides" not in retrieval_search_payload_model
    assert "function plannedTaskSearchOverrides" in retrieval_planned_task_payload_model
    assert "runPlannedTask" in retrieval_search_actions_hook
    assert "applyPlannedTaskControls" not in retrieval_search_actions_hook
    assert "applyPlannedTaskControls" in retrieval_planned_task_action_hook
    assert "function applyPlannedTaskControls" in retrieval_search_task_controls_hook
    assert "planFilterControlNotice" not in retrieval_search_actions_hook
    assert "planFilterControlNotice" not in retrieval_filter_search_actions_hook
    assert "planFilterControlNotice" in retrieval_plan_filter_action_hook
    assert "useRetrievalPlanFilterAction" in retrieval_filter_search_actions_hook
    assert "function useRetrievalPlanFilterAction" in retrieval_plan_filter_action_hook
    assert "function planFilterControlNotice" in retrieval_search_plan_notice_hook
    assert "type UseRetrievalSearchActionsArgs" in retrieval_search_action_types_hook
    assert "type SearchFilterSuggestion" in retrieval_search_action_types_hook
    assert "SearchPlanCoverageSummaryPanel" not in retrieval_search_plan_preview_content
    assert "SearchPlanCoverageSummaryPanel" in retrieval_search_plan_preview_summary_stack
    assert "./search-plan-summary-panels" not in retrieval_search_plan_preview_content
    assert "./search-plan-summary-panels" in retrieval_search_plan_preview_summary_stack
    assert "SearchPlanCoverageSummaryPanel" in retrieval_search_plan_summary_panels
    assert "function SearchPlanCoverageSummaryPanel" not in retrieval_page
    assert "SearchPlanTaskSummaryPanel" not in retrieval_search_plan_preview_content
    assert "SearchPlanTaskSummaryPanel" in retrieval_search_plan_preview_summary_stack
    assert "SearchPlanTaskSummaryPanel" in retrieval_search_plan_summary_panels
    assert "function SearchPlanTaskSummaryPanel" not in retrieval_page
    assert "Execution summary" in retrieval_search_plan_task_summary_panel
    assert "SearchPlanRunOrder" in retrieval_search_plan_task_summary_panel
    assert "SearchPlanTaskSummaryActions" in retrieval_search_plan_task_summary_panel
    assert "Run order" in retrieval_search_plan_run_order
    assert "Run first local task" in retrieval_search_plan_task_summary_actions
    assert "Copy external follow-ups" in retrieval_search_plan_task_summary_actions
    assert "plan-external-followups" in retrieval_search_plan_task_summary_actions
    assert "function firstRunnableLocalTask" in retrieval_search_plan_task_summary_actions_model
    assert "function externalMedicalIndexTasks" in retrieval_search_plan_task_summary_actions_model
    assert "searchPlanTaskSummary" in retrieval_search_plan_preview_panel_view
    assert "function searchPlanTaskSummary" not in retrieval_page
    assert "function searchPlanTaskSummary" not in retrieval_query_analysis_plan_model
    assert 'export * from "./retrieval-query-analysis-plan-task-summary";' in retrieval_query_analysis_plan_summary_model
    assert "function searchPlanTaskSummary" in retrieval_query_analysis_plan_task_summary_model
    assert "function planTaskSummaryValue" in retrieval_query_analysis_plan_values_model
    assert "Plan coverage" in retrieval_search_plan_coverage_summary_panel
    assert "Next action" in retrieval_search_plan_coverage_summary_panel
    assert "nextAction" in retrieval_query_analysis_plan_coverage_summary_model
    assert "searchPlanCoverageSummary" in retrieval_search_plan_preview_panel_view
    assert "function searchPlanCoverageSummary" not in retrieval_page
    assert "function searchPlanCoverageSummary" not in retrieval_query_analysis_plan_model
    assert 'export * from "./retrieval-query-analysis-plan-coverage-summary";' in retrieval_query_analysis_plan_summary_model
    assert "function searchPlanCoverageSummary" in retrieval_query_analysis_plan_coverage_summary_model
    assert "function planCoverageSummaryValue" in retrieval_query_analysis_plan_values_model
    assert "planCoverageSummary:" not in retrieval_query_analysis_model
    assert "planCoverageSummary:" in retrieval_query_analysis_stack_model
    assert "coverage_summary" in retrieval_query_analysis_model
    assert "task_summary" in retrieval_query_analysis_model
    assert "SearchPlanRiskSignalsPanel" in retrieval_search_plan_preview_detail_stack
    assert "SearchPlanRiskSignalsPanel" in retrieval_search_plan_summary_panels
    assert "function SearchPlanRiskSignalsPanel" not in retrieval_page
    assert "Plan risks" in retrieval_search_plan_risk_signals_panel
    assert "searchPlanRiskSignals" in retrieval_search_plan_preview_panel_view
    assert "function searchPlanRiskSignals" not in retrieval_page
    assert "function searchPlanRiskSignals" not in retrieval_query_analysis_plan_model
    assert "function searchPlanRiskSignals" in retrieval_query_analysis_plan_risk_model
    assert "function planRiskSignalsValue" in retrieval_query_analysis_plan_values_model
    assert "riskSignalListBadgeVariant" in retrieval_search_plan_risk_signals_panel
    assert "risk_signals" in retrieval_query_analysis_model
    assert "SearchAnswerCard" not in retrieval_search_results_panel
    assert "SearchAnswerCard" in retrieval_search_results_overview_section
    assert "./search-answer-card" in retrieval_search_results_overview_section
    assert "function SearchAnswerCard" not in retrieval_page
    assert "SearchAnswerHeader" in retrieval_search_answer
    assert "SearchAnswerMetrics" in retrieval_search_answer
    assert "SearchAnswerWarningPanel" in retrieval_search_answer
    assert "useSearchAnswerCardState" in retrieval_search_answer
    assert "function useSearchAnswerCardState" in retrieval_search_answer_card_state_hook
    assert "Search answer" in retrieval_search_answer_header
    assert "function SearchAnswerMetrics" in retrieval_search_answer_metrics
    assert "function SearchAnswerWarningPanel" in retrieval_search_answer_warning_panel
    assert "function formatSearchAnswerCount" in retrieval_search_answer_format
    assert "buildSearchAnswerViewModel" not in retrieval_search_answer
    assert "buildSearchAnswerViewModel" in retrieval_search_answer_card_state_hook
    assert "useCopyFeedback" not in retrieval_search_answer
    assert "useCopyFeedback" in retrieval_search_answer_card_state_hook
    assert "navigator.clipboard" not in retrieval_search_answer
    assert 'export * from "./search-answer-hints";' in retrieval_search_answer_model
    assert 'export * from "./search-answer-interpretation";' in retrieval_search_answer_model
    assert 'export * from "./search-answer-report";' in retrieval_search_answer_model
    assert 'export * from "./search-answer-status";' in retrieval_search_answer_model
    assert 'export * from "./search-answer-view-model";' in retrieval_search_answer_model
    assert "buildSearchAnswerViewModel" in retrieval_search_answer_view_model
    assert "searchAnswerReportFromPackage" in retrieval_search_answer_report_model
    assert "retrieval_search_answer" in retrieval_search_answer_report_model
    assert "searchAnswerFallbackRemediation" not in retrieval_search_answer_report_model
    assert "searchAnswerWarnings" not in retrieval_search_answer_report_model
    assert "function fallbackInterpretation" in retrieval_search_answer_interpretation_model
    assert "searchAnswerFallbackRemediation" in retrieval_search_answer_interpretation_model
    assert "searchAnswerWarnings" in retrieval_search_answer_interpretation_model
    assert "function searchHintsFromPackage" in retrieval_search_answer_hints_model
    assert "search_hints" in retrieval_search_answer_hints_model
    assert "searchAnswerStatus" in retrieval_search_answer_status_model
    assert "RetrievalReviewPathPanel" not in retrieval_search_results_panel
    assert "RetrievalReviewPathPanel" in retrieval_search_results_overview_section
    assert "./retrieval-review-path" in retrieval_search_results_overview_section
    assert "function RetrievalReviewPathPanel" not in retrieval_page
    assert "retrievalReviewGuidance" not in retrieval_page
    for split_file in RETRIEVAL_SPLIT_FILES:
        assert split_file.exists()
    assert "Review path" in retrieval_review_path
    assert "Guided retrieval review path" in retrieval_review_path
    assert "buildRetrievalReviewPath" in retrieval_review_path
    assert "RetrievalReviewPathCheckList" in retrieval_review_path
    assert "RetrievalReviewPathActionCard" in retrieval_review_path
    assert "./retrieval-review-path-check-list" in retrieval_review_path
    assert "./retrieval-review-path-action-card" in retrieval_review_path
    assert "function RetrievalReviewPathCheckCard" not in retrieval_review_path
    assert "function RetrievalReviewPathCheckList" in retrieval_review_path_check_list
    assert "RetrievalReviewPathCheckCard" in retrieval_review_path_check_list
    assert "function RetrievalReviewPathCheckCard" in retrieval_review_path_check_card
    assert "checkIcons" in retrieval_review_path_check_card
    assert "function RetrievalReviewPathActionCard" in retrieval_review_path_action_card
    assert "Next operator action" in retrieval_review_path_action_card
    assert "formatReviewPathCount" in retrieval_review_path_action_card
    assert "function reviewStatusBadgeVariant" in retrieval_review_path_format
    assert "function formatReviewPathCount" in retrieval_review_path_format
    assert 'export * from "./retrieval-review-checklist";' in retrieval_review_model
    assert 'export * from "./retrieval-review-guidance";' in retrieval_review_model
    assert 'export * from "./retrieval-review-path-builder";' in retrieval_review_model
    assert "buildRetrievalReviewPath" in retrieval_review_path_builder_model
    assert "retrievalReviewChecklist" in retrieval_review_checklist_model
    assert "retrievalReviewGuidance" in retrieval_review_guidance_model
    assert "retrievalPackageWarnings" in retrieval_review_warnings_model
    assert "Next operator action" in retrieval_review_path_action_card
    assert "A plain-language checklist built from backend retrieval quality" in retrieval_review_path
    assert "retrievalTasksValue" in retrieval_query_analysis_task_values_model
    assert "function retrievalTasksValue" not in retrieval_page
    assert "retrieval_tasks" not in retrieval_query_analysis_model
    assert "retrieval_tasks" in retrieval_query_analysis_stack_model
    assert "plan only" in retrieval_search_plan_route_decision_panel
    assert "SearchPlanPreviewNotices" in retrieval_search_plan_preview_content
    assert "SearchPlanPreviewNotices" in retrieval_search_plan_preview_summary_stack
    assert "Planning search" in retrieval_search_plan_preview_notices
    assert "Search plan unavailable" in retrieval_search_plan_preview_notices
    assert "Search running" in retrieval_search_plan_preview_notices
    assert 'request<RetrievalPlan>("/retrieval/plan"' in api_module
    assert "useRetrievalPlanQuery" in server_state
    plan_hook = server_state.split("export function useRetrievalPlanQuery", 1)[1].split(
        "export function useRetrievalJudgmentsQuery",
        1,
    )[0]
    assert "placeholderData" not in plan_hook
    assert "RetrievalPlan" in types_module
    assert "RetrievalPlanQuery" in types_module
    assert "RetrievalPlanCoverageSummary" in types_module
    assert "RetrievalPlanTaskSummary" in types_module
    assert "RetrievalPlanRiskSignal" in types_module
    assert "RetrievalSearchTask" in types_module
    assert "action_type" in types_module
    assert "POST /api/v1/retrieval/plan" in api_contract
    assert "plan-only retrieval response" in api_contract
    assert "retrieval_tasks" in api_contract
    assert "action_type" in api_contract
    assert "coverage_summary" in api_contract
    assert "task_summary" in api_contract
    assert '"runnable_local_count": 1' in api_contract
    assert '"external_open_count": 1' in api_contract
    assert '"target": "local_corpus"' in api_contract
    assert '"target": "external_medical_index"' in api_contract
    assert "next_action" in api_contract
    assert "risk_signals" in api_contract
    assert "search-plan preview" in frontend_architecture
    assert "execution tasks" in frontend_architecture
    assert "Execution-task rows should be actionable with target-aware behavior" in frontend_architecture
    assert "external medical-index tasks open their backend-provided follow-up URL" in frontend_architecture
    assert "copy-query action" in frontend_architecture
    assert "Supported filter suggestions in the same preview should also be actionable" in frontend_architecture
    assert "plan-only previews update visible controls without immediately running search" in frontend_architecture
    assert "inline confirmation near the active filter controls" in frontend_architecture
    assert "plan coverage summary" in frontend_architecture
    assert "RetrievalPlan.coverage_summary" in frontend_architecture
    assert "RetrievalPlan.task_summary" in frontend_architecture
    assert "plain-language run order" in frontend_architecture
    assert "What happens" in frontend_architecture
    assert "governed OJTFlow evidence searches" in frontend_architecture
    assert "required and optional task counts" in frontend_architecture
    assert "copy action for all queries in that group" in frontend_architecture
    assert "Task clipboard exports should use one" in frontend_architecture
    assert "coverage_summary.next_action" in frontend_architecture
    assert "RetrievalPlan.risk_signals" in frontend_architecture
    assert "QueryAnalysisBlock" in retrieval_trace_content
    assert "./query-analysis-block" in retrieval_trace_content
    assert "function QueryAnalysisBlock" not in retrieval_page
    assert "type QueryAnalysisBlockView" not in retrieval_query_analysis_block
    assert "type QueryAnalysisBlockView" in retrieval_query_analysis_block_types
    assert "./query-analysis-block-types" in retrieval_query_analysis_block
    assert "../components/query-analysis-block-types" in retrieval_trace_view_model
    assert "./query-analysis-block-types" in retrieval_trace_panel_types
    assert "Query analysis" in retrieval_query_analysis_header
    assert "QueryAnalysisHeader" in retrieval_query_analysis_block
    assert "QueryAnalysisTokenSections" in retrieval_query_analysis_block
    assert "Detected concepts" not in retrieval_query_analysis_block
    assert "Detected concepts" in retrieval_query_analysis_token_sections
    assert "Standard cues" in retrieval_query_analysis_token_sections
    assert "Expanded terms" in retrieval_query_analysis_token_sections
    assert "QueryAnalysisCounter" not in retrieval_query_analysis_block
    assert "QueryAnalysisCounter" in retrieval_query_analysis_header
    assert "function QueryAnalysisHeader" in retrieval_query_analysis_header
    assert "function QueryAnalysisCounter" in retrieval_query_analysis_counter
    assert "queryAnalysisBlockView" in retrieval_trace_view_model
    assert "QueryProfileCard" in retrieval_query_analysis_block
    assert "./query-profile-card" in retrieval_query_analysis_block
    assert "function QueryProfileCard" not in retrieval_page
    assert "Query profile" in retrieval_query_profile_card
    assert "QueryProfileFilterActions" in retrieval_query_profile_card
    assert "QueryProfileRuleList" in retrieval_query_profile_card
    assert "type QueryProfileCardView" in retrieval_query_profile_card_types
    assert "Suggested by query profile" in retrieval_query_profile_filter_actions
    assert "ruleId" in retrieval_query_profile_rule_list
    assert 'export * from "./retrieval-query-analysis-profile-value";' in retrieval_query_analysis_profile_values_model
    assert 'export * from "./retrieval-query-analysis-aspect-values";' in retrieval_query_analysis_profile_values_model
    assert 'export * from "./retrieval-query-analysis-concept-values";' in retrieval_query_analysis_profile_values_model
    assert 'export * from "./retrieval-query-analysis-filter-values";' in retrieval_query_analysis_profile_values_model
    assert 'export * from "./retrieval-query-analysis-diagnostic-values";' in retrieval_query_analysis_profile_values_model
    assert 'export * from "./retrieval-query-analysis-hint-values";' in retrieval_query_analysis_profile_values_model
    assert "function queryProfileValue" in retrieval_query_analysis_profile_value_model
    assert "function queryProfileValue" not in retrieval_page
    assert "query_profile" not in retrieval_query_analysis_model
    assert "query_profile" in retrieval_query_analysis_stack_model
    assert "QueryAspectPlan" in retrieval_query_analysis_block
    assert "function queryAspectsValue" in retrieval_query_analysis_aspect_values_model
    assert "function filterSuggestionsValue" in retrieval_query_analysis_filter_values_model
    assert "query_aspects" not in retrieval_query_analysis_model
    assert "query_aspects" in retrieval_query_analysis_stack_model
    assert "./query-aspect-plan" in retrieval_query_analysis_block
    assert "function QueryAspectPlan" not in retrieval_page
    assert "Search aspect plan" in retrieval_query_aspect_plan
    assert "QueryAspectPlanCard" in retrieval_query_aspect_plan
    assert "function QueryAspectPlanCard" in retrieval_query_aspect_plan_card
    assert "QueryAspectFilterControls" in retrieval_query_aspect_plan_card
    assert "QueryAspectFilterBadges" in retrieval_query_aspect_plan_card
    assert "function QueryAspectFilterControls" in retrieval_query_aspect_filter_controls
    assert "QueryAspectFilterAction" in retrieval_query_aspect_filter_controls
    assert "function QueryAspectFilterBadges" in retrieval_query_aspect_filter_badges
    assert "unsupported {humanize(entry.field)}" in retrieval_query_aspect_filter_action
    assert "type QueryAspectPlanItemView" in retrieval_query_aspect_plan_types
    assert "ConceptCandidateList" in retrieval_query_analysis_block
    assert "./concept-candidate-list" in retrieval_query_analysis_block
    assert "function ConceptCandidateList" not in retrieval_page
    assert "Concept candidates" in retrieval_concept_candidate_list
    assert "function conceptCandidatesValue" in retrieval_query_analysis_concept_values_model
    assert "function conceptCandidatesValue" not in retrieval_page
    assert "concept_candidates" not in retrieval_query_analysis_model
    assert "concept_candidates" in retrieval_query_analysis_stack_model
    assert "function queryDiagnosticsValue" in retrieval_query_analysis_diagnostic_values_model
    assert "function searchHintsValue" in retrieval_query_analysis_hint_values_model
    assert "QueryDiagnosticList" in retrieval_query_analysis_block
    assert "./query-diagnostic-list" in retrieval_query_analysis_block
    assert "function QueryDiagnosticList" not in retrieval_page
    assert "Query diagnostics explain parser" in retrieval_query_diagnostic_list
    assert "QueryDiagnosticRow" in retrieval_query_diagnostic_list
    assert "function QueryDiagnosticRow" in retrieval_query_diagnostic_row
    assert "function queryDiagnosticMetadataChips" in retrieval_query_diagnostic_metadata
    assert "active_metadata_filters" in retrieval_query_diagnostic_metadata
    assert "suggested_standards" in retrieval_query_diagnostic_metadata
    assert "type QueryDiagnosticListItem" in retrieval_query_diagnostic_types
    assert "SearchHintList" in retrieval_query_analysis_block
    assert "./search-hint-list" in retrieval_query_analysis_block
    assert "function SearchHintList" not in retrieval_page
    assert "SearchHintCard" in retrieval_search_hint_list
    assert "./search-hint-card" in retrieval_search_hint_list
    assert "SearchHintMetadata" in retrieval_search_hint_card
    assert "Route details" in retrieval_search_hint_metadata_summary
    assert "SearchHintMetadataSummary" in retrieval_search_hint_metadata_details
    assert "SearchHintMetadataSectionList" in retrieval_search_hint_metadata_details
    assert "formatSearchHintMetadataCount" in retrieval_search_hint_metadata_summary
    assert "function formatSearchHintMetadataCount" in retrieval_search_hint_metadata_format
    assert "SearchHintEndpointScopeSection" in retrieval_search_hint_metadata_section_list
    assert "SearchHintParameterExamplesSection" in retrieval_search_hint_metadata_section_list
    assert "SearchHintLineageFollowupSection" in retrieval_search_hint_metadata_section_list
    assert "SearchHintSelectedCandidatesSection" in retrieval_search_hint_metadata_section_list
    assert "Parameter examples" in retrieval_search_hint_parameter_examples_section
    assert "Lineage follow-up" in retrieval_search_hint_lineage_followup_section
    assert "Endpoint scope" in retrieval_search_hint_endpoint_scope_section
    assert "variant=\"success\"" in retrieval_search_hint_selected_candidates_section
    assert "Selected terminology terms" in retrieval_search_hint_metadata
    assert "Selected unit candidates" in retrieval_search_hint_metadata
    assert "selected_terms" in retrieval_search_hint_metadata
    assert "selected_unit_candidates" in retrieval_search_hint_metadata
    assert "capability_warning" in retrieval_search_hint_metadata
    assert "function searchHintParameterExamples" not in retrieval_search_hint_metadata
    assert "function searchHintParameterExamples" in retrieval_search_hint_metadata_values
    assert "function searchHintLineageFollowup" not in retrieval_search_hint_metadata
    assert "function searchHintLineageFollowup" in retrieval_search_hint_metadata_values
    assert "function optionalStringValue" not in retrieval_search_hint_metadata
    assert "function optionalStringValue" in retrieval_search_hint_metadata_values
    assert "metadata?: Record<string, unknown>" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "<RunComparisonQueryAspects" not in retrieval_search_run_comparison_panel
    assert "RunComparisonQueryAspects" in retrieval_search_run_comparison_detail_section
    assert "./run-comparison-detail-panels" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonQueryAspects" not in retrieval_page
    assert 'export * from "./run-comparison-query-aspects";' in retrieval_run_comparison_query_detail_panels
    assert 'export * from "./run-comparison-query-profile";' in retrieval_run_comparison_query_detail_panels
    assert 'export * from "./run-comparison-concept-grounding";' in retrieval_run_comparison_query_detail_panels
    assert "Search aspects" in retrieval_run_comparison_query_aspects
    assert "queryAspectComparisonBetweenRuns" not in retrieval_page
    assert 'export * from "./retrieval-run-comparison-concepts";' in retrieval_run_comparison_dimensions_model
    assert 'export * from "./retrieval-run-comparison-coverage";' in retrieval_run_comparison_dimensions_model
    assert 'export * from "./retrieval-run-comparison-facets";' in retrieval_run_comparison_dimensions_model
    assert 'export * from "./retrieval-run-comparison-profiles";' in retrieval_run_comparison_dimensions_model
    assert 'export * from "./retrieval-run-comparison-quality-signals";' in retrieval_run_comparison_dimensions_model
    assert "queryAspectComparisonBetweenRuns" in retrieval_run_comparison_concepts_model
    assert "queryAspectComparison" in retrieval_run_comparison_builder_model
    assert "Search aspects" in retrieval_search_plan_aspect_preview
    assert 'export * from "./retrieval-filter-active";' in retrieval_filter_model
    assert 'export * from "./retrieval-filter-format";' in retrieval_filter_model
    assert 'export * from "./retrieval-filter-suggestions";' in retrieval_filter_model
    assert 'export * from "./retrieval-filter-types";' in retrieval_filter_model
    assert "queryAspectFilterEntries" in retrieval_filter_suggestions_model
    assert "filterEntries: queryAspectFilterEntries(aspect, appliedFilters)" in retrieval_trace_view_model
    assert "Suggested by search aspect" in retrieval_query_aspect_filter_action
    assert (
        "entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`"
        in retrieval_query_aspect_filter_action
    )
    assert "<RunComparisonCoverage" not in retrieval_search_run_comparison_panel
    assert "RunComparisonCoverage" in retrieval_search_run_comparison_detail_section
    assert "RunComparisonCoverage" in retrieval_run_comparison_quality_detail_panels
    assert "function RunComparisonCoverage" not in retrieval_page
    assert "Coverage diagnostics" in retrieval_run_comparison_coverage_panel
    assert "CoverageStatusChangeList" in retrieval_run_comparison_coverage_panel
    assert "CoverageSummaryList" in retrieval_run_comparison_coverage_panel
    assert "function CoverageStatusChangeList" not in retrieval_run_comparison_coverage_panel
    assert "function CoverageStatusChangeList" in retrieval_run_comparison_coverage_status_list
    assert "function CoverageSummaryList" in retrieval_run_comparison_coverage_summary_list
    assert "function coverageComparisonKey" in retrieval_run_comparison_coverage_key
    assert "humanize(change.baseline.status)" in retrieval_run_comparison_coverage_status_list
    assert "humanize(item.status)" in retrieval_run_comparison_coverage_summary_list
    assert "coverageComparisonBetweenRuns" not in retrieval_page
    assert "coverageComparisonBetweenRuns" in retrieval_run_comparison_coverage_model
    assert "coverageComparison" in retrieval_run_comparison_builder_model
    assert (
        "coverage_diagnostics_changed"
        in retrieval_comparison_diagnosis_quality_rules_model
    )
    assert "QueryAspectMatchExplanation" in retrieval_hit_card_score_section
    assert "queryAspectMatchesFromHit" not in retrieval_page
    assert "function queryAspectMatchesFromHit" in retrieval_evidence_signal_extraction_model
    assert "function QueryAspectMatchExplanation" not in retrieval_page
    assert "./hit-query-aspect-support" in retrieval_hit_explanation_panels
    assert "Aspect support" in retrieval_hit_query_aspect_support
    assert "ConceptMatchExplanation" in retrieval_hit_card_score_section
    assert "conceptMatchesFromHit" not in retrieval_page
    assert "function conceptMatchesFromHit" in retrieval_evidence_signal_extraction_model
    assert "function ConceptMatchExplanation" not in retrieval_page
    assert "./hit-concept-grounding" in retrieval_hit_explanation_panels
    assert "Concept grounding" in retrieval_hit_concept_grounding
    assert "concept_grounding_requirements" in retrieval_runtime_quality_policy_model
    assert "HitCardEvidenceSection" in retrieval_hit_card
    assert "./hit-card-evidence-section" in retrieval_hit_card
    assert "HitEvidenceAuditStrip" in retrieval_hit_card_evidence_section
    assert "./hit-evidence-audit-strip" in retrieval_hit_card_evidence_section
    assert "function HitEvidenceAuditStrip" not in retrieval_page
    assert "Evidence support summary" in retrieval_hit_evidence_audit_strip
    assert "EvidenceSupportSummary" in retrieval_evidence_implementation
    assert "function evidenceSupportSummary(" not in retrieval_page
    assert "support_summary: supportSummary" in retrieval_evidence_implementation
    assert "EvidenceSupportMatrixCard" in retrieval_evidence_support_matrix
    assert "./evidence-support-matrix-card" in retrieval_evidence_support_matrix
    assert "function EvidenceSupportMatrixCard" not in retrieval_evidence_support_matrix
    assert "EvidenceSupportMatrixCardHeader" in retrieval_evidence_support_matrix_card
    assert "function EvidenceSupportMatrixCardHeader" in retrieval_evidence_support_matrix_card_header
    assert "EvidenceSupportSignalBadges" in retrieval_evidence_support_matrix_card
    assert "EvidenceSupportMatrixTableRow" in retrieval_evidence_support_matrix_table
    assert "EvidenceSupportSignalBadges" in retrieval_evidence_support_matrix_table_row
    assert "./evidence-support-signal-badges" in retrieval_evidence_support_matrix_table_row
    assert "function EvidenceSupportSignalBadges" in retrieval_evidence_support_signal_badges
    assert "function EvidenceSupportMobileField" in retrieval_evidence_support_mobile_field
    assert "EvidenceSupportMobileField" not in retrieval_evidence_support_matrix
    assert "md:hidden" in retrieval_evidence_support_matrix
    assert (
        "hidden overflow-auto rounded-md border border-border bg-card md:block"
        in retrieval_evidence_support_matrix_table
    )
    assert "EvidenceUseGuidancePanel" in retrieval_hit_card_evidence_section
    assert "./evidence-interpretation-guidance" in retrieval_hit_card_evidence_section
    assert "function EvidenceUseGuidancePanel" not in retrieval_page
    assert "function EvidenceUsabilitySummaryPanel" not in retrieval_page
    assert "function HitMatchExplanationPanel" not in retrieval_page
    assert "function EvidenceUseGuidancePanel" not in retrieval_evidence_interpretation_guidance
    assert "Evidence interpretation guidance" in retrieval_evidence_use_guidance_panel
    assert "Evidence interpretation help" in retrieval_evidence_use_guidance_panel
    assert "EvidenceUsabilitySummaryPanel" in retrieval_hit_card_evidence_section
    assert "function EvidenceUsabilitySummaryPanel" not in retrieval_evidence_interpretation_guidance
    assert "Evidence usability summary" in retrieval_evidence_usability_summary_panel
    assert "Usability summary" in retrieval_evidence_usability_summary_panel
    assert "evidenceUsabilitySummary" not in retrieval_hit_card
    assert "evidenceUsabilitySummary" not in retrieval_hit_card_evidence_section
    assert "evidenceUsabilitySummary" in retrieval_hit_card_view_model
    assert "hitCardViewModel" in retrieval_hit_card
    assert "function hitCardViewModel" in retrieval_hit_card_view_model
    assert "function evidenceUsabilitySummary" not in retrieval_page
    assert "usability_summary: usabilitySummary" in retrieval_evidence_implementation
    assert "evidenceUseGuidance" in retrieval_hit_card_evidence_section
    assert "function evidenceUseGuidance" not in retrieval_page
    assert "evidenceUseGuidanceReasons" not in retrieval_page
    assert "function evidenceUseGuidanceReasons" in retrieval_evidence_implementation
    assert "Use with provenance check" in retrieval_evidence_implementation
    assert "Review before relying on it" in retrieval_evidence_implementation
    assert "Weak evidence support" in retrieval_evidence_implementation
    assert "missing medical grounding" in retrieval_evidence_implementation
    assert "judged ${judgmentLabel(judgment.value)}" in retrieval_evidence_implementation
    assert "matched_term_count" in retrieval_evidence_implementation
    assert "ranking_signal_count" in retrieval_evidence_implementation
    assert "EvidenceProvenanceSummary" in retrieval_hit_card_evidence_section
    assert "./evidence-provenance-snippet" in retrieval_hit_card_evidence_section
    assert "function EvidenceProvenanceSummary" not in retrieval_page
    assert "function SnippetBlock" not in retrieval_page
    assert "Evidence provenance" in retrieval_evidence_provenance_summary
    assert "Best snippet" in retrieval_snippet_block
    assert "HighlightedText" in retrieval_highlighted_text
    assert "HighlightedText" in retrieval_snippet_block
    assert "matched terms" in retrieval_evidence_highlight_utils
    assert "chars {snippet.start_char}-{snippet.end_char}" in retrieval_snippet_block
    assert "uniqueMatchedTerms" in retrieval_evidence_highlight_utils
    assert 'export { SnippetBlock } from "./snippet-block";' in retrieval_evidence_provenance_snippet
    assert "provenanceEntriesFromEvidence" not in retrieval_page
    assert "function provenanceEntriesFromEvidence" not in retrieval_page
    assert "function provenanceEntriesFromEvidence" in retrieval_evidence_implementation
    assert "provenanceHrefForLocator" not in retrieval_page
    assert "function provenanceHrefForLocator" in retrieval_evidence_implementation
    assert "https://pubmed.ncbi.nlm.nih.gov" in retrieval_evidence_implementation
    assert "https://doi.org" in retrieval_evidence_implementation
    assert "Copy evidence" in retrieval_hit_card_header
    assert "HitCardHeader" in retrieval_hit_card
    assert "function HitCardHeader" in retrieval_hit_card_header
    assert "Copy evidence JSON" in retrieval_hit_card_header
    assert "Evidence JSON report help" in retrieval_hit_card_header
    assert "useHitCardCopyReport" in retrieval_hit_card
    assert "useCopyFeedback" in retrieval_hit_card_copy_hook
    assert "markCopied" in retrieval_hit_card_copy_hook
    assert "Copied" in retrieval_hit_card_header
    assert "evidenceReportFromHit(" not in retrieval_hit_card
    assert "evidenceReportFromHit(" not in retrieval_hit_card_copy_hook
    assert "evidenceReportFromHit" not in retrieval_hit_card_view_model
    assert "evidenceReportFromHit" in retrieval_hit_card_report_model
    assert "evidenceReportFromHitCardView" in retrieval_hit_card_copy_hook
    assert "../model/hit-card-report" in retrieval_hit_card_copy_hook
    assert "function evidenceReportFromHitCardView" in retrieval_hit_card_report_model
    assert "function evidenceReportFromHit" not in retrieval_page
    assert "retrieval_evidence_hit" in retrieval_evidence_implementation
    assert "<RunComparisonConceptGrounding" not in retrieval_search_run_comparison_panel
    assert "RunComparisonConceptGrounding" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonConceptGrounding" not in retrieval_page
    assert "Concept grounding" in retrieval_run_comparison_concept_grounding
    assert "conceptGroundingComparisonBetweenRuns" not in retrieval_page
    assert "conceptGroundingComparisonBetweenRuns" in retrieval_run_comparison_concepts_model
    assert "conceptGroundingComparison" in retrieval_run_comparison_builder_model
    assert (
        "concept_grounding_changed"
        in retrieval_comparison_diagnosis_profile_rules_model
    )
    assert "serverSearchSignatureFromPackage" in retrieval_run_session_record_hook
    assert "function serverSearchSignatureFromPackage" not in retrieval_page
    assert "function serverSearchSignatureFromPackage" in retrieval_run_summary_model
    assert "Search signature" in retrieval_trace_view_model
    assert "search_signature: summary.serverSignature" in retrieval_comparison_report_run_sections_model
    assert "qualityPolicyFromPackage" in retrieval_trace_view_model
    assert "function qualityPolicyFromPackage" not in retrieval_page
    assert "qualityPolicyFromPackage" in retrieval_runtime_stack_model
    assert "function qualityPolicyFromPackage" in retrieval_runtime_quality_policy_model
    assert "function qualityPolicyFromPackage" not in retrieval_page
    assert "function qualityPolicyFromPackage" in retrieval_runtime_quality_policy_model
    assert "Quality policy" in retrieval_trace_view_model
    assert "query_profiles" in retrieval_comparison_report_model
    assert 'export * from "./retrieval-run-concept-grounding";' in retrieval_run_dimensions_model
    assert 'export * from "./retrieval-run-coverage";' in retrieval_run_dimensions_model
    assert 'export * from "./retrieval-run-query-aspects";' in retrieval_run_dimensions_model
    assert 'export * from "./retrieval-run-query-profile";' in retrieval_run_dimensions_model
    assert "function queryProfileSummaryFromPackage" in retrieval_run_query_profile_model
    assert "function coverageSummariesFromPackage" in retrieval_run_coverage_model
    assert "function queryAspectSummariesFromPackage" in retrieval_run_query_aspects_model
    assert "function conceptGroundingSummariesFromPackage" in retrieval_run_concept_grounding_model
    assert "function conceptGroundingKey" in retrieval_run_concept_grounding_model
    assert "queryProfile: queryProfileSummaryFromPackage(packageData)" in retrieval_run_summary_model
    assert "function queryProfileSummaryFromPackage" not in retrieval_page
    assert "SearchRunHistoryPanel" in retrieval_query_column
    assert "./search-run-history-panel" in retrieval_query_column
    assert "components/search-run-history-panel" not in retrieval_page
    assert "SearchRunHistory" in retrieval_search_run_history_panel
    assert "./search-run-history" in retrieval_search_run_history_panel
    assert "function SearchRunHistory" not in retrieval_page
    assert "SearchRunHistoryRow" in retrieval_search_run_history
    assert "./search-run-history-row" in retrieval_search_run_history
    assert "Profile: {run.summary.queryProfile.label}" not in retrieval_search_run_history
    assert "Profile: {run.summary.queryProfile.label}" not in retrieval_search_run_history_row
    assert "Profile: {run.summary.queryProfile.label}" in retrieval_search_run_history_row_details
    assert "SearchRunEvidenceSummary" in retrieval_search_run_history_row
    assert "./search-run-evidence-summary" in retrieval_search_run_history_row
    assert "SearchRunHistoryRowSummary" in retrieval_search_run_history_row
    assert "./search-run-history-row-summary" in retrieval_search_run_history_row
    assert "SearchRunHistoryMetadataBadges" in retrieval_search_run_history_row_summary
    assert "SearchRunHistoryDetailLines" in retrieval_search_run_history_row_summary
    assert "SearchRunHistoryRowActions" in retrieval_search_run_history_row
    assert "./search-run-history-row-actions" in retrieval_search_run_history_row
    assert "formatShortSignature" not in retrieval_search_run_history_row
    assert "formatShortSignature" in retrieval_search_run_history_row_badges
    assert "function formatShortSignature" in retrieval_search_run_history_format
    assert "CorrectiveActionTypeCountChips" in retrieval_search_run_history_row_badges
    assert "Top source:" in retrieval_search_run_history_row_details
    assert "Top action:" in retrieval_search_run_history_row_details
    assert "Set baseline" not in retrieval_search_run_history_row
    assert "Set baseline" in retrieval_search_run_history_row_actions
    assert "GitCompareArrows" in retrieval_search_run_history_row_actions
    assert "SearchRunHistoryProps" in retrieval_search_run_history_types
    assert "function SearchRunEvidenceSummary" not in retrieval_page
    assert "searchRunRemediationSummary" in retrieval_search_run_remediation_model
    assert "searchRunScopeLabels" in retrieval_search_run_labels_model
    assert "Run scope" in retrieval_search_run_evidence_summary
    assert "Run remediation:" in retrieval_search_run_evidence_summary
    assert "coverageGapSummaryBadgeView" in retrieval_search_run_evidence_summary
    assert "groundedConceptSummaryBadgeView" in retrieval_search_run_evidence_summary
    assert "searchAspectSummaryBadgeView" in retrieval_search_run_evidence_summary
    assert "coverage gap" not in retrieval_search_run_evidence_summary
    assert "coverage gap" in retrieval_search_run_evidence_summary_view
    assert "grounded concept" not in retrieval_search_run_evidence_summary
    assert "grounded concept" in retrieval_search_run_evidence_summary_view
    assert "search aspect" not in retrieval_search_run_evidence_summary
    assert "search aspect" in retrieval_search_run_evidence_summary_view
    assert "SearchAnswerCard" in retrieval_search_results_overview_section
    assert "Search answer" in retrieval_search_answer_header
    assert "EvidenceInterpretationPanel" not in retrieval_search_results_panel
    assert "EvidenceInterpretationPanel" in retrieval_search_results_overview_section
    assert "./evidence-interpretation-panel" in retrieval_search_results_overview_section
    assert "function EvidenceInterpretationPanel" not in retrieval_page
    assert "Evidence interpretation" in retrieval_evidence_interpretation
    assert "EvidenceInterpretationCard" in retrieval_evidence_interpretation
    assert "./evidence-interpretation-card" in retrieval_evidence_interpretation
    assert "function EvidenceInterpretationCard" in retrieval_evidence_interpretation_card
    assert "function InterpretationCard" not in retrieval_evidence_interpretation
    assert "card.items.map" not in retrieval_evidence_interpretation
    assert "card.items.map" in retrieval_evidence_interpretation_card
    assert 'export * from "./evidence-interpretation-status";' in retrieval_evidence_interpretation_model
    assert 'export * from "./evidence-interpretation-values";' in retrieval_evidence_interpretation_model
    assert 'export * from "./evidence-interpretation-cards";' in retrieval_evidence_interpretation_model
    assert 'export * from "./evidence-interpretation-view-model";' in retrieval_evidence_interpretation_model
    assert "Why the top result matched" not in retrieval_evidence_interpretation_view_model
    assert "Why the top result matched" not in retrieval_evidence_interpretation_cards_model
    assert "Why the top result matched" in retrieval_evidence_interpretation_top_match_card_model
    assert "No required bucket policy" in retrieval_evidence_interpretation_coverage_card_model
    assert "Review evidence" in retrieval_evidence_interpretation_next_action_card_model
    assert "topMatchInterpretationCard" in retrieval_evidence_interpretation_cards_model
    assert "coverageInterpretationCard" in retrieval_evidence_interpretation_cards_model
    assert "nextActionInterpretationCard" in retrieval_evidence_interpretation_cards_model
    assert "function evidenceInterpretationCards" in retrieval_evidence_interpretation_cards_model
    assert "buildEvidenceInterpretationViewModel" in retrieval_evidence_interpretation
    assert "buildEvidenceInterpretationViewModel" in retrieval_evidence_interpretation_view_model
    assert "InterpretationCard" in retrieval_evidence_interpretation
    assert "packageData.interpretation" in retrieval_evidence_interpretation_view_model
    assert "evidenceSupportBadgeVariant" in retrieval_evidence_interpretation_status_model
    assert "supportStatusValue" in retrieval_evidence_interpretation_values_model
    assert "RetrievalInterpretation" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "StandardSearchPlanPanel" not in retrieval_search_cockpit
    assert "StandardSearchPlanPanel" in retrieval_search_cockpit_section_stack
    assert "./strategy-standard-panels" not in retrieval_search_cockpit
    assert "./strategy-standard-panels" in retrieval_search_cockpit_section_stack
    assert "function StandardSearchPlanPanel" not in retrieval_page
    assert "StandardSearchPlanPanel" in retrieval_strategy_standard_panels
    assert "StandardSearchPlanHeader" in retrieval_standard_search_plan_panel
    assert "StandardSearchStepCard" in retrieval_standard_search_plan_panel
    assert "StandardSearchPlanGuardrails" in retrieval_standard_search_plan_panel
    assert "Healthcare search plan" in retrieval_standard_search_plan_header
    assert (
        "Backend-selected playbook for the next standards-aware search"
        in retrieval_standard_search_plan_header
    )
    assert "StandardSearchMatchReasons" in retrieval_standard_search_step_card
    assert "StandardSearchGovernanceNotes" in retrieval_standard_search_step_card
    assert "Matched by" in retrieval_standard_search_match_reasons
    assert "Governance guardrails" in retrieval_standard_search_governance_notes
    assert "matched_fields" in retrieval_strategy_standard_format
    assert "matched_query_aspects" in retrieval_strategy_standard_format
    assert "retrievalStandardSearchPlanReport" not in retrieval_page
    assert "function retrievalStandardSearchPlanReport" not in retrieval_page
    assert "function retrievalStandardSearchPlanReport" not in retrieval_report_plan_model
    assert "function retrievalStandardSearchPlanReport" in retrieval_report_standard_plan_model
    assert "retrievalStandardSearchPlanReport" in retrieval_report_plan_model
    assert "retrieval-report-standard-plan" in retrieval_report_model
    assert "retrieval-report-standard-plan" in retrieval_report_cockpit_model
    assert "retrieval-report-plan" not in retrieval_report_cockpit_model
    assert "standard_search_plan" in retrieval_report_plan_model
    assert "standard_search_plan" in retrieval_report_standard_plan_model
    assert "RetrievalStandardSearchPlan" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "searchAnswerReportFromPackage" in retrieval_search_answer_report_model
    assert "retrieval_search_answer" in retrieval_search_answer_report_model
    assert "medical_search_hints" in retrieval_search_answer_report_model
    assert "searchHintsFromPackage" in retrieval_search_answer_hints_model
    assert "searchAnswerWarnings" in retrieval_search_answer_warnings_model
    assert "route_details" in retrieval_report_medical_hints_model
    assert "retrievalDiversityReport" not in retrieval_page
    assert "function retrievalDiversityReport" not in retrieval_page
    assert "function retrievalDiversityReport" in retrieval_report_diversity_model
    assert "diversity: retrievalDiversityReport(packageData)" not in retrieval_page
    assert "diversity: retrievalDiversityReport(packageData)" in retrieval_report_cockpit_readiness_model
    assert "retrievalInterpretationReport" not in retrieval_page
    assert "function retrievalInterpretationReport" not in retrieval_page
    assert "function retrievalInterpretationReport" in retrieval_report_interpretation_model
    assert "Copy answer JSON" in retrieval_search_answer_header
    assert "This is an evidence retrieval summary for workflow operations" in retrieval_search_answer_header
    assert "it is not clinical advice" in retrieval_inline_guide
    assert "remediationSummary: string | null" in retrieval_run_summary_types_model
    assert "remediationSummary: string | null" not in retrieval_page
    assert "packageData.remediation_summary" in retrieval_run_summary_model
    assert "handoff_context.remediation_summary" in retrieval_run_summary_model
    assert "handoff_context.remediation_summary" not in retrieval_page
    assert "Top action" in retrieval_search_run_history_row_details
    assert (
        "qualitySummary: packageData.quality_summary ?? null"
        in retrieval_search_results_overview_section
    )
    assert "qualitySummaryFingerprint" not in retrieval_page
    assert "qualitySummaryFingerprint" not in retrieval_run_comparison_model
    assert "qualitySummaryFingerprint" in retrieval_run_comparison_quality_summary_model
    assert "function qualitySummaryFingerprint" not in retrieval_page
    assert "function qualitySummaryFingerprint" not in retrieval_run_summary_model
    assert "function qualitySummaryFingerprint" in retrieval_run_quality_summary_model
    assert "function qualityWarningCount" in retrieval_run_quality_summary_model
    assert "./retrieval-run-quality-summary" in retrieval_run_summary_model
    assert (
        "qualitySummaryComparisonBetweenRuns"
        in retrieval_run_comparison_quality_summary_model
    )
    assert "qualitySummaryChanged" in retrieval_run_comparison_builder_model
    assert "quality_score: comparison.qualityScoreDelta" in retrieval_comparison_report_deltas_model
    assert "searchRunQualityBadgeVariant" in retrieval_search_run_quality_model
    assert "<RunComparisonQueryProfile" not in retrieval_search_run_comparison_panel
    assert "RunComparisonQueryProfile" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonQueryProfile" not in retrieval_page
    assert "QueryProfileSummaryCard" in retrieval_run_comparison_query_profile
    assert "<RunComparisonQualitySignals" not in retrieval_search_run_comparison_panel
    assert "RunComparisonQualitySignals" in retrieval_search_run_comparison_detail_section
    assert "RunComparisonQualitySignals" in retrieval_run_comparison_quality_detail_panels
    assert "function RunComparisonQualitySignals" not in retrieval_page
    assert "QualitySignalChangeList" in retrieval_run_comparison_quality_signals_panel
    assert "qualitySignalComparisonBetweenRuns" not in retrieval_page
    assert "qualitySignalComparisonBetweenRuns" in retrieval_run_comparison_quality_signals_model
    assert "qualitySignalSummariesFromRun" not in retrieval_page
    assert "qualitySignalSummariesFromRun" in retrieval_run_comparison_quality_signals_model
    assert "qualitySignalComparison" in retrieval_run_comparison_builder_model
    assert "Quality signals" in retrieval_run_comparison_quality_signals_panel
    assert "<RunComparisonFacetCoverage" not in retrieval_search_run_comparison_panel
    assert "RunComparisonFacetCoverage" in retrieval_search_run_comparison_detail_section
    assert "RunComparisonFacetCoverage" in retrieval_run_comparison_quality_detail_panels
    assert "function RunComparisonFacetCoverage" not in retrieval_page
    assert "FacetValueChange" in retrieval_run_comparison_facet_coverage_panel
    assert "facetComparisonsBetweenRuns" not in retrieval_page
    assert "facetComparisonsBetweenRuns" in retrieval_run_comparison_facets_model
    assert "facetValuesFromRun" not in retrieval_page
    assert "facetValuesFromRun" in retrieval_run_comparison_facets_model
    assert "facetComparisons" in retrieval_run_comparison_builder_model
    assert "Facet coverage" in retrieval_run_comparison_facet_coverage_panel
    assert "queryProfilesChanged" not in retrieval_page
    assert "queryProfilesChanged" in retrieval_run_comparison_profiles_model
    assert "queryProfileChanged" in retrieval_run_comparison_builder_model
    assert "profile changed" not in retrieval_search_run_comparison_header
    assert "profile changed" in retrieval_search_run_comparison_status_badges
    assert "retrievalMode" in retrieval_summary_model
    assert "suggestedFilters" in retrieval_filter_suggestions_model
    assert "queryProfileFilterEntries" in retrieval_filter_suggestions_model
    assert "function queryProfileFilterEntries" in retrieval_filter_suggestions_model
    assert "function queryAspectFilterEntries" in retrieval_filter_suggestions_model
    assert "filterEntrySuggestions" in retrieval_filter_suggestions_model
    assert "function suggestedFilterEntries" in retrieval_filter_entry_suggestions_model
    assert "function appliedFilterMatches" not in retrieval_filter_suggestions_model
    assert "function appliedFilterMatches" in retrieval_filter_entry_suggestions_model
    assert "formatFilterValue" not in retrieval_filter_suggestions_model
    assert "formatFilterValue" in retrieval_filter_entry_suggestions_model
    assert "function appliedFilterMatches" not in retrieval_page
    assert "queryAnalysisBlockView(queryAnalysis, trace.filters_applied)" in retrieval_trace_view_model
    assert "entry.applied" in retrieval_query_aspect_filter_action
    assert "entry.applied" in retrieval_query_profile_filter_actions
    assert (
        "entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`"
        in retrieval_query_profile_filter_actions
    )
    assert "RuntimeRerankBadge" in retrieval_search_results_header
    assert "RuntimeDiversityBadge" in retrieval_search_results_header
    assert "RetrievalRuntimeStatusStrip" in retrieval_results_column
    assert "./retrieval-runtime-status" in retrieval_results_column
    assert "components/retrieval-runtime-status" not in retrieval_page
    assert "function RerankBadge" not in retrieval_page
    assert "function DiversityBadge" not in retrieval_page
    assert "function RetrievalRuntimeStatusStrip" not in retrieval_page
    assert "RetrievalRuntimeStatusStrip" in retrieval_runtime_status
    assert "Retrieval runtime status" in retrieval_runtime_status_strip
    assert "RuntimeStatusFact" in retrieval_runtime_status_strip
    assert "function RuntimeStatusFact" in retrieval_runtime_status_fact
    assert "function graphStatusSupporting" in retrieval_runtime_graph_status
    assert "run search to prepare graph context" in retrieval_runtime_graph_status
    assert "Retrieval mode" in retrieval_runtime_status_strip
    assert "first stage only" in retrieval_runtime_status_strip
    assert "score order" in retrieval_runtime_status_strip
    assert "GraphPanel" in retrieval_results_column
    assert "function GraphPanel" not in retrieval_page
    assert "GraphPanel" in retrieval_runtime_status
    assert "Graph handoff" in retrieval_graph_handoff_panel
    assert "Index integrity" in retrieval_integrity_panel_header
    assert "Source checks" in retrieval_integrity_source_checks
    assert "Integrity warnings" in retrieval_integrity_warnings
    assert "IntegritySummaryMetrics" in retrieval_integrity_panel
    assert "IntegrityPanel" in retrieval_runtime_status
    assert "IntegrityPanel" in retrieval_results_column
    assert "function IntegrityPanel" not in retrieval_page
    assert "useRetrievalIntegritySession" not in retrieval_page
    assert "useRetrievalIntegritySession" in retrieval_page_controller_hook
    assert "use-retrieval-integrity-session" in retrieval_page_controller_hook
    assert "function useRetrievalIntegritySession" in retrieval_integrity_session_hook
    assert "useRetrievalIntegrityQuery" not in retrieval_page
    assert "useRetrievalReindexMutation" not in retrieval_page
    assert "useRetrievalIntegrityQuery" in retrieval_integrity_session_hook
    assert "useRetrievalReindexMutation" in retrieval_integrity_session_hook
    assert "integrityBadgeVariant" in retrieval_integrity_model
    assert "prioritizedIntegrityChecks" in retrieval_integrity_model
    assert "shortHash" in retrieval_integrity_model
    assert "function integrityBadgeVariant" not in retrieval_page
    assert "function prioritizedIntegrityChecks" not in retrieval_page
    assert "function shortHash" not in retrieval_page
    assert "Fusion agreement" in retrieval_search_cockpit_metric_grid
    assert "fusionDiagnosticsFromPackage" not in retrieval_page
    assert "fusionDiagnosticsFromPackage" in retrieval_cockpit_view_model
    assert "function fusionDiagnosticsFromPackage" not in retrieval_page
    assert "fusionDiagnosticsFromPackage" in retrieval_runtime_stack_model
    assert "function fusionDiagnosticsFromPackage" in retrieval_runtime_fusion_diagnostics_model
    assert "fusion_diagnostics" not in retrieval_page
    assert "fusion_diagnostics" in retrieval_report_cockpit_ranking_model
    assert "Whether lexical and vector retrieval agree" in retrieval_search_cockpit_metric_grid
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
    assert "DiversitySelectionExplanation" in retrieval_hit_card_score_section
    assert "function DiversitySelectionExplanation" not in retrieval_page
    assert "./hit-diversity-selection" in retrieval_hit_explanation_panels
    assert "Diversity selection" in retrieval_hit_diversity_selection
    assert "SourceDiversityPanel" not in retrieval_search_cockpit
    assert "SourceDiversityPanel" in retrieval_search_cockpit_section_stack
    assert "./source-diversity-panel" not in retrieval_search_cockpit
    assert "./source-diversity-panel" in retrieval_search_cockpit_section_stack
    assert "function SourceDiversityPanel" not in retrieval_page
    assert "Source diversity" in retrieval_source_diversity_panel
    assert "sourceDiversityDescription" in retrieval_source_diversity_panel
    assert "sourceDiversityDuplicateBadgeView" in retrieval_source_diversity_panel
    assert "visibleSourceDiversitySelections" in retrieval_source_diversity_panel
    assert "Source diversity selection is disabled" not in retrieval_source_diversity_panel
    assert "Source diversity selection is disabled" in retrieval_source_diversity_panel_view
    assert '"duplicate"' not in retrieval_source_diversity_panel
    assert "duplicate" in retrieval_source_diversity_panel_view
    assert "SourceDiversityRationale" in retrieval_source_diversity_panel
    assert "Selected-hit rationale" in retrieval_source_diversity_rationale
    assert "SourceDiversityMetricCard" in retrieval_source_diversity_panel
    assert "function SourceDiversityMetricCard" in retrieval_source_diversity_metric_card
    assert "function SourceDiversityMetricCard" not in retrieval_page
    assert "<RunComparisonSourceDiversity" not in retrieval_search_run_comparison_panel
    assert "RunComparisonSourceDiversity" in retrieval_search_run_comparison_summary_section
    assert "RunComparisonSourceDiversity" in retrieval_source_diversity_panel
    assert "function RunComparisonSourceDiversity" not in retrieval_page
    assert "Source diversity comparison" in retrieval_run_comparison_source_diversity
    assert "SourceListDelta" in retrieval_run_comparison_source_diversity
    assert "function SourceListDelta" in retrieval_source_list_delta
    assert "<RunComparisonOperatorSummary" not in retrieval_search_run_comparison_panel
    assert "RunComparisonOperatorSummary" in retrieval_search_run_comparison_summary_section
    assert "./run-comparison-summary-panels" in retrieval_search_run_comparison_summary_section
    assert "function RunComparisonOperatorSummary" not in retrieval_page
    assert "Comparison operator summary" in retrieval_run_comparison_operator_summary
    assert "comparisonOperatorSummary" in retrieval_search_run_comparison_view_hook
    assert "function comparisonOperatorSummary" not in retrieval_page
    assert "function comparisonOperatorSummary" in retrieval_comparison_operator_summary_model
    assert "formatSignedDelta" in retrieval_comparison_operator_summary_model
    assert "function formatSignedDelta" in retrieval_comparison_action_format_model
    assert 'export * from "./retrieval-comparison-operator-summary";' in retrieval_comparison_actions_model
    assert "operator_summary: comparisonOperatorSummary(comparison, recommendedActions)" in retrieval_comparison_report_model
    assert "Review focus" in retrieval_run_comparison_operator_summary
    assert "sourceDiversityComparisonBetweenRuns" not in retrieval_page
    assert "sourceDiversityComparisonBetweenRuns" in retrieval_run_comparison_source_diversity_model
    assert "sourceDiversityComparison" in retrieval_run_comparison_builder_model
    assert (
        "source_diversity_regressed"
        in retrieval_comparison_diagnosis_source_rules_model
    )
    assert (
        "source_diversity_improved"
        in retrieval_comparison_diagnosis_source_rules_model
    )
    assert 'export * from "./retrieval-comparison-diagnosis-types";' in retrieval_comparison_types_model
    assert "type RetrievalComparisonDiagnosticInput" not in retrieval_comparison_types_model
    assert "type RetrievalComparisonDiagnosticInput" in retrieval_comparison_diagnosis_types_model
    assert "type RetrievalComparisonRecommendedAction" in retrieval_comparison_recommendation_types_model
    assert "type RetrievalComparisonOperatorSummary" in retrieval_comparison_summary_types_model
    assert "type RetrievalComparisonReportInput" in retrieval_comparison_report_types_model
    assert "type RetrievalComparisonJudgmentInput" in retrieval_comparison_judgment_types_model
    assert "source_diversity: {" in retrieval_comparison_report_deltas_model
    assert "function comparisonSourceDiversityReport" in retrieval_comparison_report_source_diversity_model
    assert "selected_source_delta" in retrieval_comparison_report_summary_model
    assert "duplicate_selected_source_delta" in retrieval_comparison_report_summary_model
    assert "selected_hits: diversity.selectedHits.map" in retrieval_report_diversity_model
    assert "diversitySelectionByEvidenceId" in retrieval_runtime_stack_model
    assert "function diversitySelectionByEvidenceId" in retrieval_runtime_diversity_stack_model
    assert "function diversitySelectionByEvidenceId" not in retrieval_page
    assert "diversitySelectionByEvidenceId" in retrieval_search_results_hit_card_list
    assert "selected_hits" in retrieval_report_diversity_model
    assert "Diversity selection" in retrieval_hit_diversity_selection
    assert (
        "packageData.diversity ?? packageData.handoff_context.diversity"
        in retrieval_runtime_diversity_stack_model
    )
    assert "packageData.handoff_context.reranker" in retrieval_runtime_ranking_extraction_model
    assert "packageData.handoff_context.diversity" in retrieval_runtime_diversity_stack_model
    assert "DiversityStack" in retrieval_source_diversity_types_model
    assert "RetrievalSourceDiversityComparisonView" in retrieval_source_diversity_types_model
    assert "runtime?.rerank?.enabled" in retrieval_summary_model
    assert "rankingBoostSignalsFromHit" not in retrieval_page
    assert "function rankingBoostSignalsFromHit" in retrieval_evidence_signal_extraction_model
    assert "ranking_boosts" in retrieval_evidence_signal_extraction_model
    assert "ranking_boost_rules" in retrieval_evidence_signal_extraction_model
    assert "Ranking boost rule applied." in retrieval_evidence_signal_extraction_model
    assert "HitRankingSignals" in retrieval_hit_card_score_section
    assert "Ranking signals" in retrieval_hit_ranking_signals
    assert "HitMatchedTerms" in retrieval_hit_card_score_section
    assert "No exact terms matched." in retrieval_hit_matched_terms
    assert "HitLocatorDetails" in retrieval_hit_card
    assert "Locator and evidence ID" in retrieval_hit_locator_details
    assert "applyFilterSuggestion" in retrieval_metadata_filter_search_actions_hook
    assert "applySearchFilter" in retrieval_metadata_filter_search_actions_hook
    assert "clearSearchFilter" in retrieval_metadata_filter_search_actions_hook
    assert "clearAllSearchFilters" in retrieval_metadata_filter_search_actions_hook
    assert "applySourceIdFilter" in retrieval_source_scope_search_actions_hook
    assert "clearSourceScope" in retrieval_source_scope_search_actions_hook
    assert "executeSearchWhen" not in retrieval_filter_search_actions_hook
    assert "executeSearchWhen" in retrieval_metadata_filter_search_actions_hook
    assert "executeSearchWhen" in retrieval_source_scope_search_actions_hook
    assert "function executeSearchWhen" in retrieval_filter_search_action_policy_hook
    assert "sourceScopeOverride" not in retrieval_filter_search_actions_hook
    assert "sourceScopeOverride" in retrieval_source_scope_search_actions_hook
    assert "function sourceScopeOverride" in retrieval_filter_search_action_policy_hook
    assert "{ filters: { source_id:" not in retrieval_source_scope_search_actions_hook
    assert "RetrievalQueryColumn" in retrieval_page
    assert "components/retrieval-query-column" in retrieval_page
    assert "QueryBuilderPanel" in retrieval_query_column
    assert "./query-builder-panel" in retrieval_query_column
    assert "components/query-builder-panel" not in retrieval_page
    assert "function QueryBuilderPanel" not in retrieval_page
    assert "QueryBuilderFormContent" in retrieval_query_builder_panel
    assert "function QueryBuilderFormContent" in retrieval_query_builder_form_content
    assert "QueryBuilderTextFields" not in retrieval_query_builder_panel
    assert "QueryBuilderTextFields" in retrieval_query_builder_form_content
    assert "QueryBuilderContextFields" not in retrieval_query_builder_panel
    assert "QueryBuilderContextFields" in retrieval_query_builder_form_content
    assert "QueryBuilderScopeFields" not in retrieval_query_builder_panel
    assert "QueryBuilderScopeFields" in retrieval_query_builder_form_content
    assert "QueryBuilderNotices" not in retrieval_query_builder_panel
    assert "QueryBuilderNotices" in retrieval_query_builder_form_content
    assert "QueryBuilderHeader" in retrieval_query_builder_panel
    assert "QueryBuilderSubmitButton" not in retrieval_query_builder_panel
    assert "QueryBuilderSubmitButton" in retrieval_query_builder_form_content
    assert "QueryBuilderActiveFilterBar" not in retrieval_query_builder_panel
    assert "QueryBuilderActiveFilterBar" in retrieval_query_builder_form_content
    assert "activeFilterEntries" not in retrieval_query_builder_panel
    assert "activeFilterEntries" in retrieval_query_builder_active_filter_bar
    assert "ActiveFilterBar" in retrieval_query_builder_active_filter_bar
    assert "./query-builder-fields" not in retrieval_query_builder_panel
    assert "./query-builder-fields" in retrieval_query_builder_form_content
    assert "./query-builder-notices" not in retrieval_query_builder_panel
    assert "./query-builder-notices" in retrieval_query_builder_form_content
    assert "./query-builder-panel-types" in retrieval_query_builder_panel
    assert "Search approved schema" not in retrieval_query_builder_panel
    assert "Search approved schema" in retrieval_query_builder_header
    assert "Search evidence" not in retrieval_query_builder_panel
    assert "Search evidence" in retrieval_query_builder_submit_button
    assert "Retrieval query help" not in retrieval_query_builder_panel
    assert "QueryBuilderTextFields" in retrieval_query_builder_fields
    assert "QueryBuilderContextFields" in retrieval_query_builder_fields
    assert "QueryBuilderScopeFields" in retrieval_query_builder_fields
    assert "Retrieval query help" not in retrieval_query_builder_fields
    assert "Retrieval query help" in retrieval_query_builder_text_fields
    assert "QueryBuilderSchemaControl" in retrieval_query_builder_context_fields
    assert "QueryBuilderTopKControl" in retrieval_query_builder_context_fields
    assert "QueryBuilderFormatControl" in retrieval_query_builder_context_fields
    assert "QueryBuilderResourceControl" in retrieval_query_builder_context_fields
    assert 'export * from "./query-builder-schema-control";' in retrieval_query_builder_context_controls
    assert 'export * from "./query-builder-top-k-control";' in retrieval_query_builder_context_controls
    assert 'export * from "./query-builder-format-control";' in retrieval_query_builder_context_controls
    assert 'export * from "./query-builder-resource-control";' in retrieval_query_builder_context_controls
    assert "function QueryBuilderSchemaControl" in retrieval_query_builder_schema_control
    assert "function QueryBuilderTopKControl" in retrieval_query_builder_top_k_control
    assert "function QueryBuilderFormatControl" in retrieval_query_builder_format_control
    assert "function QueryBuilderResourceControl" in retrieval_query_builder_resource_control
    assert "Search settings changed" not in retrieval_query_builder_panel
    assert "Search settings changed" in retrieval_query_builder_notices
    assert "useRetrievalFormSession" not in retrieval_page
    assert "useRetrievalFormSession" in retrieval_page_workspace_hook
    assert "use-retrieval-form-session" in retrieval_page_workspace_hook
    assert "function useRetrievalFormSession" in retrieval_form_session_hook
    assert "useRetrievalFormState" in retrieval_form_session_hook
    assert "function useRetrievalFormState" in retrieval_form_state_hook
    assert "useRetrievalFormFieldState" in retrieval_form_state_hook
    assert "function useRetrievalFormFieldState" in retrieval_form_field_state_hook
    assert "retrievalFormStateFromInputs" in retrieval_form_state_hook
    assert "retrievalFormSettersFromInputs" in retrieval_form_state_hook
    assert "function retrievalFormStateFromInputs" in retrieval_form_state_builders_hook
    assert "function retrievalFormSettersFromInputs" in retrieval_form_state_builders_hook
    assert "useRetrievalFormPayloadActions" in retrieval_form_session_hook
    assert "function useRetrievalFormPayloadActions" in retrieval_form_payload_actions_hook
    assert "function applyPresetToForm" in retrieval_form_payload_actions_hook
    assert "function applySearchPayloadToForm" in retrieval_form_payload_actions_hook
    assert "setSchemaId(payload.schema_id" not in retrieval_form_session_hook
    assert "setSchemaId(payload.schema_id" in retrieval_form_payload_actions_hook
    assert "retrievalFormDerivedState" in retrieval_form_state_hook
    assert "activeFacetFiltersFromPayload" not in retrieval_form_state_hook
    assert "activeFacetFiltersFromPayload" in retrieval_form_derived_state_model
    assert "queryBuilderDraftActions" in retrieval_form_session_hook
    assert "useQueryBuilderDraftActions" in retrieval_form_session_hook
    assert "function useQueryBuilderDraftActions" in retrieval_query_builder_draft_actions_hook
    assert "queryBuilderDraftActions" not in retrieval_page
    assert "queryBuilderDraftActions" in retrieval_page_workspace_hook
    assert "restoreSearchPayload" in retrieval_form_session_hook
    assert "applyFilterControl" in retrieval_form_session_hook
    assert "useRetrievalFilterControls" in retrieval_form_session_hook
    assert "function useRetrievalFilterControls" in retrieval_filter_controls_hook
    assert "clearAllFilterControls" in retrieval_filter_controls_hook
    assert "<ActiveFilterBar" not in retrieval_query_builder_panel
    assert "./active-filter-bar" not in retrieval_query_builder_panel
    assert "./active-filter-bar" in retrieval_query_builder_active_filter_bar
    assert "function ActiveFilterBar" not in retrieval_page
    assert "activeFilterEntries" not in retrieval_page
    assert "activeFilters" not in retrieval_page_query_column_props
    assert "activeFilters" in retrieval_page_query_builder_props
    assert "Active filters" in retrieval_active_filter_bar
    assert "Clear all" in retrieval_active_filter_bar
    assert "useRetrievalRunSession" not in retrieval_page
    assert "useRetrievalRunSession" in retrieval_page_workspace_hook
    assert "use-retrieval-run-session" in retrieval_page_workspace_hook
    assert "useRetrievalWorkspaceSearchSubmit" in retrieval_page_workspace_hook
    assert "function useRetrievalWorkspaceSearchSubmit" in retrieval_workspace_search_submit_hook
    assert "mutateAsync(payload)" not in retrieval_page_workspace_hook
    assert "mutateAsync(payload)" in retrieval_workspace_search_submit_hook
    assert "useRetrievalWorkspaceClearActions" in retrieval_page_workspace_hook
    assert "function useRetrievalWorkspaceClearActions" in retrieval_workspace_clear_actions_hook
    assert "clearRelevanceJudgments()" not in retrieval_page_workspace_hook
    assert "clearRelevanceJudgments()" in retrieval_workspace_clear_actions_hook
    assert "useRetrievalWorkspaceView" in retrieval_page_workspace_hook
    assert "use-retrieval-workspace-view" in retrieval_page_workspace_hook
    assert "function useRetrievalWorkspaceView" in retrieval_workspace_view_hook
    assert "retrievalTracePanelView" not in retrieval_page_workspace_hook
    assert "retrievalTracePanelView" in retrieval_workspace_view_hook
    assert "function useRetrievalRunSession" in retrieval_run_session_hook
    assert "useRetrievalRunSessionState" in retrieval_run_session_hook
    assert "function useRetrievalRunSessionState" in retrieval_run_session_state_hook
    assert "lastSearchSignature" in retrieval_run_session_state_hook
    assert "useRetrievalRunSessionActions" in retrieval_run_session_hook
    assert "function useRetrievalRunSessionActions" in retrieval_run_session_actions_hook
    assert "useRetrievalRunSearchAction" in retrieval_run_session_actions_hook
    assert "useRetrievalRunHistoryActions" in retrieval_run_session_actions_hook
    assert "function useRetrievalRunSearchAction" in retrieval_run_search_action_hook
    assert "executeRetrievalRunSearch" in retrieval_run_search_action_hook
    assert "async function executeRetrievalRunSearch" in retrieval_run_search_executor_hook
    assert "function useRetrievalRunHistoryActions" in retrieval_run_history_actions_hook
    assert "function useActiveRetrievalRunState" in retrieval_active_run_state_hook
    assert "commitCompletedSearchRun" not in retrieval_run_search_action_hook
    assert "commitCompletedSearchRun" in retrieval_run_search_executor_hook
    assert "function commitCompletedSearchRun" in retrieval_run_session_completion_hook
    assert "completedSearchRunState" not in retrieval_run_search_action_hook
    assert "completedSearchRunState" not in retrieval_run_search_executor_hook
    assert "completedSearchRunState" in retrieval_run_session_completion_hook
    assert "function completedSearchRunState" not in retrieval_run_session_hook
    assert "function completedSearchRunState" in retrieval_run_session_transitions_hook
    assert "retrievalRunPayloadValidationError" not in retrieval_run_search_action_hook
    assert "retrievalRunPayloadValidationError" in retrieval_run_search_executor_hook
    assert "function retrievalRunPayloadValidationError" in retrieval_run_session_validation_hook
    assert "Enter a retrieval query before searching." in retrieval_run_session_validation_hook
    assert "currentSearchSignature" not in retrieval_page
    assert "currentSearchSignature" in retrieval_page_workspace_hook
    assert "submittedSearchSignature" in retrieval_plan_session_hook
    assert "currentSearchSignature !== submittedSearchSignature" in retrieval_plan_session_hook
    assert "isSearchResultStale" not in retrieval_page
    assert "isSearchResultStale" not in retrieval_page_query_column_props
    assert "isSearchResultStale" in retrieval_page_query_builder_props
    assert "retrievalPayloadFromForm" in retrieval_plan_session_hook
    assert "retrievalSearchSignature" in retrieval_plan_session_hook
    assert "retrievalPayloadFromForm" not in retrieval_form_state_hook
    assert "retrievalSearchSignature" not in retrieval_form_state_hook
    assert "retrievalPayloadFromForm" in retrieval_form_derived_state_model
    assert "retrievalSearchSignature" in retrieval_form_derived_state_model
    assert "defaultRetrievalFormState" not in retrieval_form_state_hook
    assert "defaultRetrievalFormState" in retrieval_form_field_state_hook
    assert "defaultRetrievalFormState" in retrieval_form_defaults_model
    assert 'React.useState("approved")' not in retrieval_form_state_hook
    assert "React.useState(5)" not in retrieval_form_state_hook
    assert "defaultRetrievalFormState.trustLevel" in retrieval_form_field_state_hook
    assert "defaultRetrievalFormState.topK" in retrieval_form_field_state_hook
    assert "function retrievalPayloadFromForm" not in retrieval_page
    assert "function retrievalSearchSignature" not in retrieval_page
    assert "function retrievalPayloadFromForm" in retrieval_search_payload_model
    assert "function retrievalSearchSignature" in retrieval_search_payload_model
    assert "function parseFields" in retrieval_search_payload_model
    assert "isRetrievalPayloadFilterField" in retrieval_planned_task_payload_model
    assert "Search settings changed" in retrieval_query_builder_notices
    assert "pending changes" in retrieval_search_results_header
    assert "submittedSearchPayload" in retrieval_run_session_hook
    assert "SubmittedSearchSummary" not in retrieval_search_results_panel
    assert "SubmittedSearchSummary" in retrieval_search_results_overview_section
    assert "./submitted-search-summary" in retrieval_search_results_overview_section
    assert "function SubmittedSearchSummary" not in retrieval_page
    assert "SubmittedSearchSummaryHeader" in retrieval_submitted_search_summary
    assert "SubmittedSearchMetadataChips" in retrieval_submitted_search_summary
    assert "SubmittedSearchFilterChips" in retrieval_submitted_search_summary
    assert "Submitted search" in retrieval_submitted_search_summary_header
    assert "Restore submitted search" in retrieval_submitted_search_summary_header
    assert "payload.fields.slice" in retrieval_submitted_search_metadata_chips
    assert "filter.displayValue" in retrieval_submitted_search_filter_chips
    assert "RankedEvidenceTriage" not in retrieval_search_results_panel
    assert "RankedEvidenceTriage" in retrieval_search_results_overview_section
    assert "./ranked-evidence-triage" in retrieval_search_results_overview_section
    assert "function RankedEvidenceTriage" not in retrieval_page
    assert "Ranked evidence triage" in retrieval_ranked_evidence_triage
    assert "Inspect first" in retrieval_ranked_evidence_triage
    assert "RankedEvidenceTriageFacts" in retrieval_ranked_evidence_triage
    assert "Refresh search before using these rankings" in retrieval_ranked_evidence_triage_guidance
    assert "Start by judging the first ranked hit" in retrieval_ranked_evidence_triage_guidance
    assert "Required buckets" in retrieval_ranked_evidence_triage_facts
    assert "qualityTone" in retrieval_ranked_evidence_triage_facts
    assert "SearchRunHistoryPanel" in retrieval_query_column
    assert "Search runs" in retrieval_search_run_history
    assert "searchRuns" in retrieval_run_session_hook
    assert "type UseRetrievalRunSessionArgs" in retrieval_run_session_types_hook
    assert "defaultSearchRunHistoryLimit" in retrieval_run_session_history_hook
    assert "activeRetrievalRunState" in retrieval_active_run_state_hook
    assert "function activeRetrievalRunState" in retrieval_run_session_history_hook
    assert "upsertSearchRunHistory" not in retrieval_run_search_action_hook
    assert "upsertSearchRunHistory" in retrieval_run_session_completion_hook
    assert "function upsertSearchRunHistory" in retrieval_run_session_history_hook
    assert "shouldClearComparisonBaseline" in retrieval_run_session_hook
    assert "function shouldClearComparisonBaseline" in retrieval_run_session_history_hook
    assert "createSearchRun" in retrieval_search_run_history_model
    assert "createRetrievalRunRecord" not in retrieval_run_search_action_hook
    assert "createRetrievalRunRecord" in retrieval_run_search_executor_hook
    assert "function createRetrievalRunRecord" in retrieval_run_session_record_hook
    assert "createSearchRun" in retrieval_run_session_record_hook
    assert "function createSearchRun" not in retrieval_page
    assert "comparisonRunForActive" in retrieval_search_run_history_model
    assert "function comparisonRunForActive" not in retrieval_page
    assert "restoreSearchRun" in retrieval_run_session_hook
    assert "restoredSearchRunState" in retrieval_run_history_actions_hook
    assert "function restoredSearchRunState" in retrieval_run_session_transitions_hook
    assert "clearedSearchRunState" in retrieval_run_history_actions_hook
    assert "function clearedSearchRunState" in retrieval_run_session_transitions_hook
    assert "retrievalRunSummary" in retrieval_run_session_record_hook
    assert "function retrievalRunSummary" not in retrieval_page
    assert "function retrievalRunSummary" in retrieval_run_summary_model
    assert "SearchRunComparisonPanel" in retrieval_search_run_comparison_node
    assert "SearchRunComparisonNode" in retrieval_search_run_history_panel
    assert "./search-run-comparison-node" in retrieval_search_run_history_panel
    assert "./search-run-comparison-panel" in retrieval_search_run_comparison_node
    assert "function SearchRunComparisonPanel" not in retrieval_page
    assert "Run comparison" in retrieval_search_run_comparison_header
    assert "SearchRunComparisonHeader" in retrieval_search_run_comparison_panel
    assert "./search-run-comparison-header" in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonHelp" in retrieval_search_run_comparison_panel
    assert "./search-run-comparison-help" in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonSummarySection" in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonDetailSection" in retrieval_search_run_comparison_panel
    assert "./search-run-comparison-summary-section" in retrieval_search_run_comparison_panel
    assert "./search-run-comparison-detail-section" in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonTopSource" in retrieval_search_run_comparison_panel
    assert "./search-run-comparison-top-source" in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonPanelView" in retrieval_search_run_comparison_types
    assert "Run comparison help" in retrieval_search_run_comparison_header
    assert "SearchRunComparisonStatusBadges" in retrieval_search_run_comparison_header
    assert "function SearchRunComparisonStatusBadges" in retrieval_search_run_comparison_status_badges
    assert "top source changed" not in retrieval_search_run_comparison_header
    assert "top source changed" in retrieval_search_run_comparison_status_badges
    assert "Copy retrieval comparison report" in retrieval_search_run_comparison_header
    assert "useCopyFeedback" in retrieval_search_run_comparison_header
    assert "useState" not in retrieval_search_run_comparison_header
    assert "useEffect" not in retrieval_search_run_comparison_header
    assert "setTimeout" not in retrieval_search_run_comparison_header
    assert "reportCopied" not in retrieval_search_run_comparison_panel
    assert (
        "Baseline is the older comparison run"
        not in retrieval_search_run_comparison_panel
    )
    assert (
        "Baseline is the older comparison run"
        in retrieval_search_run_comparison_help
    )
    assert (
        "warning deltas, quality changes, and rank movement"
        in retrieval_search_run_comparison_help
    )
    assert "Top source:" not in retrieval_search_run_comparison_panel
    assert "Top source:" in retrieval_search_run_comparison_top_source
    assert "<SearchRunComparisonBaseline" not in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonBaseline" in retrieval_search_run_comparison_summary_section
    assert "./search-run-comparison-baseline" in retrieval_search_run_comparison_summary_section
    assert "Baseline query" in retrieval_search_run_comparison_baseline
    assert "<SearchRunComparisonMetricGrid" not in retrieval_search_run_comparison_panel
    assert "SearchRunComparisonMetricGrid" in retrieval_search_run_comparison_summary_section
    assert (
        "./search-run-comparison-metric-grid"
        in retrieval_search_run_comparison_summary_section
    )
    assert "RunComparisonMetric" in retrieval_search_run_comparison_metric_grid
    assert "<RunComparisonAtAGlance" not in retrieval_search_run_comparison_panel
    assert "RunComparisonAtAGlance" in retrieval_search_run_comparison_summary_section
    assert "function RunComparisonAtAGlance" not in retrieval_page
    assert 'export { RunComparisonAtAGlance } from "./run-comparison-at-a-glance";' in retrieval_run_comparison_summary_metrics
    assert 'export { RunComparisonMetric } from "./run-comparison-delta-metric";' in retrieval_run_comparison_summary_metrics
    assert 'export { RunComparisonMetrics } from "./run-comparison-metrics";' in retrieval_run_comparison_summary_metrics
    assert "Comparison at a glance" in retrieval_run_comparison_at_a_glance
    assert "function RunComparisonMetric" in retrieval_run_comparison_delta_metric
    assert "readinessGlanceLabel" in retrieval_search_run_quality_model
    assert "baselineSummary.qualitySummary?.status" in retrieval_search_run_quality_model
    assert "activeSummary.qualitySummary?.status" in retrieval_search_run_quality_model
    assert "Action priority" in retrieval_run_comparison_at_a_glance
    assert "Evidence overlap" in retrieval_run_comparison_at_a_glance
    assert "label=\"Top source\"" in retrieval_run_comparison_at_a_glance
    assert "comparison.topSourceChanged ? \"changed\" : \"stable\"" in retrieval_run_comparison_at_a_glance
    assert "<RunComparisonDiagnosis" not in retrieval_search_run_comparison_panel
    assert "RunComparisonDiagnosis" in retrieval_search_run_comparison_summary_section
    assert "function RunComparisonDiagnosis" not in retrieval_page
    assert "Comparison diagnosis" in retrieval_run_comparison_diagnosis
    assert "<RunComparisonRecommendedActions" not in retrieval_search_run_comparison_panel
    assert "RunComparisonRecommendedActions" in retrieval_search_run_comparison_summary_section
    assert "function RunComparisonRecommendedActions" not in retrieval_page
    assert "Recommended actions" in retrieval_run_comparison_recommended_actions
    assert 'export { RunComparisonDiagnosis } from "./run-comparison-diagnosis";' in retrieval_run_comparison_summary_narrative
    assert 'export { RunComparisonOperatorSummary } from "./run-comparison-operator-summary";' in retrieval_run_comparison_summary_narrative
    assert 'export { RunComparisonRecommendedActions } from "./run-comparison-recommended-actions";' in retrieval_run_comparison_summary_narrative
    assert "const comparisonRecommendedActions = React.useMemo" in retrieval_search_run_comparison_view_hook
    assert "recommendedActions={comparisonRecommendedActions}" in retrieval_search_run_comparison_node
    assert "actions={recommendedActions}" in retrieval_search_run_comparison_summary_section
    assert "comparisonReportFromComparison(" in retrieval_search_run_comparison_view_hook
    assert "function comparisonReportFromComparison" not in retrieval_page
    assert "function comparisonReportFromComparison" in retrieval_comparison_report_model
    assert "comparisonJudgments" in retrieval_search_run_comparison_view_hook
    assert "comparisonRecommendedActionSummary" in retrieval_search_run_comparison_view_hook
    assert "function comparisonRecommendedActionSummary" not in retrieval_page
    assert (
        "function comparisonRecommendedActionSummary"
        not in retrieval_comparison_recommended_actions_model
    )
    assert (
        "function comparisonRecommendedActionSummary"
        in retrieval_comparison_recommended_action_summary_model
    )
    assert 'export * from "./retrieval-comparison-recommended-actions";' in retrieval_comparison_actions_model
    assert "recommended_action_summary: comparisonRecommendedActionSummary" in retrieval_comparison_report_model
    assert "highest_priority" in retrieval_comparison_recommended_action_summary_model
    assert "source_count" in retrieval_comparison_recommended_action_summary_model
    assert "source_counts" in retrieval_comparison_recommended_action_summary_model
    assert "actionSummary.sources.map" in retrieval_run_comparison_recommended_actions
    assert "actionSummary.source_counts[source]" in retrieval_run_comparison_recommended_actions
    assert (
        "priority: comparison.activeSummary.qualitySummary?.status === \"blocked\" ? 1 : 2"
        in retrieval_comparison_recommended_action_quality_model
    )
    assert "left.priority - right.priority" in retrieval_comparison_recommended_action_policy_model
    assert "qualitySummaryActions" in retrieval_comparison_recommended_action_policy_model
    assert "coverageActions" in retrieval_comparison_recommended_action_policy_model
    assert "queryProfileActions" in retrieval_comparison_recommended_action_policy_model
    assert "evidenceChangeActions" in retrieval_comparison_recommended_action_policy_model
    assert "judgmentActions" in retrieval_comparison_recommended_action_policy_model
    assert "stableComparisonAction" in retrieval_comparison_recommended_action_policy_model
    assert "source_diversity" in retrieval_comparison_recommended_action_evidence_model
    assert "churnRate" in retrieval_comparison_recommended_action_evidence_model
    assert "query_profile" in retrieval_comparison_recommended_action_configuration_model
    assert "rule_packs" in retrieval_comparison_recommended_action_configuration_model
    assert "explicit relevance judgments" in retrieval_comparison_recommended_action_judgments_model
    assert "comparison_stable" in retrieval_comparison_recommended_action_stable_model
    assert (
        'export { comparisonReportRecommendedActions } from "./retrieval-comparison-recommended-action-policy";'
        in retrieval_comparison_recommended_actions_model
    )
    assert (
        'export { comparisonRecommendedActionSummary } from "./retrieval-comparison-recommended-action-summary";'
        in retrieval_comparison_recommended_actions_model
    )
    assert "comparisonDiagnosisFromComparison" not in retrieval_page
    assert "comparisonDiagnosisFromComparison" in retrieval_run_comparison_builder_model
    assert 'export { compareSearchRuns } from "./retrieval-run-comparison-builder";' in retrieval_run_comparison_model
    assert 'export { comparisonRulePackChangeViews } from "./retrieval-run-comparison-metrics";' in retrieval_run_comparison_model
    assert "function compareSearchRuns" not in retrieval_run_comparison_model
    assert "function comparisonDiagnosisFromComparison" not in retrieval_page
    assert "function comparisonDiagnosisFromComparison" in retrieval_comparison_diagnosis_rules_model
    assert "comparisonProfileDiagnosis" in retrieval_comparison_diagnosis_rules_model
    assert "comparisonQualityDiagnosis" in retrieval_comparison_diagnosis_rules_model
    assert "comparisonSourceDiagnosis" in retrieval_comparison_diagnosis_rules_model
    assert "comparisonStableDiagnosis" in retrieval_comparison_diagnosis_rules_model
    assert "comparison_stable" in retrieval_comparison_diagnosis_stability_model
    assert "diagnosis: comparison.diagnosis" in retrieval_comparison_report_model
    assert "activeSearchRunComparison" in retrieval_search_run_comparison_view_hook
    assert "function activeSearchRunComparison" in retrieval_search_run_comparison_active_model
    assert "compareSearchRuns" in retrieval_search_run_comparison_active_model
    assert "function compareSearchRuns" not in retrieval_page
    assert "function compareSearchRuns" in retrieval_run_comparison_builder_model
    assert "retrievalRunComparisonDimensionValues" in retrieval_run_comparison_builder_model
    assert (
        "function retrievalRunComparisonDimensionValues"
        in retrieval_run_comparison_dimension_values_model
    )
    assert "coverageComparisonBetweenRuns" not in retrieval_run_comparison_builder_model
    assert "coverageComparisonBetweenRuns" in retrieval_run_comparison_dimension_values_model
    assert "comparisonRunForActive" in retrieval_search_run_comparison_active_model
    assert "comparisonBaselineRunId" in retrieval_run_session_hook
    assert "Set baseline" in retrieval_search_run_history_row_actions
    assert "as comparison baseline" in retrieval_search_run_history_row_actions
    assert "GitCompareArrows" in retrieval_search_run_history_row_actions
    assert "addedEvidenceIds" in retrieval_run_comparison_builder_model
    assert "retainedEvidenceIds" in retrieval_run_comparison_builder_model
    assert "evidenceIdsFromRun" not in retrieval_run_comparison_model
    assert "evidenceComparisonBetweenRuns" not in retrieval_run_comparison_builder_model
    assert "evidenceComparisonBetweenRuns" in retrieval_run_comparison_dimension_values_model
    assert "function evidenceComparisonBetweenRuns" in retrieval_run_comparison_evidence_model
    assert "addedEvidenceIds" in retrieval_run_comparison_evidence_model
    assert "retainedEvidenceIds" in retrieval_run_comparison_evidence_model
    assert "<RunComparisonRankChanges" not in retrieval_search_run_comparison_panel
    assert "RunComparisonRankChanges" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonRankChanges" not in retrieval_page
    assert "<RunComparisonEvidenceChange" not in retrieval_search_run_comparison_panel
    assert "RunComparisonEvidenceChange" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonEvidenceChange" not in retrieval_page
    assert 'export { RunComparisonRankChanges } from "./run-comparison-rank-changes";' in retrieval_run_comparison_rank_rule_panels
    assert "Rank movement" in retrieval_run_comparison_rank_changes
    assert "Rank movement help" in retrieval_run_comparison_rank_changes
    assert (
        "Stable rank means retained evidence kept the same ordering"
        in retrieval_run_comparison_rank_changes
    )
    assert "Use rank movement to debug relevance tuning" in retrieval_run_comparison_rank_changes
    assert "evidenceIds.slice(0, 4)" in retrieval_run_comparison_evidence_change
    assert "rankChangesBetweenRuns" not in retrieval_page
    assert "rankChangesBetweenRuns" in retrieval_run_comparison_rank_changes_model
    assert 'export * from "./retrieval-run-comparison-change-types";' in retrieval_run_comparison_types_model
    assert 'export * from "./retrieval-run-comparison-core-types";' in retrieval_run_comparison_types_model
    assert 'export * from "./retrieval-run-comparison-facet-types";' in retrieval_run_comparison_types_model
    assert 'export * from "./retrieval-run-comparison-metric-types";' in retrieval_run_comparison_types_model
    assert 'export * from "./retrieval-run-comparison-rank-types";' in retrieval_run_comparison_types_model
    assert 'export * from "./retrieval-run-comparison-rule-pack-types";' in retrieval_run_comparison_types_model
    assert "type RetrievalRunComparison" in retrieval_run_comparison_core_types_model
    assert "type RetrievalCoverageComparison" in retrieval_run_comparison_change_types_model
    assert "type RetrievalFacetComparison" in retrieval_run_comparison_facet_types_model
    assert "type RetrievalRulePackChange" in retrieval_run_comparison_rule_pack_types_model
    assert "rankDelta" in retrieval_run_comparison_rank_types_model
    assert "Copy comparison JSON" in retrieval_search_run_comparison_header
    assert "Copy retrieval comparison report" in retrieval_search_run_comparison_header
    assert "Comparison JSON report help" in retrieval_search_run_comparison_header
    assert "comparisonReportFromComparison" in retrieval_search_run_comparison_view_hook
    assert "comparisonReportSummary" not in retrieval_page
    assert "comparisonReportSummary" in retrieval_comparison_report_model
    assert "function comparisonReportSummary" not in retrieval_comparison_report_model
    assert "function comparisonReportSummary" in retrieval_comparison_report_summary_model
    assert "summary: comparisonReportSummary(comparison, judgments)" in retrieval_comparison_report_model
    assert "remediationSummary ??" not in retrieval_comparison_report_model
    assert 'export * from "./retrieval-comparison-report-deltas";' in retrieval_comparison_report_sections_model
    assert "function comparisonDeltaReport" not in retrieval_comparison_report_sections_model
    assert "remediationSummary ??" in retrieval_comparison_report_run_sections_model
    assert "comparisonRemediationReport" in retrieval_comparison_report_model
    assert "comparisonRunReportSections" in retrieval_comparison_report_model
    assert "before: comparison.topSourceBefore" in retrieval_comparison_report_model
    assert "after: comparison.topSourceAfter" in retrieval_comparison_report_model
    assert "comparisonReportRecommendedActions" in retrieval_search_run_comparison_view_hook
    assert "function comparisonReportRecommendedActions" not in retrieval_page
    assert (
        "function comparisonReportRecommendedActions"
        in retrieval_comparison_recommended_action_policy_model
    )
    assert "recommended_actions: recommendedActions" in retrieval_comparison_report_model
    assert "changed_dimensions" in retrieval_comparison_report_summary_model
    assert "judgment_count: judgments.length" in retrieval_comparison_report_summary_model
    assert "comparisonDeltaReport" in retrieval_comparison_report_model
    assert "comparisonDimensionReports" in retrieval_comparison_report_model
    assert "comparisonSourceDiversityReport" in retrieval_comparison_report_model
    assert "function comparisonJudgmentReport" in retrieval_comparison_report_evidence_model
    assert "function comparisonRulePackReport" in retrieval_comparison_report_evidence_model
    assert "retrieval_run_comparison" in retrieval_comparison_report_model
    assert "<RunComparisonMetrics" not in retrieval_search_run_comparison_panel
    assert "RunComparisonMetrics" in retrieval_search_run_comparison_summary_section
    assert "function RunComparisonMetrics" not in retrieval_page
    assert "Overlap shows shared evidence" in retrieval_run_comparison_metrics
    assert "churn shows how much the result set changed" in retrieval_run_comparison_metrics
    assert "mean rank delta shows ordering instability" in retrieval_run_comparison_metrics
    assert "<RunComparisonRulePacks" not in retrieval_search_run_comparison_panel
    assert "RunComparisonRulePacks" in retrieval_search_run_comparison_detail_section
    assert "function RunComparisonRulePacks" not in retrieval_page
    assert "Rule packs" in retrieval_run_comparison_rule_packs
    assert "comparisonRulePackChangeViews" in retrieval_search_run_comparison_view_hook
    assert "function comparisonRulePackChangeViews" not in retrieval_page
    assert "function comparisonRulePackChangeViews" in retrieval_run_comparison_rule_packs_model
    assert "rulePackChangesBetweenRuns" not in retrieval_page
    assert "rulePackChangesBetweenRuns" in retrieval_run_comparison_rule_packs_model
    assert "rulePackFingerprint" not in retrieval_page
    assert "rulePackFingerprint" in retrieval_run_comparison_rule_packs_model
    assert "function rulePackFingerprint" not in retrieval_page
    assert "function rulePackFingerprint" in retrieval_run_rule_packs_model
    assert "retrievalRunComparisonCoreValues" in retrieval_run_comparison_builder_model
    assert "retrievalRunComparisonRunValues" in retrieval_run_comparison_builder_model
    assert "retrievalRunComparisonMetricInput" in retrieval_run_comparison_builder_model
    assert "function retrievalRunComparisonCoreValues" in retrieval_run_comparison_core_values_model
    assert "function retrievalRunComparisonRunValues" in retrieval_run_comparison_run_values_model
    assert "function retrievalRunComparisonMetricInput" in retrieval_run_comparison_metric_input_model
    assert "activePayload: activeRun.payload" in retrieval_run_comparison_run_values_model
    assert "rulePackChanged" in retrieval_run_comparison_core_values_model
    assert "rule_packs" not in retrieval_page
    assert "retrievalCockpitRulePackReport(packageData)" in retrieval_report_cockpit_model
    assert "retrievalRulePacksFromPackage" in retrieval_run_rule_packs_model
    assert "function retrievalRulePacksFromPackage" not in retrieval_page
    assert "function retrievalRulePacksFromPackage" in retrieval_run_rule_packs_model
    assert "configured" not in retrieval_page
    assert "configured" in retrieval_integrity_session_hook
    assert "content_hash" not in retrieval_page
    assert "content_hash" in retrieval_report_cockpit_rule_packs_model
    assert "Search comparison metrics" in retrieval_run_comparison_metrics
    assert "comparisonMetrics" not in retrieval_page
    assert "comparisonMetrics" in retrieval_run_comparison_aggregate_metrics_model
    assert 'export * from "./retrieval-run-comparison-aggregate-metrics";' in retrieval_run_comparison_metrics_model
    assert "overlapRatio" in retrieval_run_comparison_metric_types_model
    assert "churnRate" in retrieval_run_comparison_metric_types_model
    assert "meanAbsoluteRankDelta" in retrieval_run_comparison_metric_types_model
    assert "RelevanceJudgmentControl" in retrieval_hit_card
    assert "./relevance-judgment-control" in retrieval_hit_card
    assert "function RelevanceJudgmentControl" not in retrieval_page
    assert "Relevance judgment" in retrieval_relevance_judgment_control
    assert "Relevance judgment help" in retrieval_relevance_judgment_control
    assert "Use relevant for direct support" in retrieval_relevance_judgment_control
    assert "judgmentLabel" in retrieval_relevance_judgment_control
    assert "judgmentBadgeVariant" in retrieval_relevance_judgment_control
    assert "relevanceJudgmentOptions" in retrieval_relevance_judgment_control
    assert "Mark this evidence as relevant" not in retrieval_relevance_judgment_control
    assert "function judgmentLabel" not in retrieval_relevance_judgment_control
    assert "function judgmentBadgeVariant" not in retrieval_relevance_judgment_control
    assert "function judgmentLabel" in retrieval_judgment_labels_model
    assert "function judgmentBadgeVariant" in retrieval_judgment_labels_model
    assert "relevanceJudgmentOptions" in retrieval_judgment_labels_model
    assert "Mark this evidence as relevant" in retrieval_judgment_labels_model
    assert "useRetrievalJudgmentSession" not in retrieval_page
    assert "useRetrievalJudgmentSession" in retrieval_page_workspace_hook
    assert "use-retrieval-judgment-session" in retrieval_page_workspace_hook
    assert "function useRetrievalJudgmentSession" in retrieval_judgment_session_hook
    assert "relevanceJudgments" in retrieval_judgment_session_hook
    assert "useRetrievalJudgmentQueries" in retrieval_judgment_session_hook
    assert "useRetrievalJudgmentActions" in retrieval_judgment_session_hook
    assert "useHydratePersistedRelevanceJudgments" in retrieval_judgment_session_hook
    assert "usePruneRelevanceJudgments" in retrieval_judgment_session_hook
    assert "useRetrievalJudgmentsQuery" in retrieval_judgment_queries_hook
    assert "useRetrievalJudgmentMutation" in retrieval_judgment_actions_hook
    assert "useRetrievalJudgmentSummaryQuery" in retrieval_judgment_queries_hook
    assert "useRetrievalJudgmentEvaluationQuery" in retrieval_judgment_queries_hook
    assert "useDeleteRetrievalJudgmentMutation" in retrieval_judgment_actions_hook
    assert "relevanceJudgmentFromPersisted" in retrieval_judgment_hydration_hook
    assert "/retrieval/judgments" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "/retrieval/judgments/summary" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "/retrieval/judgments/evaluate" in (REPO_ROOT / "frontend/src/api.ts").read_text(
        encoding="utf-8"
    )
    assert "judgmentsForComparison" in retrieval_search_run_comparison_view_hook
    assert "<RelevanceJudgmentSummary" not in retrieval_search_results_panel
    assert "RelevanceJudgmentSummary" in retrieval_search_results_judgment_section
    assert "./judgment-evaluation-panels" in retrieval_search_results_judgment_section
    assert "function RelevanceJudgmentSummary" not in retrieval_page
    assert "Judgment metrics" in retrieval_judgment_evaluation_header
    assert "Judgment metrics help" in retrieval_judgment_evaluation_header
    assert (
        "Precision@k and nDCG@k become meaningful"
        in retrieval_judgment_evaluation_help
    )
    assert "relevanceJudgmentMetrics" not in retrieval_search_results_panel
    assert "relevanceJudgmentMetrics" not in retrieval_search_results_judgment_section
    assert "relevanceJudgmentMetrics" in retrieval_search_results_view_model
    assert "retrievalJudgmentPayload" in retrieval_judgment_actions_hook
    assert "optimisticJudgmentActionState" in retrieval_judgment_actions_hook
    assert "persistedJudgmentActionState" in retrieval_judgment_actions_hook
    assert "removeJudgmentActionState" in retrieval_judgment_actions_hook
    assert "optimisticRelevanceJudgment" not in retrieval_judgment_actions_hook
    assert "relevanceJudgmentFromPersisted" not in retrieval_judgment_actions_hook
    assert "function optimisticJudgmentActionState" in retrieval_judgment_action_state_hook
    assert "function persistedJudgmentActionState" in retrieval_judgment_action_state_hook
    assert "function removeJudgmentActionState" in retrieval_judgment_action_state_hook
    assert "optimisticRelevanceJudgment" in retrieval_judgment_action_state_hook
    assert "relevanceJudgmentFromPersisted" in retrieval_judgment_action_state_hook
    assert "relevanceJudgmentRating" not in retrieval_judgment_actions_hook
    assert "relevanceJudgmentRating" in retrieval_judgment_actions_model
    assert "relevanceJudgmentRating" in retrieval_judgment_payload_model
    assert "function retrievalJudgmentPayload" not in retrieval_judgment_actions_model
    assert "function retrievalJudgmentPayload" in retrieval_judgment_payload_model
    assert 'export * from "./retrieval-judgment-payload";' in retrieval_judgment_model
    assert "function optimisticRelevanceJudgment" in retrieval_judgment_actions_model
    assert "function shouldToggleOffJudgment" in retrieval_judgment_actions_model
    assert "judgmentsForRunHits" not in retrieval_search_results_panel
    assert "judgmentsForRunHits" not in retrieval_search_results_judgment_section
    assert "judgmentsForRunHits" in retrieval_search_results_view_model
    assert "function relevanceJudgmentMetrics" not in retrieval_page
    assert "function relevanceJudgmentMetrics" not in retrieval_judgment_model
    assert "function relevanceJudgmentMetrics" in retrieval_judgment_metrics_model
    assert "function relevanceJudgmentRating" not in retrieval_page
    assert "function relevanceJudgmentRating" not in retrieval_judgment_model
    assert "function relevanceJudgmentRating" in retrieval_judgment_labels_model
    assert "function judgmentsForRunHits" not in retrieval_page
    assert "function judgmentsForRunHits" not in retrieval_judgment_model
    assert "function judgmentsForRunHits" in retrieval_judgment_mapping_model
    assert "discountedCumulativeGain" not in retrieval_page
    assert "function discountedCumulativeGain" in retrieval_judgment_metrics_model
    assert "Precision@k" in retrieval_judgment_evaluation_metrics
    assert "nDCG@k" in retrieval_judgment_evaluation_metrics
    assert "Server MAP@k" in retrieval_judgment_evaluation_metrics
    assert "Server HitRate@k" in retrieval_judgment_evaluation_metrics
    assert "Server MRR@k" in retrieval_judgment_evaluation_metrics
    assert "Server nDCG@k" in retrieval_judgment_evaluation_metrics
    assert "Evaluation recommendations" in retrieval_judgment_evaluation_recommendations
    assert "EvidenceReadinessPanel" not in retrieval_search_results_panel
    assert "EvidenceReadinessPanel" in retrieval_search_results_evidence_section
    assert "./evidence-readiness-panel" in retrieval_search_results_evidence_section
    assert "function EvidenceReadinessPanel" not in retrieval_page
    assert "Evidence readiness" in retrieval_evidence_readiness_header
    assert "EvidenceReadinessHeader" in retrieval_evidence_readiness_panel
    assert "EvidenceReadinessInterpretationCard" in retrieval_evidence_readiness_panel
    assert "evidenceReadinessShellClass" in retrieval_evidence_readiness_panel
    assert "function evidenceReadinessShellClass" in retrieval_evidence_readiness_shell_class
    assert "qualitySummaryBadgeVariant" in retrieval_evidence_readiness_header
    assert "interpretation.description" in retrieval_evidence_readiness_interpretation_card
    assert "EvidenceReadinessMissingBuckets" in retrieval_evidence_readiness_panel
    assert "./evidence-readiness-missing-buckets" in retrieval_evidence_readiness_panel
    assert "evidenceReadinessView" in retrieval_evidence_readiness_panel
    assert "readinessInterpretation" not in retrieval_evidence_readiness_panel
    assert 'export * from "./evidence-readiness-view";' in retrieval_evidence_readiness_model
    assert 'export * from "./evidence-readiness-interpretation";' in retrieval_evidence_readiness_model
    assert 'export * from "./evidence-readiness-types";' in retrieval_evidence_readiness_model
    assert 'export * from "./evidence-readiness-format";' in retrieval_evidence_readiness_model
    assert "function readinessInterpretation" in retrieval_evidence_readiness_interpretation_model
    assert "function evidenceReadinessView" in retrieval_evidence_readiness_view_model
    assert "type EvidenceReadinessView" in retrieval_evidence_readiness_types_model
    assert "function formatCount" in retrieval_evidence_readiness_format_model
    assert "Blocked for governed use" in retrieval_evidence_readiness_interpretation_model
    assert "Needs human review" in retrieval_evidence_readiness_interpretation_model
    assert "Ready for evidence review" in retrieval_evidence_readiness_interpretation_model
    assert "Readiness score unavailable" in retrieval_evidence_readiness_interpretation_model
    assert "Missing {bucket.label}" in retrieval_evidence_readiness_missing_buckets
    assert "No supported filter is available for this bucket." in retrieval_evidence_readiness_missing_buckets
    assert "onApplyBucketFilter(action.field, action.value)" in retrieval_evidence_readiness_missing_buckets
    assert "RetrievalSearchCockpit" not in retrieval_search_results_panel
    assert "RetrievalSearchCockpit" in retrieval_search_results_overview_section
    assert "./retrieval-search-cockpit" in retrieval_search_results_overview_section
    assert "retrieval-cockpit-view-model" not in retrieval_search_results_panel
    assert "retrieval-cockpit-view-model" in retrieval_search_results_view_model
    assert "function RetrievalSearchCockpit" not in retrieval_page
    assert "function retrievalSearchCockpitView" not in retrieval_page
    assert "function retrievalSearchCockpitView" in retrieval_cockpit_view_model
    assert "type RetrievalSearchCockpitView" in retrieval_cockpit_view_types_model
    assert "qualitySummaryBadgeVariant" in retrieval_cockpit_quality_summary_model
    assert "qualitySummaryBadgeVariant" not in retrieval_cockpit_view_model
    assert "function requiredEvidenceBucketSummary" in retrieval_cockpit_view_derivations_model
    assert "function cockpitRouteLabel" in retrieval_cockpit_view_derivations_model
    assert "bucket.required" not in retrieval_cockpit_view_model
    assert "humanize(strategy)" not in retrieval_cockpit_view_model
    assert "humanize(strategy)" in retrieval_cockpit_view_derivations_model
    assert "queryHealthItems" in retrieval_cockpit_signals_model
    assert "searchReadinessChecklist" in retrieval_cockpit_signals_model
    assert "activeFiltersFromPayload" in retrieval_cockpit_filter_signals_model
    assert "recommendedActionFilter" in retrieval_cockpit_filter_signals_model
    assert (
        "function recommendedActionFilter"
        in retrieval_cockpit_recommended_action_filter_model
    )
    assert "function queryHealthItems" in retrieval_cockpit_query_health_model
    assert "queryHealthSignalsFromPackage" in retrieval_cockpit_query_health_model
    assert "baseQueryHealthItems" in retrieval_cockpit_query_health_model
    assert "function baseQueryHealthItems" in retrieval_cockpit_query_health_items_model
    assert '"query_specificity"' not in retrieval_cockpit_query_health_model
    assert '"query_specificity"' not in retrieval_cockpit_query_health_items_model
    assert '"query_specificity"' in retrieval_cockpit_query_health_item_builders_model
    assert "humanize" not in retrieval_cockpit_query_health_model
    assert "humanize" not in retrieval_cockpit_query_health_items_model
    assert "humanize" not in retrieval_cockpit_query_health_item_builders_model
    assert "humanize" not in retrieval_cockpit_query_health_item_policy_model
    assert "humanize" not in retrieval_cockpit_query_health_item_status_model
    assert "humanize" in retrieval_cockpit_query_health_item_descriptions_model
    assert "formatCount" not in retrieval_cockpit_query_health_model
    assert "formatCount" not in retrieval_cockpit_query_health_items_model
    assert "formatCount" not in retrieval_cockpit_query_health_item_builders_model
    assert "formatCount" not in retrieval_cockpit_query_health_item_policy_model
    assert "formatCount" not in retrieval_cockpit_query_health_item_status_model
    assert "formatCount" in retrieval_cockpit_query_health_item_descriptions_model
    assert (
        'export * from "./retrieval-cockpit-query-health-item-descriptions";'
        in retrieval_cockpit_query_health_item_policy_model
    )
    assert (
        'export * from "./retrieval-cockpit-query-health-item-status";'
        in retrieval_cockpit_query_health_item_policy_model
    )
    assert "function querySpecificityStatus" in retrieval_cockpit_query_health_item_status_model
    assert "function readinessStatus" in retrieval_cockpit_query_health_item_status_model
    assert (
        "function querySpecificityDescription"
        in retrieval_cockpit_query_health_item_descriptions_model
    )
    assert "function readinessDescription" in retrieval_cockpit_query_health_item_descriptions_model
    assert "function queryHealthSignalsFromPackage" in retrieval_cockpit_query_health_signals_model
    assert "function queryDiagnosticHealthItems" in retrieval_cockpit_query_health_diagnostics_model
    assert "type RetrievalCockpitQueryHealthItem" in retrieval_cockpit_query_health_types_model
    assert "function searchReadinessChecklist" in retrieval_cockpit_readiness_model
    assert "queryAnalysisFromPackage" in retrieval_cockpit_runtime_model
    assert "function queryAnalysisFromPackage" in retrieval_cockpit_query_runtime_model
    assert "rankingStackFromPackage" in retrieval_cockpit_runtime_model
    assert "function rankingStackFromPackage" in retrieval_cockpit_ranking_runtime_model
    assert "function fusionDiagnosticsFromPackage" in retrieval_cockpit_ranking_runtime_model
    assert "function diversityFromPackage" in retrieval_cockpit_diversity_runtime_model
    assert "function coverageGapCountFromPackage" in retrieval_cockpit_evidence_counts_model
    assert "function conceptGroundingCountFromPackage" in retrieval_cockpit_evidence_counts_model
    assert "Search cockpit" in retrieval_search_cockpit_header
    assert "SearchReadinessChecklist" not in retrieval_search_cockpit
    assert "SearchReadinessChecklist" in retrieval_search_cockpit_section_stack
    assert "./search-cockpit-panels" not in retrieval_search_cockpit
    assert "./search-cockpit-panels" in retrieval_search_cockpit_section_stack
    assert "function SearchReadinessChecklist" not in retrieval_page
    assert "Search readiness checklist" in retrieval_search_readiness_checklist
    assert "function SearchReadinessChecklist" not in retrieval_search_cockpit_panels
    assert "searchReadinessChecklist" in retrieval_cockpit_signals_model
    assert "function searchReadinessChecklist" not in retrieval_page
    assert "readiness_checklist: readinessChecklist" not in retrieval_page
    assert "readiness_checklist: searchReadinessChecklist" in retrieval_report_cockpit_readiness_model
    assert "Evidence spread" in retrieval_search_cockpit_metric_grid
    assert "Governance" not in retrieval_page
    assert "Governance" in retrieval_cockpit_readiness_model
    assert "Query transformation" in retrieval_search_cockpit_query_transformation
    assert "Next best action" in retrieval_search_cockpit_next_best_action
    assert "SearchCockpitApplyAction" in retrieval_search_cockpit_next_best_action
    assert "SearchCockpitBroadenControls" in retrieval_search_cockpit_next_best_action
    assert "Apply {filterFieldLabel" in retrieval_search_cockpit_apply_action
    assert "Clear source scope" in retrieval_search_cockpit_broaden_controls
    assert "Broaden search" in retrieval_search_cockpit_broaden_controls
    assert "hybridStackValue" not in retrieval_page
    assert "hybridStackValue" in retrieval_cockpit_view_model
    assert "function hybridStackValue" not in retrieval_page
    assert "hybridStackValue" in retrieval_runtime_stack_model
    assert "function hybridStackValue" in retrieval_runtime_ranking_labels_model
    assert 'export * from "./retrieval-runtime-ranking-labels";' in retrieval_runtime_ranking_stack_model
    assert "SearchCockpitCopyAction" in retrieval_search_cockpit_header
    assert "SearchCockpitStatusBadges" in retrieval_search_cockpit_header
    assert "Copy cockpit" in retrieval_search_cockpit_copy_action
    assert "Copy cockpit JSON" in retrieval_search_cockpit_copy_action
    assert "Cockpit JSON report help" in retrieval_search_cockpit_copy_action
    assert "useCopyFeedback" in retrieval_search_cockpit_copy_action
    assert "useState" not in retrieval_search_cockpit_copy_action
    assert "useEffect" not in retrieval_search_cockpit_copy_action
    assert "setTimeout" not in retrieval_search_cockpit_copy_action
    assert "requiredBucketBadgeView" in retrieval_search_cockpit_status_badges
    assert "coverageGapBadgeView" in retrieval_search_cockpit_status_badges
    assert "required buckets" not in retrieval_search_cockpit_status_badges
    assert "required buckets" in retrieval_search_cockpit_status_badge_view
    assert "coverage ok" not in retrieval_search_cockpit_status_badges
    assert "coverage ok" in retrieval_search_cockpit_status_badge_view
    assert "SearchCockpitHeader" in retrieval_search_cockpit
    assert "SearchCockpitSectionStack" in retrieval_search_cockpit
    assert "function SearchCockpitSectionStack" in retrieval_search_cockpit_section_stack
    assert "SearchCockpitMetricGrid" not in retrieval_search_cockpit
    assert "SearchCockpitMetricGrid" in retrieval_search_cockpit_section_stack
    assert "SearchCockpitQueryTransformation" not in retrieval_search_cockpit
    assert "SearchCockpitQueryTransformation" in retrieval_search_cockpit_section_stack
    assert "SearchCockpitNextBestAction" not in retrieval_search_cockpit
    assert "SearchCockpitNextBestAction" in retrieval_search_cockpit_section_stack
    assert "./search-cockpit-header" in retrieval_search_cockpit
    assert "./search-cockpit-section-stack" in retrieval_search_cockpit
    assert "./search-cockpit-insights" not in retrieval_search_cockpit
    assert "./search-cockpit-insights" in retrieval_search_cockpit_section_stack
    assert "function SearchCockpitMetricGrid" not in retrieval_search_cockpit_insights
    assert 'export * from "./search-cockpit-metric-grid";' in retrieval_search_cockpit_insights
    assert "retrievalCockpitReportFromPackage" not in retrieval_page
    assert "retrievalCockpitReportFromPackage" in retrieval_search_results_view_model
    assert "function retrievalCockpitReportFromPackage" not in retrieval_page
    assert "function retrievalCockpitReportFromPackage" in retrieval_report_cockpit_model
    assert "retrievalCockpitRetrievalReport(packageData)" in retrieval_report_cockpit_model
    assert "retrievalCockpitQueryAnalysisReport(" in retrieval_report_cockpit_model
    assert "retrievalCockpitRankingStackReport(packageData)" in retrieval_report_cockpit_model
    assert "retrievalCockpitReadinessReport(" in retrieval_report_cockpit_model
    assert "retrievalCockpitRulePackReport(packageData)" in retrieval_report_cockpit_model
    assert "top_evidence_ids" in retrieval_report_cockpit_retrieval_model
    assert "medical_search_hints" in retrieval_report_cockpit_query_analysis_model
    assert "hybrid_label: hybridStackValue(ranking)" in retrieval_report_cockpit_ranking_model
    assert "readiness_checklist" in retrieval_report_cockpit_readiness_model
    assert "content_hash: pack.content_hash ?? null" in retrieval_report_cockpit_rule_packs_model
    assert "source_signal_codes" in retrieval_report_cockpit_strategy_model
    assert "retrievalCockpitEvidenceHitReports" not in retrieval_page
    assert "retrievalCockpitEvidenceHitReports" in retrieval_report_cockpit_model
    assert "function retrievalCockpitEvidenceHitReports" in retrieval_report_evidence_hits_model
    assert "evidence_hits" not in retrieval_page
    assert "evidence_hits" in retrieval_report_cockpit_model
    assert 'report_type: "retrieval_cockpit"' not in retrieval_page
    assert 'report_type: "retrieval_cockpit"' in retrieval_report_cockpit_model
    assert "interpretation: retrievalInterpretationReport(packageData)" not in retrieval_page
    assert "interpretation: retrievalInterpretationReport(packageData)" in retrieval_report_cockpit_model
    assert "RecommendedActionsPanel" not in retrieval_search_results_panel
    assert "RecommendedActionsPanel" in retrieval_search_results_overview_section
    assert "./recommended-actions-panel" in retrieval_search_results_overview_section
    assert "function RecommendedActionsPanel" not in retrieval_page
    assert "RecommendedActionsHeader" in retrieval_recommended_actions_panel
    assert "./recommended-actions-header" in retrieval_recommended_actions_panel
    assert "RecommendedActionCard" in retrieval_recommended_actions_panel
    assert "./recommended-action-card" in retrieval_recommended_actions_panel
    assert "Corrective actions" in retrieval_recommended_actions_panel
    assert "Corrective actions" in retrieval_recommended_actions_header
    assert "Backend-derived next steps" not in retrieval_recommended_actions_panel
    assert "Backend-derived next steps" in retrieval_recommended_actions_header
    assert "packageData.recommended_actions ?? []" in retrieval_search_results_overview_section
    assert "recommendedActionFilter" not in retrieval_page
    assert "recommendedActionFilter" in retrieval_page_trace_props
    assert "function recommendedActionFilter" not in retrieval_page
    assert "function recommendedActionFilter" in retrieval_cockpit_recommended_action_filter_model
    assert "recommendedActionSourceLabel" in retrieval_search_run_labels_model
    assert "corrective_rule_source" in retrieval_search_run_labels_model
    assert "query diagnostic" in retrieval_search_run_labels_model
    assert "RecommendedActionCardHeader" in retrieval_recommended_action_card
    assert "RecommendedActionFilterSummary" in retrieval_recommended_action_card
    assert "qualitySignalBadgeVariant" in retrieval_recommended_action_card_header
    assert "source_signal_codes" in retrieval_recommended_action_card_header
    assert "sourceLabel" in retrieval_recommended_action_card_header
    assert "formatFilterValue(filterAction.field, filterAction.value)" in (
        retrieval_recommended_action_filter_summary
    )
    assert "RecommendedActionBroadenControls" in retrieval_recommended_action_card
    assert (
        "./recommended-action-broaden-controls"
        in retrieval_recommended_action_card
    )
    assert "Broaden search" not in retrieval_recommended_action_card
    assert "Broaden search" in retrieval_recommended_action_broaden_controls
    assert "Clear source scope" in retrieval_recommended_action_broaden_controls
    assert 'action.action_type === "broaden_query"' not in retrieval_recommended_actions_panel
    assert 'action.action_type === "broaden_query"' in retrieval_recommended_action_card
    assert "correctiveActionSummaryFromPackage" in retrieval_run_actions_model
    assert "packageData.recommended_action_summary" in retrieval_run_actions_model
    assert "correctiveActionSummary: CorrectiveActionSummary" in retrieval_run_summary_types_model
    assert "recommendedActionTypeCounts" in retrieval_run_actions_model
    assert "recommendedActionTypeCounts" not in retrieval_recommended_actions_panel
    assert "recommendedActionTypeCounts" in retrieval_recommended_actions_panel_model
    assert "formatRecommendedActionCount" in retrieval_recommended_actions_header
    assert "function correctiveActionSummaryFromPackage" not in retrieval_page
    assert "CorrectiveActionTypeCountChips" in retrieval_search_run_history_row_badges
    assert "./corrective-action-type-count-chips" in retrieval_search_run_history_row_badges
    assert "function CorrectiveActionTypeCountChips" not in retrieval_page
    assert "correctiveActionTypeCountEntries" in retrieval_search_run_remediation_model
    assert "correctiveActionTypeCountEntries" in retrieval_corrective_action_model
    assert "action types" in retrieval_corrective_action_chips
    assert (
        "counts={run.summary.correctiveActionSummary.actionTypeCounts}"
        in retrieval_search_run_history_row_badges
    )
    assert "action_type_counts" in retrieval_run_actions_model
    assert "broaden_query_count" in retrieval_run_actions_model
    assert "actionTypeCounts" in retrieval_run_actions_model
    assert "broadenQueryCount" in retrieval_run_actions_model
    assert "Top action:" in retrieval_search_run_history_row_details
    assert "missing_required_evidence_buckets" in retrieval_evidence_readiness_view_model
    assert "qualitySummaryBadgeVariant" in retrieval_search_run_quality_model
    assert "function qualitySummaryBadgeVariant" not in retrieval_page
    assert "bucketSuggestedFilter" not in retrieval_search_results_panel
    assert "bucketSuggestedFilter" in retrieval_search_results_evidence_section
    assert "onApplyBucketFilter" not in retrieval_search_results_panel
    assert "onApplyBucketFilter" in retrieval_search_results_evidence_section
    assert "bucket.suggested_filter" not in retrieval_page
    assert "bucket.suggested_filter" in retrieval_filter_suggestions_model
    assert "EvidencePackBuckets" not in retrieval_search_results_panel
    assert "EvidencePackBuckets" in retrieval_search_results_evidence_section
    assert "./evidence-pack-buckets" in retrieval_search_results_evidence_section
    assert "function EvidencePackBuckets" not in retrieval_page
    assert "Evidence pack" in retrieval_evidence_pack_buckets
    assert "packageData.evidence_buckets ?? []" in retrieval_search_results_evidence_section
    assert "missingRequiredCount" in retrieval_evidence_pack_buckets
    assert "required gap" in retrieval_evidence_pack_buckets
    assert "EvidenceSupportMatrix" not in retrieval_search_results_panel
    assert "EvidenceSupportMatrix" in retrieval_search_results_evidence_section
    assert "./evidence-support-matrix" in retrieval_search_results_evidence_section
    assert "function EvidenceSupportMatrix" not in retrieval_page
    assert "Evidence support matrix" in retrieval_evidence_support_matrix
    assert "Evidence support matrix help" in retrieval_evidence_support_matrix
    assert "Weak rows need inspection before use" in retrieval_evidence_support_matrix
    assert "evidenceSupportMatrixRows" not in retrieval_search_results_panel
    assert "evidenceSupportMatrixRows" in retrieval_search_results_view_model
    assert "HitMatchExplanationPanel" in retrieval_hit_card_evidence_section
    assert "function HitMatchExplanationPanel" not in retrieval_evidence_interpretation_guidance
    assert "Why this matched" in retrieval_hit_match_explanation_panel
    assert "HitMatchExplanationMetric" in retrieval_hit_match_explanation_panel
    assert "./hit-match-explanation-metric" in retrieval_hit_match_explanation_panel
    assert "function HitMatchExplanationMetric" in retrieval_hit_match_explanation_metric
    assert "function MatchExplanationMetric" not in retrieval_hit_match_explanation_panel
    assert "rounded-md border border-border bg-card/70" not in retrieval_hit_match_explanation_panel
    assert "rounded-md border border-border bg-card/70" in retrieval_hit_match_explanation_metric
    assert "hitMatchExplanation" not in retrieval_page
    assert "function evidenceSignalsFromHit" in retrieval_evidence_hit_signals_model
    assert "hitMatchExplanation" in retrieval_evidence_match_explanation_model
    assert "match_explanation" not in retrieval_page
    assert "match_explanation" in retrieval_report_evidence_hits_model
    assert "match_explanation?: Record<string, unknown>" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "backendExplanation" not in retrieval_page
    assert "backendExplanation" in retrieval_evidence_match_explanation_backend_model
    assert "function backendMatchExplanationValues" in retrieval_evidence_match_explanation_backend_model
    assert "backendMatchExplanationValues" in retrieval_evidence_match_explanation_model
    assert "fallbackMatchExplanationValues" in retrieval_evidence_match_explanation_model
    assert "function fallbackMatchExplanationValues" in retrieval_evidence_match_explanation_fallback_model
    assert "mergeMatchExplanationValues" in retrieval_evidence_match_explanation_model
    assert "function mergeMatchExplanationValues" in retrieval_evidence_match_explanation_merge_model
    assert "matchExplanationArrayValue" not in retrieval_evidence_match_explanation_model
    assert "function matchExplanationArrayValue" not in retrieval_evidence_match_explanation_fallback_model
    assert "function matchExplanationArrayValue" in retrieval_evidence_match_explanation_merge_model
    assert "evidenceSupportStatus" not in retrieval_evidence_match_explanation_model
    assert "evidenceSupportStatus" in retrieval_evidence_match_explanation_merge_model
    assert "aspectIds" in retrieval_evidence_match_explanation_fallback_model
    assert "bucketIds" in retrieval_evidence_match_explanation_fallback_model
    assert "conceptIds" in retrieval_evidence_match_explanation_fallback_model
    assert "provenanceFields" in retrieval_evidence_match_explanation_fallback_model
    assert "rankingSignalRuleIds" in retrieval_evidence_match_explanation_fallback_model
    assert "topScoreComponentValue" in retrieval_evidence_match_explanation_fallback_model
    assert "function topScoreComponentValue" in retrieval_evidence_match_explanation_values_model
    assert "function matchedBucketLabels" in retrieval_evidence_match_explanation_values_model
    assert "function matchedBucketIds" in retrieval_evidence_match_explanation_values_model
    assert "evidenceReportFromHit(" not in retrieval_hit_card_view_model
    assert "evidenceReportFromHit(" in retrieval_hit_card_report_model
    assert "judgment," in retrieval_hit_card_copy_hook
    assert "Top driver" in retrieval_hit_match_explanation_panel
    assert "function supportStatusBadgeVariant" in retrieval_evidence_support_status
    assert "Evidence pack" in retrieval_evidence_pack_buckets
    assert "evidenceBucketLabelsByEvidenceId" not in retrieval_page
    assert "evidenceBucketLabelsByEvidenceId" in retrieval_evidence_implementation
    assert "evidenceSupportStatus" in retrieval_evidence_implementation
    assert '"source_id"' not in retrieval_page
    assert '"source_id"' in retrieval_page_trace_props
    assert "SourceScopePicker" not in retrieval_query_builder_panel
    assert "SourceScopePicker" in retrieval_query_builder_form_content
    assert "./source-scope-picker" not in retrieval_query_builder_panel
    assert "./source-scope-picker" in retrieval_query_builder_form_content
    assert "function SourceScopePicker" not in retrieval_page
    assert "Exact source scope" in retrieval_source_scope_picker
    assert "Exact source scope help" in retrieval_source_scope_picker
    assert "SourceScopeStatusNotice" in retrieval_source_scope_picker
    assert "useSourceScopePickerState" in retrieval_source_scope_picker
    assert "function useSourceScopePickerState" in retrieval_source_scope_picker_state_hook
    assert "getVisibleSourceOptions" not in retrieval_source_scope_picker
    assert "getVisibleSourceOptions" in retrieval_source_scope_picker_state_hook
    assert "Search is constrained to one exact source" not in retrieval_source_scope_picker
    assert "Search is constrained to one exact source" in retrieval_source_scope_status_notice
    assert "applied exact source" in retrieval_source_scope_option_row
    assert "sourceMatchesSearch" in retrieval_source_scope_picker_format
    assert "sourceMatchesSearch" not in retrieval_source_scope_picker
    assert "onUseSource" not in retrieval_page
    assert "onUseSource" in retrieval_page_results_column_props
    assert "Use source" in retrieval_source_card
    assert "payload.filters?.source_id" in retrieval_form_payload_actions_hook
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
    assert "StrategyRecommendationsPanel" not in retrieval_search_cockpit
    assert "StrategyRecommendationsPanel" in retrieval_search_cockpit_section_stack
    assert "function StrategyRecommendationsPanel" not in retrieval_page
    assert "StrategyRecommendationsPanel" in retrieval_strategy_standard_panels
    assert "StrategyRecommendationCard" in retrieval_strategy_recommendations_panel
    assert "function StrategyRecommendationCard" in retrieval_strategy_recommendation_card
    assert "Strategy recommendations" in retrieval_strategy_recommendations_panel
    assert (
        "getSuggestedFilterAction(recommendation.suggested_filters)"
        in retrieval_strategy_recommendation_card
    )
    assert "strategyRecommendations: packageData.strategy_recommendations ?? []" in retrieval_cockpit_view_model
    assert "Copy eval" not in retrieval_page
    assert "Copy evaluation JSON" in retrieval_judgment_evaluation_copy_action
    assert (
        "Copy retrieval judgment evaluation report"
        in retrieval_judgment_evaluation_copy_action
    )
    assert "Judgment evaluation JSON report help" in retrieval_judgment_evaluation_copy_action
    assert "useCopyFeedback" in retrieval_judgment_evaluation_copy_hook
    assert "useState" not in retrieval_judgment_evaluation_copy_hook
    assert "useEffect" not in retrieval_judgment_evaluation_copy_hook
    assert "window.setTimeout" not in retrieval_judgment_evaluation_copy_hook
    assert "window.setTimeout" not in retrieval_judgment_evaluation_panels
    assert "JudgmentEvaluationDetailStack" in retrieval_judgment_evaluation_panels
    assert "EvaluationReadinessPanel" in retrieval_judgment_evaluation_detail_stack
    assert "JudgmentEvaluationOutcomeBadges" in retrieval_judgment_evaluation_detail_stack
    assert "./judgment-evaluation-panels" in retrieval_search_results_judgment_section
    assert "function EvaluationReadinessPanel" not in retrieval_page
    assert "function JudgmentMetricCard" not in retrieval_page
    assert "Judgment evaluation readiness" in retrieval_judgment_evaluation_readiness
    assert "evaluationReadinessVariant" in retrieval_judgment_evaluation_readiness
    assert "usable_with_gaps" in retrieval_judgment_evaluation_readiness
    assert "Judgment readiness help" in retrieval_judgment_evaluation_readiness
    assert "evaluation_readiness: evaluation.evaluation_readiness" not in retrieval_page
    assert "evaluation_readiness: evaluation.evaluation_readiness" in retrieval_judgment_report_model
    assert "evaluationReadinessVariant" not in retrieval_page
    assert "evaluationReadinessClass" not in retrieval_page
    assert "evaluationReportFromJudgmentSummary" not in retrieval_search_results_panel
    assert (
        "evaluationReportFromJudgmentSummary"
        in retrieval_search_results_judgment_section
    )
    assert "function evaluationReportFromJudgmentSummary" not in retrieval_page
    assert "function evaluationReportFromJudgmentSummary" not in retrieval_judgment_model
    assert "function evaluationReportFromJudgmentSummary" in retrieval_judgment_report_model
    assert "retrieval_judgment_evaluation" not in retrieval_page
    assert "retrieval_judgment_evaluation" in retrieval_judgment_report_model
    assert "correctiveActionReportContext" not in retrieval_page
    assert "correctiveActionReportContext" in retrieval_evidence_implementation
    assert "corrective_actions: correctiveActions" in retrieval_evidence_implementation
    assert "package_top_actions" in retrieval_evidence_implementation
    assert 'export * from "./retrieval-evidence-corrective-actions-report";' in retrieval_evidence_model
    assert "runSummary.remediationSummary ?? searchRunRemediationSummary(runSummary)" not in retrieval_page
    assert "runSummary.remediationSummary ?? searchRunRemediationSummary(runSummary)" in retrieval_report_cockpit_model
    assert "run.summary.remediationSummary ?? searchRunRemediationSummary(run.summary)" in retrieval_search_run_evidence_summary
    assert "retrievalRulePacksFromPackage" in retrieval_run_rule_packs_model
    assert "function retrievalRulePacksFromPackage" not in retrieval_page
    assert "function retrievalRulePacksFromPackage" in retrieval_run_rule_packs_model
    assert "retrieval_rule_packs" not in retrieval_page
    assert "retrieval_rule_packs" in retrieval_report_cockpit_model
    assert "content_hash" not in retrieval_page
    assert "content_hash" in retrieval_report_cockpit_rule_packs_model
    assert "retrieval_rule_packs?: RuntimeRetrievalRulePack[]" in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "recommendations" in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert "persistedJudgmentEvaluation" not in retrieval_page
    assert "persistedJudgmentEvaluation" in retrieval_page_search_results_props
    assert "average_precision_at_k" not in retrieval_page
    assert "average_precision_at_k" in retrieval_judgment_report_model
    assert "hit_rate_at_k" not in retrieval_page
    assert "hit_rate_at_k" in retrieval_judgment_report_model
    assert "mrr_at_k" not in retrieval_page
    assert "mrr_at_k" in retrieval_judgment_report_model
    assert "judgmentCoverage" not in retrieval_page
    assert "judgmentCoverage" in retrieval_judgment_metrics_model
    assert "judgedPrecision" not in retrieval_page
    assert "judgedPrecision" in retrieval_judgment_metrics_model
    assert "not_relevant" not in retrieval_page
    assert "not_relevant" in retrieval_judgment_metrics_model
    assert "judgment-aware metrics" in frontend_architecture
    assert "labels are for the" in frontend_architecture
    assert "share of hits judged" in frontend_architecture
    assert "evaluation_readiness" in frontend_architecture
    assert "low confidence" in frontend_architecture
    assert "/retrieval/judgments" in frontend_architecture
    assert "/retrieval/judgments/summary" in frontend_architecture
    assert "/retrieval/judgments/evaluate" in frontend_architecture
    assert "stored label" in retrieval_judgment_evaluation_badges
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
    assert "QueryHealthPanel" not in retrieval_search_cockpit
    assert "QueryHealthPanel" in retrieval_search_cockpit_section_stack
    assert "function QueryHealthPanel" not in retrieval_page
    assert "Query health" in retrieval_query_health_panel
    assert "Query health help" in retrieval_query_health_panel
    assert "QueryHealthItemCard" in retrieval_query_health_panel
    assert "function QueryHealthItemCard" in retrieval_query_health_item_card
    assert "function QueryHealthPanel" not in retrieval_search_cockpit_panels
    assert "function queryHealthOverallLabel" in retrieval_query_health_status
    assert "function CockpitMetricCard" in retrieval_cockpit_metric_card
    assert "queryHealthItems" in retrieval_cockpit_signals_model
    assert "queryHealthItems" in retrieval_cockpit_query_health_model
    assert "function queryHealthItems" not in retrieval_page
    assert "queryDiagnosticHealthItems" not in retrieval_page
    assert "DiagnosticMetadataChips" in retrieval_query_diagnostic_row
    assert "metadata: recordValue(item.metadata)" in retrieval_query_analysis_diagnostic_values_model
    assert "stringRecordValue" in retrieval_query_analysis_coercion_model
    assert "metadata: diagnostic.metadata" not in retrieval_page
    assert "metadata: diagnostic.metadata" in retrieval_report_cockpit_query_analysis_model
    assert "active_metadata_filters" in retrieval_query_diagnostic_metadata
    assert "suggested_standards" in retrieval_query_diagnostic_metadata
    assert "diagnostic_${diagnostic.code}" not in retrieval_page
    assert "diagnostic_${diagnostic.code}" in retrieval_cockpit_query_health_diagnostics_model
    assert "Filter over-constraint" not in retrieval_page
    assert "Filter over-constraint" in retrieval_cockpit_query_health_diagnostics_model
    assert "overconstrained_metadata_filters" not in retrieval_page
    assert "overconstrained_metadata_filters" in retrieval_cockpit_query_health_diagnostics_model
    assert "diagnostic_overconstrained_metadata_filters" in retrieval_query_health_item_card
    assert "Clear source scope" in retrieval_query_health_item_card
    assert "Broaden search" in retrieval_query_health_item_card
    assert "onClearAllFilters" not in retrieval_page
    assert "onClearAllFilters" not in retrieval_page_query_column_props
    assert "onClearAllFilters" in retrieval_page_query_builder_props
    assert "onClearFilter" not in retrieval_page
    assert "onClearFilter" in retrieval_page_search_results_props
    assert "queryHealthBadgeVariant" in retrieval_query_health_status
    assert "queryHealthBadgeVariant" not in retrieval_page
    assert "queryHealthOverallLabel" in retrieval_query_health_status
    assert "queryHealthOverallLabel" not in retrieval_page
    assert "Query specificity" not in retrieval_page
    assert "Query specificity" not in retrieval_cockpit_query_health_model
    assert "Query specificity" not in retrieval_cockpit_query_health_items_model
    assert "Query specificity" in retrieval_cockpit_query_health_item_builders_model
    assert "The query has enough wording" in retrieval_cockpit_query_health_item_descriptions_model
    assert "The query has enough wording" not in retrieval_cockpit_query_health_item_builders_model
    assert "Clinical context" not in retrieval_page
    assert "Clinical context" not in retrieval_cockpit_query_health_model
    assert "Clinical context" not in retrieval_cockpit_query_health_items_model
    assert "Clinical context" in retrieval_cockpit_query_health_item_builders_model
    assert "No clinical data context is set" in retrieval_cockpit_query_health_item_descriptions_model
    assert "No clinical data context is set" not in retrieval_cockpit_query_health_item_builders_model
    assert "Search scope" not in retrieval_page
    assert "Search scope" not in retrieval_cockpit_query_health_model
    assert "Search scope" not in retrieval_cockpit_query_health_items_model
    assert "Search scope" in retrieval_cockpit_query_health_item_builders_model
    assert "Exact source scope is active" in retrieval_cockpit_query_health_item_descriptions_model
    assert "Exact source scope is active" not in retrieval_cockpit_query_health_item_builders_model
    assert "Result coverage" not in retrieval_page
    assert "Result coverage" not in retrieval_cockpit_query_health_model
    assert "Result coverage" not in retrieval_cockpit_query_health_items_model
    assert "Result coverage" in retrieval_cockpit_query_health_item_builders_model
    assert "No ranked evidence returned" in retrieval_cockpit_query_health_item_descriptions_model
    assert "No ranked evidence returned" not in retrieval_cockpit_query_health_item_builders_model
    assert "ResultFacets" not in retrieval_search_results_panel
    assert "ResultFacets" in retrieval_search_results_evidence_section
    assert "./result-facets" in retrieval_search_results_evidence_section
    assert "function ResultFacets" not in retrieval_page
    assert "Result facets" in retrieval_result_facets
    assert "click to refine" in retrieval_result_facets
    assert "ResultFacetBucketButton" in retrieval_result_facets
    assert "resultFacetSections" in retrieval_result_facets
    assert "function resultFacetSections" in retrieval_result_facet_sections
    assert "aria-pressed={applied}" in retrieval_result_facet_bucket_button
    assert "Apply ${label}=${displayValue}" in retrieval_result_facet_bucket_button
    assert "type ResultFacetFilterField" in retrieval_result_facet_types
    assert "Safety signals" not in retrieval_page
    assert "Safety signals" not in retrieval_cockpit_query_health_model
    assert "Safety signals" not in retrieval_cockpit_query_health_items_model
    assert "Safety signals" in retrieval_cockpit_query_health_item_builders_model
    assert "safetySignalsDescription" in retrieval_cockpit_query_health_item_descriptions_model
    assert "warning or safety signal" not in retrieval_cockpit_query_health_item_builders_model
    assert "query_health: queryHealth" not in retrieval_page
    assert "query_health: queryHealthItems" in retrieval_report_cockpit_query_analysis_model
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
    assert "isJudgmentSyncing" in retrieval_judgment_session_hook
    assert "restoreSubmittedSearch" not in retrieval_page
    assert "restoreSubmittedSearch" in retrieval_page_search_results_props
    assert "onRestoreSubmittedSearch" not in retrieval_page
    assert "onRestoreSubmittedSearch" in retrieval_page_search_results_props
    assert "displayed request" in retrieval_submitted_search_summary_header
    assert "useRetrievalPresetsQuery" not in retrieval_page
    assert "useRetrievalPresetsQuery" in retrieval_page_controller_hook
    assert "SearchPresetStrip" not in retrieval_query_builder_panel
    assert "SearchPresetStrip" in retrieval_query_builder_form_content
    assert "./search-preset-strip" not in retrieval_query_builder_panel
    assert "./search-preset-strip" in retrieval_query_builder_form_content
    assert "function SearchPresetStrip" not in retrieval_page
    assert "SearchPresetHeader" in retrieval_search_preset_strip
    assert "Search presets" not in retrieval_search_preset_strip
    assert "Search presets" in retrieval_search_preset_header
    assert "Filter retrieval presets" in retrieval_search_preset_strip
    assert "SearchPresetCard" in retrieval_search_preset_strip
    assert "./search-preset-card" in retrieval_search_preset_strip
    assert "SearchPresetCategoryFilter" in retrieval_search_preset_strip
    assert "./search-preset-category-filter" in retrieval_search_preset_strip
    assert "presetMatchesSearch" not in retrieval_search_preset_strip
    assert "presetMatchesSearch" in retrieval_search_preset_filter_model
    assert "filterSearchPresets" not in retrieval_search_preset_strip
    assert "filterSearchPresets" in retrieval_search_preset_strip_state_hook
    assert "function filterSearchPresets" in retrieval_search_preset_filter_model
    assert "presetFilterClass" not in retrieval_search_preset_strip
    assert "function presetFilterClass" in retrieval_search_preset_category_filter
    assert "activePresetId" not in retrieval_page
    assert "activePresetId" not in retrieval_page_query_column_props
    assert "activePresetId" in retrieval_page_query_builder_props
    assert "Loading retrieval presets" in retrieval_search_preset_strip
    assert "data-driven" in retrieval_search_preset_header
    assert "useRetrievalSearchOptionsQuery" not in retrieval_page
    assert "useRetrievalSearchOptionsQuery" in retrieval_page_controller_hook
    assert "retrievalQueryBuilderOptionsView" not in retrieval_page
    assert "retrievalQueryBuilderOptionsView" not in retrieval_page_query_column_props
    assert "retrievalQueryBuilderOptionsView" in retrieval_page_query_builder_props
    assert "function retrievalQueryBuilderOptionsView" in retrieval_search_options_model
    assert "formatOptions" in retrieval_search_options_model
    assert "selectedSource" in retrieval_search_options_model
    assert "mergeSearchOptions" in retrieval_search_options_model
    assert "uniqueNumberValues" in retrieval_search_options_model
    assert "function mergeSearchOptions" not in retrieval_page
    assert "function uniqueNumberValues" not in retrieval_page
    assert "categoryFilter" in retrieval_search_preset_strip
    assert "categoryFilter" in retrieval_search_preset_strip_state_hook
    assert "presetSearch" in retrieval_search_preset_strip
    assert "presetSearch" in retrieval_search_preset_strip_state_hook
    assert "useSearchPresetStripState" in retrieval_search_preset_strip
    assert "function useSearchPresetStripState" in retrieval_search_preset_strip_state_hook
    assert "presetMatchesSearch" not in retrieval_page
    assert "Filter retrieval presets" in retrieval_search_preset_strip
    assert "Preset categories" not in retrieval_search_preset_strip
    assert "Preset categories" in retrieval_search_preset_category_filter
    assert "top {preset.top_k}" not in retrieval_search_preset_strip
    assert "top {preset.top_k}" in retrieval_search_preset_card
    assert "SourceInventoryPanel" in retrieval_results_column
    assert "./source-inventory-panel" in retrieval_results_column
    assert "components/source-inventory-panel" not in retrieval_page
    assert "function SourcesPanel" not in retrieval_page
    assert "filters" in retrieval_source_inventory_panel
    assert "filters" in retrieval_source_inventory_panel_state_hook
    assert "useSourceInventoryPanelState" in retrieval_source_inventory_panel
    assert "function useSourceInventoryPanelState" in retrieval_source_inventory_panel_state_hook
    assert "SourceInventoryFilterControls" in retrieval_source_inventory_panel
    assert "./source-inventory-filter-controls" in retrieval_source_inventory_panel
    assert "SourceInventorySourceList" in retrieval_source_inventory_panel
    assert "SourceCard" in retrieval_source_inventory_source_list
    assert "./source-card" in retrieval_source_inventory_source_list
    assert "sourceMatchesInventoryFilters" not in retrieval_source_inventory_panel
    assert "filteredSourcesForInventory" not in retrieval_source_inventory_panel
    assert "filteredSourcesForInventory" in retrieval_source_inventory_panel_state_hook
    assert 'export * from "./retrieval-source-inventory-filters";' in retrieval_source_inventory_model
    assert 'export * from "./retrieval-source-inventory-readiness";' in retrieval_source_inventory_model
    assert 'export * from "./retrieval-source-inventory-types";' in retrieval_source_inventory_model
    assert "type SourceInventoryFilters" in retrieval_source_inventory_types_model
    assert "type SourceInventoryReadiness" in retrieval_source_inventory_types_model
    assert "function uniqueSourceInventoryValues" in retrieval_source_inventory_values_model
    assert "function sourceMatchesInventoryFilters" in retrieval_source_inventory_filters_model
    assert "Filter trusted sources" in retrieval_source_inventory_filter_controls
    assert "SourceInventoryFilterHeader" in retrieval_source_inventory_filter_controls
    assert "SourceFilterChipGroup" in retrieval_source_inventory_filter_controls
    assert "Source inventory filters" in retrieval_source_inventory_filter_header
    assert "function SourceFilterChipGroup" in retrieval_source_filter_chip_group
    assert "function sourceFilterChipClass" in retrieval_source_filter_chip_class
    assert "SourceInventoryReadinessPanel" in retrieval_source_inventory_panel
    assert "./source-inventory-readiness-panel" in retrieval_source_inventory_panel
    assert "Source inventory readiness" in retrieval_source_inventory_readiness_panel
    assert "Source readiness" in retrieval_source_inventory_readiness_panel
    assert "Source readiness help" in retrieval_source_inventory_readiness_panel
    assert "sourceInventoryReadiness" not in retrieval_source_inventory_panel
    assert "sourceInventoryReadiness" in retrieval_source_inventory_panel_state_hook
    assert "function sourceInventoryReadiness" in retrieval_source_inventory_readiness_model
    assert "sourceInventoryReadinessMessage" in retrieval_source_inventory_readiness_panel
    assert "function sourceInventoryReadinessMessage" in retrieval_source_inventory_readiness_model
    assert "filtered inventory" in retrieval_source_inventory_readiness_panel
    assert "all shown sources have chunks" in retrieval_source_inventory_readiness_panel
    assert "No trusted sources are loaded" in retrieval_source_inventory_readiness_model
    assert "SourceInventoryHeader" in retrieval_source_inventory_panel
    assert "SourceInventorySourceList" in retrieval_source_inventory_panel
    assert "Trusted sources help" in retrieval_source_inventory_header
    assert "Clear filters" in retrieval_source_inventory_header
    assert "Inventory filters only inspect available sources" in retrieval_source_inventory_panel
    assert "No sources match the current filters." in retrieval_source_inventory_source_list
    assert "No retrieval sources indexed." in retrieval_source_inventory_source_list
    assert "Use source" in retrieval_source_card
    assert '<option value="csv">CSV</option>' not in retrieval_page
    assert '<option value="fhir_like">FHIR-like</option>' not in retrieval_page
    assert "defaultQuery" not in retrieval_page
    assert "activeFilterEntriesForSearch" not in retrieval_page
    assert "activeFilterEntriesForSearch" in retrieval_page_trace_props
    assert "activeFacetFiltersFromPayload" not in retrieval_page
    assert "function activeFilterEntriesForSearch" in retrieval_filter_active_model
    assert "function activeFacetFiltersFromPayload" not in retrieval_page
    assert "function activeFacetFiltersFromPayload" in retrieval_filter_active_model
    assert "onApplyFacet" not in retrieval_page
    assert "onApplyFacet" in retrieval_page_search_results_props
    assert "aria-pressed={applied}" in retrieval_result_facet_bucket_button
    assert "supportedSuggestionFilterFields" in retrieval_filter_types_model
    assert "onApplyFilterSuggestion" in retrieval_page_trace_props
    assert "FilterSuggestionList" in retrieval_query_analysis_block
    assert "./filter-suggestion-list" in retrieval_query_analysis_block
    assert "function FilterSuggestionList" not in retrieval_page
    assert "Suggested filters" in retrieval_filter_suggestion_list
    assert "isSuggestionSupported" in retrieval_filter_suggestion_list
    assert "Apply" in retrieval_filter_suggestion_list
    assert "coverageSuggestedFilter" not in retrieval_page
    assert "coverageSuggestedFilter" in retrieval_page_trace_props
    assert "function coverageSuggestedFilter" not in retrieval_page
    assert "function coverageSuggestedFilter" in retrieval_filter_suggestions_model
    assert "coverageSuggestedAction" not in retrieval_page
    assert "coverageSuggestedAction" in retrieval_page_trace_props
    assert "function coverageSuggestedAction" not in retrieval_page
    assert "function coverageSuggestedAction" in retrieval_filter_suggestions_model
    assert "CoverageDiagnosticsPanel" in retrieval_trace_content
    assert "./coverage-diagnostics-panel" in retrieval_trace_content
    assert "function CoverageDiagnosticsBlock" not in retrieval_page
    assert "CoverageDiagnosticsItemList" not in retrieval_page
    assert "CoverageDiagnosticsItemList" in retrieval_coverage_diagnostics_panel
    assert "CoverageDiagnosticsItemRow" in retrieval_coverage_diagnostics_item_list
    assert "Aspect coverage" in retrieval_coverage_diagnostics_panel
    assert "coverage?.query_aspects" in retrieval_coverage_diagnostics_panel
    assert "Coverage diagnostics" in retrieval_coverage_diagnostics_header
    assert "getCoverageSuggestedFilter" in retrieval_coverage_diagnostics_panel
    assert "getCoverageSuggestedFilter(item)" in retrieval_coverage_diagnostics_item_row
    assert "Apply {actionHelpers.filterFieldLabel" in retrieval_coverage_diagnostics_item_row
    assert "suggested_filter" in retrieval_filter_suggestions_model
    assert "onApplyCoverageFilter" not in retrieval_page
    assert "onApplyCoverageFilter" in retrieval_page_trace_props
    assert "Copy medical search hint" in retrieval_search_hint_card
    assert "Open medical search hint" in retrieval_search_hint_card
    assert "launchable hint" in retrieval_search_hint_card
    assert "copyTextToClipboard" in retrieval_search_hint_list
    assert "./copy-feedback" in retrieval_search_hint_list
    assert "copyTextToClipboard" not in retrieval_page
    assert "copyTextToClipboard" not in retrieval_page_query_column_props
    assert "copyTextToClipboard" in retrieval_page_search_run_history_props
    assert "retrievalPageQueryBuilderProps" in retrieval_page_query_column_props
    assert "retrievalPageSearchPlanPreviewProps" in retrieval_page_query_column_props
    assert "retrievalPageSearchRunHistoryProps" in retrieval_page_query_column_props
    assert (
        "function retrievalPageSearchRunHistoryProps"
        in retrieval_page_search_run_history_props
    )
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
    app = (FRONTEND_SRC / "App.tsx").read_text(encoding="utf-8")
    auth_provider = AUTH_PROVIDER.read_text(encoding="utf-8")
    assistant_page = ASSISTANT_PAGE.read_text(encoding="utf-8")
    assistant_attachments = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-attachments.ts"
    ).read_text(encoding="utf-8")
    assistant_empty_state = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-empty-state.tsx"
    ).read_text(encoding="utf-8")
    assistant_inline_guide = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-inline-guide.tsx"
    ).read_text(encoding="utf-8")
    assistant_input_panels = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-input-panels.tsx"
    ).read_text(encoding="utf-8")
    assistant_response_details = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-response-details.tsx"
    ).read_text(encoding="utf-8")
    assistant_response_model = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-response-model.ts"
    ).read_text(encoding="utf-8")
    assistant_live_timeline = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-live-timeline.tsx"
    ).read_text(encoding="utf-8")
    assistant_live_timeline_model = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-live-timeline-model.ts"
    ).read_text(encoding="utf-8")
    assistant_session = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-session.ts"
    ).read_text(encoding="utf-8")
    assistant_session_sidebar = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-session-sidebar.tsx"
    ).read_text(encoding="utf-8")
    assistant_tool_catalog = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-tool-catalog-panel.tsx"
    ).read_text(encoding="utf-8")
    evidence_links = (FRONTEND_SRC / "lib" / "evidence-links.ts").read_text(
        encoding="utf-8"
    )
    hash_scroll_hook = (FRONTEND_SRC / "lib" / "use-hash-target-scroll.ts").read_text(
        encoding="utf-8"
    )
    retrieval_hit_card = (
        FRONTEND_SRC / "features" / "retrieval" / "components" / "hit-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results = (
        FRONTEND_SRC / "features" / "retrieval" / "components" / "search-results-panel.tsx"
    ).read_text(encoding="utf-8")
    workflow_detail = (
        FRONTEND_SRC / "features" / "workflows" / "workflow-detail.tsx"
    ).read_text(encoding="utf-8")
    workflow_detail_sections = (
        FRONTEND_SRC / "features" / "workflows" / "workflow-detail-sections.tsx"
    ).read_text(encoding="utf-8")
    app_shell = APP_SHELL.read_text(encoding="utf-8")
    api_module = API_MODULE.read_text(encoding="utf-8")
    server_state = (FRONTEND_SRC / "lib" / "server-state.ts").read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )

    assert '<Navigate to="/assistant" />' in app
    assert 'window.history.replaceState({}, document.title, "/assistant")' in auth_provider
    assert 'to="/assistant"' in app_shell
    assert "Open assistant" in app_shell
    assert "AssistantToolSpec" in assistant_tool_catalog
    assert "ToolCatalogPanel" in assistant_page
    assert "Assistant tool catalog" in assistant_tool_catalog
    assert "AI Assistant" in assistant_page
    assert "Advanced context" in assistant_input_panels
    assert "LiveToolTimeline" in assistant_page
    assert "Live timeline" in assistant_live_timeline
    assert "Planning, tools, results, and answer text in order." in assistant_live_timeline
    assert "ConversationTurn" in assistant_page
    assert "AssistantRecoveryActions" in assistant_page
    assert "Retry failed tool call" in assistant_page
    assert "Continue without retry" in assistant_page
    assert "assistant_recovery" in assistant_page
    assert "retry_tool" in assistant_page
    assert "continue_after_failure" in assistant_page
    assert "streamed_answer" in assistant_page
    assert "AssistantResponseDetails" in assistant_page
    assert "AssistantEvidenceMatchStrip" in assistant_response_details
    assert "AssistantReviewTaskAction" in assistant_response_details
    assert "Create review task" in assistant_response_details
    assert "assistantReviewTaskDraft" in assistant_response_details
    assert "AssistantReviewTaskDraft" in assistant_page
    assert "prepareReviewTask" in assistant_page
    assert "assistant_review_task" in assistant_response_model
    assert "create_review_task" in assistant_response_model
    assert "assistantEvidenceMatchExplanation" in assistant_response_model
    assert "matchSupportBadgeVariant" in assistant_response_model
    assert "item.match_explanation" in assistant_response_model
    assert "AssistantStandardSearchPlan" in assistant_response_details
    assert "Standards plan" in assistant_response_details
    assert "AssistantStandardSearchMatchReasons" in assistant_response_details
    assert "Matched by" in assistant_response_details
    assert "matched_fields" in assistant_response_model
    assert "AssistantMedicalSearchHints" in assistant_response_details
    assert "Medical search hints" in assistant_response_details
    assert "AssistantSourceDiversity" in assistant_response_details
    assert "toolDiversitySummary" in assistant_response_model
    assert "diversitySummaryValue" in assistant_response_model
    assert "Evidence spread after final retrieval selection" in assistant_response_details
    assert "_compact_retrieval_diversity" in (
        REPO_ROOT / "src/ojtflow/application/assistant_service.py"
    ).read_text(encoding="utf-8")
    assert "toolSearchHints" in assistant_response_model
    assert "evidenceJumpActionsForSummary" in assistant_response_model
    assert "workflowEvidenceHref" in assistant_response_model
    assert "evidenceLocatorSummary" in assistant_response_model
    assert "AssistantEvidenceJumpActions" in assistant_response_details
    assert "Show evidence" in assistant_response_model
    assert "assistantEvidenceAnchorId" in assistant_response_details
    assert "evidenceAnchorId" in evidence_links
    assert "workflowEventAnchorId" in evidence_links
    assert "validationIssueAnchorId" in evidence_links
    assert "useHashTargetScroll" in hash_scroll_hook
    assert "useHashTargetScroll" in workflow_detail
    assert "useHashTargetScroll" in retrieval_search_results
    assert "evidenceAnchorId(evidence.evidence_id)" in workflow_detail_sections
    assert "workflowEventAnchorId(event.event_id)" in workflow_detail_sections
    assert "validationIssueAnchorId(issue.issue_id)" in workflow_detail_sections
    assert "evidenceAnchorId(evidence.evidence_id)" in retrieval_hit_card
    assert "selected_unit_candidates" in assistant_response_details
    assert "scope_endpoints" in assistant_response_details
    assert "ExternalLink" in assistant_response_details
    assert "Clipboard" in assistant_response_details
    assert "copyTextToClipboard" in assistant_response_details
    assert "Copied" in assistant_response_details
    assert 'rel="noopener noreferrer"' in assistant_response_details
    assert "toolStandardSearchPlan" in assistant_response_model
    assert "standardSearchPlanValue" in assistant_response_model
    assert "RetrievalStandardSearchPlan" in assistant_response_model
    assert "AssistantSessionSidebar" in assistant_page
    assert "createAssistantChatSession" in assistant_session
    assert "sessionWithAppendedTranscriptItem" in assistant_session
    assert "New chat" in assistant_session
    assert "Chats" in assistant_session_sidebar
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
    assert "ComposerContextPreview" in assistant_page
    assert "selectedContextsFromContext" in assistant_page
    assert "textSnippetsFromContext" in assistant_page
    assert "filesFromClipboard" in assistant_page
    assert "multiple" in assistant_page
    assert "Add text snippet" in assistant_page
    assert "Context for next message" in assistant_page
    assert "fileFromClipboard" in assistant_attachments
    assert "assistantContextWithAttachments" in assistant_attachments
    assert "assistantContextWithAttachment" in assistant_attachments
    assert "AssistantTextSnippet" in assistant_attachments
    assert "AssistantSelectedContext" in assistant_attachments
    assert "buildAssistantWorkflowContextHref" in assistant_attachments
    assert "buildAssistantRetrievalContextHref" in assistant_attachments
    assert "buildAssistantWorkflowContextHref" in workflow_detail
    assert "Ask Assistant" in workflow_detail
    assert "buildAssistantRetrievalContextHref" in retrieval_search_results
    assert "Paste an image" in assistant_page
    assert "handleAttachmentDrop" in assistant_page
    assert "onDrop={handleAttachmentDrop}" in assistant_page
    assert "Drop the file here to attach it to this chat." in assistant_page
    assert "Drop files here or attach" in assistant_page
    assert "Attach" in assistant_page
    assert "ChatEmptyState" in assistant_page
    assert "No starter tasks are configured." in assistant_empty_state
    assert "Message" in assistant_page
    assert "Send" in assistant_page
    assert "answer {response.synthesis_mode}" in assistant_response_details
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
    assert 'type: "tool_progress"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'type: "cancelled"' in (REPO_ROOT / "frontend/src/types.ts").read_text(
        encoding="utf-8"
    )
    assert 'status: "completed" | "failed" | "cancelled"' in (
        REPO_ROOT / "frontend/src/types.ts"
    ).read_text(encoding="utf-8")
    assert "chronologicalTimelineItems" in assistant_live_timeline
    assert "AssistantTextStreamPreview" in assistant_live_timeline
    assert "ToolTimelineCard" in assistant_live_timeline
    assert "<details" in assistant_live_timeline
    assert "ToolProgressRow" in assistant_live_timeline
    assert "tool_progress" in assistant_live_timeline
    assert "Cancelled" in assistant_live_timeline
    assert "Search and rerank evidence" in (
        REPO_ROOT / "knowledge" / "assistant" / "tool_progress_policies.json"
    ).read_text(encoding="utf-8")
    assert "load_assistant_tool_progress_policies" in (
        REPO_ROOT / "src" / "ojtflow" / "interfaces" / "api" / "deps.py"
    ).read_text(encoding="utf-8")
    assert "formatPlannerStreamText" in assistant_live_timeline
    assert "PlannerStreamPreview" in assistant_live_timeline
    assert "Planner stream" in assistant_live_timeline
    assert "Planning ${event.elapsed_seconds}s" in assistant_live_timeline
    assert "PlanReadyPreview" in assistant_live_timeline
    assert "Validated plan" in assistant_live_timeline
    assert "planningStartedDetail" in assistant_live_timeline
    assert "Tools available:" in assistant_live_timeline_model
    assert "Max tool calls:" in assistant_live_timeline_model
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
    assert "assistantMemoryPolicy" in server_state
    assert "assistantMemory" in server_state
    assert "getAssistantMemoryPolicy" in api_module
    assert "getAssistantMemory" in api_module
    assert "upsertAssistantMemoryPreference" in api_module
    assert "Assistant memory" in assistant_input_panels
    assert "policy={memoryPolicy}" in assistant_input_panels
    assert "onMemoryPreferenceChange" in assistant_page
    assert "localStorage" not in assistant_input_panels
    assert "server allowlisted assistant/MCP tools" in frontend_architecture
    assert "The primary authenticated route is `/assistant`" in frontend_architecture
    assert "drag-and-drop file selection" in frontend_architecture
    assert "assistant-empty-state.tsx" in frontend_architecture
    assert "assistant-inline-guide.tsx" in frontend_architecture
    assert "assistant-tool-catalog-panel.tsx" in frontend_architecture
    assert "How to use Assistant" in assistant_inline_guide


def test_help_center_surfaces_user_guidance() -> None:
    app = (FRONTEND_SRC / "App.tsx").read_text(encoding="utf-8")
    app_shell = APP_SHELL.read_text(encoding="utf-8")
    assistant_page = ASSISTANT_PAGE.read_text(encoding="utf-8")
    assistant_input_panels = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-input-panels.tsx"
    ).read_text(encoding="utf-8")
    assistant_inline_guide = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-inline-guide.tsx"
    ).read_text(encoding="utf-8")
    assistant_tool_catalog = (
        FRONTEND_SRC / "features" / "assistant" / "assistant-tool-catalog-panel.tsx"
    ).read_text(encoding="utf-8")
    frontend_architecture = (REPO_ROOT / "docs" / "frontend_architecture.md").read_text(
        encoding="utf-8"
    )
    help_page = HELP_PAGE.read_text(encoding="utf-8")
    guide_panel = GUIDE_PANEL.read_text(encoding="utf-8")
    retrieval_page = RETRIEVAL_PAGE.read_text(encoding="utf-8")
    retrieval_first_run_guide = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "first-run-guide.tsx"
    ).read_text(encoding="utf-8")
    retrieval_inline_guide = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-inline-guide.tsx"
    ).read_text(encoding="utf-8")
    retrieval_page_chrome = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-page-chrome.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_remediation_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-remediation-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_loosen_scope_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-loosen-scope-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_quality_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-quality-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_remediation_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-remediation-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_no_result_suggestion_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "no-result-suggestion-card.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_text_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-text-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_context_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-context-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_schema_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-schema-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_top_k_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-top-k-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_format_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-format-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_resource_control = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-resource-control.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_fields = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-fields.tsx"
    ).read_text(encoding="utf-8")
    retrieval_query_builder_scope_select = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "query-builder-scope-select.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_strip = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-strip.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_preset_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-preset-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_hit_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-hit-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_hit_card_list = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-hit-card-list.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_results_no_result_remediation = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-results-no-result-remediation.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "retrieval-search-cockpit.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_insights = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-insights.tsx"
    ).read_text(encoding="utf-8")
    retrieval_search_cockpit_metric_grid = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "search-cockpit-metric-grid.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filter_controls = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-filter-controls.tsx"
    ).read_text(encoding="utf-8")
    retrieval_source_inventory_filter_header = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "source-inventory-filter-header.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_standard_panels = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-standard-panels.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendations_panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendations-panel.tsx"
    ).read_text(encoding="utf-8")
    retrieval_strategy_recommendation_card = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "retrieval"
        / "components"
        / "strategy-recommendation-card.tsx"
    ).read_text(encoding="utf-8")
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
    assert "Execution summary" in help_page
    assert "Run first local task" in help_page
    assert "Copy external follow-ups" in help_page
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
    assert "How to use Assistant" in assistant_inline_guide
    assert "RetrievalInlineGuide" not in retrieval_page
    assert "RetrievalInlineGuide" in retrieval_page_chrome
    assert "./retrieval-inline-guide" in retrieval_page_chrome
    assert "function RetrievalInlineGuide" not in retrieval_page
    assert "How to read Retrieval" in retrieval_inline_guide
    assert "RetrievalFirstRunGuide" in retrieval_search_results_header
    assert "./first-run-guide" in retrieval_search_results_header
    assert "function RetrievalFirstRunGuide" not in retrieval_page
    assert "SearchResultsNoResultRemediation" in retrieval_search_results_hit_list
    assert "./search-results-no-result-remediation" in retrieval_search_results_hit_list
    assert "SearchResultsHitCardList" in retrieval_search_results_hit_list
    assert "HitCard" in retrieval_search_results_hit_card_list
    assert "NoResultRemediationPanel" in retrieval_search_results_no_result_remediation
    assert "./no-result-remediation-panel" in retrieval_search_results_no_result_remediation
    assert "function NoResultRemediationPanel" not in retrieval_page
    assert "Retrieval query help" in retrieval_query_builder_text_fields
    assert "Retrieval fields help" in retrieval_query_builder_text_fields
    assert "Schema filter help" not in retrieval_query_builder_context_fields
    assert "Schema filter help" not in retrieval_query_builder_context_controls
    assert "Schema filter help" in retrieval_query_builder_schema_control
    assert "Top K help" not in retrieval_query_builder_context_fields
    assert "Top K help" not in retrieval_query_builder_context_controls
    assert "Top K help" in retrieval_query_builder_top_k_control
    assert "Format filter help" not in retrieval_query_builder_context_fields
    assert "Format filter help" not in retrieval_query_builder_context_controls
    assert "Format filter help" in retrieval_query_builder_format_control
    assert "Resource filter help" not in retrieval_query_builder_context_fields
    assert "Resource filter help" not in retrieval_query_builder_context_controls
    assert "Resource filter help" in retrieval_query_builder_resource_control
    assert "Clinical domain help" in retrieval_query_builder_scope_fields
    assert "Standard filter help" in retrieval_query_builder_scope_fields
    assert "Trust filter help" in retrieval_query_builder_scope_fields
    assert "Source type filter help" in retrieval_query_builder_scope_fields
    assert "QueryBuilderScopeSelect" in retrieval_query_builder_scope_fields
    assert "function QueryBuilderScopeSelect" in retrieval_query_builder_scope_select
    assert "HelpTooltip" in retrieval_query_builder_scope_select
    assert "Select" in retrieval_query_builder_scope_select
    assert "explain missing units for lab_result_v1" in retrieval_query_builder_text_fields
    assert "date, patient_id, lab_name, value, unit" in retrieval_query_builder_text_fields
    assert "Start with a concrete healthcare data question" in retrieval_first_run_guide
    assert "first search guide" in retrieval_first_run_guide
    assert "Good starter questions" in retrieval_first_run_guide
    assert "NoResultRemediationHeader" in retrieval_no_result_remediation_panel
    assert "NoResultLoosenScopeCard" in retrieval_no_result_remediation_panel
    assert "NoResultQualityCard" in retrieval_no_result_remediation_panel
    assert "NoResultSuggestionCard" in retrieval_no_result_remediation_panel
    assert "No matching evidence returned" in retrieval_no_result_remediation_header
    assert "Loosen scope" in retrieval_no_result_loosen_scope_card
    assert "Clear all filters" in retrieval_no_result_loosen_scope_card
    assert (
        "Clear exact source scope and rerun search"
        in retrieval_no_result_loosen_scope_card
    )
    assert "Check source inventory" in retrieval_no_result_quality_card
    assert "Apply backend suggestion" in retrieval_no_result_suggestion_card
    assert "firstSupportedRecommendedAction" not in retrieval_search_results_hit_list
    assert "firstSupportedRecommendedAction" in retrieval_search_results_no_result_remediation
    assert "direct controls to clear exact source scope" in frontend_architecture
    assert "Search presets help" in retrieval_search_preset_header
    assert "Source inventory filters help" in retrieval_source_inventory_filter_header
    assert "Execute write actions help" in assistant_input_panels
    assert "Write action confirmation" in assistant_input_panels
    assert "writeGatedTools.map" in assistant_input_panels
    assert "writeConfirmationRequired" in assistant_page
    assert "Confirm write-gated assistant actions before sending." in assistant_page
    assert "Optional context JSON help" in assistant_input_panels
    assert "Tool catalog help" in assistant_tool_catalog
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
    assert "The backend route chosen for this query" in retrieval_search_cockpit_metric_grid
    assert "The retrieval stack combines lexical search" in retrieval_search_results_header
    assert (
        "How many independent sources survived source-diversity selection"
        in retrieval_search_results_header
    )
    assert (
        "Concepts and query aspects detected from the search"
        in retrieval_search_results_header
    )
    assert "Strategy recommendations help" in retrieval_strategy_recommendations_panel
    assert "Open full manual" in assistant_inline_guide
    assert "Open full manual" in retrieval_inline_guide
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
