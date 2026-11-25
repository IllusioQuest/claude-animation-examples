#!/bin/bash
# Concatenate preview frames (every 2nd frame → 12 fps) and mux the soundtrack.
cd "$(dirname "$0")/.."
LIST=preview/frames/list.txt
: > "$LIST"
for sc in S1_Scrapyard_Dawn S2_Workshop_Night S3_Village_Day S4_Chase S5_Depot_Night S6_New_Beginning; do
  for f in preview/frames/$sc/f_*.png; do
    echo "file '$(realpath "$f")'" >> "$LIST"
    echo "duration 0.0833333" >> "$LIST"
  done
done
# the very first frame of the film is frame 1 → audio t=0
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -i sound/soundtrack.wav \
  -vf "fps=12,format=yuv420p" -c:v libx264 -crf 24 -preset medium -c:a aac -b:a 160k -shortest \
  preview/ausschuss_preview.mp4
ls -la preview/ausschuss_preview.mp4
