#!/usr/bin/env python3
"""Scan logs for raw PHI-like values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ojtflow.observability.logging_guard import scan_paths_for_raw_phi, scan_text_for_raw_phi


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["logs", "var/logs"],
        help="Files or directories to scan.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Ignore paths that do not exist.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify scanner behavior with synthetic safe and unsafe samples.",
    )
    args = parser.parse_args()

    if args.self_test and not _self_test_passes():
        print("no_raw_phi_scan_self_test_failed", file=sys.stderr)
        return 1

    results = scan_paths_for_raw_phi(
        [Path(path) for path in args.paths],
        allow_missing=args.allow_missing,
    )
    if not results:
        print("no_raw_phi_scan_ok")
        return 0

    for result in results:
        for finding in result.findings:
            print(
                (
                    f"{finding.source_ref}:{finding.line_number}: "
                    f"{finding.kind}: {finding.reason}"
                ),
                file=sys.stderr,
            )
    return 1


def _self_test_passes() -> bool:
    unsafe = scan_text_for_raw_phi("patient_id=P001 ssn=123-45-6789")
    safe = scan_text_for_raw_phi(
        "patient_id=[REDACTED:PATIENT_IDENTIFIER] ssn=[REDACTED:SSN]"
    )
    return unsafe.finding_count >= 2 and safe.finding_count == 0


if __name__ == "__main__":
    raise SystemExit(main())
