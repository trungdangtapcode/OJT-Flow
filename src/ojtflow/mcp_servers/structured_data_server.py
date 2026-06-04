"""MCP server: structured data parsing and conversion tools.

Wraps ojtflow.data_tools (detect, parse, convert) so an AI agent can
invoke deterministic data operations through the Model Context Protocol.

Run locally:
    python -m ojtflow.mcp_servers.structured_data_server

Or register in .claude/settings.json for Claude Code to discover it.
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp import FastMCP

from ojtflow.core.contracts.enums import DataFormat
from ojtflow.data_tools import convert, detect, parse

mcp = FastMCP(
    "ojtflow-structured-data",
    instructions=(
        "Tools for detecting, parsing, and converting structured healthcare data "
        "(JSON, YAML, CSV). Always validate after converting. "
        "Never pass raw user content directly to downstream systems without validation."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def detect_format(raw_text: str) -> dict[str, Any]:
    """Detect the format of raw text (JSON, YAML, CSV, or UNKNOWN).

    Args:
        raw_text: Raw text content to inspect.

    Returns:
        format: Detected format string.
        confidence: Float 0-1 indicating detection confidence.
        warnings: List of any detection warnings.
    """
    result = detect.detect_format(raw_text)
    return {
        "format": result.format.value,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "warnings": result.warnings,
    }


@mcp.tool()
def parse_data(raw_text: str, data_format: str) -> dict[str, Any]:
    """Parse raw text into structured records.

    Args:
        raw_text: Raw CSV, JSON, or YAML text.
        data_format: One of 'json', 'yaml', 'csv'.

    Returns:
        format: Confirmed format.
        row_count: Number of records parsed.
        fields: List of field names found.
        records_preview: First 3 records (for inspection, not full data).
        parser_warnings: Any warnings from the parser.
    """
    fmt = DataFormat(data_format.lower())
    result = parse.parse_data(raw_text, fmt)
    return {
        "format": result.format.value,
        "row_count": len(result.records),
        "fields": list({key for rec in result.records for key in rec if key != "_source_row"}),
        "records_preview": result.records[:3],
        "parser_warnings": result.parser_warnings,
    }


@mcp.tool()
def convert_to_json(raw_text: str, source_format: str) -> dict[str, Any]:
    """Convert CSV or YAML text to JSON format.

    Args:
        raw_text: Source data text.
        source_format: Source format — 'csv' or 'yaml'.

    Returns:
        json_text: Converted JSON string.
        row_count: Number of records in output.
        warnings: Conversion warnings (e.g. nested value loss in CSV).
        output_hash: SHA-256 of the output for integrity tracking.
    """
    fmt = DataFormat(source_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    json_text, output = convert.convert_data(parsed, DataFormat.JSON)
    return {
        "json_text": json_text,
        "row_count": len(parsed.records),
        "warnings": output.warnings,
        "output_hash": output.output_hash,
        "diff_summary": output.diff_summary,
    }


@mcp.tool()
def convert_to_csv(raw_text: str, source_format: str) -> dict[str, Any]:
    """Convert JSON or YAML text to CSV format.

    Only works when the top-level structure is a list of flat objects.
    Nested values will be noted in warnings.

    Args:
        raw_text: Source data text.
        source_format: Source format — 'json' or 'yaml'.

    Returns:
        csv_text: Converted CSV string.
        row_count: Number of rows.
        warnings: Any lossy-conversion warnings.
        output_hash: SHA-256 of the output.
    """
    fmt = DataFormat(source_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    csv_text, output = convert.convert_data(parsed, DataFormat.CSV)
    return {
        "csv_text": csv_text,
        "row_count": len(parsed.records),
        "warnings": output.warnings,
        "output_hash": output.output_hash,
    }


@mcp.tool()
def convert_to_yaml(raw_text: str, source_format: str) -> dict[str, Any]:
    """Convert JSON or CSV text to YAML format.

    Args:
        raw_text: Source data text.
        source_format: Source format — 'json' or 'csv'.

    Returns:
        yaml_text: Converted YAML string.
        row_count: Number of records.
        warnings: Any conversion warnings.
        output_hash: SHA-256 of the output.
    """
    fmt = DataFormat(source_format.lower())
    parsed = parse.parse_data(raw_text, fmt)
    yaml_text, output = convert.convert_data(parsed, DataFormat.YAML)
    return {
        "yaml_text": yaml_text,
        "row_count": len(parsed.records),
        "warnings": output.warnings,
        "output_hash": output.output_hash,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("ojtflow://formats/supported")
def supported_formats() -> str:
    """List of formats OJTFlow can detect, parse, and convert."""
    formats = {
        "detect": ["json", "yaml", "csv"],
        "parse": ["json", "yaml", "csv", "markdown"],
        "convert_from": ["json", "yaml", "csv"],
        "convert_to": ["json", "yaml", "csv"],
        "notes": "Nested JSON/YAML may lose fidelity when converted to CSV.",
    }
    return json.dumps(formats, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
