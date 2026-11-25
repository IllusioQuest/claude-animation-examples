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
SETTLE = 4  # frames after a segment start before the cloth is shown (initial sag)


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


def _segments(ctx, rig, f_end):
    """Continuous stretches of the film: split at sequence starts, teleports and seated ranges."""
    cuts = set(s_["f0"] for s_ in ctx.seq.values()) | set(_teleports(rig, 1, f_end))
    blocked = set()
    for (who, a, b) in ctx.ground_skip:
        if who == "Hedda":
            blocked |= set(range(a - 2, b + 6))
    segs = []
    cur = None
    for f in range(1, f_end + 1):
        if f in cuts or f in blocked:
            if cur and f - cur >= 30:
                segs.append((cur, f - 1))
            cur = None if f in blocked else f
        elif cur is None:
            cur = f
    if cur and f_end - cur >= 30:
        segs.append((cur, f_end))
    # rig offstage (far below) is useless to simulate
    act = rig.animation_data.action
    fz = act.fcurves.find("location", index=2)
    return [(a, b) for a, b in segs if fz is None or fz.evaluate((a + b) / 2) > -50]


def _make_cloth(sk, name, f0, f1):
    cs = _dup(sk, name)
    for m in list(cs.modifiers):
        if m.type != "ARMATURE":
            cs.modifiers.remove(m)
    vg = cs.vertex_groups.new(name="pin")
    zs = [v.co.z for v in cs.data.vertices]
    ztop, zbot = max(zs), min(zs)
    for v in cs.data.vertices:
        t = (v.co.z - zbot) / (ztop - zbot)
        # waist pinned; the rest has a weak goal towards the skinned shape (no slow creep)
        vg.add([v.index], max(0.06, min(1.0, (t - 0.72) / 0.2)), "REPLACE")
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
    cl.point_cache.use_disk_cache = True
    cl.point_cache.name = name
    cl.point_cache.frame_start = f0
    cl.point_cache.frame_end = f1
    return cs, cl


def apply(ctx, f_end):
    t0 = time.time()
    h = ctx.hedda
    rig = h.rig
    sk = bpy.data.objects.get("Hedda_skirt")
    if sk is None:
        return
    for n in ("thighL", "thighR", "shinL", "shinR", "kneeL", "kneeR"):
        o = bpy.data.objects.get("Hedda_" + n)
        if o and not any(m.type == "COLLISION" for m in o.modifiers):
            o.modifiers.new("coll", "COLLISION")
            o.collision.thickness_outer = 0.01
            o.collision.cloth_friction = 0.0
    segs = _segments(ctx, rig, f_end)
    sc = next(iter(ctx.seq.values()))["scene"]
    sets = []  # (f0, f1, [cloth parts])
    originals = [bpy.data.objects.get("Hedda" + suf) for suf in DETAILS]
    originals = [o for o in originals if o]
    for i, (a, b) in enumerate(segs):
        cs, cl = _make_cloth(sk, f"Hedda_skirt_cloth{i:02d}", a, b)
        parts = [cs]
        for o in originals:
            c = _dup(o, f"{o.name}_cloth{i:02d}")
            for m in list(c.modifiers):
                if m.type == "ARMATURE":
                    c.modifiers.remove(m)
            sd = c.modifiers.new("sd", "SURFACE_DEFORM")
            sd.target = cs
            while c.modifiers[0].name != "sd":
                c.modifiers.move(len(c.modifiers) - 1, 0)
            parts.append(c)
        sets.append((a, b, parts, cs, cl))
    rig.data.pose_position = "REST"
    sc.frame_set(1)
    bpy.context.view_layer.update()
    for a, b, parts, cs, cl in sets:
        for c in parts[1:]:
            with bpy.context.temp_override(scene=sc, object=c, active_object=c):
                bpy.ops.object.surfacedeform_bind(modifier="sd")
    rig.data.pose_position = "POSE"
    for a, b, parts, cs, cl in sets:
        sc.frame_set(a)
        with bpy.context.temp_override(scene=sc, object=cs, active_object=cs, point_cache=cl.point_cache):
            bpy.ops.ptcache.bake(bake=True)
    # ---- visibility: one cloth set inside its segment (after a short settle), the skinned coat elsewhere
    seated = [o for o in rig.children if o.name.endswith(("_lapL", "_lapR", "_seatback"))]
    seat_frames = set()
    for o in seated:
        ad = o.animation_data
        fc = ad.action.fcurves.find("hide_render") if ad and ad.action else None
        if fc:
            seat_frames |= {f for f in range(1, f_end + 1) if fc.evaluate(f) < 0.5}
    long_parts = [sk] + originals
    for o in long_parts:
        ad = o.animation_data
        if ad and ad.action:
            for p in ("hide_render", "hide_viewport"):
                fc = ad.action.fcurves.find(p)
                if fc:
                    ad.action.fcurves.remove(fc)

    def keyvis(objs, intervals):
        """visible exactly inside the given [a, b] intervals"""
        for o in objs:
            o.hide_render = o.hide_viewport = True
            o.keyframe_insert("hide_render", frame=0)
            o.keyframe_insert("hide_viewport", frame=0)
            for a, b in intervals:
                for f, hid in ((a, False), (b + 1, True)):
                    o.hide_render = o.hide_viewport = hid
                    o.keyframe_insert("hide_render", frame=f)
                    o.keyframe_insert("hide_viewport", frame=f)
            for fc in o.animation_data.action.fcurves:
                if fc.data_path.startswith("hide"):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
    cloth_frames = set()
    for a, b, parts, cs, cl in sets:
        iv = (a + SETTLE, b)
        keyvis(parts, [iv] if iv[0] <= b else [])
        cloth_frames |= set(range(iv[0], b + 1))
    skin_iv = []
    cur = None
    for f in range(0, f_end + 2):
        on = f not in cloth_frames and f not in seat_frames
        if on and cur is None:
            cur = f
        if not on and cur is not None:
            skin_iv.append((cur, f - 1))
            cur = None
    if cur is not None:
        skin_iv.append((cur, f_end + 1))
    keyvis(long_parts, skin_iv)
    print("cloth baked", len(sets), "segments,", len(cloth_frames), "cloth frames in", round(time.time() - t0, 1), "s")
