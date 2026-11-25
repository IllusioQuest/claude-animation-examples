#!/bin/bash
# Low-res preview: every 2nd frame (12 fps), two parallel workers.
# usage: tools/render_preview.sh [scenes...]   (default: all)
cd "$(dirname "$0")/.."
SCENES=("$@")
[ ${#SCENES[@]} -eq 0 ] && SCENES=(S1_Scrapyard_Dawn S2_Workshop_Night S3_Village_Day S4_Chase S5_Depot_Night S6_New_Beginning)
render_one() {
  local sc=$1
  rm -rf "preview/frames/$sc"; mkdir -p "preview/frames/$sc"
  blender -b ausschuss.blend -S "$sc" -o "//preview/frames/$sc/f_#####" -F PNG -j 2 -a > "preview/frames/$sc.log" 2>&1
  echo "done $sc"
}
export -f render_one
printf "%s\n" "${SCENES[@]}" | xargs -P 2 -I{} bash -c 'render_one {}'
