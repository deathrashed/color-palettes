#!/usr/bin/env python3
"""Validate palettes.json against files in the repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "palettes.json"
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
VALID_SOURCE_STATUSES = {"canonical", "binary-only", "external", "derived"}


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    palettes = data.get("palettes")
    if not isinstance(palettes, list):
        fail("palettes.json must contain a palettes array")

    seen_ids: set[str] = set()
    seen_clr: set[str] = set()
    failures = 0

    for index, palette in enumerate(palettes, start=1):
        label = palette.get("id") or f"palette #{index}"
        if not isinstance(palette, dict):
            print(f"FAIL {label}: entry must be an object")
            failures += 1
            continue

        failures += check_required_string(palette, "id", label)
        failures += check_required_string(palette, "name", label)
        failures += check_required_string(palette, "clr", label)
        failures += check_source_status(palette, label)

        palette_id = palette.get("id")
        if isinstance(palette_id, str):
            if palette_id in seen_ids:
                print(f"FAIL {label}: duplicate id")
                failures += 1
            seen_ids.add(palette_id)

        clr = palette.get("clr")
        if isinstance(clr, str):
            if clr in seen_clr:
                print(f"FAIL {label}: duplicate clr path {clr}")
                failures += 1
            seen_clr.add(clr)
            failures += check_existing_file(clr, label, "clr")

        source = palette.get("source")
        if source is not None:
            if not isinstance(source, str):
                print(f"FAIL {label}: source must be a string or null")
                failures += 1
            else:
                failures += check_existing_file(source, label, "source")
                failures += check_source_palette(source, palette, label)

    failures += check_clr_coverage(seen_clr)

    if failures:
        print(f"{failures} palette manifest check(s) failed", file=sys.stderr)
        return 1

    print(f"OK   palettes.json ({len(palettes)} palettes)")
    return 0


def check_required_string(palette: dict, key: str, label: str) -> int:
    value = palette.get(key)
    if not isinstance(value, str) or not value:
        print(f"FAIL {label}: {key} must be a non-empty string")
        return 1
    return 0


def check_source_status(palette: dict, label: str) -> int:
    status = palette.get("source_status")
    if status not in VALID_SOURCE_STATUSES:
        print(
            f"FAIL {label}: source_status must be one of "
            f"{', '.join(sorted(VALID_SOURCE_STATUSES))}"
        )
        return 1
    if status == "canonical" and not palette.get("source"):
        print(f"FAIL {label}: canonical palettes need a source path")
        return 1
    return 0


def check_existing_file(path_text: str, label: str, field: str) -> int:
    path = REPO_ROOT / path_text
    if not path.is_file():
        print(f"FAIL {label}: {field} file does not exist: {path_text}")
        return 1
    return 0


def check_source_palette(path_text: str, palette: dict, label: str) -> int:
    path = REPO_ROOT / path_text
    if path.suffix.lower() != ".json" or not path.is_file():
        return 0

    try:
        source = load_colorgen_json(path)
    except json.JSONDecodeError as error:
        print(f"FAIL {label}: source JSON could not be parsed: {path_text}:{error.lineno}")
        return 1
    colors = source.get("colors")
    if not isinstance(colors, list):
        print(f"FAIL {label}: source JSON must contain a colors array")
        return 1

    failures = 0
    for color_index, color in enumerate(colors, start=1):
        if not isinstance(color, dict):
            print(f"FAIL {label}: source color #{color_index} must be an object")
            failures += 1
            continue
        if not isinstance(color.get("name"), str) or not color["name"]:
            print(f"FAIL {label}: source color #{color_index} needs a name")
            failures += 1
        if not isinstance(color.get("hex"), str) or not HEX_RE.match(color["hex"]):
            print(f"FAIL {label}: source color #{color_index} needs #rrggbb hex")
            failures += 1

    expected_count = palette.get("color_count")
    if expected_count is not None and expected_count != len(colors):
        print(
            f"FAIL {label}: manifest color_count {expected_count} "
            f"does not match source count {len(colors)}"
        )
        failures += 1

    return failures


def check_clr_coverage(manifest_clr_paths: set[str]) -> int:
    failures = 0
    for path in sorted((REPO_ROOT / "clr").glob("*.clr")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative not in manifest_clr_paths:
            print(f"FAIL manifest: missing clr entry for {relative}")
            failures += 1
    return failures


def load_colorgen_json(path: Path) -> dict:
    """Load source JSON while tolerating trailing commas accepted by colorgen."""
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA_RE.sub(r"\1", text))


def fail(message: str) -> None:
    raise SystemExit(message)


if __name__ == "__main__":
    raise SystemExit(main())
