#!/bin/bash
# Render the per-shot sample frames (${FRAMES:-preview/shotframes.txt}) and make contact sheets.
cd "$(dirname "$0")/.."
while read sc frames; do
  [ -n "$ONLY" ] && [[ "$sc" != *"$ONLY"* ]] && continue
  d=preview/shots/$sc; mkdir -p $d; rm -f $d/*.png
  blender -b ausschuss.blend -S $sc -o "//$d/f_#####" -F PNG -f $frames > $d.log 2>&1
  python3 tools/sheet.py preview/shots/sheet_$sc.png 6 $d/f_*.png
  echo "done $sc"
done < ${FRAMES:-preview/shotframes.txt}
