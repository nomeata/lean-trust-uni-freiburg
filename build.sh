#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  ""|--html) export_pdf=false ;;
  --pdf) export_pdf=true ;;
  *) printf 'Usage: %s [--html|--pdf]\n' "$0" >&2; exit 2 ;;
esac
# MD4Lean compiles C with `cc`; fall back to the Lean toolchain's compiler.
if ! command -v cc >/dev/null; then
  PATH="$(dirname "$(elan which lean)"):$PATH"
fi
python3 tools/figures.py
lake build
lake exe lean-trust-freiburg-slides
if "$export_pdf"; then
  node export-pdf.mjs
fi
