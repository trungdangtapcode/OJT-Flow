"""Local file reference validation for dataset and output artifacts."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from ojtflow.core.errors import NotFoundError


def artifact_path_from_file_ref(storage_ref: str, allowed_roots: list[Path]) -> Path:
    """Resolve a file:// artifact ref and require it to stay under allowed roots."""

    parsed = urlparse(storage_ref)
    if parsed.scheme != "file":
        raise NotFoundError("Unsupported dataset storage ref.")
    if parsed.netloc and parsed.netloc not in {"localhost", "127.0.0.1"}:
        raise NotFoundError("Dataset storage ref must be a local file URI.")

    raw_path = Path(unquote(parsed.path))
    if not raw_path.is_absolute():
        raise NotFoundError("Dataset storage ref must be an absolute file URI.")

    path = raw_path.resolve()
    roots = [root.resolve() for root in allowed_roots]
    if not any(path == root or root in path.parents for root in roots):
        raise NotFoundError("Dataset storage ref is outside the configured artifact directory.")
    if not path.exists() or not path.is_file():
        raise NotFoundError("Dataset file not found.")
    return path
