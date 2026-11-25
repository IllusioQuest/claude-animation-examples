"""Print, per scene, frames sampling every camera shot (start+6, middle, end-6).
    blender -b ausschuss.blend -P tools/shotframes.py -- out.txt"""
import sys
import bpy
out = sys.argv[sys.argv.index("--") + 1]
lines = []
for sc in sorted(bpy.data.scenes, key=lambda s: s.name):
    if not sc.name.startswith("S"):
        continue
    mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
    fr = []
    for i, m in enumerate(mk):
        a = m.frame
        b = (mk[i + 1].frame if i + 1 < len(mk) else sc.frame_end + 1) - 1
        for f in (a + 6, (a + b) // 2, b - 6):
            if a <= f <= b and f not in fr:
                fr.append(f)
    lines.append(sc.name + " " + ",".join(str(f) for f in fr))
open(out, "w").write("\n".join(lines) + "\n")
