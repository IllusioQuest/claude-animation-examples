"""Better-built body parts for the stylised humans: a shaped head, eyes with iris/catchlight/lids,
gloved hands with fingers, proper boots, coat details. All parts are rigid pieces parented to bones
(the rig in characters.build_human is unchanged)."""
import math
import bmesh
import bpy
from mathutils import Vector
import core as C

V = Vector


def _gauss(p, c, r):
    d = (p - c).length / r
    return math.exp(-d * d)


def head_mesh(name, hr, hc, style, m, coll):
    """UV sphere sculpted into a head: egg shape, softer jaw, cheeks, brow, eye sockets."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=22, radius=1.0)
    kid = style == "kid"
    old = style in ("oldman", "hedda")
    for v in bm.verts:
        p = v.co.copy()
        x, y, z = p
        # egg: a little narrower towards the crown, rounder lower face
        if z > 0:
            k = 1.0 - (0.05 if kid else 0.09) * z
            p.x *= k
            p.y *= k * 1.02
        else:
            k = 1.0 - (0.04 if kid else 0.13) * z * z
            p.x *= k
            p.y *= 1.0 - 0.05 * z * z
            if y < 0:  # lower face slightly forward
                p.y -= 0.05 * (-z) * (-y)
        # flatter face plane, fuller back of the head
        if y < -0.5:
            p.y = -0.5 + (p.y + 0.5) * 0.9
        if y > 0.3 and z > -0.2:
            p.y *= 1.05
        n = p.normalized()
        for sx in (-1, 1):
            cheek = _gauss(V((x, y, z)), V((0.55 * sx, -0.72, -0.28)), 0.38)
            p += n * cheek * (0.07 if (kid or old) else 0.045)
            sock = _gauss(V((x, y, z)), V((0.34 * sx, -0.88, 0.14)), 0.24)
            p -= n * sock * 0.05
            brow = _gauss(V((x, y, z)), V((0.36 * sx, -0.86, 0.43)), 0.26)
            p += n * brow * 0.03
        # a hint of chin
        p += n * _gauss(V((x, y, z)), V((0, -0.8, -0.6)), 0.3) * (0.02 if kid else 0.04)
        v.co = p * hr
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = C.new_obj(name, me, hc, scale=(1, 0.96, 1.02), mat_=m, coll=coll)
    C.subsurf(ob, 1)
    return ob


def eye(n, s, ec, er, iris_col, skin_m, coll, lid=0.32, kid=False):
    """Sclera, coloured iris, pupil, catchlight and an upper lid. Returns objects for the eye bone."""
    out = []
    white = C.mat("eye_white2", (0.93, 0.91, 0.87), rough=0.25, dirt=0.0, bump=0.0, coat=0.6)
    sc = (0.85, 0.6, 1.2)
    out.append(C.sphere(n("eye" + s), er, loc=ec, scale=sc, m=white, coll=coll))
    # layered on the front of the (0.6-deep) eyeball: iris, pupil, catchlight – each a flat lens
    im = C.mat(f"iris_{'%.2f_%.2f_%.2f' % tuple(iris_col)}", iris_col, rough=0.3, dirt=0.25, scale=40, bump=0.0, coat=0.8)
    out.append(C.sphere(n("iris" + s), er * 0.56, loc=ec + V((0, -er * 0.45, -er * 0.05)), scale=(1, 0.3, 1.15), m=im,
                        coll=coll))
    out.append(C.sphere(n("pupil" + s), er * 0.3, loc=ec + V((0, -er * 0.52, -er * 0.05)), scale=(1, 0.3, 1.15),
                        m=C.mat("eye_black"), coll=coll))
    out.append(C.sphere(n("catch" + s), er * 0.11, loc=ec + V((er * 0.17, -er * 0.6, er * 0.22)), scale=(1, 0.5, 1),
                        m=C.emission("catchlight", (1, 1, 1), 3.0), coll=coll, seg=8, rings=4))
    # upper lid: a skin shell over the top of the eyeball
    prof = [(er * 1.08 * math.sin(math.radians(a)), er * 1.08 * math.cos(math.radians(a)))
            for a in range(0, 46 + int(lid * 40), 8)]
    prof[0] = (0.0005, prof[0][1])
    lidob = C.lathe(n("lid" + s), prof, loc=ec, m=skin_m, coll=coll, seg=24)
    lidob.scale = sc
    lidob.rotation_euler = (math.radians(12), 0, 0)
    out.append(lidob)
    return out


def brow(n, s, sx, p, h, m, coll):
    pts = [p + V((-0.03 * sx * h, 0.004 * h, -0.006 * h)), p + V((0, 0, 0.004 * h)),
           p + V((0.03 * sx * h, 0.006 * h, -0.008 * h))]
    return C.curve_tube(n("brow" + s), pts, radius=0.0085 * h, m=m, coll=coll, res=6)


def glove(n, s, sx, hd, h, m, coll, bare=False):
    """Palm block with four fingers and a thumb (hand hangs down, palm facing the body)."""
    out = []
    palm = C.box(n("hand" + s), (0.04 * h, 0.08 * h, 0.075 * h), loc=hd + V((0, 0, 0.012 * h)), m=m,
                 bevel=0.015 * h, coll=coll)
    C.subsurf(palm, 1)
    out.append(palm)
    for i in range(4):
        y = (-0.027 + i * 0.018) * h
        L = (0.055 if i in (1, 2) else 0.046) * h
        a = hd + V((0, y, -0.025 * h))
        b = a + V((-0.012 * sx * h, 0, -L))
        f = C.limb(n(f"handf{i}" + s), a, b, 0.0105 * h, 0.009 * h, m=m, coll=coll, verts=10)
        out.append(f)
        out.append(C.sphere(n(f"handt{i}" + s), 0.009 * h, loc=b, m=m, coll=coll, seg=10, rings=6))
    ta = hd + V((-0.016 * sx * h, -0.036 * h, 0.015 * h))
    tb = ta + V((-0.012 * sx * h, -0.018 * h, -0.04 * h))
    out.append(C.limb(n("thumb" + s), ta, tb, 0.013 * h, 0.011 * h, m=m, coll=coll, verts=10))
    out.append(C.sphere(n("thumbt" + s), 0.011 * h, loc=tb, m=m, coll=coll, seg=10, rings=6))
    if not bare:
        cuff = C.cyl(n("glovecuff" + s), 0.038 * h, 0.035 * h, loc=hd + V((0, 0, 0.055 * h)), m=m, coll=coll, verts=16)
        cuff.scale = (0.8, 1.15, 1)
        out.append(cuff)
    return out


def boot(n, s, sx, h, m, coll):
    out = []
    body = C.box(n("boot" + s), (0.105 * h, 0.235 * h, 0.1 * h), loc=V((0.09 * sx * h, -0.05 * h, 0.075 * h)),
                 m=m, bevel=0.035 * h, coll=coll)
    C.subsurf(body, 2)
    out.append(body)
    toe = C.sphere(n("boottoe" + s), 0.055 * h, loc=V((0.09 * sx * h, -0.135 * h, 0.06 * h)), scale=(0.95, 1.1, 0.8),
                   m=m, coll=coll)
    out.append(toe)
    shaft = C.cyl(n("bootshaft" + s), 0.06 * h, 0.12 * h, loc=V((0.09 * sx * h, 0.0, 0.15 * h)), m=m, coll=coll,
                  verts=20)
    shaft.scale = (0.95, 1.05, 1)
    out.append(shaft)
    sole_m = C.mat("sole_m2", (0.045, 0.035, 0.03), rough=0.8, dirt=0.3, bump=0.3)
    out.append(C.box(n("sole" + s), (0.118 * h, 0.27 * h, 0.022 * h), loc=V((0.09 * sx * h, -0.055 * h, 0.011 * h)),
                     m=sole_m, bevel=0.009 * h, coll=coll))
    out.append(C.box(n("heel" + s), (0.1 * h, 0.07 * h, 0.03 * h), loc=V((0.09 * sx * h, 0.035 * h, 0.03 * h)),
                     m=sole_m, bevel=0.006 * h, coll=coll))
    lace = C.mat("lace_m", (0.6, 0.55, 0.45), rough=0.9)
    for i in range(3):
        out.append(C.box(n(f"lace{i}" + s), (0.06 * h, 0.008 * h, 0.006 * h),
                         loc=V((0.09 * sx * h, (-0.07 + i * 0.03) * h, (0.12 + i * 0.012) * h)),
                         rot=(-25, 0, 0), m=lace, bevel=0, coll=coll))
    return out


def coat_details(n, h, g, coat_m, trim_m, coll, long_coat=True, hem_z=0.38, hem_r=0.33):
    """Returns [(bone, obj)]: front opening, lapels, pockets with flaps, hem."""
    out = []
    seam = C.mat("seam_dark", (0.03, 0.025, 0.02), rough=0.9, dirt=0.0, bump=0.0)
    if long_coat:
        # hem: a rolled edge at the bottom of the coat
        hem = C.torus(n("hem"), hem_r * g * h, 0.012 * h, loc=V((0, 0, hem_z * h)), m=coat_m, coll=coll, seg=40)
        hem.scale = (1, 0.85, 1)
        out.append(("hips", hem))
        # front opening line down the skirt
        out.append(("hips", C.box(n("front_seam"), (0.006 * h, 0.004 * h, (0.98 - hem_z) * h),
                                  loc=V((0.018 * h, -0.85 * (0.21 + hem_r) / 2 * g * h - 0.004 * h, (0.98 + hem_z) / 2 * h)),
                                  rot=(math.degrees(math.atan2((hem_r - 0.2) * 0.85 * g, 0.98 - hem_z)), 0, 0),
                                  m=seam, bevel=0, coll=coll)))
        # pockets with flaps on both hips
        for sx in (-1, 1):
            px = 0.15 * sx * g
            pocket = C.box(n(f"pocket{sx}"), (0.11 * h, 0.012 * h, 0.1 * h), loc=V((px * h, -0.215 * g * h, 0.74 * h)),
                           rot=(-12, 0, -32 * sx), m=coat_m, bevel=0.006 * h, coll=coll)
            out.append(("hips", pocket))
            flap = C.box(n(f"flap{sx}"), (0.12 * h, 0.016 * h, 0.035 * h), loc=V((px * h, -0.222 * g * h, 0.795 * h)),
                         rot=(-12, 0, -32 * sx), m=trim_m, bevel=0.006 * h, coll=coll)
            out.append(("hips", flap))
    # lapels: two angled flaps on the chest
    for sx in (-1, 1):
        lap = C.box(n(f"lapel{sx}"), (0.075 * h, 0.014 * h, 0.17 * h), loc=V((0.055 * sx * h, -0.165 * g * h, 1.27 * h)),
                    rot=(-8, 18 * sx, -12 * sx), m=trim_m, bevel=0.008 * h, coll=coll)
        out.append(("chest", lap))
    return out


def scarf(n, h, hc, m, coll):
    """Hedda's scarf: a thick wrap up to the nose, a knot and two fringed tails."""
    out = []
    wrap = C.lathe(n("scarf"), [(0.105 * h, -0.03 * h), (0.15 * h, 0.0), (0.172 * h, 0.05 * h), (0.176 * h, 0.09 * h),
                               (0.168 * h, 0.125 * h), (0.148 * h, 0.138 * h), (0.13 * h, 0.13 * h)],
                   loc=hc - V((0, 0.01 * h, 0.2 * h)), m=m, coll=coll, seg=36)
    C.subsurf(wrap, 1)
    out.append(("head", wrap))
    # fold rings
    for i, z in enumerate((-0.17, -0.12)):
        r = C.torus(n(f"scarffold{i}"), (0.163 + i * 0.006) * h, 0.012 * h, loc=hc + V((0, -0.01 * h, z * h)),
                    rot=(4, 0, 0), m=m, coll=coll, seg=36)
        out.append(("head", r))
    knot = C.sphere(n("scarfknot"), 0.045 * h, loc=V((0.06 * h, -0.15 * h, 1.36 * h)), scale=(1.2, 0.8, 1), m=m,
                    coll=coll)
    out.append(("chest", knot))
    for i, (dx, rz) in enumerate(((0.04, 6), (0.085, -8))):
        t = C.box(n(f"scarftail{i}"), (0.07 * h, 0.022 * h, 0.24 * h), loc=V((dx * h, -0.165 * h, 1.22 * h)),
                  rot=(-14, 0, rz), m=m, bevel=0.01 * h, coll=coll)
        C.subsurf(t, 1)
        out.append(("chest", t))
        for k in range(4):
            out.append(("chest", C.cyl(n(f"fringe{i}{k}"), 0.004 * h, 0.04 * h,
                                       loc=V(((dx - 0.025 + k * 0.017) * h, -0.142 * h - 0.03 * h * math.sin(math.radians(14)),
                                              1.09 * h)), rot=(-14, 0, rz), m=m, coll=coll, verts=5)))
    return out


def dense_profile(prof, n=14):
    """Resample a (r, z) lathe profile to n points (bottom -> top) so it can bend smoothly."""
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(prof) - 1)
        k = min(int(t), len(prof) - 2)
        u = t - k
        r = prof[k][0] * (1 - u) + prof[k + 1][0] * u
        z = prof[k][1] * (1 - u) + prof[k + 1][1] * u
        out.append((r, z))
    return out


def coat_weight(p, h):
    """Skin weights of a coat point (rest pose, world units): hips above the hip joint, the thighs below,
    the front following the legs more than the back; left/right blended across the middle."""
    z_hip, z_knee = 0.9 * h, 0.5 * h
    t = min(1.0, max(0.0, (z_hip - p.z) / (z_hip - z_knee)))
    t = t ** 0.9
    r = max(1e-4, math.hypot(p.x, p.y))
    front = (1 - p.y / r) / 2  # 1 at the front (-y), 0 at the back
    wt = t * (0.55 + 0.45 * front)
    xl = min(1.0, max(0.0, (p.x + 0.07 * h) / (0.14 * h)))
    xl = xl * xl * (3 - 2 * xl)
    return {"hips": 1.0 - wt, "thigh_L": wt * xl, "thigh_R": wt * (1 - xl)}


def skin(ob, rig, h):
    """Bind a rest-pose mesh to the rig with coat weights (Armature modifier, smooth deform)."""
    from mathutils import Matrix
    bpy.context.view_layer.update()
    me = ob.data
    me.transform(ob.matrix_world)  # bake transform: weights and binding in rig rest space (rig at origin)
    ob.matrix_world = Matrix.Identity(4)
    groups = {n: ob.vertex_groups.new(name=n) for n in ("hips", "thigh_L", "thigh_R")}
    for v in me.vertices:
        for n, w in coat_weight(v.co, h).items():
            if w > 1e-4:
                groups[n].add([v.index], w, "REPLACE")
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    # armature first, then the existing modifiers (subsurf/solidify) again after it
    keep = []
    for m_ in list(ob.modifiers):
        spec = {"type": m_.type, "name": m_.name}
        for a in ("levels", "render_levels", "thickness", "offset", "width", "segments", "limit_method"):
            if hasattr(m_, a):
                spec[a] = getattr(m_, a)
        keep.append(spec)
        ob.modifiers.remove(m_)
    md = ob.modifiers.new("arm", "ARMATURE")
    md.object = rig
    md.use_vertex_groups = True
    for spec in keep:
        m_ = ob.modifiers.new(spec["name"], spec["type"])
        for a in ("levels", "render_levels", "thickness", "offset", "width", "segments", "limit_method"):
            if a in spec:
                setattr(m_, a, spec[a])
    return ob
