"""Identifier helpers for auditable domain objects."""

from __future__ import annotations

from uuid import uuid4


def new_id(prefix: str) -> str:
    """Return a short prefixed identifier suitable for logs and fixtures."""

    return f"{prefix}_{uuid4().hex[:12]}"

