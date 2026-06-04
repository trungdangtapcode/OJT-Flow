"""API request size guards."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from ojtflow.config import Settings
from ojtflow.core.errors import UploadTooLargeError


def enforce_inline_text_limit(
    value: str,
    settings: Settings,
    *,
    field_name: str = "data",
) -> None:
    """Reject inline text payloads that should be uploaded as files instead."""

    _raise_if_too_large(
        byte_size=len(value.encode("utf-8")),
        limit=settings.max_inline_data_bytes,
        field_name=field_name,
    )


def enforce_inline_json_limit(
    value: Any,
    settings: Settings,
    *,
    field_name: str,
) -> None:
    """Reject structured inline payloads that exceed the configured API limit."""

    value = _jsonable(value)
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    _raise_if_too_large(
        byte_size=len(serialized.encode("utf-8")),
        limit=settings.max_inline_data_bytes,
        field_name=field_name,
    )


def _raise_if_too_large(*, byte_size: int, limit: int, field_name: str) -> None:
    if byte_size <= limit:
        return
    raise UploadTooLargeError(
        f"Inline field '{field_name}' exceeds the {limit} byte limit.",
        details={
            "field": field_name,
            "byte_size": byte_size,
            "limit": limit,
        },
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
