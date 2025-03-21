#!/bin/bash

FONTDIR=~/.local/share/fonts/JetBrainsMono
cd /opt || exit 1
git clone https://github.com/odem/mps.git
cd mps || exit 2
./terminal.bash
./installer/terminal-nvim.bash -a all


# for file in "$FONTDIR"/*.ttf; do
#     filename=$(basename "$file" .ttf)  # Extract filename without path and extension
#     echo "$filename"
#     otf2bdf -p 16 -o "$FONTDIR/$filename".bdf "$FONTDIR/$filename".ttf
#     fontforge -lang=ff -c "Open(\"$FONTDIR/$filename.ttf\"); Generate(\"$FONTDIR/$filename.bdf\")"
#     bdf2psd "$FONTDIR/$filename".bdf "$FONTDIR/$filename".ttf
#     bdf2psd -unicode "$FONTDIR/$filename".bdf "$FONTDIR/$filename".ttf
#     gzip "$FONTDIR/$filename".psfu
# done
#
# for f in "$FONTDIR"/*.ttf ; do
#     echo "FILE: $f"
# done
#
