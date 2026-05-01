# bin

This directory contains the runnable `colorgen` binary, the `palette-tui`
launcher, and the example input formats used to validate the converter.

## Binary

```sh
./bin/colorgen -i <palette file> -o <output path>
```

The binary always writes a `.clr` file. If the output path has another extension, it is replaced with `.clr`.

When run without arguments in a terminal, `colorgen` prompts for:

- input palette file path
- repo `clr/` output folder or a custom folder
- output palette name

Batch mode converts every supported palette source file in a directory:

```sh
./bin/colorgen -d 'palettes/terminal-colors'
```

That writes into `clr/terminal-colors/` by default. To choose a different batch
destination:

```sh
./bin/colorgen -d 'palettes/terminal-colors' -o '~/Downloads/terminal-colors'
```

Examples:

```sh
./bin/colorgen -i 'bin/formats/HTML.csv' -o 'clr/HTML Colors'
./bin/colorgen -i 'bin/formats/HTML.yaml' -o '~/Downloads/HTML'
```

## TUI Launcher

```sh
./bin/palette-tui
```

This starts the menu-driven repo TUI from `scripts/palette-tui.py`. It is safe to symlink:

```sh
ln -sf '/Users/rd/Documents/Color Palettes/bin/palette-tui' ~/.local/bin/palette-tui
```

## Local Install

From the repository root:

```sh
make install
```

This copies `bin/colorgen` to `~/.local/bin/colorgen`.
