"""Real cloth for Hedda's coat skirt.

A copy of the skinned skirt gets a cloth simulation: the waist is pinned to the armature, the rest
swings, drapes and collides with her legs. The coat details (hem, pockets, flaps, patches, seam) are
copied and glued to the simulated skirt with Surface Deform. One bake covers the whole film timeline.

Simulations cannot survive teleports (sequence starts, jumps) or sitting, so around those the skinned
skirt is shown instead. Switching inside a shot would pop, so each cloth copy blends towards the skinned
shape (stored before the cloth modifier) at its segment ends: the swap then happens on identical shapes.
"""
import time
import bpy
from mathutils import Vector

DETAILS = ("_hem", "_pocket1", "_pocket-1", "_flap1", "_flap-1", "_front_seam", "_patch0", "_patch1")
RAMP = 10  # frames to blend between cloth and skinned shape at a segment end inside a shot


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
    """Frames where the rig jumps (cut) – translation > 0.3 m or yaw > 70 deg in one frame (a quick turn is
    something the cloth can follow: it swings)."""
    act = rig.animation_data.action
    fx = [act.fcurves.find("location", index=i) for i in range(3)]
    fr = act.fcurves.find("rotation_euler", index=2)
    out = []
    prev = None
    for f in range(f0, f1 + 1):
        p = Vector([c.evaluate(f) if c else 0.0 for c in fx])
        r = fr.evaluate(f) if fr else 0.0
        if prev is not None:
            if (p - prev[0]).length > 0.3 or abs(r - prev[1]) > 1.2:
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
    # carried by something (netted, in a cage): her own keys say nothing about how she moves then,
    # and the throws are far too fast for the cloth
    act = rig.animation_data.action
    for c in rig.constraints:
        fc = act.fcurves.find(f'constraints["{c.name}"].influence')
        if fc:
            on = [f for f in range(1, f_end + 1) if fc.evaluate(f) > 0.01]
            for f in on:
                blocked |= set(range(f - 2, f + 6))
    # tilted (a fall, lying in the dirt): her whole frame - and the cloth's floor with it - rotates, the
    # simulation goes wild and never recovers (S4: after the fall the coat hung 0.6-0.9 m off her for the
    # rest of the shot). Skinned coat while tilted; a fresh simulation once she is upright again.
    fx_ = act.fcurves.find("rotation_euler", index=0)
    fy_ = act.fcurves.find("rotation_euler", index=1)
    for f in range(1, f_end + 1):
        tx = abs(fx_.evaluate(f)) if fx_ else 0.0
        ty = abs(fy_.evaluate(f)) if fy_ else 0.0
        if max(tx, ty) > 0.25:
            blocked |= set(range(f - 3, f + 10))
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


def _node_groups():
    st = bpy.data.node_groups.get("coat_store_skin")
    if st is None:
        st = bpy.data.node_groups.new("coat_store_skin", "GeometryNodeTree")
        st.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        st.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        gi, go = st.nodes.new("NodeGroupInput"), st.nodes.new("NodeGroupOutput")
        sn = st.nodes.new("GeometryNodeStoreNamedAttribute")
        sn.data_type = "FLOAT_VECTOR"
        sn.inputs["Name"].default_value = "skin_pos"
        st.links.new(gi.outputs[0], sn.inputs["Geometry"])
        st.links.new(st.nodes.new("GeometryNodeInputPosition").outputs[0], sn.inputs["Value"])
        st.links.new(sn.outputs[0], go.inputs[0])
    mx = bpy.data.node_groups.get("coat_mix_skin")
    if mx is None:
        mx = bpy.data.node_groups.new("coat_mix_skin", "GeometryNodeTree")
        mx.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        k = mx.interface.new_socket("Skin", in_out="INPUT", socket_type="NodeSocketFloat")
        k.min_value, k.max_value = 0.0, 1.0
        mx.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        gi, go = mx.nodes.new("NodeGroupInput"), mx.nodes.new("NodeGroupOutput")
        na = mx.nodes.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT_VECTOR"
        na.inputs["Name"].default_value = "skin_pos"
        mix = mx.nodes.new("ShaderNodeMix")
        mix.data_type = "VECTOR"
        sp = mx.nodes.new("GeometryNodeSetPosition")
        mx.links.new(gi.outputs[1], mix.inputs["Factor"])
        mx.links.new(mx.nodes.new("GeometryNodeInputPosition").outputs[0], mix.inputs[4])
        mx.links.new(na.outputs["Attribute"], mix.inputs[5])
        mx.links.new(gi.outputs[0], sp.inputs["Geometry"])
        mx.links.new(mix.outputs[1], sp.inputs["Position"])
        mx.links.new(sp.outputs[0], go.inputs[0])
    return st, mx


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
    ng_store, ng_mix = _node_groups()
    cs.modifiers.new("store", "NODES").node_group = ng_store
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
    cs.modifiers.new("mix", "NODES").node_group = ng_mix
    cs.modifiers.new("solid", "SOLIDIFY").thickness = 0.008
    cl.point_cache.use_disk_cache = True
    cl.point_cache.name = name
    cl.point_cache.frame_start = f0
    cl.point_cache.frame_end = f1
    return cs, cl


def _key_skin(cs, keys):
    """keys: (frame, skin factor) – 1 = skinned shape, 0 = pure cloth"""
    m = cs.modifiers["mix"]
    sock = next(k for k in m.keys() if k.startswith("Socket_") and not k.endswith(("_use_attribute", "_attribute_name")))
    path = f'modifiers["mix"]["{sock}"]'
    for f, v in keys:
        m[sock] = v
        cs.keyframe_insert(path, frame=f)
    fc = cs.animation_data.action.fcurves.find(path)
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"


def bind_details(sc, rig):
    """Bind the coat details (Surface Deform) to their cloth skirt in its calm rest shape: simulation off,
    rest pose. Bound against a mid-simulation state the bind fails (concave polygons) and the details
    stay behind, floating off the coat. Returns (bound, total)."""
    cloths = [o for o in bpy.data.objects if o.name.startswith("Hedda_skirt_cloth")]
    for cs in cloths:
        cs.modifiers["cloth"].show_viewport = cs.modifiers["cloth"].show_render = False
    # hidden objects are not evaluated, and a hidden target cannot be bound to: unhide for the bind
    muted = []
    for o in bpy.data.objects:
        if o.name.startswith("Hedda_") and "_cloth" in o.name:
            ad = o.animation_data
            for fc in (ad.action.fcurves if ad and ad.action else []):
                if fc.data_path.startswith("hide") and not fc.mute:
                    fc.mute = True
                    muted.append(fc)
            o.hide_viewport = o.hide_render = False
    rig.data.pose_position = "REST"
    sc.frame_set(1)
    vl = sc.view_layers[0]
    vl.update()
    bound = total = 0
    for o in bpy.data.objects:
        sd = o.modifiers.get("sd") if o.type == "MESH" else None
        if sd is None or sd.type != "SURFACE_DEFORM" or not o.name.startswith("Hedda_"):
            continue
        total += 1
        with bpy.context.temp_override(scene=sc, view_layer=vl, object=o, active_object=o):
            if sd.is_bound:
                bpy.ops.object.surfacedeform_bind(modifier="sd")  # unbind
            bpy.ops.object.surfacedeform_bind(modifier="sd")
        bound += sd.is_bound
    rig.data.pose_position = "POSE"
    for cs in cloths:
        cs.modifiers["cloth"].show_viewport = cs.modifiers["cloth"].show_render = True
    for fc in muted:
        fc.mute = False
    sc.frame_set(1)
    vl.update()
    print("coat details bound", bound, "of", total)
    return bound, total


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
    # a floor for the cloth: an invisible plane at her feet that goes everywhere with her (sitting or
    # kneeling on the ground the coat used to sink through the floor)
    if bpy.data.objects.get("Hedda_coatfloor") is None:
        me = bpy.data.meshes.new("Hedda_coatfloor")
        r_ = 1.4
        me.from_pydata([(-r_, -r_, 0), (r_, -r_, 0), (r_, r_, 0), (-r_, r_, 0)], [], [(0, 1, 2, 3)])
        fl = bpy.data.objects.new("Hedda_coatfloor", me)
        for col in sk.users_collection:
            col.objects.link(fl)
        fl.parent = rig
        fl.location = (0, 0, 0.004)
        fl.hide_render = True
        fl.display_type = "WIRE"
        fl.modifiers.new("coll", "COLLISION")
        fl.collision.thickness_outer = 0.006
        fl.collision.cloth_friction = 8.0
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
    bind_details(sc, rig)
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
    # camera cuts: a segment that ends or starts on one may swap shapes hard, the cut hides it
    cam_cuts = {m.frame for s_ in ctx.seq.values() for m in s_["scene"].timeline_markers if m.camera}
    cam_cuts |= {s_["f0"] for s_ in ctx.seq.values()}
    cloth_frames = set()
    # whip turns (> 17 deg per frame): no cloth follows those, it balloons into a sack – lean on the
    # skinned shape for the turn and let the cloth take over again afterwards
    fr_yaw = rig.animation_data.action.fcurves.find("rotation_euler", index=2)
    spin = set()
    if fr_yaw:
        prev_y = fr_yaw.evaluate(1)
        for f in range(2, f_end + 1):
            y = fr_yaw.evaluate(f)
            if abs(y - prev_y) > 0.3:
                spin.add(f)
            prev_y = y

    def clamp(x):
        return max(0.0, min(1.0, x))

    for a, b, parts, cs, cl in sets:
        end_in_shot = (b + 1) not in cam_cuts and b < f_end
        sp = sorted(f for f in spin if a <= f <= b)
        w = {}
        for f in range(a, b + 1):
            v = clamp(1 - (f - a) / RAMP)  # the cloth begins in the skinned shape and sags: blend it in
            if end_in_shot:
                v = max(v, clamp(1 - (b - f) / RAMP))
            for g in sp:
                v = max(v, clamp(1 - (g - f) / 3) if f <= g else clamp(1 - (f - g) / 12))
            w[f] = round(v, 3)
        keys = [(f, v) for f, v in w.items() if v != w.get(f - 1) or v != w.get(f + 1)]
        _key_skin(cs, keys)
        keyvis(parts, [(a, b)])
        cloth_frames |= set(range(a, b + 1))
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
