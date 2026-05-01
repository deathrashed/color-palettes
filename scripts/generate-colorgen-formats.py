#!/usr/bin/env python3
"""Generate colorgen-compatible palette files from one canonical JSON file."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shlex
from pathlib import Path
from typing import Iterable


DEFAULT_FORMATS = [
    "json",
    "csv",
    "txt",
    "conf",
    "env",
    "yaml",
    "toml",
    "xml",
    "css",
    "html",
    "swift",
    "kt",
    "extensionless",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate palette source files that can be passed to colorgen."
    )
    parser.add_argument("source", type=Path, help="Canonical JSON palette file")
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("bin/formats/generated"),
        help="Output directory, default: bin/formats/generated",
    )
    parser.add_argument(
        "-b",
        "--basename",
        help="Output filename stem, default: source filename without extension",
    )
    parser.add_argument(
        "-f",
        "--formats",
        default=",".join(DEFAULT_FORMATS),
        help=f"Comma-separated formats, default: {','.join(DEFAULT_FORMATS)}",
    )
    args = parser.parse_args()

    palette = load_palette(args.source)
    basename = args.basename or args.source.stem
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]

    unknown = sorted(set(formats) - set(DEFAULT_FORMATS))
    if unknown:
        parser.error(f"unknown format(s): {', '.join(unknown)}")

    args.out.mkdir(parents=True, exist_ok=True)
    written = []
    for format_name in formats:
        path = output_path(args.out, basename, format_name)
        path.write_text(render_palette(palette, basename, format_name), encoding="utf-8")
        written.append(path)

    for path in written:
        print(path)
    return 0


def load_palette(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("source JSON must be an object with name and colors")

    name = str(data.get("name") or path.stem)
    colors = data.get("colors")
    if not isinstance(colors, list):
        raise SystemExit("source JSON must contain a colors array")

    normalized = []
    for index, item in enumerate(colors, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"color #{index} must be an object")
        color_name = item.get("name")
        color_hex = item.get("hex") or item.get("color")
        if not isinstance(color_name, str) or not isinstance(color_hex, str):
            raise SystemExit(f"color #{index} must contain string name and hex/color")
        normalized.append({"name": color_name, "hex": normalize_hex(color_hex)})

    return {"name": name, "colors": normalized}


def normalize_hex(value: str) -> str:
    clean = value.strip().strip("'\"")
    if clean.startswith("#"):
        clean = clean[1:]
    elif clean.lower().startswith("0x"):
        clean = clean[2:]
    if len(clean) == 8:
        clean = clean[2:]
    if len(clean) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", clean):
        raise SystemExit(f"invalid hex color: {value}")
    return f"#{clean.lower()}"


def output_path(directory: Path, basename: str, format_name: str) -> Path:
    if format_name == "extensionless":
        return directory / basename
    return directory / f"{basename}.{format_name}"


def render_palette(palette: dict, basename: str, format_name: str) -> str:
    renderers = {
        "json": render_json,
        "csv": render_csv,
        "txt": render_txt,
        "conf": render_conf,
        "env": render_env,
        "yaml": render_yaml,
        "toml": render_toml,
        "xml": render_xml,
        "css": render_css,
        "html": render_html,
        "swift": render_swift,
        "kt": render_kt,
        "extensionless": render_conf,
    }
    return renderers[format_name](palette, basename)


def render_json(palette: dict, _basename: str) -> str:
    return json.dumps(palette, indent=2, ensure_ascii=False) + "\n"


def render_csv(palette: dict, _basename: str) -> str:
    rows = [["name", "hex"], *[[color["name"], color["hex"]] for color in palette["colors"]]]
    lines = []
    for row in rows:
        output = []
        writer = csv.writer(output := CsvLineBuffer(), lineterminator="")
        writer.writerow(row)
        lines.append(output.value)
    return "\n".join(lines) + "\n"


class CsvLineBuffer:
    value = ""

    def write(self, value: str) -> None:
        self.value += value


def render_txt(palette: dict, basename: str) -> str:
    lines = [f"# {basename}", "Created for colorgen", ""]
    for color in palette["colors"]:
        lines.extend([f"*{color['name']}*", color["hex"].lstrip("#").upper(), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_conf(palette: dict, _basename: str) -> str:
    width = max(len(color["name"]) for color in palette["colors"])
    lines = [f"# {palette['name']}", f"name = {palette['name']}", ""]
    lines.extend(f"{color['name']:<{width}} = {color['hex']}" for color in palette["colors"])
    return "\n".join(lines) + "\n"


def render_env(palette: dict, _basename: str) -> str:
    lines = [f"# {palette['name']}", f"PALETTE_NAME={shlex.quote(palette['name'])}", ""]
    lines.extend(f"{env_name(color['name'])}={color['hex']}" for color in palette["colors"])
    return "\n".join(lines) + "\n"


def render_yaml(palette: dict, _basename: str) -> str:
    lines = [f"name: {quote_yaml(palette['name'])}", "colors:"]
    for color in palette["colors"]:
        lines.append(f"  - name: {quote_yaml(color['name'])}")
        lines.append(f"    hex: {quote_yaml(color['hex'])}")
    return "\n".join(lines) + "\n"


def render_toml(palette: dict, _basename: str) -> str:
    lines = [f"name = {json.dumps(palette['name'])}", ""]
    for color in palette["colors"]:
        lines.extend(["[[colors]]", f"name = {json.dumps(color['name'])}", f"hex = {json.dumps(color['hex'])}", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_xml(palette: dict, _basename: str) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for color in palette["colors"]:
        lines.append(f'  <color name="{html.escape(color["name"], quote=True)}">{color["hex"]}</color>')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def render_css(palette: dict, basename: str) -> str:
    selector = slug(basename)
    lines = [f"/* {palette['name']} */", f":root, .{selector} {{"]
    lines.extend(f"  --{slug(color['name'])}: {color['hex']};" for color in palette["colors"])
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_html(palette: dict, _basename: str) -> str:
    blocks = []
    for color in palette["colors"]:
        name = html.escape(color["name"])
        hex_value = html.escape(color["hex"])
        blocks.append(
            f'<div class="color">\n'
            f'  <div class="color-name">{name}</div>\n'
            f'  <div class="color-value">{hex_value}</div>\n'
            f"</div>"
        )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{html.escape(palette['name'])}</title>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{html.escape(palette['name'])}</h1>\n"
        "  <section class=\"colors\">\n"
        + "\n".join(blocks)
        + "\n  </section>\n"
        "</body>\n"
        "</html>\n"
    )


def render_swift(palette: dict, basename: str) -> str:
    class_name = pascal_name(basename)
    lines = ["import SwiftUI", "", f"enum {class_name} {{"]
    for color in palette["colors"]:
        lines.append(f"  /// {color['name']} {color['hex']}")
        lines.append(f"  static let {camel_name(color['name'])} = Color(hex: \"{color['hex']}\")")
        lines.append("")
    lines.append("}")
    return "\n".join(lines).rstrip() + "\n"


def render_kt(palette: dict, basename: str) -> str:
    object_name = pascal_name(basename)
    lines = [f"object {object_name} {{"]
    for color in palette["colors"]:
        lines.append(f"    // {color['name']}")
        lines.append(f"    val {camel_name(color['name'])} = Color(0xFF{color['hex'].lstrip('#').upper()})")
        lines.append("")
    lines.append("}")
    return "\n".join(lines).rstrip() + "\n"


def quote_yaml(value: str) -> str:
    return json.dumps(value)


def env_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()


def slug(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return value or "palette"


def words(name: str) -> Iterable[str]:
    return [word for word in re.split(r"[^A-Za-z0-9]+", name) if word]


def pascal_name(name: str) -> str:
    return "".join(word[:1].upper() + word[1:] for word in words(name)) or "Palette"


def camel_name(name: str) -> str:
    parts = list(words(name))
    if not parts:
        return "color"
    first = parts[0][:1].lower() + parts[0][1:]
    rest = "".join(part[:1].upper() + part[1:] for part in parts[1:])
    return first + rest


if __name__ == "__main__":
    raise SystemExit(main())

