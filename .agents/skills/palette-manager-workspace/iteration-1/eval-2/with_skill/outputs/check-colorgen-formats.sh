#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
colorgen="${COLORGEN:-$repo_root/bin/colorgen}"
formats_dir="${FORMATS_DIR:-$repo_root/bin/formats}"
expected_count="${EXPECTED_COUNT:-141}"

# --- State ---
VERBOSE=false
failures=0

# --- Cleanup Logic ---
tmpdir=""
cleanup() {
  if [[ -n "${tmpdir:-}" && -d "$tmpdir" ]]; then
    if [[ "$VERBOSE" == "true" ]]; then
      echo "Cleaning up temporary directory: $tmpdir"
    fi
    rm -rf "$tmpdir"
  fi
}
trap cleanup EXIT ERR INT TERM

# --- Helpers ---
usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  -v, --verbose    Enable verbose output
  -h, --help       Show this help message
EOF
}

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

log_verbose() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "$@"
  fi
}

# --- Validation ---
if [[ ! -x "$colorgen" ]]; then
  echo "Error: colorgen is not executable or not found at: $colorgen" >&2
  exit 1
fi

if [[ ! -d "$formats_dir" ]]; then
  echo "Error: formats directory not found at: $formats_dir" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
log_verbose "Created temporary directory: $tmpdir"

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

check_file() {
  local input="$1"
  local label="$2"
  local safe_label
  safe_label="$(printf '%s' "$label" | sed 's/[^A-Za-z0-9_-]/_/g')"
  local output="$tmpdir/$safe_label"
  local log_out
  local exit_code=0

  log_verbose "Checking $label ($input)..."

  if ! [[ -f "$input" ]]; then
    echo "FAIL $label (Input file missing: $input)"
    failures=$((failures + 1))
    return
  fi

  # Run colorgen and capture both stdout and stderr
  if ! log_out="$("$colorgen" -i "$input" -o "$output" 2>&1)"; then
    exit_code=$?
    echo "FAIL $label (colorgen exited with $exit_code)"
    echo "$log_out"
    failures=$((failures + 1))
    return
  fi

  if [[ "$log_out" != *"Wrote $expected_count colors"* ]]; then
    echo "FAIL $label (Unexpected color count)"
    echo "Expected $expected_count colors, got:"
    echo "$log_out"
    failures=$((failures + 1))
    return
  fi

  local output_file="$output.clr"
  if [[ ! -s "$output_file" ]]; then
    echo "FAIL $label (Empty or missing output file)"
    echo "Expected output at: $output_file"
    failures=$((failures + 1))
    return
  fi

  echo "OK   $label"
  log_verbose "Successfully processed $label"
}

# --- Main Execution ---

for example in "${examples[@]}"; do
  check_file "$formats_dir/$example" "$example"
done

log_verbose "Testing dotfile variants..."
dotfile_dir="$tmpdir/dotfiles"
mkdir -p "$dotfile_dir"

# Helper to copy if exists
safe_cp() {
  if [[ -f "$1" ]]; then
    cp "$1" "$2"
  else
    log_verbose "Warning: Source file for dotfile test missing: $1"
  fi
}

safe_cp "$formats_dir/HTML.env" "$dotfile_dir/.HTML.env"
safe_cp "$formats_dir/HTML.conf" "$dotfile_dir/.HTML"
safe_cp "$formats_dir/HTML.csv" "$dotfile_dir/.csvpalette"

if [[ -f "$dotfile_dir/.HTML.env" ]]; then check_file "$dotfile_dir/.HTML.env" ".HTML.env"; fi
if [[ -f "$dotfile_dir/.HTML" ]]; then check_file "$dotfile_dir/.HTML" ".HTML"; fi
if [[ -f "$dotfile_dir/.csvpalette" ]]; then check_file "$dotfile_dir/.csvpalette" ".csvpalette"; fi

if (( failures > 0 )); then
  echo "---------------------------------------"
  echo "$failures check(s) failed" >&2
  exit 1
fi

echo "All colorgen format checks passed."
