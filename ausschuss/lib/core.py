"""Core helpers: scene/collection management, procedural primitives, materials."""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler, Matrix

R = random.Random(7)
FPS = 24


def sec(s):
    """Seconds -> frame number (global timeline starts at frame 1)."""
    return int(round(s * FPS))


# --------------------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for s in list(bpy.data.scenes):
        if s.name != "Scene":
            bpy.data.scenes.remove(s)


def collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        if parent is not None:
            parent.children.link(c)
    return c


_active_coll = [None]


def set_coll(c):
    _active_coll[0] = c


def link(ob, coll=None):
    c = coll or _active_coll[0]
    if c is None:
        c = bpy.context.scene.collection
    c.objects.link(ob)
    return ob


# --------------------------------------------------------------------------- materials
_mats = {}


def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt


def mat(name, color=(0.5, 0.5, 0.5), rough=0.6, metal=0.0, rust=0.0, dirt=0.25,
        emit=None, emit_strength=0.0, scale=3.0, bump=0.15, rust_color=(0.32, 0.12, 0.04),
        alpha=1.0, transmission=0.0, coat=0.0, spec=0.5):
    """Generic procedural material. rust: 0..1 coverage of rust patches. dirt: darkening variation."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = N.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
    L.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    col = (*color[:3], 1.0)
    # coordinates with per-object random offset
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    oi = N.new("ShaderNodeObjectInfo"); oi.location = (-900, -250)
    mul = N.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY_ADD"; mul.location = (-700, -100)
    mul.inputs[1].default_value = (0, 0, 0)
    L.new(tc.outputs["Object"], mul.inputs[0])
    mul.inputs[1].default_value = (1, 1, 1)
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.location = (-850, -400)
    L.new(oi.outputs["Random"], sc.inputs[0])
    sc.inputs["Scale"].default_value = 37.0
    L.new(sc.outputs[0], mul.inputs[2])
    vec = mul.outputs[0]

    base = N.new("ShaderNodeRGB"); base.location = (-300, 300)
    base.outputs[0].default_value = col
    color_sock = base.outputs[0]
    if dirt > 0:
        nz = N.new("ShaderNodeTexNoise"); nz.location = (-500, 150)
        nz.inputs["Scale"].default_value = scale * 0.7
        nz.inputs["Detail"].default_value = 6
        L.new(vec, nz.inputs["Vector"])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.location = (-100, 250)
        mx.inputs["Factor"].default_value = dirt
        L.new(color_sock, mx.inputs["A"])
        ramp = N.new("ShaderNodeValToRGB"); ramp.location = (-320, 100)
        ramp.color_ramp.elements[0].position = 0.3
        ramp.color_ramp.elements[0].color = (0.35, 0.33, 0.3, 1)
        ramp.color_ramp.elements[1].position = 0.7
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(nz.outputs["Fac"], ramp.inputs[0])
        L.new(ramp.outputs[0], mx.inputs["B"])
        color_sock = mx.outputs["Result"]
    rough_sock = None
    if rust > 0:
        nz2 = N.new("ShaderNodeTexNoise"); nz2.location = (-500, -150)
        nz2.inputs["Scale"].default_value = scale
        nz2.inputs["Detail"].default_value = 8
        nz2.inputs["Roughness"].default_value = 0.65
        L.new(vec, nz2.inputs["Vector"])
        rr = N.new("ShaderNodeMapRange"); rr.location = (-320, -150)
        t = 0.62 - 0.3 * rust
        rr.inputs["From Min"].default_value = t
        rr.inputs["From Max"].default_value = t + 0.06
        L.new(nz2.outputs["Fac"], rr.inputs["Value"])
        # rust colour variation
        rc = N.new("ShaderNodeValToRGB"); rc.location = (-320, -400)
        rc.color_ramp.elements[0].color = (*[c * 0.5 for c in rust_color], 1)
        rc.color_ramp.elements[1].color = (*[min(1, c * 1.6) for c in rust_color], 1)
        nz3 = N.new("ShaderNodeTexNoise"); nz3.location = (-500, -450)
        nz3.inputs["Scale"].default_value = scale * 6
        L.new(vec, nz3.inputs["Vector"])
        L.new(nz3.outputs["Fac"], rc.inputs[0])
        mx2 = N.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.location = (100, 100)
        L.new(rr.outputs[0], mx2.inputs["Factor"])
        L.new(color_sock, mx2.inputs["A"])
        L.new(rc.outputs[0], mx2.inputs["B"])
        color_sock = mx2.outputs["Result"]
        # roughness/metal: rust is rough & non-metal
        mr = N.new("ShaderNodeMix"); mr.data_type = "FLOAT"; mr.location = (300, -200)
        mr.inputs["A"].default_value = rough
        mr.inputs["B"].default_value = 0.95
        L.new(rr.outputs[0], mr.inputs["Factor"])
        L.new(mr.outputs[0], bsdf.inputs["Roughness"])
        if metal > 0:
            mm = N.new("ShaderNodeMix"); mm.data_type = "FLOAT"; mm.location = (300, -350)
            mm.inputs["A"].default_value = metal
            mm.inputs["B"].default_value = 0.0
            L.new(rr.outputs[0], mm.inputs["Factor"])
            L.new(mm.outputs[0], bsdf.inputs["Metallic"])
        rough_sock = rr.outputs[0]
    L.new(color_sock, bsdf.inputs["Base Color"])
    if bump > 0:
        nzb = N.new("ShaderNodeTexNoise"); nzb.location = (100, -500)
        nzb.inputs["Scale"].default_value = scale * 8
        nzb.inputs["Detail"].default_value = 4
        L.new(vec, nzb.inputs["Vector"])
        bp = N.new("ShaderNodeBump"); bp.location = (350, -500)
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.02
        L.new(nzb.outputs["Fac"], bp.inputs["Height"])
        L.new(bp.outputs[0], bsdf.inputs["Normal"])
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit[:3], 1)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    m.diffuse_color = col
    _mats[name] = m
    return m


def emission(name, color, strength=5.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color[:3], 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (*color[:3], 1)
    _mats[name] = m
    return m


def emit_socket(m):
    """Return the animatable emission strength socket of a material."""
    for n in m.node_tree.nodes:
        if n.type == "EMISSION":
            return n.inputs[1]
        if n.type == "BSDF_PRINCIPLED":
            return n.inputs["Emission Strength"]


def glass(name, color=(0.8, 0.9, 1.0), rough=0.05):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Alpha"].default_value = 0.18
    b.inputs["Specular IOR Level"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        m.blend_method = "BLEND"
    m.use_backface_culling = False
    m.diffuse_color = (*color, 1)
    _mats[name] = m
    return m


# --------------------------------------------------------------------------- meshes
def _finish(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def mesh_box(name, sx, sy, sz, origin="center"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    off = Vector((0, 0, 0.5 if origin == "bottom" else 0.0))
    for v in bm.verts:
        v.co = Vector(((v.co.x) * sx, (v.co.y) * sy, (v.co.z + off.z) * sz))
    return _finish(bm, name)


def mesh_cyl(name, r, h, verts=24, r2=None, origin="center", cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    if origin == "bottom":
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    return _finish(bm, name)


def mesh_sphere(name, r, seg=24, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    return _finish(bm, name)


def mesh_torus(name, R_, r, seg=32, segr=12):
    bm = bmesh.new()
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(segr):
            b = 2 * math.pi * j / segr
            x = (R_ + r * math.cos(b)) * math.cos(a)
            y = (R_ + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(seg):
        for j in range(segr):
            a = verts[i][j]; b = verts[(i + 1) % seg][j]
            c = verts[(i + 1) % seg][(j + 1) % segr]; d = verts[i][(j + 1) % segr]
            bm.faces.new((a, b, c, d))
    return _finish(bm, name)


def mesh_lathe(name, profile, seg=32, cap_top=False, cap_bottom=False):
    """profile: list of (r, z) from bottom to top. Revolved around Z."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            a = rings[k][i]; b = rings[k][(i + 1) % seg]
            c = rings[k + 1][(i + 1) % seg]; d = rings[k + 1][i]
            bm.faces.new((a, b, c, d))
    if cap_bottom:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top:
        bm.faces.new(rings[-1])
    bm.normal_update()
    return _finish(bm, name)


def mesh_from_pydata(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def smooth(me, on=True):
    for p in me.polygons:
        p.use_smooth = on
    return me


def new_obj(name, me=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat_=None,
            parent=None, coll=None, bevel=0.0, bevel_seg=2, subsurf=0, smooth_=False):
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.scale = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    if me is not None and mat_ is not None:
        if isinstance(mat_, (list, tuple)):
            for m in mat_:
                me.materials.append(m)
        else:
            me.materials.append(mat_)
    if parent is not None:
        ob.parent = parent
    link(ob, coll)
    if me is not None:
        if bevel > 0:
            md = ob.modifiers.new("bevel", "BEVEL")
            md.width = bevel
            md.segments = bevel_seg
            md.limit_method = "ANGLE"
            md.harden_normals = False
        if subsurf:
            md = ob.modifiers.new("subsurf", "SUBSURF")
            md.levels = subsurf
            md.render_levels = subsurf
        if smooth_ or subsurf:
            smooth(me)
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=None, parent=None, bevel=0.02, origin="center", coll=None):
    return new_obj(name, mesh_box(name, *size, origin=origin), loc, rot, mat_=m, parent=parent, bevel=bevel, coll=coll)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), m=None, parent=None, verts=24, r2=None, bevel=0.0,
        origin="center", coll=None, smooth_=True):
    ob = new_obj(name, mesh_cyl(name, r, h, verts, r2, origin), loc, rot, mat_=m, parent=parent, bevel=bevel, coll=coll)
    if smooth_:
        _autosmooth(ob)
    return ob


def sphere(name, r, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), m=None, parent=None, seg=24, rings=12, coll=None):
    return new_obj(name, mesh_sphere(name, r, seg, rings), loc, rot, scale, mat_=m, parent=parent, coll=coll, smooth_=True)


def torus(name, R_, r, loc=(0, 0, 0), rot=(0, 0, 0), m=None, parent=None, seg=32, segr=12, coll=None):
    return new_obj(name, mesh_torus(name, R_, r, seg, segr), loc, rot, mat_=m, parent=parent, coll=coll, smooth_=True)


def lathe(name, profile, loc=(0, 0, 0), rot=(0, 0, 0), m=None, parent=None, seg=32, coll=None, cap_top=False,
          cap_bottom=False, subsurf=0):
    return new_obj(name, mesh_lathe(name, profile, seg, cap_top, cap_bottom), loc, rot, mat_=m, parent=parent,
                   coll=coll, smooth_=True, subsurf=subsurf)


def _autosmooth(ob):
    """Smooth shading but keep hard edges at sharp angles (cylinder caps)."""
    me = ob.data
    smooth(me)
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, coll=None, size=0.2, kind="PLAIN_AXES"):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    if parent:
        ob.parent = parent
    link(ob, coll)
    return ob


def instance(name, src, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, parent=None, coll=None):
    """Linked duplicate (shares mesh) incl. modifiers."""
    ob = bpy.data.objects.new(name, src.data)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    ob.scale = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    for md in src.modifiers:
        n = ob.modifiers.new(md.name, md.type)
        for attr in ("width", "segments", "limit_method", "levels", "render_levels"):
            if hasattr(md, attr):
                setattr(n, attr, getattr(md, attr))
    if parent:
        ob.parent = parent
    link(ob, coll)
    return ob


def text(name, body, size=0.3, loc=(0, 0, 0), rot=(90, 0, 0), m=None, parent=None, coll=None, extrude=0.0,
         align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    if m:
        cu.materials.append(m)
    if parent:
        ob.parent = parent
    link(ob, coll)
    return ob


def curve_tube(name, points, radius=0.02, m=None, parent=None, coll=None, res=8, bevel_res=3, cyclic=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.resolution_u = res
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    if m:
        cu.materials.append(m)
    if parent:
        ob.parent = parent
    link(ob, coll)
    return ob


def sag_points(a, b, sag=0.5, n=6):
    """Points of a hanging cable between a and b."""
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(tuple(p))
    return pts


def look_at_rot(src, dst):
    d = Vector(dst) - Vector(src)
    return d.to_track_quat("-Z", "Y").to_euler()


def limb(name, p0, p1, r0, r1=None, m=None, parent=None, verts=16, coll=None):
    """Tapered cylinder from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    me = mesh_cyl(name, r0, d.length, verts, r1 if r1 is not None else r0)
    ob = new_obj(name, me, (p0 + p1) / 2, mat_=m, parent=parent, coll=coll)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    # mesh_cyl: radius1 at -z (p0 side), radius2 at +z (p1 side)
    _autosmooth(ob)
    return ob


def fabric(name, color, rough=0.88, dirt=0.35, weave=90.0, bump=0.3, sheen=0.5, knit=False, scale=4.0):
    """Cloth: procedural material + woven (or knitted) micro bump and sheen."""
    new = name not in _mats
    m = mat(name, color, rough=rough, dirt=dirt, scale=scale, bump=0.0)
    if not new:
        return m
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = next(n for n in N if n.type == "TEX_COORD")
    try:
        bsdf.inputs["Sheen Weight"].default_value = sheen
        bsdf.inputs["Sheen Roughness"].default_value = 0.4
    except KeyError:
        pass
    waves = []
    for i, ax in enumerate(("X", "Y" if not knit else "Z")):
        w = N.new("ShaderNodeTexWave"); w.location = (-200, -700 - i * 200)
        w.wave_type = "BANDS"
        w.bands_direction = ax
        w.inputs["Scale"].default_value = weave * (1.0 if not knit else (0.6 if i else 1.4))
        w.inputs["Distortion"].default_value = 1.5 if knit else 0.4
        w.inputs["Detail"].default_value = 1.0
        L.new(tc.outputs["Object"], w.inputs["Vector"])
        waves.append(w)
    mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.location = (0, -800)
    L.new(waves[0].outputs["Fac"], mu.inputs[0]); L.new(waves[1].outputs["Fac"], mu.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.location = (300, -800)
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.004
    L.new(mu.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], bsdf.inputs["Normal"])
    return m


def skin(name, color, rough=0.5):
    new = name not in _mats
    m = mat(name, color, rough=rough, dirt=0.08, scale=8, bump=0.03, spec=0.45)
    if new:
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        try:
            bsdf.inputs["Subsurface Weight"].default_value = 0.18
            bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
            bsdf.inputs["Subsurface Scale"].default_value = 0.02
        except KeyError:
            pass
    return m


def subsurf(ob, levels=1):
    md = ob.modifiers.new("sub", "SUBSURF")
    md.levels = levels
    md.render_levels = levels
    return ob


def soft_alpha(m, kind="puddle", alpha=1.0):
    """Feathered transparency for flat decals (puddles, stains: ragged radial edge) and puffs (smoke: fresnel
    falloff, fades with the object's colour alpha)."""
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    if kind == "puddle":
        tc = N.new("ShaderNodeTexCoord")
        sub = N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        mul = N.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = (2.0, 2.0, 0.0)
        ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
        L.new(tc.outputs["Generated"], sub.inputs[0]); L.new(sub.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], ln.inputs[0])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 3
        nz.noise_dimensions = "4D"
        L.new(tc.outputs["Generated"], nz.inputs["Vector"])
        oi = N.new("ShaderNodeObjectInfo")
        rw = N.new("ShaderNodeMath"); rw.operation = "MULTIPLY"; rw.inputs[1].default_value = 17.0
        L.new(oi.outputs["Random"], rw.inputs[0]); L.new(rw.outputs[0], nz.inputs["W"])
        ad = N.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"
        ad.inputs[1].default_value = 0.45
        L.new(nz.outputs["Fac"], ad.inputs[0]); L.new(ln.outputs["Value"], ad.inputs[2])
        rp = N.new("ShaderNodeMapRange"); rp.inputs["From Min"].default_value = 0.95; rp.inputs["From Max"].default_value = 1.2
        rp.inputs["To Min"].default_value = alpha; rp.inputs["To Max"].default_value = 0.0
        L.new(ad.outputs[0], rp.inputs["Value"])
        L.new(rp.outputs["Result"], bsdf.inputs["Alpha"])
    else:
        lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
        inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        L.new(lw.outputs["Facing"], inv.inputs[1])
        pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.5
        L.new(inv.outputs[0], pw.inputs[0])
        oi = N.new("ShaderNodeObjectInfo")
        m1 = N.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
        L.new(pw.outputs[0], m1.inputs[0]); L.new(oi.outputs["Alpha"], m1.inputs[1])
        # wispy: a noise breaks the sphere silhouette
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 4
        nz.inputs["Roughness"].default_value = 0.6
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.38; mr.inputs["From Max"].default_value = 0.7
        L.new(nz.outputs["Fac"], mr.inputs["Value"])
        m3 = N.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
        L.new(m1.outputs[0], m3.inputs[0]); L.new(mr.outputs["Result"], m3.inputs[1])
        m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = alpha
        L.new(m3.outputs[0], m2.inputs[0])
        # a puff right at the lens would milk out the whole frame: fade it out close to the camera
        cd = N.new("ShaderNodeCameraData")
        cf = N.new("ShaderNodeMapRange"); cf.inputs["From Min"].default_value = 0.8; cf.inputs["From Max"].default_value = 3.0
        L.new(cd.outputs["View Distance"], cf.inputs["Value"])
        m4 = N.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
        L.new(m2.outputs[0], m4.inputs[0]); L.new(cf.outputs["Result"], m4.inputs[1])
        L.new(m4.outputs[0], bsdf.inputs["Alpha"])
        m.use_backface_culling = True
    try:
        m.surface_render_method = "BLENDED" if kind != "puddle" else "DITHERED"
    except Exception:
        pass
    return m
