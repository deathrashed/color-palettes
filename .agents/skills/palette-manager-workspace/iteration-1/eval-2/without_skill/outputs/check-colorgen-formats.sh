#!/usr/bin/env bash
set -euo pipefail

# --- Configuration & Defaults ---
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
colorgen="${COLORGEN:-$repo_root/bin/colorgen}"
formats_dir="${FORMATS_DIR:-$repo_root/bin/formats}"
expected_count="${EXPECTED_COUNT:-141}"
verbose=false

# --- Argument Parsing ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose|-v)
      verbose=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--verbose|-v] [--help|-h]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# --- Validation ---
if [[ ! -x "$colorgen" ]]; then
  echo "Error: colorgen is not executable or not found at: $colorgen" >&2
  exit 1
fi

if [[ ! -d "$formats_dir" ]]; then
  echo "Error: formats directory not found at: $formats_dir" >&2
  exit 1
fi

# --- Setup & Cleanup ---
tmpdir="$(mktemp -d)"

cleanup() {
  local exit_code=$?
  if [[ -d "$tmpdir" ]]; then
    if [[ "$verbose" == true ]]; then
      echo "Cleaning up temporary directory: $tmpdir"
    fi
    rm -rf "$tmpdir"
  fi
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

# --- Test Data ---
examples=(
  "HTML"
  "HTML.conf"
  "HTML.css"
  "HTML.csv"
  "HTML.env"
  "HTML.html"
  "HTML.json"
  "HTML.kt"
  "HTML.swift"
  "HTML.toml"
  "HTML.txt"
  "HTML.xml"
  "HTML.yaml"
)

# --- Check Function ---
failures=0

check_file() {
  local input="$1"
  local label="$2"
  
  if [[ ! -f "$input" ]]; then
    echo "FAIL $label (Input file missing: $input)"
    failures=$((failures + 1))
    return
  fi

  local safe_label
  safe_label="$(printf '%s' "$label" | sed 's/[^A-Za-z0-9_-]/_/g')"
  local output_prefix="$tmpdir/$safe_label"
  local log_file="$tmpdir/${safe_label}.log"

  if [[ "$verbose" == true ]]; then
    echo "Checking $label..."
  fi

  # Run colorgen and capture both stdout and stderr
  if ! "$colorgen" -i "$input" -o "$output_prefix" > "$log_file" 2>&1; then
    echo "FAIL $label (Command failed)"
    cat "$log_file"
    failures=$((failures + 1))
    return
  fi

  local log_content
  log_content=$(cat "$log_file")

  if [[ "$log_content" != *"Wrote $expected_count colors"* ]]; then
    echo "FAIL $label (Count mismatch)"
    echo "Expected $expected_count colors, got:"
    echo "$log_content"
    failures=$((failures + 1))
    return
  fi

  # Depending on how colorgen works, it might append .clr or not. 
  # Original script assumed $output.clr
  local output_file="${output_prefix}.clr"

  if [[ ! -s "$output_file" ]]; then
    echo "FAIL $label (Missing or empty output file: $output_file)"
    if [[ "$verbose" == true ]]; then
        ls -la "$tmpdir"
    fi
    failures=$((failures + 1))
    return
  fi

  echo "OK   $label"
  if [[ "$verbose" == true ]]; then
    echo "     Log: $log_content"
  fi
}

# --- Execution ---
if [[ "$verbose" == true ]]; then
  echo "Starting colorgen format checks..."
  echo "  colorgen:     $colorgen"
  echo "  formats_dir:  $formats_dir"
  echo "  tmpdir:       $tmpdir"
fi

for example in "${examples[@]}"; do
  check_file "$formats_dir/$example" "$example"
done

# Dotfile edge cases
dotfile_dir="$tmpdir/dotfiles"
mkdir -p "$dotfile_dir"

if cp "$formats_dir/HTML.env" "$dotfile_dir/.HTML.env" 2>/dev/null && \
   cp "$formats_dir/HTML.conf" "$dotfile_dir/.HTML" 2>/dev/null && \
   cp "$formats_dir/HTML.csv" "$dotfile_dir/.csvpalette" 2>/dev/null; then
  
  check_file "$dotfile_dir/.HTML.env" ".HTML.env"
  check_file "$dotfile_dir/.HTML" ".HTML"
  check_file "$dotfile_dir/.csvpalette" ".csvpalette"
else
  echo "FAIL dotfiles (Setup failed)"
  failures=$((failures + 1))
fi

# --- Result ---
if (( failures > 0 )); then
  echo "------------------------------------------------"
  echo "Error: $failures check(s) failed." >&2
  exit 1
fi

echo "All colorgen format checks passed."
exit 0
