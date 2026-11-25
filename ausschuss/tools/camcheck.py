"""Camera sanity: for each shot, cast a grid of rays through the frame and report what blocks
the view close to the lens (walls, poles, a coat right in front of the camera ...).

    blender -b ausschuss.blend -S S2_Workshop_Night -P tools/camcheck.py
"""
import bpy
from collections import Counter
from mathutils import Vector

sc = bpy.context.scene
VL = sc.view_layers[0]
dg = VL.depsgraph
mk = sorted(((m.frame, m.camera) for m in sc.timeline_markers if m.camera), key=lambda x: x[0])
NEAR = 0.7
for i, (a, cam) in enumerate(mk):
    b = (mk[i + 1][0] if i + 1 < len(mk) else sc.frame_end + 1) - 1
    for f in sorted({a + 2, (a + b) // 2, max(a, b - 2)}):
        sc.frame_set(f)
        VL.update()
        ce = cam.evaluated_get(dg)
        mw = ce.matrix_world
        o = mw.translation
        fr = ce.data.view_frame(scene=sc)
        hits = Counter()
        n = 0
        for u in range(7):
            for v in range(5):
                p = fr[2].lerp(fr[3], u / 6)  # bottom edge
                q = fr[1].lerp(fr[0], u / 6)  # top edge
                loc = p.lerp(q, v / 4)
                d = (mw.to_3x3() @ loc).normalized()
                ok, hp, nrm, idx, ob, _ = sc.ray_cast(dg, o, d, distance=NEAR)
                n += 1
                if ok:
                    hits[ob.name] += 1
        tot = sum(hits.values())
        if tot / n > 0.12:
            print(f"CAM {cam.name:22s} f{f}  {round(100 * tot / n)}% blocked within {NEAR}m: "
                  + ", ".join(f"{k}({v})" for k, v in hits.most_common(3)))
print("CAMCHECK done", sc.name)
