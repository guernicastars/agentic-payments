#!/usr/bin/env bash
# Build PDFs for every memo .tex in this directory.
# Usage: bash memos/build.sh [memo_basename]   # build one
#        bash memos/build.sh                   # build all
set -euo pipefail
cd "$(dirname "$0")"

build_one() {
  local stem="$1"
  echo ">> $stem.tex"
  pdflatex -interaction=nonstopmode -halt-on-error "$stem.tex" > /tmp/build_$stem.log 2>&1 || {
    echo "   FAIL — see /tmp/build_$stem.log"; return 1
  }
  # second pass for hyperrefs / TOC if any
  pdflatex -interaction=nonstopmode -halt-on-error "$stem.tex" > /tmp/build_$stem.log 2>&1
  rm -f "$stem.aux" "$stem.log" "$stem.out" "$stem.toc"
  echo "   ok -> $stem.pdf"
}

if [[ $# -eq 1 ]]; then
  build_one "$1"
else
  shopt -s nullglob
  for f in [0-9]*_*.tex; do
    build_one "${f%.tex}"
  done
fi
