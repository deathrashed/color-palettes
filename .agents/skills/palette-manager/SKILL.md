---
name: palette-manager
description: Create and maintain a complete color palette management workflow for generated palettes and related repositories. Trigger this skill when mentioning colorgen, color palette generation, palette folders, naming, categories, repo cleanup, refactoring, color scheme organization, generated themes, theme repo management, CSS theme palettes, terminal/editor color palettes, palette metadata, or adding features to the palette generator. Use it whenever asked to clean up, restructure, refactor, rename, categorize, or improve anything related to the color palette generator or palette repository.
---

# Palette Manager

A specialized skill for managing the end-to-end lifecycle of color palettes in the **macOS Color Palette Toolkit**. This repo focuses on converting text-based source palettes (JSON, CSV, etc.) into binary Apple Color List (`.clr`) files using `colorgen`.

## Core Responsibilities

1.  **Manifest-First Maintenance**: Use `palettes.json` as the source of truth for all repository tools.
2.  **Source Lifecycle**: Manage the transition from `binary-only` (no source) to `canonical` (editable JSON source) for all palettes.
3.  **Validation**: Rigorously use `scripts/check-palette-manifest.py` to ensure every `.clr` file is indexed and every source is valid.
4.  **Workflow Automation**: Leverage the `Makefile` and scripts (`refresh-clr`, `name-colors`, `generate-formats`) to keep the repo synced.
5.  **Tool Improvement**: Enhance the converter, TUI, and helper scripts while maintaining compatibility with the established JSON schema.

## Trigger Conditions

Trigger this skill when the user mentions:
- `colorgen`, `clr` files, or Apple Color Lists.
- `palettes.json` or the "manifest".
- Adding or "recovering" a canonical source for a palette.
- Fixing color names using the reference list (`name-colors.py`).
- Repo cleanup, deduplication, or restructuring palette categories.
- Updating or improving the TUI (`palette-tui.py`) or ColorSlurp integration.
- Generating exports (CSS, Swift, Kotlin, etc.) from palette sources.

## Repository Knowledge

### 1. The Manifest (`palettes.json`)
- **Schema**: Each palette has `id`, `name`, `clr`, `source`, `source_status`, `color_count`, and `category`.
- **Status Types**:
  - `canonical`: Has a matching source in `palettes/` that can regenerate the `.clr`.
  - `binary-only`: Only the `.clr` exists; needs an editable source recovered.
  - `external` / `derived`: Other specialized statuses.
- **Constraints**: IDs and CLR paths must be unique. Every file in `clr/` MUST be in the manifest.

### 2. File Organization
- `palettes/`: Canonical source files (JSON). Subdirectories like `terminal-colors/` or `brand-colors/` are encouraged.
- `clr/`: Generated binary files. Structure should mirror `palettes/` where possible.
- `scripts/`: Python and Shell tools for maintenance.
- `bin/formats/`: Reference examples showing how `colorgen` parses different text formats.

### 3. Core Tools
- `bin/colorgen`: The binary converter (macOS arm64).
- `scripts/check-palette-manifest.py`: Validates the whole repo. Run this after any structural change.
- `scripts/refresh-clr.py`: Syncs all `canonical` palettes. Run `make refresh-clr`.
- `scripts/name-colors.py`: Nearest-match naming using `data/color-names.csv`.
- `scripts/colorslurp.py`: Handles `colorslurp://` URL schemes for picker/contrast actions.

## Standard Procedures

### Procedure A: Adding a Canonical Source
1.  **Analyze**: Locate the `binary-only` entry in `palettes.json`.
2.  **Recover/Create**: Place the new JSON source in `palettes/`. Ensure it uses the `{ "name": "...", "colors": [{ "name": "...", "hex": "#..." }] }` shape.
3.  **Name Colors**: If the source has generic names (Color 1), run `scripts/name-colors.py`.
4.  **Update Manifest**: Change `source_status` to `canonical`, set the `source` path, and update `color_count`.
5.  **Verify**: Run `scripts/check-palette-manifest.py`.
6.  **Regenerate**: Run `make refresh-clr --only <id>` to update the binary file.

### Procedure B: Repo Restructuring
1.  **Plan**: Propose a category structure (e.g., `brand-colors/`, `system-colors/`).
2.  **Move Files**: Move files in both `palettes/` and `clr/` to maintain symmetry.
3.  **Update Manifest**: Update all paths in `palettes.json`.
4.  **Validate**: Run `scripts/check-palette-manifest.py` to ensure no orphans or broken links.

### Procedure C: Script Refactoring
- **Patterns**: Prefer `argparse` for Python scripts and robust `trap` cleanup for Shell scripts.
- **Tolerance**: Maintain the "practical parser" philosophy—tolerate trailing commas and varied hex casing where possible.

## Output Format

When responding to a `palette-manager` request, ALWAYS use the following structure:

### 1. Summary
Briefly explain the goal and the recommended direction.

### 2. Repository Analysis
Identify current status in `palettes.json` and file locations. Note any "binary-only" or "orphaned" files.

### 3. Proposed Changes
- **Files**: Listing of move/rename/create actions.
- **Manifest**: Exact JSON patches for `palettes.json`.
- **Naming/Categories**: Recommended Title Case names and folder groupings.

### 4. Implementation
Provide runnable commands (zsh/bash).
- Include `dry-run` checks where possible.
- Use `scripts/check-palette-manifest.py` as a validation step.

### 5. Verification & Repo Safety
Steps to confirm success: `make test`, `make refresh-clr`, or manual inspection. Include git commit suggestions.

### 6. Final Recommended Next Step
A single, concrete action to take next.
