"""MCP server: schema inference and validation tools.

Wraps ojtflow.data_tools (profile, validate) so an AI agent can
validate healthcare data against known schemas through MCP.

Run locally:
    python -m ojtflow.mcp_servers.schema_validation_server
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.data_tools import parse, profile, validate

mcp = FastMCP(
    "ojtflow-schema-validation",
    instructions=(
        "Tools for profiling datasets and validating them against healthcare schemas. "
        "Always profile before validating. Report issues with severity levels. "
        "Treat CRITICAL and ERROR issues as blockers before transformation."
    ),
)

_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[4] / "knowledge"


def _load_schema(schema_id: str) -> dict | None:
    path = _KNOWLEDGE_ROOT / "schemas" / f"{schema_id}.schema.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def profile_dataset(raw_text: str, data_format: str) -> dict[str, Any]:
    """Profile a dataset to understand its structure, types, and data quality.

    Run this before validate_dataset to understand what fields exist
    and whether any PHI or anomalies are present.

    Args:
        raw_text: Raw CSV, JSON, or YAML text.
        data_format: One of 'json', 'yaml', 'csv'.

    Returns:
        row_count: Number of records.
        column_count: Number of fields.
        fields: List of field profiles with types, sample values, missing counts.
        warnings: Parser warnings.
        has_possible_phi: Whether any field looks like it contains PHI.
    """
    fmt = DataFormat(data_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    data_profile = profile.profile_data(parsed)

    fields_out = [
        {
            "name": f.name,
            "inferred_types": f.inferred_types,
            "sample_values": f.sample_values,
            "missing_count": f.missing_count,
            "non_empty_count": f.non_empty_count,
            "unique_count": f.unique_count,
            "confidence": f.confidence,
            "possible_phi": f.possible_phi,
        }
        for f in data_profile.fields
    ]

    return {
        "row_count": data_profile.row_count,
        "column_count": data_profile.column_count,
        "fields": fields_out,
        "warnings": data_profile.warnings,
        "has_possible_phi": any(f.possible_phi for f in data_profile.fields),
    }


@mcp.tool()
def validate_dataset(
    raw_text: str,
    data_format: str,
    schema_id: str | None = None,
) -> dict[str, Any]:
    """Validate a dataset against a known schema and return a full issue report.

    Args:
        raw_text: Raw CSV, JSON, or YAML text.
        data_format: One of 'json', 'yaml', 'csv'.
        schema_id: Optional schema name from the registry (e.g. 'lab_result_v1').
                   If omitted, only PHI and structural checks run.

    Returns:
        valid: True if no ERROR or CRITICAL issues found.
        schema_id: The schema used (if any).
        schema_confidence: 0-1 match score between data fields and schema.
        requires_review: True if any issue has requires_review=True.
        severity_summary: Count of issues per severity level.
        issues: Full list of issues with location, message, and suggested action.
    """
    fmt = DataFormat(data_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    data_profile = profile.profile_data(parsed)
    schema = _load_schema(schema_id) if schema_id else None

    report = validate.validate_against_schema(parsed, data_profile, schema)

    issues_out = [
        {
            "kind": issue.kind,
            "severity": issue.severity.value,
            "message": issue.message,
            "field": issue.location.field if issue.location else None,
            "row": issue.location.row if issue.location else None,
            "suggested_action": issue.suggested_action,
            "requires_review": issue.requires_review,
        }
        for issue in report.issues
    ]

    return {
        "valid": report.valid,
        "schema_id": report.schema_id,
        "schema_confidence": report.schema_confidence,
        "requires_review": report.requires_review,
        "severity_summary": report.severity_summary,
        "issue_count": len(issues_out),
        "issues": issues_out,
    }


@mcp.tool()
def list_available_schemas() -> dict[str, Any]:
    """List all schemas available in the knowledge base.

    Returns:
        schemas: List of schema entries with id, title, version, and fields.
        count: Total number of schemas available.
    """
    schemas_dir = _KNOWLEDGE_ROOT / "schemas"
    schemas = []
    for path in sorted(schemas_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas.append(
            {
                "schema_id": schema.get("$id", path.stem),
                "title": schema.get("title", path.stem),
                "version": schema.get("version", "unversioned"),
                "required_fields": schema.get("required", []),
                "field_count": len(schema.get("properties", {})),
            }
        )
    return {"schemas": schemas, "count": len(schemas)}


@mcp.tool()
def get_schema_definition(schema_id: str) -> dict[str, Any]:
    """Return the full definition of a schema from the registry.

    Args:
        schema_id: Schema identifier (e.g. 'lab_result_v1').

    Returns:
        found: Whether the schema was found.
        schema: Full schema definition (if found).
    """
    schema = _load_schema(schema_id)
    return {"found": schema is not None, "schema": schema}


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://schemas/list")
def schema_list_resource() -> str:
    """JSON list of all available schema IDs and titles."""
    schemas_dir = _KNOWLEDGE_ROOT / "schemas"
    entries = []
    for path in sorted(schemas_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        entries.append(
            {
                "schema_id": schema.get("$id", path.stem),
                "title": schema.get("title", path.stem),
            }
        )
    return json.dumps(entries, indent=2)


@mcp.resource("ojtflow://schemas/{schema_id}")
def schema_resource(schema_id: str) -> str:
    """Return the raw JSON schema for a given schema_id."""
    schema = _load_schema(schema_id)
    if schema is None:
        return json.dumps({"error": f"Schema '{schema_id}' not found."})
    return json.dumps(schema, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
