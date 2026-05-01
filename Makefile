PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
COLORGEN ?= ./bin/colorgen
SOURCE ?= bin/formats/HTML.json
OUT ?= bin/formats/generated
BASENAME ?=
FORMATS ?=

.PHONY: install test generate-formats list clean

install:
	mkdir -p "$(BINDIR)"
	cp "$(COLORGEN)" "$(BINDIR)/colorgen"
	chmod 755 "$(BINDIR)/colorgen"
	@echo "Installed $(BINDIR)/colorgen"

test:
	./scripts/check-colorgen-formats.sh

generate-formats:
	./scripts/generate-colorgen-formats.py "$(SOURCE)" -o "$(OUT)" $(if $(BASENAME),--basename "$(BASENAME)",) $(if $(FORMATS),--formats "$(FORMATS)",)

list:
	@find clr -maxdepth 1 -type f -name '*.clr' -print | sort

clean:
	@find . -name '.DS_Store' -delete
	@echo "Removed .DS_Store files"
