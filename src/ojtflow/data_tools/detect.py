"""Format detection."""

from __future__ import annotations

import csv
import json
from io import StringIO

import yaml

from ojtflow.core.contracts.data import FormatDetection
from ojtflow.core.contracts.enums import DataFormat


def detect_format(text: str, declared_format: DataFormat | None = None) -> FormatDetection:
    """Detect structured data format with conservative parser probes."""

    if declared_format and declared_format != DataFormat.UNKNOWN:
        return FormatDetection(
            format=declared_format,
            confidence=1.0,
            reasons=["format declared by caller"],
        )

    stripped = text.strip()
    if not stripped:
        return FormatDetection(
            format=DataFormat.UNKNOWN,
            confidence=0.0,
            warnings=["empty input"],
        )

    try:
        json.loads(stripped)
        return FormatDetection(format=DataFormat.JSON, confidence=0.96, reasons=["valid JSON"])
    except json.JSONDecodeError:
        pass

    if "\n" in stripped and ("," in stripped.splitlines()[0] or "\t" in stripped.splitlines()[0]):
        sample = StringIO(stripped)
        try:
            dialect = csv.Sniffer().sniff(sample.read(2048))
            sample.seek(0)
            rows = list(csv.reader(sample, dialect))
            if len(rows) >= 2:
                return FormatDetection(
                    format=DataFormat.CSV,
                    confidence=0.88,
                    reasons=["delimited header and multiple rows"],
                )
        except csv.Error:
            pass

    try:
        loaded = yaml.safe_load(stripped)
        if isinstance(loaded, dict | list):
            return FormatDetection(format=DataFormat.YAML, confidence=0.74, reasons=["safe YAML"])
    except yaml.YAMLError:
        pass

    return FormatDetection(
        format=DataFormat.UNKNOWN,
        confidence=0.0,
        warnings=["could not detect JSON, YAML, or CSV"],
    )

