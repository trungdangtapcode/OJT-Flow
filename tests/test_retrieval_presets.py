import json

from ojtflow.infrastructure.retrieval.presets import (
    load_retrieval_search_options,
    load_retrieval_search_presets,
)


def test_retrieval_registry_loads_fresh_file_content(tmp_path) -> None:
    registry_dir = tmp_path / "retrieval"
    registry_dir.mkdir()

    presets_path = registry_dir / "search_presets.json"
    presets_path.write_text(
        json.dumps(
            {
                "version": "retrieval_search_presets.v1",
                "presets": [
                    {
                        "preset_id": "demo",
                        "label": "Original",
                        "description": "Original preset",
                        "query": "FHIR Observation lab result",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert load_retrieval_search_presets(tmp_path)[0].label == "Original"

    presets_path.write_text(
        json.dumps(
            {
                "version": "retrieval_search_presets.v1",
                "presets": [
                    {
                        "preset_id": "demo",
                        "label": "Reloaded",
                        "description": "Reloaded preset",
                        "query": "PubMed HbA1c systematic review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert load_retrieval_search_presets(tmp_path)[0].label == "Reloaded"

    options_path = registry_dir / "search_options.json"
    options_path.write_text(
        json.dumps(
            {
                "version": "retrieval_search_options.v1",
                "detected_formats": [{"value": "csv", "label": "CSV"}],
                "top_k_values": [4],
            }
        ),
        encoding="utf-8",
    )
    assert load_retrieval_search_options(tmp_path).top_k_values == [4]

    options_path.write_text(
        json.dumps(
            {
                "version": "retrieval_search_options.v1",
                "detected_formats": [{"value": "markdown", "label": "Markdown"}],
                "top_k_values": [6],
            }
        ),
        encoding="utf-8",
    )
    options = load_retrieval_search_options(tmp_path)
    assert options.detected_formats[0].value == "markdown"
    assert options.top_k_values == [6]
