# Color Palettes

A small macOS color-palette toolkit built around `colorgen`: a command-line converter that turns palette files into Apple `.clr` color lists.

The repo keeps the working pieces separate:

```text
bin/             macOS arm64 colorgen binary
bin/formats/     example palette exports in common text/code formats
palettes/        canonical editable palette sources
clr/             generated Apple .clr palette files
scripts/         repo helpers for validation and local install
palettes.json    manifest of palettes, sources, and source status
```

## Why

Apple `.clr` files are useful in macOS color pickers, design tools, and apps that read `NSColorList` palettes. The source palettes are easier to edit as text, so this repo keeps both: readable source examples and ready-to-use `.clr` outputs.

## Quick Start

Open the interactive TUI:

```sh
make tui
```

Use it to browse palettes, search, generate `.clr` files, batch-convert
directories, preview color names, and jump into ColorSlurp picker/contrast
views.

Run the bundled binary directly:

```sh
./bin/colorgen -i 'bin/formats/HTML.json' -o 'clr/HTML Colors'
```

Or run it without arguments for an interactive prompt:

```sh
./bin/colorgen
```

The prompt asks for an input palette file, whether to save into this repo's
`clr/` folder or a custom folder, and the output palette name.

Batch-convert a directory of palette source files:

```sh
./bin/colorgen -d 'palettes/terminal-colors'
```

By default, directory mode writes into `clr/<input-directory-name>/`. For
example, `palettes/terminal-colors` writes `.clr` files into
`clr/terminal-colors/`, using each input file's name as the output filename.

The output is always forced to `.clr`, so these all write a `.clr` file:

```sh
./bin/colorgen -i 'bin/formats/HTML.txt' -o 'clr/HTML Colors'
./bin/colorgen -i 'bin/formats/HTML.txt' -o 'clr/HTML Colors.json'
./bin/colorgen -i 'bin/formats/HTML.txt' -o '~/Downloads/HTML'
```

> [!NOTE]
> `-o /Downloads/HTML` is treated as `~/Downloads/HTML.clr` for convenience.

## Install

Install the bundled binary to `~/.local/bin`:

```sh
make install
```

Then use it from anywhere:

```sh
colorgen -i '/path/to/palette.json' -o '~/Downloads/My Palette'
```

## Supported Inputs

`colorgen` accepts palette files that contain names and hex colors.

| Format | Example |
| --- | --- |
| JSON | `bin/formats/HTML.json` |
| CSV | `bin/formats/HTML.csv` |
| XML | `bin/formats/HTML.xml` |
| TXT | `bin/formats/HTML.txt` |
| YAML | `bin/formats/HTML.yaml` |
| TOML | `bin/formats/HTML.toml` |
| CONF / ENV | `bin/formats/HTML.conf`, `bin/formats/HTML.env` |
| HTML / CSS | `bin/formats/HTML.html`, `bin/formats/HTML.css` |
| Swift / Kotlin | `bin/formats/HTML.swift`, `bin/formats/HTML.kt` |
| Extensionless and dotfiles | `HTML`, `.HTML`, `.HTML.env` |

The parser is intentionally practical rather than a full language parser. It looks for common palette shapes such as:

```json
{
  "name": "HTML Colors",
  "colors": [
    { "name": "Gainsboro", "hex": "#dcdcdc" }
  ]
}
```

```csv
name,hex
Gainsboro,#dcdcdc
```

```conf
Gainsboro = #dcdcdc
```

## Verify

Run the bundled sample conversion checks:

```sh
make test
```

The check script converts the known-good examples into a temporary directory and verifies each conversion writes 141 colors.

## Refresh `.clr` Palettes

Regenerate every palette marked `canonical` in `palettes.json`:

```sh
make refresh-clr
```

To preview what would be regenerated:

```sh
./scripts/refresh-clr.py --dry-run
```

## Generate Source Formats

Use the generator when you have one canonical JSON palette and want matching files for `colorgen` to consume:

```sh
make generate-formats SOURCE='bin/formats/HTML.json' OUT='bin/formats/generated' BASENAME='HTML'
```

Or run it directly:

```sh
./scripts/generate-colorgen-formats.py 'bin/formats/HTML.json' -o /tmp/html-formats -b HTML
```

The source JSON should use this shape:

```json
{
  "name": "My Palette",
  "colors": [
    { "name": "Ink", "hex": "#111111" },
    { "name": "Paper", "hex": "#f6f1e8" }
  ]
}
```

By default it writes `json`, `csv`, `txt`, `conf`, `env`, `yaml`, `toml`, `xml`, `css`, `html`, `swift`, `kt`, and an extensionless file.

## Name Colors

Use the bundled color-name reference list to fill missing or generic color names:

```sh
./scripts/name-colors.py 'palettes/My Palette.json' --dry-run
./scripts/name-colors.py 'palettes/My Palette.json' --output 'palettes/My Palette.named.json'
```

By default it only writes names for missing/generic entries such as `Color 1`.
To rename every entry to the nearest reference color name:

```sh
./scripts/name-colors.py 'palettes/My Palette.json' --all --output 'palettes/My Palette.named.json'
```

To keep existing names and add suggestions in a separate field:

```sh
./scripts/name-colors.py 'palettes/My Palette.json' --field nearest_name --output 'palettes/My Palette.with-nearest.json'
```

The reference list is vendored in `data/color-names.csv` from the MIT-licensed
`meodai/color-names` project.

## ColorSlurp Helpers

Open ColorSlurp from palette data using its URL scheme:

```sh
./scripts/colorslurp.py picker '#FC8392'
./scripts/colorslurp.py picker 'Bright Blue' --palette 'palettes/terminal-colors/Breeze.json'
./scripts/colorslurp.py picker 4 --palette 'palettes/terminal-colors/Breeze.json'
./scripts/colorslurp.py contrast --foreground 'Bright Blue' --background Black --palette 'palettes/terminal-colors/Breeze.json'
./scripts/colorslurp.py palettes
./scripts/colorslurp.py settings --tab formats
```

Use `--print` to preview the `colorslurp://` URL without opening the app:

```sh
./scripts/colorslurp.py --print picker 'Bright Blue' --palette 'palettes/terminal-colors/Breeze.json'
```

## Terminal UI

The TUI is the easiest way to interact with the repo when you are working
through lots of palettes:

```sh
make tui
```

It opens on a menu first, then drops into the palette browser when you need to
work on a specific file or folder.

Useful keys:

| Key | Action |
| --- | --- |
| `/` | Search palettes |
| `o` / Enter | Inspect selected palette or directory |
| `g` | Generate one `.clr` file |
| `b` | Batch-convert the selected directory, or the selected file's folder |
| `n` | Preview missing/generic color-name fixes |
| `N` | Write a renamed JSON copy using nearest color names |
| `s` / `S` | Open or print a ColorSlurp picker URL |
| `c` / `C` | Open or print a ColorSlurp contrast URL |
| `p` | Open ColorSlurp palettes |
| `r` | Reload repo state |
| `q` | Quit |

## Palette Inventory

`palettes.json` is the repository index. It records each `.clr` file, whether an
editable source exists, the source path when available, and any notes about
duplicates, spelling drift, upstream versions, or attribution concerns.

Canonical editable sources live in `palettes/`. Several palettes now have
recovered canonical JSON sources; the remaining `.clr` files are marked
`binary-only` until editable sources are added or rebuilt.

Useful workflow ideas for keeping, generating, referencing, and working with
palettes are tracked in `docs/WORKFLOWS.md`.

## Notes

- The bundled `bin/colorgen` is a macOS arm64 executable.
- `.clr` files are binary Apple typedstream color-list files, so they are marked as binary in Git.
- `bin/formats/RBG-*` / `RGB-*` files are retained as reference exports; the converter is focused on hex-backed palette inputs.
