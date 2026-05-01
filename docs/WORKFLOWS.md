# Color Palette Workflow Ideas

This repo is most useful when it can keep palettes, generate formats, preview
results, and help choose colors during real design work. These are the tools
worth adding next.

## Keep

- `manifest` validation: make sure every `.clr` file is listed in
  `palettes.json`, every canonical source exists, ids are unique, and color
  counts match.
- `source` normalization: sort or preserve source order intentionally, normalize
  hex case, trim duplicate names, and report duplicate hex values.
- `attribution` records: track upstream URL, version, retrieval date, license
  note, and whether redistribution is safe.
- `rename` helper: rename a palette across `palettes/`, `clr/`, generated
  exports, and `palettes.json` in one step.

## Generate

- `make refresh-clr`: regenerate `.clr` files from every canonical source.
- `make export`: generate CSS variables, Sass maps, Swift, Kotlin, JSON, CSV,
  YAML, TOML, and HTML previews from any source palette.
- `make install-palettes`: copy selected `.clr` files into
  `~/Library/Colors`.
- `make package`: build a clean release folder or zip with `.clr` files,
  source JSON, manifest, and attribution.

## Work With

- TUI: browse palette directories, search, inspect colors, generate `.clr`
  files, batch-convert folders, preview color naming, and trigger ColorSlurp
  picker/contrast actions from one terminal screen.
- Preview gallery: generate a static HTML page with swatches, names, hex values,
  search, and copy buttons.
- Contrast checker: calculate WCAG contrast for foreground/background pairs and
  suggest readable combinations.
- Color transforms: generate tints, shades, alpha variants, grayscale checks,
  and perceptual lightness ramps.
- Palette compare: show added, removed, renamed, and changed colors between two
  versions of a palette.
- Duplicate finder: detect identical hex values, near-duplicates, and names that
  differ only by punctuation or spacing.
- Color picker import: ingest a copied list of hex values or a CSV export from
  Sip, ColorSlurp, Figma, or another color tool.
- Color naming: fill missing/generic color names, rename entire palettes, or
  add nearest-name suggestions before generating `.clr` files.
- ColorSlurp URL actions: open picker, magnifier, palettes, settings, and
  contrast views from palette JSON entries.

## Reference

- `palettes.json` should stay the repository index: it is the stable thing other
  tools can read.
- Add `docs/SOURCES.md` when more canonical palettes are recovered or rebuilt.
- Add `docs/PALETTE-NAMING.md` if this grows: it should define filename casing,
  display names, ids, and how to handle trademarks or upstream version names.
- Add generated previews under `site/` or `docs/gallery/` only if the output is
  useful to browse in GitHub or a browser.

## Good Next Scripts

- `scripts/check-palette-manifest.py`: validate inventory and source files.
- `scripts/refresh-clr.py`: read `palettes.json` and regenerate every canonical
  `.clr`. Implemented.
- `scripts/export-palette.py`: export one source palette to selected formats.
- `scripts/palette-audit.py`: report duplicates, invalid hex values, color
  counts, near matches, and naming drift.
- `scripts/build-gallery.py`: generate a static swatch browser from
  `palettes.json`.
- `scripts/name-colors.py`: name colors from `data/color-names.csv` using
  nearest-color matching. Implemented.
- `scripts/colorslurp.py`: build or open `colorslurp://` URLs from raw colors
  or palette JSON selectors. Implemented.
- `scripts/palette-tui.py`: interactive terminal UI for browsing, generating,
  naming, batching, and opening ColorSlurp actions. Implemented.
