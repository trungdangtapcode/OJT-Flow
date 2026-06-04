"""Small text-formatting helpers for user-visible backend summaries."""

from __future__ import annotations


def format_count(count: int, singular: str, plural: str | None = None) -> str:
    """Return a count with singular/plural wording."""

    label = singular if count == 1 else plural or f"{singular}s"
    return f"{count} {label}"
