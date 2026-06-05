import json

import pytest

from ojtflow.infrastructure.assistant_examples import load_assistant_examples


def test_assistant_examples_registry_loads_fresh_file_content(tmp_path) -> None:
    registry_dir = tmp_path / "assistant"
    registry_dir.mkdir()
    examples_path = registry_dir / "examples.json"
    examples_path.write_text(
        json.dumps(
            {
                "version": "assistant_examples.v1",
                "examples": [
                    {
                        "example_id": "example",
                        "label": "Original",
                        "description": "Original description",
                        "message": "Find evidence",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_assistant_examples(tmp_path)[0].label == "Original"

    examples_path.write_text(
        json.dumps(
            {
                "version": "assistant_examples.v1",
                "examples": [
                    {
                        "example_id": "example",
                        "label": "Reloaded",
                        "description": "Reloaded description",
                        "message": "Show pending reviews",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_assistant_examples(tmp_path)[0].label == "Reloaded"


def test_assistant_examples_registry_rejects_duplicate_ids(tmp_path) -> None:
    registry_dir = tmp_path / "assistant"
    registry_dir.mkdir()
    (registry_dir / "examples.json").write_text(
        json.dumps(
            {
                "version": "assistant_examples.v1",
                "examples": [
                    {
                        "example_id": "duplicate",
                        "label": "One",
                        "description": "One",
                        "message": "Find evidence",
                    },
                    {
                        "example_id": "duplicate",
                        "label": "Two",
                        "description": "Two",
                        "message": "Find evidence",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate example_id duplicate"):
        load_assistant_examples(tmp_path)
