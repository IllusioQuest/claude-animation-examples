"""Render a list of frames of one scene: blender -b file.blend -P tools/stills.py -- SCENE outprefix f1 f2 ..."""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
scn = bpy.data.scenes[a[0]]
bpy.context.window_manager  # noop
pref = a[1]
frames = [int(x) for x in a[2:]]
scn.render.resolution_percentage = 25
scn.eevee.taa_render_samples = 2
for fr in frames:
    scn.frame_set(fr)
    # pick bound camera from markers
    cam = None
    for m in sorted(scn.timeline_markers, key=lambda m: m.frame):
        if m.frame <= fr and m.camera:
            cam = m.camera
    if cam:
        scn.camera = cam
    scn.render.filepath = f"{pref}{fr:05d}.png"
    bpy.ops.render.render(write_still=True, scene=scn.name)
