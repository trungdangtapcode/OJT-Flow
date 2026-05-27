"""Static knowledge repository for scaffold fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from ojtflow.core.contracts.enums import EvidenceSourceType, TrustLevel
from ojtflow.core.contracts.evidence import Evidence


class StaticKnowledgeRepository:
    """Loads trusted schemas and fixture evidence from local files."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.schemas_dir = self.root / "schemas"

    def get_schema(self, schema_id: str | None) -> dict | None:
        if not schema_id:
            return None
        path = self.schemas_dir / f"{schema_id}.schema.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_schemas(self) -> list[dict]:
        """Return lightweight schema registry entries for the product UI."""

        schemas: list[dict] = []
        for path in sorted(self.schemas_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            properties = schema.get("properties", {})
            schemas.append(
                {
                    "schema_id": schema.get("$id", path.name.removesuffix(".schema.json")),
                    "title": schema.get("title", schema.get("$id", path.stem)),
                    "version": schema.get("version", "unversioned"),
                    "required": schema.get("required", []),
                    "field_count": len(properties),
                    "fields": [
                        {
                            "name": name,
                            "type": definition.get("type", "unknown"),
                            "description": definition.get("description"),
                        }
                        for name, definition in properties.items()
                    ],
                    "source_ref": str(path.relative_to(self.root.parent)),
                }
            )
        return schemas

    def search(self, query: str, *, top_k: int = 5) -> list[Evidence]:
        """Return simple trusted evidence fixtures.

        This is intentionally plain. Hybrid retrieval, embeddings, and GraphRAG
        should replace this adapter without changing the application service.
        """

        lowered = query.lower()
        candidates = [
            Evidence(
                source_type=EvidenceSourceType.SCHEMA,
                source_id="schema:lab_result_v1",
                source_version="1.0.0",
                claim="Lab result records require date, patient_id, lab_name, value, and unit fields.",
                confidence=0.93,
                trust_level=TrustLevel.APPROVED,
            ),
            Evidence(
                source_type=EvidenceSourceType.DATA_DICTIONARY,
                source_id="dictionary:lab_fields_v1",
                source_version="1.0.0",
                claim="Missing lab units should be surfaced for human review before downstream use.",
                confidence=0.88,
                trust_level=TrustLevel.APPROVED,
            ),
            Evidence(
                source_type=EvidenceSourceType.TRANSFORMATION_EXAMPLE,
                source_id="example:csv_lab_to_json_records_v1",
                source_version="1.0.0",
                claim="CSV lab rows can be converted to JSON records when source rows and validation warnings are preserved.",
                confidence=0.81,
                trust_level=TrustLevel.APPROVED,
            ),
        ]
        if "patient" in lowered or "lab" in lowered or "csv" in lowered:
            return candidates[:top_k]
        return candidates[: min(1, top_k)]
