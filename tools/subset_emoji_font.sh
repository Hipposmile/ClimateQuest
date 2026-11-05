#!/bin/bash
# Rebuilds static/fonts/OpenMoji-subset.woff2 (≈29 KB instead of the 2.6 MB full font).
# Run this after using a NEW emoji (<span class="emoji">&#x....;</span>) anywhere in the project.
# Requires: pip install fonttools brotli
# Verwendung: tools/subset_emoji_font.sh
set -e
cd "$(dirname "$0")/.."

CODEPOINTS=$(git ls-files '*.html' '*.py' '*.js' '*.css' '*.po' \
  | grep -v -E 'static/libraries|static/pwa/workbox|migrations|qrcode' \
  | xargs cat \
  | grep -o -E '&#x[0-9A-Fa-f]{4,6};' | sed -E 's/&#x([0-9A-Fa-f]+);/U+\1/' | sort -u | paste -sd, -)

pyftsubset tools/fonts/OpenMoji-color-glyf_colr_0.ttf \
  --unicodes="${CODEPOINTS},U+200D,U+FE0F,U+1F3FB-1F3FF" \
  --flavor=woff2 --layout-features='*' --glyph-names \
  --output-file=static/fonts/OpenMoji-subset.woff2
ls -la static/fonts/OpenMoji-subset.woff2
