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
