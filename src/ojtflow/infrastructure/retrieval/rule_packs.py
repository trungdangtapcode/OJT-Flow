"""Sanitized metadata for data-driven retrieval rule packs."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any


RULE_PACK_SPECS: tuple[tuple[str, Path, str], ...] = (
    (
        "query_expansion",
        Path("retrieval/query_expansion_rules.json"),
        "OJT_QUERY_EXPANSION_RULES_PATH",
    ),
    (
        "filter_suggestions",
        Path("retrieval/filter_suggestion_rules.json"),
        "OJT_FILTER_SUGGESTION_RULES_PATH",
    ),
    (
        "query_diagnostics",
        Path("retrieval/query_diagnostic_rules.json"),
        "OJT_QUERY_DIAGNOSTIC_RULES_PATH",
    ),
    (
        "query_profiles",
        Path("retrieval/query_profile_rules.json"),
        "OJT_QUERY_PROFILE_RULES_PATH",
    ),
    (
        "query_aspects",
        Path("retrieval/query_aspect_rules.json"),
        "OJT_QUERY_ASPECT_RULES_PATH",
    ),
    (
        "query_transformations",
        Path("retrieval/query_transformation_rules.json"),
        "OJT_QUERY_TRANSFORMATION_RULES_PATH",
    ),
    (
        "query_routes",
        Path("retrieval/query_route_rules.json"),
        "OJT_QUERY_ROUTE_RULES_PATH",
    ),
    (
        "ranking_boosts",
        Path("retrieval/ranking_boost_rules.json"),
        "OJT_RANKING_BOOST_RULES_PATH",
    ),
    (
        "evaluation_policy",
        Path("retrieval/evaluation_policy.json"),
        "OJT_RETRIEVAL_EVALUATION_POLICY_PATH",
    ),
    (
        "quality_gate_policy",
        Path("retrieval/quality_gate_policy.json"),
        "OJT_RETRIEVAL_QUALITY_POLICY_PATH",
    ),
    (
        "graph_rag",
        Path("retrieval/graph_rag_policy.json"),
        "OJT_GRAPH_RAG_POLICY_PATH",
    ),
    (
        "corrective_actions",
        Path("retrieval/corrective_action_rules.json"),
        "OJT_CORRECTIVE_ACTION_RULES_PATH",
    ),
    (
        "strategy_recommendations",
        Path("retrieval/strategy_recommendation_rules.json"),
        "OJT_STRATEGY_RECOMMENDATION_RULES_PATH",
    ),
    (
        "standard_search_playbook",
        Path("retrieval/standard_search_playbook_rules.json"),
        "OJT_STANDARD_SEARCH_PLAYBOOK_RULES_PATH",
    ),
    (
        "evidence_buckets",
        Path("retrieval/evidence_bucket_rules.json"),
        "OJT_EVIDENCE_BUCKET_RULES_PATH",
    ),
    (
        "search_hint_targets",
        Path("retrieval/search_hint_targets.json"),
        "OJT_SEARCH_HINT_TARGETS_PATH",
    ),
    (
        "fhir_search_parameters",
        Path("terminologies/fhir_search_parameters.json"),
        "OJT_FHIR_SEARCH_PARAMETERS_PATH",
    ),
)


def retrieval_rule_packs(knowledge_root: Path) -> list[dict[str, Any]]:
    """Return sanitized active retrieval rule-pack metadata."""

    return [
        retrieval_rule_pack(
            knowledge_root,
            name=name,
            relative_path=relative_path,
            env_var=env_var,
        )
        for name, relative_path, env_var in RULE_PACK_SPECS
    ]


def retrieval_rule_pack(
    knowledge_root: Path,
    *,
    name: str,
    relative_path: Path,
    env_var: str,
) -> dict[str, Any]:
    """Return sanitized metadata for one retrieval rule pack."""

    override = os.environ.get(env_var)
    path = Path(override) if override else knowledge_root / relative_path
    source = "override" if override else "knowledge"
    details: dict[str, Any] = {
        "name": name,
        "status": "missing",
        "source": source,
        "env_var": env_var,
        "configured": bool(override),
        "rule_count": 0,
    }
    if not path.exists():
        return details
    try:
        content = path.read_bytes()
        raw = json.loads(content.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            **details,
            "status": "error",
            "error": type(exc).__name__,
        }
    version = raw.get("version") if isinstance(raw, dict) else None
    rules = raw.get("rules") if isinstance(raw, dict) else None
    targets = raw.get("targets") if isinstance(raw, dict) else None
    buckets = raw.get("buckets") if isinstance(raw, dict) else None
    resources = raw.get("resources") if isinstance(raw, dict) else None
    items = (
        rules
        if isinstance(rules, list)
        else targets
        if isinstance(targets, list)
        else buckets
        if isinstance(buckets, list)
        else resources
        if isinstance(resources, list)
        else []
    )
    return {
        **details,
        "status": "ok",
        "rule_count": len(items),
        "version": version if isinstance(version, str) else None,
        "content_hash": sha256(content).hexdigest(),
    }
