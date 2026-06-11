"""Local trusted corpus ingestion for retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.retrieval import (
    CorpusAdapterCatalog,
    CorpusIngestionItem,
    CorpusIngestionManifest,
    CorpusLicenseMetadata,
    CorpusSourceAdapter,
)
from ojtflow.infrastructure.retrieval.catalogs import load_corpus_adapter_catalog
from ojtflow.infrastructure.retrieval.engine import KnowledgeChunk


SUPPORTED_CORPUS_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}


@dataclass(frozen=True)
class CorpusIndexResult:
    """Summary of local corpus ingestion."""

    files_seen: int
    files_indexed: int
    chunks_indexed: int
    skipped_files: list[str]
    manifest: CorpusIngestionManifest | None = None

    def to_dict(self) -> dict:
        return {
            "files_seen": self.files_seen,
            "files_indexed": self.files_indexed,
            "chunks_indexed": self.chunks_indexed,
            "skipped_files": list(self.skipped_files),
            "manifest": (
                self.manifest.model_dump(mode="json") if self.manifest is not None else None
            ),
        }


def build_corpus_ingestion_manifest(
    corpus_dirs: tuple[Path, ...],
    *,
    knowledge_root: Path,
    generated_at: datetime | None = None,
) -> CorpusIngestionManifest:
    """Build a governed manifest for local corpus files available to ingestion."""

    catalog = load_corpus_adapter_catalog(knowledge_root)
    adapters_by_path = _adapters_by_local_path(catalog, knowledge_root=knowledge_root)
    generated_at_value = _isoformat(generated_at or datetime.now(UTC))
    items: list[CorpusIngestionItem] = []
    for path in _iter_supported_corpus_files(corpus_dirs):
        relative = _display_path(path, knowledge_root)
        adapter = adapters_by_path.get(relative)
        text = _read_text(path)
        items.append(
            _manifest_item_for_file(
                path,
                text,
                knowledge_root=knowledge_root,
                adapter=adapter,
            )
        )
    return CorpusIngestionManifest(
        version="corpus_ingestion_manifest.v1",
        generated_at=generated_at_value,
        adapter_catalog_version=catalog.version,
        knowledge_root=_display_path(knowledge_root, knowledge_root),
        item_count=len(items),
        enabled_adapter_count=sum(1 for adapter in catalog.adapters if adapter.enabled),
        approved_item_count=sum(1 for item in items if item.reviewer_state == "approved"),
        needs_review_item_count=sum(
            1 for item in items if item.reviewer_state == "needs_review"
        ),
        items=items,
    )


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
    manifest = build_corpus_ingestion_manifest(corpus_dirs, knowledge_root=knowledge_root)
    manifest_by_path = {
        item.path: item
        for item in manifest.items
        if item.path
    }

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
            manifest_item = manifest_by_path.get(_display_path(path, knowledge_root))
            if manifest_item and (
                not manifest_item.enabled
                or manifest_item.lifecycle_state in {"blocked", "failed"}
            ):
                skipped_files.append(
                    f"{_display_path(path, knowledge_root)}:{manifest_item.lifecycle_state}"
                )
                continue
            files_indexed += 1
            chunks.extend(
                _chunks_for_file(
                    path,
                    text,
                    knowledge_root=knowledge_root,
                    max_chars=max_chars,
                    overlap_chars=overlap_chars,
                    manifest_item=manifest_item,
                )
            )

    return chunks, CorpusIndexResult(
        files_seen=files_seen,
        files_indexed=files_indexed,
        chunks_indexed=len(chunks),
        skipped_files=skipped_files[:50],
        manifest=manifest,
    )


def _chunks_for_file(
    path: Path,
    text: str,
    *,
    knowledge_root: Path,
    max_chars: int,
    overlap_chars: int,
    manifest_item: CorpusIngestionItem | None = None,
) -> list[KnowledgeChunk]:
    relative = _display_path(path, knowledge_root)
    title = _title_from_text(path, text)
    source_id = f"corpus:{_stable_slug(relative)}"
    source_type = _source_type_for(path, text)
    clinical_domain = _clinical_domain_for(path, text)
    standard_system = _standard_system_for(path, text)
    source_version = "local-unversioned"
    metadata = {
        "origin": "local_corpus",
        "content_hash": sha256(text.encode("utf-8")).hexdigest(),
        "extension": path.suffix.lower(),
    }
    if manifest_item is not None:
        title = manifest_item.title
        source_id = manifest_item.source_id
        source_type = manifest_item.source_type
        clinical_domain = manifest_item.clinical_domain
        standard_system = manifest_item.standard_system
        source_version = manifest_item.release_version
        metadata.update(_metadata_from_manifest_item(manifest_item))
    text_chunks = _chunk_text(text, max_chars=max_chars, overlap_chars=overlap_chars)

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
                source_version=source_version,
                trust_level=TrustLevel.APPROVED,
                clinical_domain=clinical_domain,
                standard_system=standard_system,
                locator={"path": relative, "chunk_index": index},
                metadata=metadata,
            )
        )
    return chunks


def _manifest_item_for_file(
    path: Path,
    text: str,
    *,
    knowledge_root: Path,
    adapter: CorpusSourceAdapter | None,
) -> CorpusIngestionItem:
    relative = _display_path(path, knowledge_root)
    stat = path.stat()
    content_hash = sha256(path.read_bytes()).hexdigest()
    fallback_license = CorpusLicenseMetadata(
        license_id="operator_provided",
        name="Operator-provided local corpus",
        constraints=[
            "Operator must confirm source rights and reviewer approval before production use"
        ],
    )
    source_id = f"corpus:{_stable_slug(relative)}"
    warnings: list[str] = []
    if adapter is None:
        warnings.append("uncataloged_local_corpus_file")
    elif not adapter.enabled:
        warnings.append("adapter_disabled")
    return CorpusIngestionItem(
        item_id=f"corpus_item:{_stable_slug(relative)}",
        source_id=source_id,
        adapter_id=adapter.adapter_id if adapter else None,
        title=adapter.title if adapter else _title_from_text(path, text),
        source_type=adapter.source_type if adapter else _source_type_for(path, text),
        clinical_domain=(
            adapter.clinical_domain if adapter else _clinical_domain_for(path, text)
        ),
        standard_system=(
            adapter.standard_system if adapter else _standard_system_for(path, text)
        ),
        release_version=adapter.release_version if adapter else "local-unversioned",
        fetched_at=_isoformat(datetime.fromtimestamp(stat.st_mtime, UTC)),
        fetch_time_source="filesystem_mtime",
        content_hash=f"sha256:{content_hash}",
        size_bytes=stat.st_size,
        path=relative,
        source_url=_primary_source_url(adapter),
        license=adapter.license if adapter else fallback_license,
        reviewer_state=adapter.reviewer_state if adapter else "needs_review",
        lifecycle_state=adapter.lifecycle_state if adapter else "needs_review",
        enabled=adapter.enabled if adapter else True,
        warnings=warnings,
        metadata={
            "canonical_source_id": adapter.source_id if adapter else None,
            "authority": adapter.authority if adapter else None,
            "access_mode": adapter.access_mode if adapter else "local_file",
            "ingestion_mode": adapter.ingestion_mode if adapter else "operator_local_file",
            "origin": "local_corpus",
            "extension": path.suffix.lower(),
        },
    )


def _metadata_from_manifest_item(item: CorpusIngestionItem) -> dict:
    return {
        "corpus_item_id": item.item_id,
        "adapter_id": item.adapter_id,
        "canonical_source_id": item.metadata.get("canonical_source_id"),
        "authority": item.metadata.get("authority"),
        "access_mode": item.metadata.get("access_mode"),
        "ingestion_mode": item.metadata.get("ingestion_mode"),
        "release_version": item.release_version,
        "fetched_at": item.fetched_at,
        "fetch_time_source": item.fetch_time_source,
        "content_hash": item.content_hash,
        "size_bytes": item.size_bytes,
        "license_id": item.license.license_id,
        "license_name": item.license.name,
        "license_constraints": list(item.license.constraints),
        "reviewer_state": item.reviewer_state,
        "lifecycle_state": item.lifecycle_state,
        "source_url": item.source_url,
        "warnings": list(item.warnings),
    }


def _iter_supported_corpus_files(corpus_dirs: tuple[Path, ...]) -> list[Path]:
    paths: list[Path] = []
    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists() or not corpus_dir.is_dir():
            continue
        for path in sorted(corpus_dir.rglob("*")):
            if (
                path.is_file()
                and not _has_hidden_part(path)
                and path.suffix.lower() in SUPPORTED_CORPUS_EXTENSIONS
            ):
                paths.append(path)
    return paths


def _adapters_by_local_path(
    catalog: CorpusAdapterCatalog,
    *,
    knowledge_root: Path,
) -> dict[str, CorpusSourceAdapter]:
    adapters: dict[str, CorpusSourceAdapter] = {}
    for adapter in catalog.adapters:
        for local_path in adapter.local_paths:
            path = Path(local_path)
            relative = str(path) if not path.is_absolute() else _display_path(path, knowledge_root)
            adapters[relative] = adapter
    return adapters


def _primary_source_url(adapter: CorpusSourceAdapter | None) -> str | None:
    if adapter is None or not adapter.source_urls:
        return None
    if "primary" in adapter.source_urls:
        return adapter.source_urls["primary"]
    return next(iter(adapter.source_urls.values()))


def _isoformat(value: datetime) -> str:
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


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
    if any(
        term in inspected
        for term in ["loinc", "ucum", "rxnorm", "snomed", "mesh", "icd-10"]
    ):
        return EvidenceSourceType.TERMINOLOGY_SYSTEM
    if any(term in inspected for term in ["fhir", "omop", "hl7", "standard", "clinicaltrials.gov"]):
        return EvidenceSourceType.HEALTHCARE_STANDARD
    if "example" in inspected:
        return EvidenceSourceType.TRANSFORMATION_EXAMPLE
    return EvidenceSourceType.DATA_DICTIONARY


def _clinical_domain_for(path: Path, text: str) -> str:
    inspected = f"{path} {text[:1000]}".lower()
    if any(
        term in inspected
        for term in [
            "allergy",
            "allergies",
            "intolerance",
            "allergyintolerance",
            "adverse reaction",
            "reaction manifestation",
            "latex sensitivity",
        ]
    ):
        return "allergy"
    if any(
        term in inspected
        for term in [
            "condition",
            "diagnosis",
            "diagnoses",
            "problem list",
            "problem-list",
            "icd-10",
            "snomed",
        ]
    ):
        return "problem_list"
    if any(
        term in inspected
        for term in [
            "lab",
            "laboratory",
            "observation",
            "hba1c",
            "glucose",
            "creatinine",
            "sodium",
            "potassium",
            "cholesterol",
        ]
    ):
        return "laboratory"
    if any(term in inspected for term in ["medication", "rxnorm", "drug", "openfda", "ndc"]):
        return "medication"
    if any(
        term in inspected
        for term in ["mesh", "pubmed", "medline", "literature", "clinicaltrials", "trial"]
    ):
        return "literature"
    if any(term in inspected for term in ["fhir", "hl7", "interoperability"]):
        return "interoperability"
    if any(term in inspected for term in ["omop", "analytics", "cohort"]):
        return "analytics"
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
        "MeSH": ["mesh", "pubmed", "medline"],
        "OMOP": ["omop"],
        "ClinicalTrials.gov": ["clinicaltrials.gov", "clinicaltrials"],
        "openFDA": ["openfda", "fda adverse", "drug label"],
        "SNOMED CT": ["snomed"],
        "ICD-10-CM": ["icd-10"],
        "MedlinePlus": ["medlineplus"],
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
