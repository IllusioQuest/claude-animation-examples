#!/bin/bash
# usage: tools/stills.sh file.blend SCENE outdir f1,f2,f3
mkdir -p "$3"; rm -f "$3"/*.png
blender -b "$1" -S "$2" -o "$3/f_#####" -F PNG -f "$4" 2>&1 | grep -iE "Traceback|Error:" | grep -v EGL
