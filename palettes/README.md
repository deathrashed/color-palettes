# palettes

Canonical, editable palette sources live here.

Use this directory for source-of-truth JSON files that can be regenerated into
Apple `.clr` files and other export formats. Keep generated examples in
`bin/formats/` and generated Apple color lists in `clr/`.

## JSON Shape

```json
{
  "name": "My Palette",
  "colors": [
    { "name": "Ink", "hex": "#111111" },
    { "name": "Paper", "hex": "#f6f1e8" }
  ]
}
```

## Workflow

Generate text/code formats from a canonical source:

```sh
make generate-formats SOURCE='palettes/HTML.json' OUT='bin/formats/generated' BASENAME='HTML'
```

Generate an Apple `.clr` file:

```sh
./bin/colorgen -i 'palettes/HTML Colors.json' -o 'clr/HTML Colors'
```

Update `palettes.json` whenever a palette is added, renamed, sourced, or
regenerated.
