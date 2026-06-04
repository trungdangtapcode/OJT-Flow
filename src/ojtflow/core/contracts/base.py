"""Shared Pydantic configuration for domain contracts."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints


NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _ensure_non_blank_text(value: str) -> str:
    if not value.strip():
        raise ValueError("String should not be blank")
    return value


NonBlankText = Annotated[str, AfterValidator(_ensure_non_blank_text)]


class ContractModel(BaseModel):
    """Base class for typed contracts at architecture boundaries."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )
