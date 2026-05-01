#!/usr/bin/env python3
"""Open ColorSlurp URL-scheme actions from palette files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode


TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or open colorslurp:// URL scheme actions."
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_only",
        help="Print the URL instead of opening ColorSlurp.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_simple_command(subparsers, "show", "Show ColorSlurp.")
    add_simple_command(subparsers, "magnifier", "Show the magnifier.")
    add_simple_command(subparsers, "palettes", "Show ColorSlurp palettes.")

    picker = subparsers.add_parser("picker", help="Show picker for a color.")
    add_color_arguments(picker)

    contrast = subparsers.add_parser("contrast", help="Show contrast for two colors.")
    contrast.add_argument("--foreground", "-f", required=True, help="Foreground color or palette selector.")
    contrast.add_argument("--background", "-b", required=True, help="Background color or palette selector.")
    contrast.add_argument("--palette", "-p", type=Path, help="Palette JSON used for selectors.")

    settings = subparsers.add_parser("settings", help="Show ColorSlurp settings.")
    settings.add_argument(
        "--tab",
        choices=("general", "shortcuts", "formats", "magnifier", "pro"),
        help="Settings tab.",
    )

    args = parser.parse_args()
    url = build_url(args)
    if args.print_only:
        print(url)
        return 0

    subprocess.run(["open", url], check=True)
    return 0


def add_simple_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str, help_text: str) -> None:
    subparsers.add_parser(name, help=help_text)


def add_color_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("color", nargs="?", help="Color string, hex value, palette color name, or 1-based index.")
    parser.add_argument("--palette", "-p", type=Path, help="Palette JSON used for name/index lookup.")


def build_url(args: argparse.Namespace) -> str:
    if args.command == "show":
        return colorslurp_url("show-colorslurp")
    if args.command == "magnifier":
        return colorslurp_url("show-magnifier")
    if args.command == "palettes":
        return colorslurp_url("show-palettes")
    if args.command == "settings":
        params = {"tab": args.tab} if args.tab else None
        return colorslurp_url("show-settings", params)
    if args.command == "picker":
        color = resolve_color(args.color, args.palette) if args.color else None
        params = {"color": color} if color else None
        return colorslurp_url("show-picker", params)
    if args.command == "contrast":
        foreground = resolve_color(args.foreground, args.palette)
        background = resolve_color(args.background, args.palette)
        return colorslurp_url("show-contrast", {"foreground": foreground, "background": background})

    raise SystemExit(f"Unknown command: {args.command}")


def colorslurp_url(action: str, params: dict[str, str] | None = None) -> str:
    base = f"colorslurp://x-callback-url/{quote(action)}"
    if not params:
        return base
    clean_params = {key: normalize_color_for_url(value) for key, value in params.items() if value}
    return f"{base}?{urlencode(clean_params)}"


def resolve_color(selector: str, palette_path: Path | None) -> str:
    direct = normalize_hex(selector)
    if direct:
        return direct

    if not palette_path:
        return selector

    colors = load_palette_colors(palette_path)
    if selector.isdigit():
        index = int(selector) - 1
        if 0 <= index < len(colors):
            return color_hex(colors[index])
        raise SystemExit(f"Palette index out of range: {selector}")

    selector_key = selector.strip().lower()
    for color in colors:
        name = str(color.get("name") or "").strip().lower()
        if name == selector_key:
            return color_hex(color)

    raise SystemExit(f"Color not found in {palette_path}: {selector}")


def load_palette_colors(path: Path) -> list[dict[str, Any]]:
    palette = load_relaxed_json(path)
    if isinstance(palette, list):
        colors = palette
    elif isinstance(palette, dict):
        colors = palette.get("colors")
    else:
        colors = None

    if not isinstance(colors, list):
        raise SystemExit(f"No colors array found in {path}")

    return [color for color in colors if isinstance(color, dict)]


def load_relaxed_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA_RE.sub(r"\1", text))


def color_hex(color: dict[str, Any]) -> str:
    hex_value = normalize_hex(color.get("hex") or color.get("color"))
    if not hex_value:
        raise SystemExit(f"Palette color has no usable hex value: {color}")
    return hex_value


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
    return clean.upper()


def normalize_color_for_url(value: str) -> str:
    return normalize_hex(value) or value


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"Could not open ColorSlurp URL: {error}", file=sys.stderr)
        raise SystemExit(error.returncode)
