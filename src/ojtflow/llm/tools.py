"""Tool definitions and executors for Groq function calling.

Each tool has:
  - A JSON schema definition (passed to Groq so it knows what tools exist)
  - An executor function (called when Groq requests the tool)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.core.contracts.retrieval import RetrievalQuery
from ojtflow.data_tools import convert, detect, parse, profile, validate
from ojtflow.infrastructure.retrieval.static import StaticRetrievalRepository

_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[3] / "knowledge"


# ---------------------------------------------------------------------------
# Tool schema definitions (sent to Groq)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "detect_format",
            "description": (
                "Detect whether raw text is CSV, JSON, YAML, or unknown. "
                "Use this first when the user provides data without specifying format."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {
                        "type": "string",
                        "description": "Raw data text to inspect.",
                    }
                },
                "required": ["raw_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "profile_dataset",
            "description": (
                "Analyze a dataset's structure: field names, data types, missing values, "
                "and whether PHI (patient identifiers) may be present. "
                "Run this before validating or converting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "Raw CSV, JSON, or YAML text."},
                    "data_format": {
                        "type": "string",
                        "enum": ["csv", "json", "yaml"],
                        "description": "Format of the data.",
                    },
                },
                "required": ["raw_text", "data_format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_dataset",
            "description": (
                "Validate a dataset and return a list of issues with severity levels. "
                "Reports missing values, PHI fields, type mismatches, and prompt injection. "
                "Use schema_id='lab_result_v1' for lab data if available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "Raw CSV, JSON, or YAML text."},
                    "data_format": {
                        "type": "string",
                        "enum": ["csv", "json", "yaml"],
                        "description": "Format of the data.",
                    },
                    "schema_id": {
                        "type": "string",
                        "description": "Optional schema name, e.g. 'lab_result_v1'.",
                    },
                },
                "required": ["raw_text", "data_format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_data",
            "description": (
                "Convert data between formats: CSV↔JSON↔YAML. "
                "Returns converted text and a SHA-256 hash for integrity. "
                "Always validate after converting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "Source data text."},
                    "source_format": {
                        "type": "string",
                        "enum": ["csv", "json", "yaml"],
                        "description": "Format of the input data.",
                    },
                    "target_format": {
                        "type": "string",
                        "enum": ["csv", "json", "yaml"],
                        "description": "Desired output format.",
                    },
                },
                "required": ["raw_text", "source_format", "target_format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "Search the trusted healthcare knowledge base for evidence before making clinical claims. "
                "Returns relevant chunks with source IDs. Only cite source_ids from this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query, e.g. 'HbA1c normal range LOINC'.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executors (called when Groq requests a tool)
# ---------------------------------------------------------------------------

def _execute_detect_format(raw_text: str) -> dict[str, Any]:
    result = detect.detect_format(raw_text)
    return {
        "format": result.format.value,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "warnings": result.warnings,
    }


def _execute_profile_dataset(raw_text: str, data_format: str) -> dict[str, Any]:
    fmt = DataFormat(data_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    data_profile = profile.profile_data(parsed)
    return {
        "row_count": data_profile.row_count,
        "column_count": data_profile.column_count,
        "has_possible_phi": any(f.possible_phi for f in data_profile.fields),
        "fields": [
            {
                "name": f.name,
                "inferred_types": f.inferred_types,
                "missing_count": f.missing_count,
                "sample_values": f.sample_values[:3],
                "possible_phi": f.possible_phi,
            }
            for f in data_profile.fields
        ],
        "warnings": data_profile.warnings,
    }


def _execute_validate_dataset(
    raw_text: str,
    data_format: str,
    schema_id: str | None = None,
) -> dict[str, Any]:
    fmt = DataFormat(data_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    data_profile = profile.profile_data(parsed)

    schema = None
    if schema_id:
        schema_path = _KNOWLEDGE_ROOT / "schemas" / f"{schema_id}.schema.json"
        if schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

    report = validate.validate_against_schema(parsed, data_profile, schema)
    return {
        "valid": report.valid,
        "requires_review": report.requires_review,
        "schema_confidence": report.schema_confidence,
        "severity_summary": report.severity_summary,
        "issues": [
            {
                "kind": issue.kind,
                "severity": issue.severity.value,
                "message": issue.message,
                "field": issue.location.field if issue.location else None,
                "row": issue.location.row if issue.location else None,
                "suggested_action": issue.suggested_action,
            }
            for issue in report.issues
        ],
    }


def _execute_convert_data(
    raw_text: str,
    source_format: str,
    target_format: str,
) -> dict[str, Any]:
    src = DataFormat(source_format.lower())
    tgt = DataFormat(target_format.lower())
    parsed = parse.parse_data(raw_text, src)
    output_text, output = convert.convert_data(parsed, tgt)
    return {
        "output_text": output_text,
        "output_format": tgt.value,
        "row_count": len(parsed.records),
        "warnings": output.warnings,
        "output_hash": output.output_hash,
    }


def _execute_search_knowledge(query: str, top_k: int = 5) -> dict[str, Any]:
    repo = StaticRetrievalRepository(_KNOWLEDGE_ROOT)
    rq = RetrievalQuery(query=query, top_k=min(top_k, 10))
    package = repo.search(rq)
    return {
        "evidence": [
            {
                "source_id": hit.evidence.source_id,
                "claim": hit.evidence.claim,
                "score": hit.score,
            }
            for hit in package.hits
        ],
        "warnings": package.trace.warnings,
        "result_count": len(package.hits),
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

EXECUTORS: dict[str, Any] = {
    "detect_format": _execute_detect_format,
    "profile_dataset": _execute_profile_dataset,
    "validate_dataset": _execute_validate_dataset,
    "convert_data": _execute_convert_data,
    "search_knowledge": _execute_search_knowledge,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name and return JSON string result."""
    executor = EXECUTORS.get(name)
    if executor is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = executor(**arguments)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)})
