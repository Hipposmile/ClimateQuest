#!/bin/bash
set -e

if [[ -z "$1" ]]; then
  echo "Verwendung: imgvariants <bild.jpg> [bild2.png ...]"
  exit 1
fi

for input in "$@"; do
  base="${input%.*}"

  for width in 320 640 1280 1920; do
    magick "$input" -resize "${width}>" \
      -quality 80 "${base}-${width}.avif"

    magick "$input" -resize "${width}>" \
      -quality 80 "${base}-${width}.webp"

    echo "  → ${base}-${width}.avif/.webp"
  done

  magick "$input" "${base}-fallback.png"
  echo "  → ${base}-fallback.png"
  echo "✓ $input abgeschlossen"
done