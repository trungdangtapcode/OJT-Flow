"""Direct deterministic conversion routes."""

from __future__ import annotations

from fastapi import APIRouter

from ojtflow.data_tools.convert import convert_data
from ojtflow.data_tools.detect import detect_format
from ojtflow.data_tools.parse import parse_data
from ojtflow.interfaces.api.responses import ok
from ojtflow.interfaces.api.schemas import ConvertRequest

router = APIRouter(tags=["convert"])


@router.post("/convert")
def convert(request: ConvertRequest) -> dict:
    detection = detect_format(request.data, request.input_format)
    parsed = parse_data(request.data, detection.format)
    output_text, output = convert_data(parsed, request.target_format)
    return ok({
        "status": "success",
        "detected_format": detection.format,
        "output_format": output.output_format,
        "output": output_text,
        "metadata": output.model_dump(mode="json"),
    })
