"""Check the baked coat simulation of a built blend: how far the simulated skirt strays from the skinned
coat (its 'skin_pos' attribute), per segment. Flags frames where it hangs far off her body.

    blender -b ausschuss.blend --python tools/check_cloth.py [-- step]
"""
import sys
import bpy

step = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 6
LIMIT = 0.35  # m, 95th percentile distance from the skinned shape
scenes = [s for s in bpy.data.scenes if s.name != "FILM"]
cloths = sorted((o for o in bpy.data.objects if o.name.startswith("Hedda_skirt_cloth")), key=lambda o: o.name)
bad = []
for cs in cloths:
    pc = cs.modifiers["cloth"].point_cache
    sc = next((s for s in scenes if s.frame_start <= pc.frame_start <= s.frame_end and cs.name in s.objects), None)
    if sc is None:
        continue
    worst = (0.0, None)
    for f in range(pc.frame_start, pc.frame_end + 1, step):
        sc.frame_set(f)
        vl = sc.view_layers[0]
        e = cs.evaluated_get(vl.depsgraph)
        if e.hide_render:
            continue
        me = e.to_mesh()
        at = me.attributes.get("skin_pos")
        if at:
            d = sorted((me.vertices[i].co - at.data[i].vector).length for i in range(len(me.vertices)))
            p95 = d[int(len(d) * 0.95)]
            worst = max(worst, (p95, f))
            if p95 > LIMIT:
                bad.append((cs.name, f, round(p95, 2)))
        e.to_mesh_clear()
    print(f"CHECK {cs.name} {pc.frame_start}-{pc.frame_end} worst p95 {worst[0]:.2f} m at {worst[1]}")
print("CHECK frames over", LIMIT, "m:", len(bad))
for b in bad[:60]:
    print("CHECK BAD", *b)
