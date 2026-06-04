"""Local trusted corpus ingestion for retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


SUPPORTED_CORPUS_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}


@dataclass(frozen=True)
class CorpusIndexResult:
    """Summary of local corpus ingestion."""

    files_seen: int
    files_indexed: int
    chunks_indexed: int
    skipped_files: list[str]


def load_local_corpus_chunks(
    corpus_dirs: tuple[Path, ...],
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
) -> tuple[list[KnowledgeChunk], CorpusIndexResult]:
    """Load operator-provided trusted corpus files into retrieval chunks."""

    chunks: list[KnowledgeChunk] = []
    files_seen = 0
    files_indexed = 0
    skipped_files: list[str] = []

    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists():
            skipped_files.append(f"{_display_path(corpus_dir, knowledge_root)}:missing")
            continue
        if not corpus_dir.is_dir():
            skipped_files.append(f"{_display_path(corpus_dir, knowledge_root)}:not_directory")
            continue
        for path in sorted(corpus_dir.rglob("*")):
            if not path.is_file() or _has_hidden_part(path):
                continue
            files_seen += 1
            if path.suffix.lower() not in SUPPORTED_CORPUS_EXTENSIONS:
                skipped_files.append(f"{_display_path(path, knowledge_root)}:unsupported_extension")
                continue
            text = _read_text(path)
            if not text.strip():
                skipped_files.append(f"{_display_path(path, knowledge_root)}:blank")
                continue
            files_indexed += 1
            chunks.extend(
                _chunks_for_file(
                    path,
                    text,
                    knowledge_root=knowledge_root,
                    max_chars=max_chars,
                    overlap_chars=overlap_chars,
                )
            )

    return chunks, CorpusIndexResult(
        files_seen=files_seen,
        files_indexed=files_indexed,
        chunks_indexed=len(chunks),
        skipped_files=skipped_files[:50],
    )


def _chunks_for_file(
    path: Path,
    text: str,
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
) -> list[KnowledgeChunk]:
    relative = _display_path(path, knowledge_root)
    title = _title_from_text(path, text)
    source_id = f"corpus:{_stable_slug(relative)}"
    source_type = _source_type_for(path, text)
    clinical_domain = _clinical_domain_for(path, text)
    standard_system = _standard_system_for(path, text)
    text_chunks = _chunk_text(text, max_chars=max_chars, overlap_chars=overlap_chars)
    content_hash = sha256(text.encode("utf-8")).hexdigest()

    chunks: list[KnowledgeChunk] = []
    for index, chunk_text in enumerate(text_chunks):
        chunk_hash = sha256(f"{relative}:{index}:{chunk_text}".encode("utf-8")).hexdigest()[:16]
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"chunk_corpus_{chunk_hash}",
                source_id=source_id,
                source_type=source_type,
                title=title,
                content=chunk_text,
                trust_level=TrustLevel.APPROVED,
                clinical_domain=clinical_domain,
                standard_system=standard_system,
                locator={"path": relative, "chunk_index": index},
                metadata={
                    "origin": "local_corpus",
                    "content_hash": content_hash,
                    "extension": path.suffix.lower(),
                },
            )
        )
    return chunks


def _chunk_text(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_sliding_chunks(paragraph, max_chars=max_chars, overlap_chars=overlap_chars))
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current.strip())
            prefix = current[-overlap_chars:].strip() if overlap_chars else ""
            current = f"{prefix}\n\n{paragraph}".strip() if prefix else paragraph
    if current:
        chunks.append(current.strip())
    return chunks


def _sliding_chunks(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    step = max(1, max_chars - overlap_chars)
    chunks: list[str] = []
    for start in range(0, len(text), step):
        chunk = text[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + max_chars >= len(text):
            break
    return chunks


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _title_from_text(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem.replace("_", " ").title()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _source_type_for(path: Path, text: str) -> EvidenceSourceType:
    inspected = f"{path} {text[:1000]}".lower()
    if any(term in inspected for term in ["loinc", "ucum", "rxnorm", "snomed"]):
        return EvidenceSourceType.TERMINOLOGY_SYSTEM
    if any(term in inspected for term in ["fhir", "omop", "hl7", "standard"]):
        return EvidenceSourceType.HEALTHCARE_STANDARD
    if "example" in inspected:
        return EvidenceSourceType.TRANSFORMATION_EXAMPLE
    return EvidenceSourceType.DATA_DICTIONARY


def _clinical_domain_for(path: Path, text: str) -> str:
    inspected = f"{path} {text[:1000]}".lower()
    if any(term in inspected for term in ["lab", "observation", "hba1c", "glucose"]):
        return "laboratory"
    if any(term in inspected for term in ["medication", "rxnorm", "drug"]):
        return "medication"
    if any(term in inspected for term in ["imaging", "dicom", "radiology"]):
        return "imaging"
    if any(term in inspected for term in ["governance", "policy", "review"]):
        return "governance"
    return "general"


def _standard_system_for(path: Path, text: str) -> str:
    inspected = f"{path} {text[:1000]}".lower()
    candidates = {
        "FHIR": ["fhir", "hl7"],
        "LOINC": ["loinc"],
        "UCUM": ["ucum"],
        "RxNorm": ["rxnorm"],
        "OMOP": ["omop"],
    }
    for system, markers in candidates.items():
        if any(marker in inspected for marker in markers):
            return system
    return "local_corpus"


def _display_path(path: Path, knowledge_root: Path) -> str:
    try:
        return str(path.relative_to(knowledge_root.parent))
    except ValueError:
        return str(path)


def _stable_slug(value: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", Path(value).stem.lower()).strip("_") or "document"
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{stem}_{digest}"


def _has_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)
