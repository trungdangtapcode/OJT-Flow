"""Direct validation routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from ojtflow.data_tools.detect import detect_format
from ojtflow.data_tools.parse import parse_data
from ojtflow.data_tools.profile import profile_data
from ojtflow.data_tools.validate import validate_against_schema
from ojtflow.infrastructure.retrieval.static import StaticKnowledgeRepository
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import ValidateRequest

router = APIRouter(tags=["validate"])


@router.post("/validate")
async def validate(request: ValidateRequest) -> dict:
    detection = detect_format(request.data, request.input_format)
    parsed = parse_data(request.data, detection.format)
    profile = profile_data(parsed)
    repo_root = Path(__file__).resolve().parents[5]
    schema = StaticKnowledgeRepository(repo_root / "knowledge").get_schema(request.schema_id)
    report = validate_against_schema(parsed, profile, schema)
    return ok({
        "status": "success",
        "detected_format": detection.format,
        "profile": profile.model_dump(mode="json"),
        "validation_report": report.model_dump(mode="json"),
    })
