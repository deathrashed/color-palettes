#!/usr/bin/env python3
"""Name palette colors from the bundled color-names reference list."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLOR_NAMES = REPO_ROOT / "data" / "color-names.csv"
TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
GENERIC_NAME_RE = re.compile(r"^(color|colour|swatch|unnamed|untitled)(\s*[-_#]?\s*\d+)?$", re.I)


@dataclass(frozen=True)
class NamedColor:
    name: str
    hex: str
    good_name: bool
    oklab: tuple[float, float, float]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest or apply human color names to palette JSON files."
    )
    parser.add_argument("palette", type=Path, help="Palette JSON file to name")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write renamed JSON to this path. Use --apply to overwrite input.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Overwrite the input palette JSON.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Rename every color, not only missing/generic names.",
    )
    parser.add_argument(
        "--field",
        default="name",
        choices=("name", "nearest_name"),
        help="Field to write. Default: name. Use nearest_name to keep existing names.",
    )
    parser.add_argument(
        "--prefer-good",
        action="store_true",
        help="Prefer rows marked as good names when choosing nearest names.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_COLOR_NAMES,
        help="Color-name CSV source, default: data/color-names.csv",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=None,
        help="Only write nearest names within this OKLab distance.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposed names without writing output.",
    )
    args = parser.parse_args()

    if args.apply and args.output:
        parser.error("--apply and --output are mutually exclusive")

    names = load_color_names(args.source, prefer_good=args.prefer_good)
    palette = load_relaxed_json(args.palette)
    colors = palette_colors(palette)

    if not colors:
        print(f"No colors found in {args.palette}", file=sys.stderr)
        return 1

    changes = []
    for index, color in enumerate(colors, start=1):
        if not isinstance(color, dict):
            continue
        hex_value = normalize_hex(color.get("hex") or color.get("color"))
        if not hex_value:
            continue

        current_name = str(color.get("name") or "").strip()
        should_write = args.all or args.field != "name" or is_generic_name(current_name)
        if not should_write:
            continue
        match, distance = nearest_name(hex_value, names)
        if not match:
            continue
        if args.max_distance is not None and distance > args.max_distance:
            continue

        proposed = match.name
        changes.append((index, hex_value, current_name, proposed, distance))
        if not args.dry_run:
            color[args.field] = proposed

    print_report(changes, args.field)

    if args.dry_run or not changes:
        return 0

    output_path = args.palette if args.apply else args.output
    if not output_path:
        print("No output requested. Use --dry-run, --output, or --apply.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(palette, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def load_color_names(path: Path, prefer_good: bool) -> list[NamedColor]:
    rows: list[NamedColor] = []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            hex_value = normalize_hex(row.get("hex"))
            name = (row.get("name") or "").strip()
            if not hex_value or not name:
                continue
            good_name = (row.get("good name") or "").strip().lower() == "x"
            rows.append(NamedColor(name, hex_value, good_name, rgb_to_oklab(hex_to_rgb(hex_value))))

    if prefer_good:
        rows.sort(key=lambda item: (not item.good_name, item.name.lower()))
    return rows


def load_relaxed_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA_RE.sub(r"\1", text))


def palette_colors(palette: Any) -> list[Any]:
    if isinstance(palette, list):
        return palette
    if isinstance(palette, dict) and isinstance(palette.get("colors"), list):
        return palette["colors"]
    return []


def nearest_name(hex_value: str, names: list[NamedColor]) -> tuple[NamedColor | None, float]:
    target = rgb_to_oklab(hex_to_rgb(hex_value))
    exact = next((item for item in names if item.hex == hex_value), None)
    if exact:
        return exact, 0.0

    best: NamedColor | None = None
    best_distance = math.inf
    for item in names:
        distance = oklab_distance(target, item.oklab)
        if distance < best_distance:
            best = item
            best_distance = distance
    return best, best_distance


def print_report(changes: list[tuple[int, str, str, str, float]], field: str) -> None:
    if not changes:
        print("No name suggestions.")
        return

    print(f"{'row':>4}  {'hex':<7}  {'distance':>8}  {'current':<28}  {field}")
    for index, hex_value, current_name, proposed, distance in changes:
        current = current_name or "(missing)"
        if len(current) > 28:
            current = current[:25] + "..."
        print(f"{index:>4}  {hex_value:<7}  {distance:>8.5f}  {current:<28}  {proposed}")


def is_generic_name(name: str) -> bool:
    return not name or bool(GENERIC_NAME_RE.match(name.strip()))


def normalize_hex(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    clean = value.strip().strip("'\"")
    if clean.startswith("#"):
        clean = clean[1:]
    elif clean.lower().startswith("0x"):
        clean = clean[2:]
    if len(clean) == 8:
        clean = clean[2:]
    if len(clean) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", clean):
        return None
    return f"#{clean.lower()}"


def hex_to_rgb(hex_value: str) -> tuple[float, float, float]:
    clean = hex_value.lstrip("#")
    return tuple(int(clean[index : index + 2], 16) / 255 for index in (0, 2, 4))  # type: ignore[return-value]


def linearize(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def rgb_to_oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = (linearize(channel) for channel in rgb)

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = math.copysign(abs(l) ** (1 / 3), l)
    m_ = math.copysign(abs(m) ** (1 / 3), m)
    s_ = math.copysign(abs(s) ** (1 / 3), s)

    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def oklab_distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


if __name__ == "__main__":
    raise SystemExit(main())
