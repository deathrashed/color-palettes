# Example Formats

This folder contains source-format examples for the HTML color palette.

## Supported By `colorgen`

These examples are used by `scripts/check-colorgen-formats.sh`:

```text
HTML
HTML.conf
HTML.css
HTML.csv
HTML.env
HTML.html
HTML.json
HTML.kt
HTML.swift
HTML.toml
HTML.txt
HTML.xml
HTML.yaml
```

Each should convert to a `.clr` file containing 141 colors.

## Reference Exports

Some files are kept as useful reference exports even if they are not part of the default converter test set:

```text
ALL-HTML.json
HMTL.js
HMTL.sh
HTML-NS.swift
HTML-UI.swift
HTML.less
HTML.py
HTML.sass
HTML.scss
HTML.ts
HTML.zsh
RBG-HTML.css
RBG-HTML.json
RGB-HTML.html
```

The `RBG-*` / `RGB-*` files are RGB-oriented references. `colorgen` is primarily designed for name plus hex input.

## Adding A New Format

Start from a canonical JSON palette and generate the common input formats:

```sh
make generate-formats SOURCE='bin/formats/HTML.json' OUT='bin/formats/generated' BASENAME='HTML'
```

To emit only selected formats:

```sh
./scripts/generate-colorgen-formats.py bin/formats/HTML.json -o /tmp/html-formats -b HTML -f json,csv,yaml,toml
```

Then run:

```sh
make test
```

If the format is meant to be supported by `colorgen`, add it to `scripts/check-colorgen-formats.sh`.
