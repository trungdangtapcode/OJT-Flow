"""Hashing helpers for audit references."""

from __future__ import annotations

from hashlib import sha256


def sha256_text(text: str) -> str:
    """Return the SHA-256 hex digest for text."""

    return sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest for bytes."""

    return sha256(data).hexdigest()
