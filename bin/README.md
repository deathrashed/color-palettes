# bin

This directory contains the runnable `colorgen` binary and the example input formats used to validate it.

## Binary

```sh
./bin/colorgen -i <palette file> -o <output path>
```

The binary always writes a `.clr` file. If the output path has another extension, it is replaced with `.clr`.

When run without arguments in a terminal, `colorgen` prompts for:

- input palette file path
- repo `clr/` output folder or a custom folder
- output palette name

Examples:

```sh
./bin/colorgen -i 'bin/formats/HTML.csv' -o 'clr/HTML Colors'
./bin/colorgen -i 'bin/formats/HTML.yaml' -o '~/Downloads/HTML'
```

## Local Install

From the repository root:

```sh
make install
```

This copies `bin/colorgen` to `~/.local/bin/colorgen`.
