PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
COLORGEN ?= ./bin/colorgen
PALETTE_TUI ?= ./bin/palette-tui
SOURCE ?= bin/formats/HTML.json
OUT ?= bin/formats/generated
BASENAME ?=
FORMATS ?=
PALETTE ?=
COLOR ?=
FOREGROUND ?=
BACKGROUND ?=
COLORSLURP_FLAGS ?=

.PHONY: install test check-manifest refresh-clr generate-formats name-colors colorslurp-picker colorslurp-contrast tui list clean

install:
	mkdir -p "$(BINDIR)"
	cp "$(COLORGEN)" "$(BINDIR)/colorgen"
	chmod 755 "$(BINDIR)/colorgen"
	@echo "Installed $(BINDIR)/colorgen"
	cp "$(PALETTE_TUI)" "$(BINDIR)/palette-tui"
	chmod 755 "$(BINDIR)/palette-tui"
	@echo "Installed $(BINDIR)/palette-tui"

test:
	./scripts/check-colorgen-formats.sh
	./scripts/check-palette-manifest.py

check-manifest:
	./scripts/check-palette-manifest.py

refresh-clr:
	./scripts/refresh-clr.py

generate-formats:
	./scripts/generate-colorgen-formats.py "$(SOURCE)" -o "$(OUT)" $(if $(BASENAME),--basename "$(BASENAME)",) $(if $(FORMATS),--formats "$(FORMATS)",)

name-colors:
	@test -n "$(PALETTE)" || (echo "Usage: make name-colors PALETTE='palettes/My Palette.json'"; exit 1)
	./scripts/name-colors.py "$(PALETTE)" --dry-run

colorslurp-picker:
	@test -n "$(COLOR)" || (echo "Usage: make colorslurp-picker COLOR='#FC8392' [PALETTE='palettes/My Palette.json']"; exit 1)
	./scripts/colorslurp.py $(COLORSLURP_FLAGS) picker "$(COLOR)" $(if $(PALETTE),--palette "$(PALETTE)",)

colorslurp-contrast:
	@test -n "$(FOREGROUND)" || (echo "Usage: make colorslurp-contrast FOREGROUND='#BECE86' BACKGROUND='#2D3D2E'"; exit 1)
	@test -n "$(BACKGROUND)" || (echo "Usage: make colorslurp-contrast FOREGROUND='#BECE86' BACKGROUND='#2D3D2E'"; exit 1)
	./scripts/colorslurp.py $(COLORSLURP_FLAGS) contrast --foreground "$(FOREGROUND)" --background "$(BACKGROUND)" $(if $(PALETTE),--palette "$(PALETTE)",)

tui:
	./scripts/palette-tui.py

list:
	@find clr -type f -name '*.clr' -print | sort

clean:
	@find . -name '.DS_Store' -delete
	@echo "Removed .DS_Store files"
