"""Bake Hedda's coat cloth caches of a built blend to disk (blendcache_<name>/ next to the file).

    blender -b ausschuss.blend --python tools/bake_cloth.py

build.py runs this on its output: caches baked inside the build session did not reliably end up on disk
(the caches claimed to be baked with 0 frames on disk), which left the coat unsimulated in renders.
"""
import os
import time
import bpy

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import cloth as CL

t0 = time.time()
cloths = sorted((o for o in bpy.data.objects if o.name.startswith("Hedda_skirt_cloth")), key=lambda o: o.name)
sc = next(s for s in bpy.data.scenes if s.name != "FILM" and "Hedda" in s.objects)
CL.bind_details(sc, bpy.data.objects["Hedda"])
total = 0
for o in cloths:
    cl = o.modifiers.get("cloth")
    if cl is None:
        continue
    pc = cl.point_cache
    pc.use_disk_cache = True
    with bpy.context.temp_override(scene=sc, object=o, active_object=o, point_cache=pc):
        bpy.ops.ptcache.free_bake()
    sc.frame_set(pc.frame_start)
    with bpy.context.temp_override(scene=sc, object=o, active_object=o, point_cache=pc):
        bpy.ops.ptcache.bake(bake=True)
    n = int(pc.info.split()[0]) if pc.info and pc.info.split()[0].isdigit() else 0
    want = pc.frame_end - pc.frame_start + 1
    total += n
    print(f"baked {o.name} {pc.frame_start}-{pc.frame_end}: {pc.info}", "" if n >= want else "  <-- INCOMPLETE")
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
d = os.path.join(os.path.dirname(bpy.data.filepath), "blendcache_" + os.path.splitext(os.path.basename(bpy.data.filepath))[0])
print("cloth frames on disk", total, "files", len(os.listdir(d)) if os.path.isdir(d) else 0, "in", round(time.time() - t0, 1), "s")
