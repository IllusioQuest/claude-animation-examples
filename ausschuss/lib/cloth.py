"""Real cloth for Hedda's coat skirt.

A copy of the skinned skirt gets a cloth simulation: the waist is pinned to the armature, the rest
swings, drapes and collides with her legs. The coat details (hem, pockets, flaps, patches, seam) are
copied and glued to the simulated skirt with Surface Deform. One bake covers the whole film timeline.

Simulations cannot survive teleports (shot cuts, sequence starts) or sitting, so around those the
skinned skirt is shown instead: cloth_ok(f) decides per frame, visibility keys switch the two sets.
"""
import time
import bpy
from mathutils import Vector

DETAILS = ("_hem", "_pocket1", "_pocket-1", "_flap1", "_flap-1", "_front_seam", "_patch0", "_patch1")
SETTLE = 14  # frames after a teleport before the cloth is trusted again


def _dup(o, name):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name
    for col in o.users_collection:
        col.objects.link(c)
    if c.animation_data:
        c.animation_data_clear()
    return c


def _teleports(rig, f0, f1):
    """Frames where the rig jumps (cut) – translation > 0.3 m or yaw > 25 deg in one frame."""
    act = rig.animation_data.action
    fx = [act.fcurves.find("location", index=i) for i in range(3)]
    fr = act.fcurves.find("rotation_euler", index=2)
    out = []
    prev = None
    for f in range(f0, f1 + 1):
        p = Vector([c.evaluate(f) if c else 0.0 for c in fx])
        r = fr.evaluate(f) if fr else 0.0
        if prev is not None:
            if (p - prev[0]).length > 0.3 or abs(r - prev[1]) > 0.44:
                out.append(f)
        prev = (p, r)
    return out


def apply(ctx, f_end):
    t0 = time.time()
    h = ctx.hedda
    rig = h.rig
    sk = bpy.data.objects.get("Hedda_skirt")
    if sk is None:
        return
    # ---- the simulated copy
    cs = _dup(sk, "Hedda_skirt_cloth")
    for m in list(cs.modifiers):
        if m.type != "ARMATURE":
            cs.modifiers.remove(m)
    vg = cs.vertex_groups.new(name="pin")
    zs = [v.co.z for v in cs.data.vertices]
    ztop, zbot = max(zs), min(zs)
    for v in cs.data.vertices:
        t = (v.co.z - zbot) / (ztop - zbot)
        # waist fully pinned; the rest gets a weak goal towards the skinned shape, so the coat can
        # swing and sway but never creeps up the legs over thousands of frames
        vg.add([v.index], max(0.1, min(1.0, (t - 0.72) / 0.2)), "REPLACE")
    cl = cs.modifiers.new("cloth", "CLOTH")
    s = cl.settings
    s.quality = 6
    s.mass = 0.4
    s.tension_stiffness = 25
    s.compression_stiffness = 25
    s.shear_stiffness = 15
    s.bending_stiffness = 2.0
    s.air_damping = 1.5
    s.vertex_group_mass = "pin"
    s.pin_stiffness = 1.0
    cl.collision_settings.distance_min = 0.008
    cs.modifiers.new("solid", "SOLIDIFY").thickness = 0.008
    cl.point_cache.use_disk_cache = True  # blendcache_ausschuss/ next to the .blend (keeps the file small)
    cl.point_cache.name = "hedda_coat"
    cl.point_cache.frame_start = 1
    cl.point_cache.frame_end = f_end
    for n in ("thighL", "thighR", "shinL", "shinR", "kneeL", "kneeR"):
        o = bpy.data.objects.get("Hedda_" + n)
        if o and not any(m.type == "COLLISION" for m in o.modifiers):
            o.modifiers.new("coll", "COLLISION")
            o.collision.thickness_outer = 0.01
            o.collision.cloth_friction = 0.0  # the hem slides off the knees instead of riding up
    # ---- details glued to the cloth (bound in the rest pose, where skinned and cloth coincide)
    dcopies = []
    for suf in DETAILS:
        o = bpy.data.objects.get("Hedda" + suf)
        if o is None:
            continue
        c = _dup(o, o.name + "_cloth")
        for m in list(c.modifiers):
            if m.type == "ARMATURE":
                c.modifiers.remove(m)
        sd = c.modifiers.new("sd", "SURFACE_DEFORM")
        sd.target = cs
        # move it first in the stack
        while c.modifiers[0].name != "sd":
            c.modifiers.move(len(c.modifiers) - 1, 0)
        dcopies.append((o, c))
    sc = next(iter(ctx.seq.values()))["scene"]
    rig.data.pose_position = "REST"
    sc.frame_set(1)
    bpy.context.view_layer.update()
    for o, c in dcopies:
        with bpy.context.temp_override(scene=sc, object=c, active_object=c):
            bpy.ops.object.surfacedeform_bind(modifier="sd")
    rig.data.pose_position = "POSE"
    # ---- bake the whole film in one go
    sc.frame_set(1)
    with bpy.context.temp_override(scene=sc, object=cs, active_object=cs, point_cache=cl.point_cache):
        bpy.ops.ptcache.bake(bake=True)
    # ---- which set is visible when
    bad = set()
    for i, s_ in ctx.seq.items():
        for f in range(s_["f0"], s_["f0"] + SETTLE):
            bad.add(f)
    for f in _teleports(rig, 1, f_end):
        for k in range(f - 1, f + SETTLE):
            bad.add(k)
    for (who, a, b) in ctx.ground_skip:
        if who == "Hedda":
            for k in range(a - 2, b + SETTLE):
                bad.add(k)
    long_parts = [sk] + [o for o, _ in dcopies]
    cloth_parts = [cs] + [c for _, c in dcopies]
    seated = [o for o in rig.children if o.name.endswith(("_lapL", "_lapR", "_seatback"))]
    seat_frames = set()
    for o in seated:
        ad = o.animation_data
        if ad and ad.action:
            fc = ad.action.fcurves.find("hide_render")
            if fc:
                for f in range(1, f_end + 1):
                    if fc.evaluate(f) < 0.5:
                        seat_frames.add(f)
    for o in long_parts + cloth_parts:
        if o.animation_data and o.animation_data.action:
            for p in ("hide_render", "hide_viewport"):
                fc = o.animation_data.action.fcurves.find(p)
                if fc:
                    o.animation_data.action.fcurves.remove(fc)
    state = None
    for f in range(0, f_end + 2):
        if f in seat_frames:
            st = "none"
        elif f in bad or f == 0:
            st = "skin"
        else:
            st = "cloth"
        if st != state:
            for o in long_parts:
                o.hide_render = o.hide_viewport = st != "skin"
                o.keyframe_insert("hide_render", frame=f)
                o.keyframe_insert("hide_viewport", frame=f)
            for o in cloth_parts:
                o.hide_render = o.hide_viewport = st != "cloth"
                o.keyframe_insert("hide_render", frame=f)
                o.keyframe_insert("hide_viewport", frame=f)
            state = st
    for o in long_parts + cloth_parts:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path.startswith("hide"):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    print("cloth baked", f_end, "frames, cloth on", f_end - len(bad | seat_frames), "in", round(time.time() - t0, 1), "s")
