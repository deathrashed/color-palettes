#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
colorgen="${COLORGEN:-$repo_root/bin/colorgen}"
formats_dir="${FORMATS_DIR:-$repo_root/bin/formats}"
expected_count="${EXPECTED_COUNT:-141}"

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

if [[ ! -x "$colorgen" ]]; then
  echo "colorgen is not executable: $colorgen" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

failures=0

check_file() {
  local input="$1"
  local label="$2"
  local safe_label
  safe_label="$(printf '%s' "$label" | sed 's/[^A-Za-z0-9_-]/_/g')"
  local output="$tmpdir/$safe_label"
  local log

  if ! log="$("$colorgen" -i "$input" -o "$output" 2>&1)"; then
    echo "FAIL $label"
    echo "$log"
    failures=$((failures + 1))
    return
  fi

  if [[ "$log" != *"Wrote $expected_count colors"* ]]; then
    echo "FAIL $label"
    echo "Expected $expected_count colors, got:"
    echo "$log"
    failures=$((failures + 1))
    return
  fi

  local output_file="$output.clr"

  if [[ ! -s "$output_file" ]]; then
    echo "FAIL $label"
    echo "Missing output file: $output_file"
    failures=$((failures + 1))
    return
  fi

  echo "OK   $label"
}

for example in "${examples[@]}"; do
  check_file "$formats_dir/$example" "$example"
done

dotfile_dir="$tmpdir/dotfiles"
mkdir -p "$dotfile_dir"
cp "$formats_dir/HTML.env" "$dotfile_dir/.HTML.env"
cp "$formats_dir/HTML.conf" "$dotfile_dir/.HTML"
cp "$formats_dir/HTML.csv" "$dotfile_dir/.csvpalette"

check_file "$dotfile_dir/.HTML.env" ".HTML.env"
check_file "$dotfile_dir/.HTML" ".HTML"
check_file "$dotfile_dir/.csvpalette" ".csvpalette"

if (( failures > 0 )); then
  echo "$failures check(s) failed" >&2
  exit 1
fi

echo "All colorgen format checks passed."
