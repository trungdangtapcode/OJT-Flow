"""Real AI/RAG smoke tests against a running backend.

These tests are product smoke tests, not unit tests. They do not use fake
providers, dependency overrides, ASGI transports, static fixtures, monkeypatches,
or deterministic fallback providers. A pass here should mean the live API,
authentication, GPU visibility, configured provider metadata, vector retrieval,
Graph-NER handoff, and assistant citation behavior are working together.

Required environment:
- OJT_REAL_SMOKE_API_BASE_URL, defaults to http://127.0.0.1:18000
- OJT_REAL_SMOKE_AUTH_TOKEN, optional OJTFlow bearer token. If omitted, the test
  issues a real local service-account token from the configured auth database.
"""

from __future__ import annotations

import os
import base64
import math
import subprocess
import struct
import zlib
from pathlib import Path
from typing import Any

import httpx
import pytest


API_BASE_URL = os.getenv("OJT_REAL_SMOKE_API_BASE_URL", "http://127.0.0.1:18000").rstrip(
    "/"
)
_CACHED_AUTH_TOKEN = os.getenv("OJT_REAL_SMOKE_AUTH_TOKEN", "")
TIMEOUT_SECONDS = float(os.getenv("OJT_REAL_SMOKE_TIMEOUT_SECONDS", "60"))

FORBIDDEN_PROVIDER_TERMS = (
    "deterministic",
    "fake",
    "mock",
    "stub",
    "hash",
    "sha256",
    "random",
    "lexical",
    "keyword",
    "bm25",
    "test",
)

LAB_QUERY_VI = "Tôi cần bằng chứng FHIR Observation cho HbA1c và đơn vị xét nghiệm"
EXPECTED_LAB_SOURCES = {
    "standard:fhir_observation_r4",
    "terminology:loinc",
}
LAB_CSV_BYTES = b"patient_id,lab_name,value,unit\nP001,HbA1c,7.4,%\n"
DIABETES_VISIT_LINES = [
    "RIVER CITY HOSPITAL",
    "DIABETES FOLLOW-UP VISIT SUMMARY",
    "PATIENT MAYA TRAN",
    "DOB 1978-04-12 MRN MRN-004219",
    "PROVIDER DR AMY LEE",
    "VISIT DATE 2026-06-11",
    "REASON DIABETES FOLLOW-UP",
    "PROBLEM LIST",
    "TYPE 2 DIABETES",
    "HYPERLIPIDEMIA",
    "LAB RESULTS",
    "TEST VALUE UNIT FLAG",
    "HBA1C 7.4 % HIGH",
    "GLUCOSE 182 MG/DL HIGH",
    "CREATININE 0.9 MG/DL NORMAL",
    "LDL 138 MG/DL HIGH",
    "MEDICATIONS",
    "METFORMIN 1000 MG BID",
    "ATORVASTATIN 20 MG NIGHTLY",
    "LISINOPRIL 10 MG DAILY",
    "ASSESSMENT A1C ABOVE GOAL",
    "REVIEW MEDS",
    "DIET AND EXERCISE",
    "FOLLOW UP 3 MONTHS",
    "SIGNED DR AMY LEE",
]
DIABETES_VISIT_CLINICAL_FACTS = (
    "RIVER CITY HOSPITAL",
    "DIABETES FOLLOW-UP VISIT SUMMARY",
    "VISIT DATE 2026-06-11",
    "REASON DIABETES FOLLOW-UP",
    "TYPE 2 DIABETES",
    "HYPERLIPIDEMIA",
    "HBA1C 7.4 % HIGH",
    "GLUCOSE 182 MG/DL HIGH",
    "CREATININE 0.9 MG/DL NORMAL",
    "LDL 138 MG/DL HIGH",
    "METFORMIN 1000 MG BID",
    "ATORVASTATIN 20 MG NIGHTLY",
    "LISINOPRIL 10 MG DAILY",
    "ASSESSMENT A1C ABOVE GOAL",
    "REVIEW MEDS",
    "PLAN DIET AND EXERCISE",
    "FOLLOW UP 3 MONTHS",
)
DIABETES_VISIT_PHI_FACT_GROUPS = (
    ("PATIENT MAYA TRAN", "PATIENT REDACTED", "PATIENT NAME REDACTED"),
    ("DOB 1978-04-12", "DOB REDACTED"),
    ("MRN MRN-004219", "MRN REDACTED"),
    ("PROVIDER DR AMY LEE", "PROVIDER REDACTED", "PROVIDER NAME REDACTED"),
    ("SIGNED DR AMY LEE", "SIGNED REDACTED", "SIGNED PROVIDER REDACTED"),
)
_DIABETES_VISIT_SCAN_RGB_CACHE: tuple[int, int, bytes] | None = None

_FONT_5X7 = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "%": ("10001", "00010", "00100", "01000", "10000", "00000", "10001"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("10010", "10010", "10010", "11111", "00010", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01111", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "11110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_auth_token()}"}


def _auth_token() -> str:
    global _CACHED_AUTH_TOKEN
    if _CACHED_AUTH_TOKEN:
        return _CACHED_AUTH_TOKEN
    try:
        _CACHED_AUTH_TOKEN = _issue_local_smoke_token()
    except Exception as exc:
        pytest.fail(
            "OJT_REAL_SMOKE_AUTH_TOKEN is empty and the test could not issue a "
            f"real local service-account token: {exc}"
        )
    return _CACHED_AUTH_TOKEN


def _issue_local_smoke_token() -> str:
    _load_dotenv_defaults()

    from ojtflow.config import get_settings
    from ojtflow.core.contracts.auth import GoogleIdentityProfile
    from ojtflow.interfaces.api.deps import (
        _build_auth_service,
        _build_governance_service,
    )

    settings = get_settings()
    auth = _build_auth_service()
    governance = _build_governance_service()

    owner = auth.repository.upsert_google_user(
        GoogleIdentityProfile(
            google_sub="local-real-smoke-owner",
            email="local-real-smoke-owner@ojtflow.local",
            email_verified=True,
            display_name="Local Real Smoke Owner",
        )
    )
    workspace = governance.get_or_create_current_workspace(owner)
    role_key = settings.service_account_default_role_key
    slug = "real-smoke"

    service_account = next(
        (
            account
            for account in auth.list_service_accounts(
                organization_id=workspace.organization.organization_id
            )
            if account.slug == slug
        ),
        None,
    )
    if service_account is None:
        service_account = auth.create_service_account_identity(
            organization_id=workspace.organization.organization_id,
            slug=slug,
            display_name="Real Smoke Service Account",
            role_key=role_key,
            created_by_user_id=owner.user_id,
        )

    try:
        governance.add_organization_member(
            user=owner,
            organization_id=workspace.organization.organization_id,
            member_user_id=service_account.user_id,
            role_key=role_key,
        )
    except Exception as exc:
        message = str(exc).lower()
        if (
            "unique" not in message
            and "duplicate" not in message
            and "already exists" not in message
        ):
            raise

    token = auth.issue_service_account_token(service_account=service_account)
    access_token = str(token["access_token"])
    assert access_token.startswith("ojt_sa_")
    return access_token


def _load_dotenv_defaults() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AssertionError(
            f"API returned non-JSON response: {response.text[:500]}"
        ) from exc
    assert isinstance(payload, dict)
    assert payload.get("error") is None, payload.get("error")
    return payload


def _diabetes_visit_png_bytes() -> bytes:
    width, height, pixels = _diabetes_visit_scan_rgb()
    return _png_from_rgb(width, height, pixels)


def _diabetes_visit_scanned_pdf_bytes() -> bytes:
    width, height, pixels = _diabetes_visit_scan_rgb()
    return _pdf_from_rgb_image(width, height, pixels)


def _diabetes_visit_scan_rgb() -> tuple[int, int, bytes]:
    global _DIABETES_VISIT_SCAN_RGB_CACHE
    if _DIABETES_VISIT_SCAN_RGB_CACHE is None:
        base_width, base_height, base_pixels = _render_diabetes_visit_summary_rgb()
        rotated_width, rotated_height, rotated_pixels = _rotate_rgb(
            base_width,
            base_height,
            base_pixels,
            degrees=-3.5,
        )
        noisy_pixels = _add_scan_noise(rotated_width, rotated_height, rotated_pixels)
        _DIABETES_VISIT_SCAN_RGB_CACHE = rotated_width, rotated_height, noisy_pixels
    return _DIABETES_VISIT_SCAN_RGB_CACHE


def _render_diabetes_visit_summary_rgb() -> tuple[int, int, bytes]:
    width = 1700
    height = 2200
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            shade = 252 - (1 if (x + y) % 23 == 0 else 0)
            pixels.extend((shade, shade, shade))

    def text(x: int, y: int, value: str, *, scale: int = 5) -> None:
        _draw_text_rgb(pixels, width, height, x, y, value, scale=scale)

    def rect(x0: int, y0: int, x1: int, y1: int, shade: int = 80) -> None:
        _draw_rect_rgb(pixels, width, height, x0, y0, x1, y1, shade=shade)

    def line(x0: int, y0: int, x1: int, y1: int, shade: int = 120) -> None:
        _draw_line_rgb(pixels, width, height, x0, y0, x1, y1, shade=shade)

    rect(60, 54, width - 60, height - 54, shade=120)
    text(96, 96, "RIVER CITY HOSPITAL", scale=8)
    text(96, 178, "DIABETES FOLLOW-UP VISIT SUMMARY", scale=5)
    text(1150, 108, "PORTAL EXPORT", scale=4)
    text(1150, 158, "PAGE 1 OF 1", scale=4)
    line(80, 245, width - 80, 245, shade=100)

    rect(90, 285, width - 90, 610, shade=100)
    line(90, 360, width - 90, 360, shade=160)
    line(900, 285, 900, 610, shade=160)
    text(120, 313, "PATIENT INFORMATION", scale=4)
    text(930, 313, "VISIT INFORMATION", scale=4)
    text(120, 392, "PATIENT MAYA TRAN", scale=5)
    text(120, 462, "DOB 1978-04-12", scale=5)
    text(120, 532, "MRN MRN-004219", scale=5)
    text(930, 392, "PROVIDER DR AMY LEE", scale=5)
    text(930, 462, "VISIT DATE 2026-06-11", scale=5)
    text(930, 532, "REASON DIABETES FOLLOW-UP", scale=4)

    rect(90, 655, width - 90, 820, shade=100)
    text(120, 690, "PROBLEM LIST", scale=4)
    text(120, 755, "TYPE 2 DIABETES", scale=5)
    text(760, 755, "HYPERLIPIDEMIA", scale=5)

    rect(90, 865, width - 90, 1215, shade=100)
    text(120, 900, "LAB RESULTS", scale=5)
    y_header = 975
    row_h = 58
    x_cols = [110, 610, 900, 1185, width - 110]
    for x in x_cols:
        line(x, y_header - 20, x, y_header + row_h * 5, shade=150)
    for row in range(6):
        y = y_header - 20 + row * row_h
        line(110, y, width - 110, y, shade=150)
    text(135, y_header, "TEST", scale=4)
    text(635, y_header, "VALUE", scale=4)
    text(925, y_header, "UNIT", scale=4)
    text(1210, y_header, "FLAG", scale=4)
    lab_rows = [
        ("HBA1C", "7.4", "%", "HIGH"),
        ("GLUCOSE", "182", "MG/DL", "HIGH"),
        ("CREATININE", "0.9", "MG/DL", "NORMAL"),
        ("LDL", "138", "MG/DL", "HIGH"),
    ]
    for row_index, (name, value, unit, flag) in enumerate(lab_rows, start=1):
        y = y_header + row_h * row_index
        text(135, y, name, scale=4)
        text(635, y, value, scale=4)
        text(925, y, unit, scale=4)
        text(1210, y, flag, scale=4)

    rect(90, 1265, width - 90, 1545, shade=100)
    text(120, 1300, "MEDICATIONS", scale=5)
    med_rows = [
        "METFORMIN 1000 MG BID",
        "ATORVASTATIN 20 MG NIGHTLY",
        "LISINOPRIL 10 MG DAILY",
    ]
    for index, value in enumerate(med_rows):
        y = 1375 + index * 58
        line(110, y - 20, width - 110, y - 20, shade=170)
        text(135, y, value, scale=4)

    rect(90, 1590, width - 90, 1975, shade=100)
    text(120, 1625, "ASSESSMENT A1C ABOVE GOAL", scale=5)
    text(120, 1715, "PLAN REVIEW MEDS", scale=5)
    text(120, 1795, "PLAN DIET AND EXERCISE", scale=5)
    text(120, 1875, "FOLLOW UP 3 MONTHS", scale=5)

    line(90, 2055, width - 90, 2055, shade=150)
    text(120, 2015, "SIGNED DR AMY LEE", scale=5)
    text(120, 2100, "RIVER CITY HOSPITAL PORTAL", scale=4)
    text(1180, 2100, "CONFIDENTIAL", scale=4)

    return width, height, bytes(pixels)


def _render_block_text_rgb(lines: list[str]) -> tuple[int, int, bytes]:
    scale = 8
    margin = 44
    char_width = 5
    char_height = 7
    char_spacing = 2
    line_spacing = 5
    width = max(len(line) for line in lines) * (char_width + char_spacing) * scale
    width += margin * 2
    height = len(lines) * (char_height + line_spacing) * scale + margin * 2
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            shade = 248 - (1 if (x + y) % 17 == 0 else 0)
            pixels.extend((shade, shade, shade - 1))

    for y in range(margin - 16, height - margin + 18, (char_height + line_spacing) * scale):
        if 0 <= y < height:
            for x in range(margin - 14, width - margin + 14):
                offset = (y * width + x) * 3
                pixels[offset : offset + 3] = b"\xd8\xd8\xd8"

    for line_index, line in enumerate(lines):
        y0 = margin + line_index * (char_height + line_spacing) * scale
        for char_index, char in enumerate(line.upper()):
            pattern = _FONT_5X7.get(char, _FONT_5X7[" "])
            x0 = margin + char_index * (char_width + char_spacing) * scale
            for row_index, row in enumerate(pattern):
                for col_index, bit in enumerate(row):
                    if bit != "1":
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            x = x0 + col_index * scale + dx
                            y = y0 + row_index * scale + dy
                            offset = (y * width + x) * 3
                            pixels[offset : offset + 3] = b"\x18\x18\x18"

    return width, height, bytes(pixels)


def _draw_text_rgb(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    text: str,
    *,
    scale: int,
) -> None:
    for char_index, char in enumerate(text.upper()):
        pattern = _FONT_5X7.get(char, _FONT_5X7[" "])
        x_char = x0 + char_index * (5 + 2) * scale
        for row_index, row in enumerate(pattern):
            for col_index, bit in enumerate(row):
                if bit != "1":
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        x = x_char + col_index * scale + dx
                        y = y0 + row_index * scale + dy
                        if 0 <= x < width and 0 <= y < height:
                            offset = (y * width + x) * 3
                            pixels[offset : offset + 3] = b"\x18\x18\x18"


def _draw_rect_rgb(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    shade: int,
) -> None:
    _draw_line_rgb(pixels, width, height, x0, y0, x1, y0, shade=shade)
    _draw_line_rgb(pixels, width, height, x1, y0, x1, y1, shade=shade)
    _draw_line_rgb(pixels, width, height, x1, y1, x0, y1, shade=shade)
    _draw_line_rgb(pixels, width, height, x0, y1, x0, y0, shade=shade)


def _draw_line_rgb(
    pixels: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    shade: int,
) -> None:
    if x0 == x1:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            if 0 <= x0 < width and 0 <= y < height:
                offset = (y * width + x0) * 3
                pixels[offset : offset + 3] = bytes((shade, shade, shade))
        return
    if y0 == y1:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            if 0 <= x < width and 0 <= y0 < height:
                offset = (y0 * width + x) * 3
                pixels[offset : offset + 3] = bytes((shade, shade, shade))
        return
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for step in range(steps + 1):
        x = round(x0 + (x1 - x0) * step / steps)
        y = round(y0 + (y1 - y0) * step / steps)
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset : offset + 3] = bytes((shade, shade, shade))


def _rotate_rgb(
    width: int,
    height: int,
    pixels: bytes,
    *,
    degrees: float,
) -> tuple[int, int, bytes]:
    radians = math.radians(degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    new_width = int(abs(width * cos_a) + abs(height * sin_a)) + 36
    new_height = int(abs(width * sin_a) + abs(height * cos_a)) + 36
    src_cx = (width - 1) / 2
    src_cy = (height - 1) / 2
    dst_cx = (new_width - 1) / 2
    dst_cy = (new_height - 1) / 2
    out = bytearray([250] * new_width * new_height * 3)

    for y in range(new_height):
        dy = y - dst_cy
        for x in range(new_width):
            dx = x - dst_cx
            src_x = cos_a * dx + sin_a * dy + src_cx
            src_y = -sin_a * dx + cos_a * dy + src_cy
            nearest_x = int(round(src_x))
            nearest_y = int(round(src_y))
            if 0 <= nearest_x < width and 0 <= nearest_y < height:
                src_offset = (nearest_y * width + nearest_x) * 3
                dst_offset = (y * new_width + x) * 3
                out[dst_offset : dst_offset + 3] = pixels[src_offset : src_offset + 3]

    return new_width, new_height, bytes(out)


def _add_scan_noise(width: int, height: int, pixels: bytes) -> bytes:
    out = bytearray(pixels)
    for y in range(height):
        row_shadow = -7 if y % 61 == 0 else 0
        for x in range(width):
            offset = (y * width + x) * 3
            speckle = ((x * 37 + y * 101 + 17) % 43) - 21
            if (x * 19 + y * 29) % 1543 == 0:
                out[offset : offset + 3] = b"\x33\x33\x33"
                continue
            for channel in range(3):
                value = out[offset + channel] + speckle + row_shadow
                out[offset + channel] = max(0, min(255, value))
    return bytes(out)


def _png_from_rgb(width: int, height: int, pixels: bytes) -> bytes:
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(pixels[start : start + stride])

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )


def _pdf_from_rgb_image(width: int, height: int, pixels: bytes) -> bytes:
    page_width = 612.0
    page_height = page_width * height / width
    image_stream = zlib.compress(pixels, level=9)
    content = f"q {page_width:.2f} 0 0 {page_height:.2f} 0 0 cm /Im0 Do Q\n".encode(
        "ascii"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            + f"/MediaBox [0 0 {page_width:.2f} {page_height:.2f}] ".encode("ascii")
            + b"/Resources << /XObject << /Im0 5 0 R >> >> "
            + b"/Contents 4 0 R >>"
        ),
        (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"endstream"
        ),
        (
            b"<< /Type /XObject /Subtype /Image "
            + f"/Width {width} /Height {height} ".encode("ascii")
            + b"/ColorSpace /DeviceRGB /BitsPerComponent 8 "
            + f"/Filter /FlateDecode /Length {len(image_stream)} >>\nstream\n".encode(
                "ascii"
            )
            + image_stream
            + b"\nendstream"
        ),
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def _gpu_name() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return str(torch.cuda.get_device_name(0))
    except Exception:
        pass

    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.splitlines()[0].strip()
    pytest.fail("GPU is not visible through torch.cuda or nvidia-smi")


def _source_ids_from_hits(payload: dict[str, Any]) -> list[str]:
    source_ids: list[str] = []
    for hit in payload.get("hits") or []:
        evidence = hit.get("evidence") or {}
        source_id = evidence.get("source_id")
        assert isinstance(source_id, str) and source_id, hit
        source_ids.append(source_id)
    return source_ids


def _source_ids_from_findings(payload: dict[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for finding in payload.get("findings") or []:
        source_ids.update(str(source_id) for source_id in finding.get("source_ids") or [])
    return source_ids


def _citation_source_ids(answer: dict[str, Any]) -> set[str]:
    return {
        str(citation["source_id"])
        for citation in answer.get("citations") or []
        if citation.get("source_id")
    }


def _assert_no_forbidden_provider_terms(*values: object) -> None:
    joined = " ".join(str(value).lower() for value in values if value is not None)
    forbidden = [term for term in FORBIDDEN_PROVIDER_TERMS if term in joined]
    assert forbidden == [], f"forbidden fake/non-semantic provider metadata: {forbidden}"


def _normalized_upper_text(text: str) -> str:
    return " ".join(
        "".join(char if char.isalnum() or char in {"%", "-"} else " " for char in text.upper()).split()
    )


def _assert_exact_diabetes_visit_facts(text: str) -> None:
    normalized = _normalized_upper_text(text)
    missing = [
        fact
        for fact in DIABETES_VISIT_CLINICAL_FACTS
        if _normalized_upper_text(fact) not in normalized
    ]
    missing_phi_context = [
        " or ".join(options)
        for options in DIABETES_VISIT_PHI_FACT_GROUPS
        if not any(_normalized_upper_text(option) in normalized for option in options)
    ]
    forbidden_confusions = {
        "RIVER C1TY": "RIVER CITY",
        "MAYA TRAM": "MAYA TRAN",
        "AMV LEE": "AMY LEE",
        "HBALC": "HBA1C",
        "HBAIC": "HBA1C",
        "CREATINLNE": "CREATININE",
        "AT0RVASTATIN": "ATORVASTATIN",
        "LISIN0PRIL": "LISINOPRIL",
    }
    observed_confusions = [
        f"{wrong} should be {right}"
        for wrong, right in forbidden_confusions.items()
        if _normalized_upper_text(wrong) in normalized
    ]

    assert missing == [], f"OCR missed generated clinical ground-truth facts: {missing}\n{text}"
    assert missing_phi_context == [], (
        "OCR neither preserved nor explicitly redacted expected PHI context: "
        f"{missing_phi_context}\n{text}"
    )
    assert observed_confusions == [], (
        f"OCR returned known wrong readings: {observed_confusions}\n{text}"
    )


def _assert_answer_contains_hba1c_fhir_unit_truth(message: str) -> None:
    normalized = _normalized_upper_text(message)
    required_terms = {
        "HBA1C",
        "FHIR",
        "OBSERVATION",
        "UNIT",
    }
    missing = [term for term in required_terms if term not in normalized]
    refusal_phrases = (
        "CANNOT ANSWER",
        "CAN T ANSWER",
        "KHONG THE TRA LOI",
        "KHÔNG THỂ TRẢ LỜI",
        "NO EVIDENCE",
    )
    refusals = [phrase for phrase in refusal_phrases if phrase in normalized]

    assert missing == [], f"answer missed required generated truth terms {missing}: {message}"
    assert refusals == [], f"answer refused or claimed no evidence despite expected evidence: {message}"


def test_live_runtime_config_uses_real_stack_real_provider_and_visible_gpu() -> None:
    assert _gpu_name()

    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text

        response = client.get("/api/v1/runtime/config", headers=_headers())
        assert response.status_code == 200, response.text
        data = _json(response)["data"]

    embedding = data["embedding"]
    llm = data["llm"]
    retrieval = data["retrieval"]

    assert data["storage_backend"] == "postgres"
    assert data["postgres_configured"] is True
    assert data["redis_configured"] is True
    assert embedding["provider"] in {"openai", "huggingface"}
    assert llm["provider"] == "openai"
    assert llm["openai_configured"] is True
    if embedding["provider"] == "openai":
        assert embedding["openai_configured"] is True
    else:
        assert str(embedding["hf_device"]).lower() not in {"cpu", "none"}

    assert retrieval["runtime_settings"]["retrieval_mode"] == "semantic_vector"
    assert retrieval["runtime_settings"]["retrieval_framework"] == "custom"
    _assert_no_forbidden_provider_terms(
        embedding["provider"],
        embedding["model"],
        llm["provider"],
        llm["model"],
        llm.get("planning_model"),
        llm.get("synthesis_model"),
    )


def test_live_workbench_file_upload_workflow_accepts_real_csv() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/parse/upload/workflow",
            headers=_headers(),
            data={
                "instruction": "Extract this CSV lab file, convert it to JSON, and validate it.",
                "target_format": "json",
                "schema_id": "lab_result_v1",
                "require_human_review": "false",
                "extractor": "auto",
            },
            files={
                "file": (
                    "real-smoke-lab.csv",
                    LAB_CSV_BYTES,
                    "text/csv",
                )
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    step_names = [step["name"] for step in data["steps"]]
    extraction_step = next(step for step in data["steps"] if step["name"] == "document_extraction")

    assert data["status"] == "completed"
    assert data["input"]["declared_format"] == "csv"
    assert data["intent"]["options"]["source_filename"] == "real-smoke-lab.csv"
    assert data["profile"]["row_count"] == 1
    assert data["profile"]["column_count"] == 4
    assert "document_extraction" in step_names
    assert "direct_text_upload" in extraction_step["summary"]
    assert data["intent"]["target_format"] == "json"
    assert data["output"]["transformation"]["output_ref"]


def test_live_assistant_file_attachment_extracts_real_csv() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/parse/extract",
            headers=_headers(),
            data={"extractor": "auto"},
            files={
                "file": (
                    "real-smoke-lab.csv",
                    LAB_CSV_BYTES,
                    "text/csv",
                )
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    text = data["text"]
    assert data["filename"] == "real-smoke-lab.csv"
    assert data["source_format"] == "csv"
    assert "HbA1c" in text
    assert "7.4" in text
    assert "fake" not in str(data).lower()


def test_live_assistant_file_attachment_extracts_scanned_diabetes_followup_pdf() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/parse/extract",
            headers=_headers(),
            data={"extractor": "auto"},
            files={
                "file": (
                    "real-smoke-scanned-diabetes-followup-visit.pdf",
                    _diabetes_visit_scanned_pdf_bytes(),
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    assert data["filename"] == "real-smoke-scanned-diabetes-followup-visit.pdf"
    assert data["source_format"] == "pdf"
    _assert_exact_diabetes_visit_facts(data["text"])
    assert "FAKE" not in str(data).upper()


def test_live_assistant_clipboard_image_auto_upload_returns_extracted_text() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/parse/clipboard/images/jobs",
            headers=_headers(),
            json={
                "data_base64": base64.b64encode(_diabetes_visit_png_bytes()).decode("ascii"),
                "mime_type": "image/png",
                "filename": "real-smoke-scanned-diabetes-followup-visit.png",
                "extractor": "auto",
                "execute_now": True,
                "include_extracted_document": True,
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    artifact = data["artifact"]
    job = data["job"]
    trace = data["trace"]
    extracted = data["extracted_document"]

    assert artifact["source"] == "clipboard"
    assert artifact["mime_type"] == "image/png"
    assert artifact["filename"] == "real-smoke-scanned-diabetes-followup-visit.png"
    assert job["status"] == "succeeded", job
    assert trace is not None
    assert extracted is not None
    assert extracted["artifact_id"] == artifact["artifact_id"]
    assert extracted["trace_id"] == trace["trace_id"]
    assert extracted["source"] == "clipboard"

    _assert_exact_diabetes_visit_facts(extracted["text"])
    assert "FAKE" not in str(trace.get("metadata", "")).upper()


def test_live_vector_retrieval_returns_expected_lab_sources_and_real_citations() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/retrieval/search",
            headers=_headers(),
            json={
                "query": LAB_QUERY_VI,
                "top_k": 3,
                "clinical_domain": "laboratory",
                "trust_level": "approved",
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    hits = data.get("hits") or []
    source_ids = _source_ids_from_hits(data)

    assert len(hits) == 3
    assert source_ids[0] == "standard:fhir_observation_r4", (
        "FHIR Observation should be the top result for an explicit FHIR "
        f"Observation HbA1c query; got {source_ids}"
    )
    assert EXPECTED_LAB_SOURCES.issubset(set(source_ids))

    answer = data.get("answer") or {}
    assert answer.get("status") == "supported", answer
    _assert_answer_contains_hba1c_fhir_unit_truth(answer.get("answer_text", ""))
    assert _citation_source_ids(answer).issubset(set(source_ids))
    assert EXPECTED_LAB_SOURCES & _citation_source_ids(answer)
    assert answer.get("unsupported_claims") == []

    graph = (data.get("handoff_context") or {}).get("graph_context") or {}
    node_ids = {node.get("id") for node in graph.get("nodes", [])}
    assert graph.get("graph_contract") == "graph_ner_handoff.v0"
    assert {"clinical_concept:hba1c_lab_test", "standard:fhir", "standard:ucum"} <= node_ids

    for hit in hits:
        evidence = hit["evidence"]
        metadata = ((evidence.get("source_locator") or {}).get("metadata") or {})
        _assert_no_forbidden_provider_terms(
            metadata.get("embedding_provider"),
            metadata.get("embedding_model"),
        )
        assert metadata.get("embedding_provider") in {"openai", "huggingface"}
        assert isinstance(metadata.get("retrieval_vector_distance"), float)
        assert metadata.get("retrieval_lexical_match") is False


@pytest.mark.parametrize(
    "query",
    [
        "What paperwork is needed for a downtown cafe parking permit?",
        "Which forms do I file for employee payroll tax withholding?",
        "How do I renew a Vietnamese passport at the consulate?",
    ],
)
def test_live_vector_retrieval_rejects_negative_queries_without_ranked_hits(
    query: str,
) -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/retrieval/search",
            headers=_headers(),
            json={"query": query, "top_k": 3, "trust_level": "approved"},
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    answer = data.get("answer") or {}

    assert data.get("hits") == [], (
        "negative out-of-domain queries must not return keyword-similar or random "
        f"ranked evidence; got {_source_ids_from_hits(data)}"
    )
    assert answer.get("status") == "refused", answer
    assert answer.get("citations") == []
    assert answer.get("claims") == []


def test_live_assistant_positive_rag_answer_has_retrieved_source_citations() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/assistant/chat",
            headers=_headers(),
            json={
                "message": (
                    "Answer only from trusted documents. In Vietnamese terms: "
                    "HbA1c và đơn vị xét nghiệm nên được biểu diễn ở đâu trong FHIR?"
                ),
                "context": {
                    "clinical_domain": "laboratory",
                    "fields": ["test_name", "result_value", "result_unit"],
                },
                "execute_write_actions": False,
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]

    assert data["mode"] == "llm"
    assert data.get("synthesis_mode") == "llm"

    evidence_summary = data.get("evidence_summary") or []
    findings_source_ids = _source_ids_from_findings(data)
    tool_source_ids = {
        str(evidence["source_id"])
        for tool_call in data.get("tool_calls") or []
        for evidence in ((tool_call.get("output") or {}).get("evidence") or [])
        if evidence.get("source_id")
    }

    assert evidence_summary, "assistant must not answer positive RAG queries without evidence"
    assert tool_source_ids, "assistant retrieval tool returned no evidence"
    assert findings_source_ids, "assistant findings contain no cited source_ids"
    assert findings_source_ids.issubset(tool_source_ids)
    assert EXPECTED_LAB_SOURCES & findings_source_ids
    _assert_answer_contains_hba1c_fhir_unit_truth(data.get("message", ""))
    assert "cannot answer" not in data.get("message", "").lower()
    assert "can't answer" not in data.get("message", "").lower()
    assert "can’t answer" not in data.get("message", "").lower()
    assert "không thể trả lời" not in data.get("message", "").lower()


def test_live_assistant_negative_question_refuses_without_fabricated_citations() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = client.post(
            "/api/v1/assistant/chat",
            headers=_headers(),
            json={
                "message": (
                    "Answer only from trusted documents: what paperwork is needed "
                    "for a downtown cafe parking permit?"
                ),
                "execute_write_actions": False,
            },
        )

    assert response.status_code == 200, response.text
    data = _json(response)["data"]
    message = data.get("message", "").lower()

    assert data["mode"] == "llm"
    assert data.get("synthesis_mode") == "llm"
    assert data.get("evidence_summary") == []
    assert _source_ids_from_findings(data) == set()
    assert any(
        phrase in message
        for phrase in ("can't answer", "can’t answer", "cannot answer")
    )
    assert "evidence" in message
