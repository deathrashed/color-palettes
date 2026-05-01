#!/usr/bin/env python3
"""Terminal UI for browsing and working with this color palette repo."""

from __future__ import annotations

import curses
import json
import re
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PALETTES_DIR = REPO_ROOT / "palettes"
CLR_DIR = REPO_ROOT / "clr"
COLORGEN = REPO_ROOT / "bin" / "colorgen"
TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
PALETTE_SUFFIXES = {
    "",
    ".json",
    ".csv",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".conf",
    ".env",
    ".html",
    ".css",
    ".xml",
    ".swift",
    ".kt",
}


@dataclass
class PaletteEntry:
    path: Path
    label: str
    kind: str


class PaletteTUI:
    def __init__(self, screen: curses.window) -> None:
        self.screen = screen
        self.entries: list[PaletteEntry] = []
        self.filtered: list[PaletteEntry] = []
        self.selected = 0
        self.offset = 0
        self.query = ""
        self.status = "Ready"
        self.palette_cache: dict[Path, dict[str, Any]] = {}

    def run(self) -> None:
        curses.curs_set(0)
        self.screen.keypad(True)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        self.reload()

        while True:
            self.draw()
            key = self.screen.getch()
            if key in (ord("q"), 27):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                self.move(1)
            elif key in (curses.KEY_UP, ord("k")):
                self.move(-1)
            elif key in (curses.KEY_NPAGE, ord(" ")):
                self.move(10)
            elif key == curses.KEY_PPAGE:
                self.move(-10)
            elif key in (ord("/"),):
                self.search()
            elif key in (ord("r"),):
                self.reload()
            elif key in (ord("g"),):
                self.generate_selected()
            elif key in (ord("b"),):
                self.batch_selected()
            elif key in (ord("n"),):
                self.name_selected()
            elif key in (ord("N"),):
                self.name_selected(rename_all=True)
            elif key in (ord("s"),):
                self.colorslurp_picker_selected(print_only=False)
            elif key in (ord("S"),):
                self.colorslurp_picker_selected(print_only=True)
            elif key in (ord("c"),):
                self.colorslurp_contrast_selected(print_only=False)
            elif key in (ord("C"),):
                self.colorslurp_contrast_selected(print_only=True)
            elif key in (ord("p"),):
                self.run_command([str(REPO_ROOT / "scripts" / "colorslurp.py"), "palettes"])
            elif key in (ord("o"), curses.KEY_ENTER, 10, 13):
                self.inspect_selected()
            elif key == curses.KEY_RESIZE:
                pass

    def reload(self) -> None:
        self.entries = discover_entries()
        self.palette_cache.clear()
        self.apply_filter()
        self.status = f"Loaded {len(self.entries)} entries"

    def apply_filter(self) -> None:
        query = self.query.lower()
        if query:
            self.filtered = [entry for entry in self.entries if query in entry.label.lower()]
        else:
            self.filtered = list(self.entries)
        self.selected = min(self.selected, max(0, len(self.filtered) - 1))
        self.offset = min(self.offset, self.selected)

    def move(self, delta: int) -> None:
        if not self.filtered:
            return
        self.selected = max(0, min(len(self.filtered) - 1, self.selected + delta))
        height = max(1, self.screen.getmaxyx()[0] - 7)
        if self.selected < self.offset:
            self.offset = self.selected
        elif self.selected >= self.offset + height:
            self.offset = self.selected - height + 1

    def current(self) -> PaletteEntry | None:
        if not self.filtered:
            return None
        return self.filtered[self.selected]

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        left_width = max(32, min(56, width // 2))
        self.draw_header(width)
        self.draw_list(2, 0, height - 5, left_width)
        self.draw_detail(2, left_width + 1, height - 5, width - left_width - 1)
        self.draw_footer(height - 3, width)
        self.screen.refresh()

    def draw_header(self, width: int) -> None:
        title = " Color Palettes TUI "
        self.addstr(0, 0, title[:width], curses.A_BOLD | curses.color_pair(2))
        meta = f" {len(self.filtered)}/{len(self.entries)} | search: {self.query or '-'} "
        self.addstr(1, 0, meta[:width], curses.color_pair(3))

    def draw_list(self, y: int, x: int, height: int, width: int) -> None:
        visible = self.filtered[self.offset : self.offset + height]
        for row in range(height):
            line_y = y + row
            if row >= len(visible):
                self.addstr(line_y, x, " " * max(0, width - 1))
                continue
            entry = visible[row]
            marker = ">" if self.offset + row == self.selected else " "
            label = f"{marker} {entry.kind:<4} {entry.label}"
            attr = curses.color_pair(1) if self.offset + row == self.selected else 0
            self.addstr(line_y, x, label[: width - 1].ljust(width - 1), attr)

    def draw_detail(self, y: int, x: int, height: int, width: int) -> None:
        entry = self.current()
        if not entry:
            self.addstr(y, x, "No entries", curses.color_pair(5))
            return

        lines = [entry.label, str(entry.path.relative_to(REPO_ROOT)), ""]
        if entry.kind == "dir":
            count = len(discover_palette_files(entry.path))
            output = CLR_DIR / entry.path.name
            lines.extend(
                [
                    f"Directory batch source: {count} file(s)",
                    f"Default output: {output.relative_to(REPO_ROOT)}",
                    "",
                    "b  batch convert directory",
                ]
            )
        else:
            info = self.palette_info(entry.path)
            lines.extend(
                [
                    f"Palette: {info.get('name', entry.path.stem)}",
                    f"Colors:  {info.get('count', '?')}",
                    f"Format:  {entry.path.suffix or '(extensionless)'}",
                    "",
                    "Preview:",
                ]
            )
            for color in info.get("colors", [])[: min(12, max(0, height - 14))]:
                name = color.get("name") or "(unnamed)"
                hex_value = color.get("hex") or color.get("color") or ""
                lines.append(f"  {hex_value:<9} {name}")

        lines.extend(
            [
                "",
                "Actions:",
                "o inspect   g generate clr   n name missing   N rename all",
                "s open picker   S print picker URL   c contrast   C print contrast URL",
                "p ColorSlurp palettes   / search   r reload   q quit",
            ]
        )

        for row, line in enumerate(lines[:height]):
            attr = curses.A_BOLD if row == 0 else 0
            self.addstr(y + row, x, line[: max(0, width - 1)], attr)

    def draw_footer(self, y: int, width: int) -> None:
        self.addstr(y, 0, "-" * max(0, width - 1), curses.color_pair(2))
        self.addstr(y + 1, 0, self.status[: max(0, width - 1)])

    def search(self) -> None:
        value = self.prompt("Search")
        if value is not None:
            self.query = value
            self.selected = 0
            self.offset = 0
            self.apply_filter()

    def inspect_selected(self) -> None:
        entry = self.current()
        if not entry:
            return
        if entry.kind == "dir":
            files = discover_palette_files(entry.path)
            lines = [f"{entry.label}: {len(files)} file(s)", ""]
            lines.extend(str(path.relative_to(REPO_ROOT)) for path in files[:300])
            self.show_text("Directory", lines)
            return
        info = self.palette_info(entry.path)
        lines = [
            f"Name: {info.get('name', entry.path.stem)}",
            f"Path: {entry.path.relative_to(REPO_ROOT)}",
            f"Colors: {info.get('count', '?')}",
            "",
        ]
        for color in info.get("colors", []):
            lines.append(f"{color.get('hex') or color.get('color') or '':<9} {color.get('name') or '(unnamed)'}")
        self.show_text("Palette", lines)

    def generate_selected(self) -> None:
        entry = self.current()
        if not entry or entry.kind == "dir":
            self.status = "Select a palette file to generate a .clr"
            return
        default_dir = CLR_DIR
        try:
            relative_parent = entry.path.parent.relative_to(PALETTES_DIR)
            if relative_parent != Path("."):
                default_dir = CLR_DIR / relative_parent
        except ValueError:
            pass
        default = str((default_dir / entry.path.stem).relative_to(REPO_ROOT))
        output = self.prompt("Output path", default)
        if not output:
            return
        self.run_command([str(COLORGEN), "-i", str(entry.path), "-o", output])

    def batch_selected(self) -> None:
        entry = self.current()
        if not entry:
            return
        directory = entry.path if entry.kind == "dir" else entry.path.parent
        default = str((CLR_DIR / directory.name).relative_to(REPO_ROOT))
        output = self.prompt("Batch output dir", default)
        if not output:
            return
        self.run_command([str(COLORGEN), "-d", str(directory), "-o", output])

    def name_selected(self, rename_all: bool = False) -> None:
        entry = self.current()
        if not entry or entry.kind == "dir" or entry.path.suffix.lower() != ".json":
            self.status = "Select a JSON palette to name colors"
            return
        if rename_all:
            default = str(entry.path.with_name(f"{entry.path.stem}.named.json").relative_to(REPO_ROOT))
            output = self.prompt("Write renamed JSON", default)
            if output:
                self.run_command([str(REPO_ROOT / "scripts" / "name-colors.py"), str(entry.path), "--all", "--output", output])
        else:
            self.run_command([str(REPO_ROOT / "scripts" / "name-colors.py"), str(entry.path), "--dry-run"])

    def colorslurp_picker_selected(self, print_only: bool) -> None:
        entry = self.current()
        if not entry or entry.kind == "dir":
            self.status = "Select a palette file for ColorSlurp picker"
            return
        color = self.prompt("Color name/index/hex", "1")
        if not color:
            return
        command = [str(REPO_ROOT / "scripts" / "colorslurp.py")]
        if print_only:
            command.append("--print")
        command.extend(["picker", color, "--palette", str(entry.path)])
        self.run_command(command)

    def colorslurp_contrast_selected(self, print_only: bool) -> None:
        entry = self.current()
        if not entry or entry.kind == "dir":
            self.status = "Select a palette file for ColorSlurp contrast"
            return
        foreground = self.prompt("Foreground name/index/hex", "1")
        if not foreground:
            return
        background = self.prompt("Background name/index/hex", "2")
        if not background:
            return
        command = [str(REPO_ROOT / "scripts" / "colorslurp.py")]
        if print_only:
            command.append("--print")
        command.extend(["contrast", "--foreground", foreground, "--background", background, "--palette", str(entry.path)])
        self.run_command(command)

    def palette_info(self, path: Path) -> dict[str, Any]:
        if path in self.palette_cache:
            return self.palette_cache[path]
        info = read_palette_info(path)
        self.palette_cache[path] = info
        return info

    def run_command(self, command: list[str]) -> None:
        self.screen.erase()
        self.addstr(0, 0, "Running command", curses.A_BOLD | curses.color_pair(2))
        self.addstr(2, 0, shell_join(command))
        self.screen.refresh()
        result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        output = []
        if result.stdout:
            output.extend(result.stdout.rstrip().splitlines())
        if result.stderr:
            output.extend(result.stderr.rstrip().splitlines())
        if not output:
            output = [f"Exit status: {result.returncode}"]
        self.status = f"Command exited {result.returncode}"
        self.show_text("Command Output", [shell_join(command), ""] + output)

    def show_text(self, title: str, lines: list[str]) -> None:
        top = 0
        while True:
            self.screen.erase()
            height, width = self.screen.getmaxyx()
            self.addstr(0, 0, f" {title} ", curses.A_BOLD | curses.color_pair(2))
            body_height = height - 3
            for row, line in enumerate(lines[top : top + body_height]):
                self.addstr(row + 1, 0, line[: max(0, width - 1)])
            self.addstr(height - 1, 0, "j/k scroll  q/backspace return"[: max(0, width - 1)], curses.color_pair(3))
            self.screen.refresh()
            key = self.screen.getch()
            if key in (ord("q"), 27, curses.KEY_BACKSPACE, 127, 10, 13):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                top = min(max(0, len(lines) - body_height), top + 1)
            elif key in (curses.KEY_UP, ord("k")):
                top = max(0, top - 1)
            elif key == curses.KEY_NPAGE:
                top = min(max(0, len(lines) - body_height), top + body_height)
            elif key == curses.KEY_PPAGE:
                top = max(0, top - body_height)

    def prompt(self, label: str, default: str = "") -> str | None:
        curses.curs_set(1)
        height, width = self.screen.getmaxyx()
        value = default
        while True:
            prompt = f"{label}: {value}"
            self.addstr(height - 1, 0, " " * max(0, width - 1))
            self.addstr(height - 1, 0, prompt[: max(0, width - 1)], curses.color_pair(3))
            self.screen.refresh()
            key = self.screen.getch()
            if key in (27,):
                curses.curs_set(0)
                return None
            if key in (10, 13):
                curses.curs_set(0)
                return value.strip()
            if key in (21,):
                value = ""
            if key in (curses.KEY_BACKSPACE, 127, 8):
                value = value[:-1]
            elif 32 <= key <= 126:
                value += chr(key)

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        try:
            self.screen.addstr(y, x, text, attr)
        except curses.error:
            pass


def discover_entries() -> list[PaletteEntry]:
    entries: list[PaletteEntry] = []
    for directory in sorted((path for path in PALETTES_DIR.iterdir() if path.is_dir()), key=lambda p: p.name.lower()):
        entries.append(PaletteEntry(directory, directory.relative_to(REPO_ROOT).as_posix(), "dir"))
    for path in discover_palette_files(PALETTES_DIR):
        entries.append(PaletteEntry(path, path.relative_to(PALETTES_DIR).as_posix(), "file"))
    return entries


def discover_palette_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(directory.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        if path.suffix.lower() in {".md", ".markdown", ".clr"}:
            continue
        if path.suffix.lower() in PALETTE_SUFFIXES or not path.suffix:
            files.append(path)
    return files


def read_palette_info(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        try:
            data = load_relaxed_json(path)
            if isinstance(data, dict):
                colors = data.get("colors") if isinstance(data.get("colors"), list) else []
                return {
                    "name": data.get("name") or path.stem,
                    "count": len(colors),
                    "colors": normalize_preview_colors(colors),
                }
            if isinstance(data, list):
                return {"name": path.stem, "count": len(data), "colors": normalize_preview_colors(data)}
        except Exception as error:  # noqa: BLE001 - UI preview should not crash.
            return {"name": path.stem, "count": "?", "colors": [{"name": str(error), "hex": ""}]}
    return preview_text_palette(path)


def preview_text_palette(path: Path) -> dict[str, Any]:
    colors: list[dict[str, str]] = []
    pattern = re.compile(r"#?[0-9a-fA-F]{6,8}")
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[:200]:
            match = pattern.search(line)
            if match:
                colors.append({"name": line.strip()[:80], "hex": normalize_hex(match.group(0)) or match.group(0)})
    except OSError as error:
        colors.append({"name": str(error), "hex": ""})
    return {"name": path.stem, "count": len(colors) or "?", "colors": colors[:20]}


def normalize_preview_colors(items: Any) -> list[dict[str, str]]:
    colors: list[dict[str, str]] = []
    if not isinstance(items, list):
        return colors
    for item in items:
        if not isinstance(item, dict):
            continue
        colors.append(
            {
                "name": str(item.get("name") or item.get("nearest_name") or ""),
                "hex": normalize_hex(item.get("hex") or item.get("color")) or "",
            }
        )
    return colors


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


def load_relaxed_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA_RE.sub(r"\1", text))


def shell_join(command: list[str]) -> str:
    return " ".join(quote_arg(part) for part in command)


def quote_arg(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=@+-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main() -> int:
    curses.wrapper(lambda screen: PaletteTUI(screen).run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
