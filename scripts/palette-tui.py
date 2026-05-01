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


@dataclass(frozen=True)
class MenuItem:
    label: str
    kind: str
    detail: str
    action: str


class PaletteTUI:
    def __init__(self, screen: curses.window) -> None:
        self.screen = screen
        self.mode = "home"
        self.home_items: list[MenuItem] = self.build_home_items()
        self.home_selected = 0
        self.home_offset = 0
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
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        self.reload()

        while True:
            self.draw()
            key = self.screen.getch()
            if self.mode == "home":
                if self.handle_home_key(key):
                    return
            else:
                if self.handle_browser_key(key):
                    return

    def handle_home_key(self, key: int) -> bool:
        if key in (ord("q"), 27):
            return True
        if key in (curses.KEY_DOWN, ord("j")):
            self.home_move(1)
        elif key in (curses.KEY_UP, ord("k")):
            self.home_move(-1)
        elif key in (curses.KEY_NPAGE, ord(" ")):
            self.home_move(5)
        elif key == curses.KEY_PPAGE:
            self.home_move(-5)
        elif key in (curses.KEY_ENTER, 10, 13):
            self.activate_home_item()
        elif key in (ord("b"),):
            self.enter_browser("Browse palettes and folders. Select a palette file, then press g/n/s/c.")
        elif key in (ord("/"),):
            self.enter_browser("Search palettes with /, then use g/b/n/s/c on the selected item.")
            self.search()
        elif key in (ord("r"),):
            self.reload()
        elif key in (ord("?"),):
            self.show_help()
        elif key == curses.KEY_RESIZE:
            pass
        return False

    def handle_browser_key(self, key: int) -> bool:
        if key in (ord("q"), 27):
            return True
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
        elif key in (ord("h"), ord("H"), ord("m")):
            self.mode = "home"
            self.status = "Back at the main menu"
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
        return False

    def build_home_items(self) -> list[MenuItem]:
        return [
            MenuItem("Browse palettes", "navigation", "Open the palette browser and work on a selected palette or folder.", "browse"),
            MenuItem("Generate .clr", "colorgen", "Choose a palette file, then press g to write a .clr file.", "browse-generate"),
            MenuItem("Batch convert folders", "colorgen", "Choose a directory, or a palette inside one, then press b.", "browse-batch"),
            MenuItem("Name colors", "naming", "Choose a JSON palette, then press n for suggestions or N to write names.", "browse-name"),
            MenuItem("ColorSlurp picker", "colorslurp", "Choose a palette and press s or S to open or print a picker URL.", "browse-picker"),
            MenuItem("ColorSlurp contrast", "colorslurp", "Choose a palette and press c or C to compare two colors.", "browse-contrast"),
            MenuItem("ColorSlurp palettes", "colorslurp", "Open ColorSlurp directly on the palettes view.", "colorslurp-palettes"),
            MenuItem("ColorSlurp magnifier", "colorslurp", "Open the magnifier in ColorSlurp.", "colorslurp-magnifier"),
            MenuItem("ColorSlurp settings", "colorslurp", "Open ColorSlurp settings at the formats tab.", "colorslurp-settings"),
            MenuItem("Refresh .clr files", "maintenance", "Regenerate canonical .clr outputs from palettes.json.", "refresh"),
            MenuItem("Check colorgen formats", "maintenance", "Run the sample format validation script.", "check-formats"),
            MenuItem("Check palette manifest", "maintenance", "Run the inventory and source coverage validator.", "check-manifest"),
            MenuItem("Workflow guide", "docs", "Open the repo workflow notes inside the TUI.", "docs"),
        ]

    def home_move(self, delta: int) -> None:
        if not self.home_items:
            return
        self.home_selected = max(0, min(len(self.home_items) - 1, self.home_selected + delta))
        height = max(1, self.screen.getmaxyx()[0] - 7)
        if self.home_selected < self.home_offset:
            self.home_offset = self.home_selected
        elif self.home_selected >= self.home_offset + height:
            self.home_offset = self.home_selected - height + 1

    def activate_home_item(self) -> None:
        item = self.home_items[self.home_selected]
        if item.action == "browse":
            self.enter_browser("Browse palettes and folders. Select a palette file, then press g/n/s/c.")
        elif item.action == "browse-generate":
            self.enter_browser("Select a palette file, then press g to generate a .clr.")
        elif item.action == "browse-batch":
            self.enter_browser("Select a folder or a palette inside a folder, then press b to batch convert.")
        elif item.action == "browse-name":
            self.enter_browser("Select a JSON palette, then press n or N to name colors.")
        elif item.action == "browse-picker":
            self.enter_browser("Select a palette, then press s or S for ColorSlurp picker URLs.")
        elif item.action == "browse-contrast":
            self.enter_browser("Select a palette, then press c or C for ColorSlurp contrast URLs.")
        elif item.action == "colorslurp-palettes":
            self.run_command([str(REPO_ROOT / "scripts" / "colorslurp.py"), "palettes"])
        elif item.action == "colorslurp-magnifier":
            self.run_command([str(REPO_ROOT / "scripts" / "colorslurp.py"), "magnifier"])
        elif item.action == "colorslurp-settings":
            self.run_command([str(REPO_ROOT / "scripts" / "colorslurp.py"), "settings", "--tab", "formats"])
        elif item.action == "colorslurp":
            self.show_text(
                "ColorSlurp",
                [
                    "ColorSlurp app views",
                    "",
                    "p  palettes",
                    "m  magnifier",
                    "t  settings",
                    "",
                    "These open ColorSlurp directly without needing a selected palette.",
                ],
            )
        elif item.action == "refresh":
            self.run_command([str(REPO_ROOT / "scripts" / "refresh-clr.py")])
        elif item.action == "check-formats":
            self.run_command([str(REPO_ROOT / "scripts" / "check-colorgen-formats.sh")])
        elif item.action == "check-manifest":
            self.run_command([str(REPO_ROOT / "scripts" / "check-palette-manifest.py")])
        elif item.action == "docs":
            self.show_help()

    def enter_browser(self, status: str | None = None) -> None:
        self.mode = "browser"
        if status:
            self.status = status
        if not self.filtered:
            self.apply_filter()

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
        if self.mode == "home":
            self.draw_home(width, left_width, height)
        else:
            self.draw_browser(width, left_width, height)
        self.draw_footer(height - 3, width)
        self.screen.refresh()

    def draw_home(self, width: int, left_width: int, height: int) -> None:
        self.addstr(0, 0, " Color Palettes TUI ", curses.A_BOLD | curses.color_pair(2))
        self.addstr(1, 0, " Home | choose a workflow with arrows and Enter ", curses.color_pair(3))
        self.draw_item_list(self.home_items, self.home_offset, self.home_selected, 2, 0, height - 5, left_width)
        self.draw_home_detail(2, left_width + 1, height - 5, width - left_width - 1)

    def draw_browser(self, width: int, left_width: int, height: int) -> None:
        self.draw_header(width)
        self.draw_item_list(self.filtered, self.offset, self.selected, 2, 0, height - 5, left_width)
        self.draw_detail(2, left_width + 1, height - 5, width - left_width - 1)

    def draw_header(self, width: int) -> None:
        title = " Color Palettes TUI "
        self.addstr(0, 0, title[:width], curses.A_BOLD | curses.color_pair(2))
        meta = f" Browser | {len(self.filtered)}/{len(self.entries)} | search: {self.query or '-'} | h home "
        self.addstr(1, 0, meta[:width], curses.color_pair(3))

    def draw_item_list(self, items: list[Any], offset: int, selected: int, y: int, x: int, height: int, width: int) -> None:
        visible = items[offset : offset + height]
        for row in range(height):
            line_y = y + row
            if row >= len(visible):
                self.addstr(line_y, x, " " * max(0, width - 1))
                continue
            entry = visible[row]
            kind = getattr(entry, "kind", "")
            label = getattr(entry, "label", "")
            marker = ">" if offset + row == selected else " "
            label = f"{marker} {kind:<10} {label}"
            attr = curses.color_pair(1) if offset + row == selected else 0
            self.addstr(line_y, x, label[: width - 1].ljust(width - 1), attr)

    def draw_home_detail(self, y: int, x: int, height: int, width: int) -> None:
        item = self.home_items[self.home_selected] if self.home_items else None
        if not item:
            self.addstr(y, x, "No menu items", curses.color_pair(5))
            return

        lines = [item.label, "", *self.wrap_text(item.detail, max(20, width - 2))]
        lines.extend(
            [
                "",
                "Enter opens this workflow.",
                "b jumps into the browser from anywhere.",
                "q quits, h returns home from the browser.",
            ]
        )
        for row, line in enumerate(lines[:height]):
            attr = curses.A_BOLD if row == 0 else 0
            self.addstr(y + row, x, line[: max(0, width - 1)], attr)

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
                "p ColorSlurp palettes   / search   r reload   h home   q quit",
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

    def show_help(self) -> None:
        self.show_text(
            "Workflow Guide",
            [
                "Main menu",
                "  Browse palettes: open the palette browser.",
                "  Generate .clr: jump to browser, select a palette, press g.",
                "  Batch convert folders: jump to browser, select a directory, press b.",
                "  Name colors: jump to browser, select a JSON palette, press n or N.",
                "  ColorSlurp picker/contrast: select a palette, then press s/c or S/C.",
                "  ColorSlurp palettes/magnifier/settings: open the app directly.",
                "  Refresh .clr files: regenerate canonical outputs from palettes.json.",
                "  Check colorgen formats: validate the sample inputs.",
                "  Check palette manifest: validate inventory coverage.",
                "",
                "Browser mode",
                "  arrows or j/k move",
                "  / search",
                "  o inspect",
                "  g generate",
                "  b batch convert",
                "  n name missing colors",
                "  N rename every color",
                "  s/S picker",
                "  c/C contrast",
                "  p ColorSlurp palettes",
                "  h return home",
                "",
                "The browser works on the current selection; the home screen is the menu.",
            ],
        )

    def wrap_text(self, text: str, width: int) -> list[str]:
        if width <= 0:
            return [text]
        lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            wrapped = textwrap.wrap(paragraph, width=width) or [""]
            lines.extend(wrapped)
        return lines

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
