"""Life & atmosphere pass, applied after all sequences are animated.

- idle noise (breathing, small head drift) layered on top of the keyed animation
- automatic blinks where nothing else happens with the eyes
- springy antenna (Funke), balancing wobble (Erfasser), ear/head drift (Bello)
- floating dust motes per scene, birds over the sunrise
"""
import math
import random
import bmesh
import bpy
from mathutils import Vector
import core as C
import anim as A


def _fc(rig, bone, prop, idx):
    ad = rig.animation_data
    path = f'pose.bones["{bone}"].{prop}'
    fc = ad.action.fcurves.find(path, index=idx) if ad and ad.action else None
    if fc is None:
        pb = rig.pose.bones.get(bone)
        if pb is None:
            return None
        pb.keyframe_insert(prop, frame=1, index=idx)
        fc = rig.animation_data.action.fcurves.find(path, index=idx)
    return fc


def noise(fc, amp_deg, period, seed):
    if fc is None:
        return
    m = fc.modifiers.new("NOISE")
    m.scale = period
    m.strength = math.radians(amp_deg)
    m.phase = seed * 13.7 % 100
    m.offset = seed * 31 % 200


def onstage(rig, f):
    fc = rig.animation_data.action.fcurves.find("location", index=2)
    return fc is None or fc.evaluate(f) > -100


def auto_blinks(rig, f0, f1, eye_bones, closed, rnd, gap=(60, 140), open_test=None, prop="scale", idx=2):
    """Insert blinks into the eye channels where no other eye animation happens nearby."""
    fcs = [_fc(rig, b, prop, idx) for b in eye_bones]
    if any(fc is None for fc in fcs):
        return 0
    keys = sorted({round(k.co.x) for fc in fcs for k in fc.keyframe_points})
    n = 0
    f = f0 + rnd.randint(20, gap[1])
    while f < f1 - 6:
        near = any(abs(k - f) < 8 for k in keys)
        cur = [fc.evaluate(f) for fc in fcs]
        if not near and onstage(rig, f) and (open_test is None or open_test(cur[0])):
            for b, fc, c in zip(eye_bones, fcs, cur):
                pb = rig.pose.bones[b]
                for fr, v in ((f - 2, c), (f, closed), (f + 3, c)):
                    vals = list(getattr(pb, prop))
                    vals[idx] = v
                    setattr(pb, prop, vals)
                    pb.keyframe_insert(prop, frame=fr, index=idx)
            n += 1
        f += rnd.randint(*gap)
    return n


def humans(ctx, f_end):
    rnd = random.Random(7)
    people = [ctx.hedda] + list(ctx.vill.values())
    for k, a in enumerate(people):
        r = a.rig
        noise(_fc(r, "chest", "rotation_euler", 0), 1.6, 38, k * 3 + 1)
        noise(_fc(r, "spine", "rotation_euler", 2), 0.8, 70, k * 3 + 2)
        noise(_fc(r, "head", "rotation_euler", 0), 2.2, 55, k * 3 + 3)
        noise(_fc(r, "head", "rotation_euler", 2), 3.0, 75, k * 3 + 4)
        auto_blinks(r, 1, f_end, ["eye_L", "eye_R"], 0.08, rnd, open_test=lambda v: v > 0.6)


def robots(ctx, f_end):
    rnd = random.Random(11)
    f = ctx.funke.rig
    noise(_fc(f, "antenna", "rotation_euler", 0), 5.0, 6, 1)
    noise(_fc(f, "antenna", "rotation_euler", 2), 5.0, 7, 2)
    noise(_fc(f, "head", "rotation_euler", 2), 2.0, 40, 3)
    auto_blinks(f, 1, f_end, ["lid"], math.radians(-5), rnd, gap=(80, 170),
                open_test=lambda v: v < math.radians(-85), prop="rotation_euler", idx=0)
    e = ctx.erf.rig
    noise(_fc(e, "body", "rotation_euler", 0), 1.6, 22, 4)
    noise(_fc(e, "body", "rotation_euler", 1), 1.6, 26, 5)
    noise(_fc(e, "head", "rotation_euler", 2), 1.5, 50, 6)
    b = ctx.bello.rig
    noise(_fc(b, "head", "rotation_euler", 0), 3.0, 30, 7)
    noise(_fc(b, "head", "rotation_euler", 2), 4.0, 45, 8)


def dust(name, coll, lo, hi, n, color, r=(0.004, 0.01), strength=0.5, seed=0):
    rnd = random.Random(seed)
    m = bpy.data.materials.get(name + "_m") or C.emission(name + "_m", color, strength)
    me = bpy.data.meshes.new(name + "_me")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    for i in range(n):
        o = bpy.data.objects.new(f"{name}{i}", me)
        coll.objects.link(o)
        s = rnd.uniform(*r)
        o.scale = (s, s, s)
        o.location = Vector([rnd.uniform(a, b) for a, b in zip(lo, hi)])
        o.keyframe_insert("location", frame=1)
        for k in range(3):
            fc = o.animation_data.action.fcurves.find("location", index=k)
            md = fc.modifiers.new("NOISE")
            md.scale = rnd.uniform(70, 140)
            md.strength = 0.6 if k < 2 else 0.35
            md.phase = rnd.uniform(0, 100)


def bird(name, coll, path, f0, f1, flap=5, size=0.35, seed=0):
    """Simple silhouette bird flying a straight line with flapping wings."""
    rnd = random.Random(seed)
    m = bpy.data.materials.get("bird_m") or C.mat("bird_m", (0.05, 0.04, 0.04), rough=0.9, dirt=0)
    root = bpy.data.objects.new(name, None)
    coll.objects.link(root)
    body = C.sphere(name + "_b", size * 0.18, scale=(0.7, 2.2, 0.7), m=m, seg=8, rings=4, coll=coll)
    body.parent = root
    wings = []
    for sx in (-1, 1):
        piv = bpy.data.objects.new(f"{name}_wp{sx}", None)
        coll.objects.link(piv)
        piv.parent = root
        me = bpy.data.meshes.new(f"{name}_w{sx}")
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in ((0, -0.1 * size, 0), (sx * size, 0.05 * size, 0), (0, 0.15 * size, 0))]
        bm.faces.new(vs)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        w = bpy.data.objects.new(f"{name}_w{sx}", me)
        coll.objects.link(w)
        w.parent = piv
        wings.append((piv, sx))
    p0, p1 = Vector(path[0]), Vector(path[1])
    d = p1 - p0
    root.rotation_euler = (0, 0, A.yaw_towards(-d))
    root.location = (0, 0, -300)
    root.keyframe_insert("location", frame=f0 - 1)
    A.set_interp(root, "location", f0 - 1, "CONSTANT")
    steps = max(2, (f1 - f0) // 12)
    for i in range(steps + 1):
        t = i / steps
        root.location = p0.lerp(p1, t) + Vector((0, 0, 0.4 * math.sin(t * 6 + seed)))
        root.keyframe_insert("location", frame=f0 + (f1 - f0) * t)
    root.location = (0, 0, -300)
    root.keyframe_insert("location", frame=f1 + 1)
    A.set_interp(root, "location", f1, "CONSTANT")
    fr = f0 + rnd.randint(0, flap)
    up = True
    while fr < f1:
        glide = rnd.random() < 0.15
        for piv, sx in wings:
            piv.rotation_euler = (0, math.radians((35 if up else -25) * sx * (0.3 if glide else 1.0)), 0)
            piv.keyframe_insert("rotation_euler", frame=fr)
        up = not up
        fr += flap + rnd.randint(0, 1)


def atmosphere(ctx):
    import sets2 as S2
    s = ctx.seq
    if 1 in s:
        dust("dust_s1", s[1]["lights"], (-2, 2, 0.1), (10, 16, 4.0), 90, (1.0, 0.75, 0.55), strength=0.6, seed=1)
    if 2 in s:
        W = S2.WORKSHOP
        dust("dust_s2", s[2]["lights"], W + Vector((-2.8, -2.3, 0.3)), W + Vector((2.8, 2.3, 2.5)), 90,
             (1.0, 0.8, 0.55), r=(0.003, 0.007), strength=0.25, seed=2)
    if 5 in s:
        H = S2.HALL
        dust("dust_s5", s[5]["lights"], H + Vector((-18, -7, 0.5)), H + Vector((12, 4, 8)), 160,
             (1.0, 0.75, 0.5), r=(0.006, 0.014), strength=0.4, seed=5)
    if 6 in s:
        hr = ctx.scrap["hut"]["root"]
        bpy.context.view_layer.update()
        HL = lambda x, y, z=0.0: hr.matrix_world @ Vector((x, y, z))
        lo, hi = HL(-6, -14, 0.2), HL(6, 2, 3.5)
        lo, hi = Vector([min(a, b) for a, b in zip(lo, hi)]), Vector([max(a, b) for a, b in zip(lo, hi)])
        dust("dust_s6", s[6]["lights"], lo, hi, 90, (1.0, 0.8, 0.5), strength=0.7, seed=6)
        f0, f1 = s[6]["f0"], s[6]["f1"]
        coll = s[6]["lights"]
        rnd = random.Random(3)
        # a few birds over the sunrise – the first ones, then a small flock later
        for i in range(3):
            y = 9 + i * 1.5
            bird(f"bird_a{i}", coll, (HL(-22, y, 8 + i), HL(20, y + 3, 10 + i)), f0 + 20 + i * 14,
                 f0 + 20 + i * 14 + 260, seed=i)
        for i in range(6):
            y = 7 + rnd.uniform(-1, 3)
            st = f1 - 340 + i * 9
            bird(f"bird_b{i}", coll, (HL(24, y, 9 + rnd.uniform(0, 2)), HL(-26, y + 4, 11 + rnd.uniform(0, 2))),
                 st, st + 300, seed=10 + i)


def apply(ctx, f_end):
    humans(ctx, f_end)
    robots(ctx, f_end)
    atmosphere(ctx)
