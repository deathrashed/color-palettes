#!/usr/bin/env python3
"""Regenerate Apple .clr files for canonical palettes in palettes.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "palettes.json"
DEFAULT_COLORGEN = REPO_ROOT / "bin" / "colorgen"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate .clr files for palettes with canonical sources."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="Palette manifest, default: palettes.json",
    )
    parser.add_argument(
        "--colorgen",
        type=Path,
        default=DEFAULT_COLORGEN,
        help="colorgen executable, default: bin/colorgen",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="ID",
        help="Refresh only this palette id. May be passed more than once.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned conversions without writing files.",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    palettes = manifest.get("palettes", [])
    requested = set(args.only)

    if not args.colorgen.is_file():
        print(f"colorgen not found: {args.colorgen}", file=sys.stderr)
        return 1

    selected = [
        palette
        for palette in palettes
        if palette.get("source_status") == "canonical"
        and palette.get("source")
        and (not requested or palette.get("id") in requested)
    ]

    missing = requested - {palette.get("id") for palette in selected}
    if missing:
        print(f"No canonical palette found for: {', '.join(sorted(missing))}", file=sys.stderr)
        return 1

    if not selected:
        print("No canonical palettes to refresh.")
        return 0

    failures = 0
    for palette in selected:
        source = REPO_ROOT / palette["source"]
        output = REPO_ROOT / palette["clr"]
        output_stem = output.with_suffix("")

        if not source.is_file():
            print(f"FAIL {palette['id']}: missing source {palette['source']}")
            failures += 1
            continue

        relative_source = source.relative_to(REPO_ROOT)
        relative_output = output.relative_to(REPO_ROOT)
        if args.dry_run:
            print(f"DRY  {palette['id']}: {relative_source} -> {relative_output}")
            continue

        result = subprocess.run(
            [str(args.colorgen), "-i", str(source), "-o", str(output_stem)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"FAIL {palette['id']}: {relative_source}")
            if result.stdout:
                print(result.stdout.rstrip())
            if result.stderr:
                print(result.stderr.rstrip())
            failures += 1
            continue

        output_text = "\n".join(
            text.rstrip() for text in (result.stdout, result.stderr) if text.strip()
        )
        print(f"OK   {palette['id']}: {relative_output}")
        if output_text:
            print(output_text)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
