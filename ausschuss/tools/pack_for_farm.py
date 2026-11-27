"""Write a self-contained copy of a built blend for a render farm: the coat simulation baked into the file
itself (no blendcache folder), every external file packed. The original file is not touched.

    blender -b ausschuss.blend --python tools/pack_for_farm.py [-- out.blend]

The farm renders the scene "FILM" (frames 1-6458, 24 fps); its sequencer strips pull in the six
sequence scenes. The soundtrack is not inside (sound/soundtrack.ogg is muxed onto the frames afterwards).
"""
import os
import sys
import time
import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import cloth as CL

t0 = time.time()
src = bpy.data.filepath
out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.splitext(src)[0] + "_farm.blend"
out = os.path.abspath(out)
sc = next(s for s in bpy.data.scenes if s.name != "FILM" and "Hedda" in s.objects)
CL.bind_details(sc, bpy.data.objects["Hedda"])
total = want = 0
for o in sorted((o for o in bpy.data.objects if o.name.startswith("Hedda_skirt_cloth")), key=lambda o: o.name):
    cl = o.modifiers.get("cloth")
    if cl is None:
        continue
    pc = cl.point_cache
    with bpy.context.temp_override(scene=sc, object=o, active_object=o, point_cache=pc):
        bpy.ops.ptcache.free_bake()
    pc.use_disk_cache = False  # an in-memory cache is saved inside the .blend
    sc.frame_set(pc.frame_start)
    with bpy.context.temp_override(scene=sc, object=o, active_object=o, point_cache=pc):
        bpy.ops.ptcache.bake(bake=True)
    n = int(pc.info.split()[0]) if pc.info and pc.info.split()[0].isdigit() else 0
    total += n
    want += pc.frame_end - pc.frame_start + 1
    print(f"baked into file: {o.name} {pc.frame_start}-{pc.frame_end}: {pc.info}")
# pack images, fonts, sounds, ...; then list anything that still points outside the file
bpy.ops.file.pack_all()
external = []
for coll in (bpy.data.images, bpy.data.fonts, bpy.data.sounds, bpy.data.movieclips, bpy.data.volumes,
             bpy.data.cache_files, bpy.data.libraries, bpy.data.texts):
    for d in coll:
        fp = getattr(d, "filepath", "")
        if fp and not getattr(d, "packed_file", None) and not getattr(d, "is_in_memory", False) \
                and fp != "<builtin>" and getattr(d, "source", "FILE") not in ("GENERATED", "VIEWER"):
            external.append((type(d).__name__, d.name, fp))
for o in bpy.data.objects:
    for m in o.modifiers:
        pc = getattr(m, "point_cache", None)
        if pc and pc.use_disk_cache:
            external.append(("PointCache", o.name, "disk cache"))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
print("FARM cloth frames in file", total, "of", want)
print("FARM external references left:", len(external))
for e in external:
    print("FARM EXTERNAL", *e)
print("FARM wrote", out, round(os.path.getsize(out) / 1e6, 1), "MB in", round(time.time() - t0, 1), "s")
