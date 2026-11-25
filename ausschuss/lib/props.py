"""Reusable props: scrap items, piles, pylons, trucks, shacks, lights."""
import bpy
import math
from mathutils import Vector
import core as C
import anim as A

M = C.mat


def mats():
    return {
        "rust": M("p_rust", (0.35, 0.2, 0.12), metal=0.6, rough=0.6, rust=0.8, scale=3),
        "steel": M("steel", (0.6, 0.6, 0.62), metal=1, rough=0.35, rust=0.25),
        "paint_red": M("p_red", (0.55, 0.12, 0.08), metal=0.3, rough=0.5, rust=0.5),
        "paint_blue": M("p_blue", (0.15, 0.25, 0.4), metal=0.3, rough=0.5, rust=0.5),
        "paint_green": M("p_green", (0.2, 0.33, 0.2), metal=0.3, rough=0.5, rust=0.5),
        "paint_yel": M("p_yel", (0.7, 0.5, 0.12), metal=0.3, rough=0.5, rust=0.5),
        "paint_white": M("p_white", (0.7, 0.68, 0.62), metal=0.2, rough=0.5, rust=0.4),
        "rubber": M("tire", (0.02, 0.02, 0.02), rough=0.8, dirt=0.2),
        "plastic": M("p_plastic", (0.45, 0.42, 0.35), rough=0.5, dirt=0.5),
        "wood": M("p_wood", (0.35, 0.22, 0.12), rough=0.8, dirt=0.5, bump=0.3, scale=6),
        "screen": M("p_screen", (0.03, 0.04, 0.04), rough=0.15, dirt=0.1, bump=0),
        "dark": M("dark_metal", (0.08, 0.08, 0.09), metal=0.8, rough=0.5, rust=0.2),
        "concrete": M("p_concrete", (0.45, 0.44, 0.42), rough=0.9, dirt=0.5, bump=0.3, scale=2),
        "corr1": M("p_corr1", (0.45, 0.45, 0.43), metal=0.7, rough=0.5, rust=0.32, scale=2),
        "corr2": M("p_corr2", (0.5, 0.25, 0.15), metal=0.4, rough=0.6, rust=0.3, scale=2),
        "corr3": M("p_corr3", (0.25, 0.38, 0.4), metal=0.4, rough=0.6, rust=0.3, scale=2),
        "cable": M("cable_m", (0.02, 0.02, 0.02), rough=0.6, dirt=0.0, bump=0),
        "chrome": M("chrome", (0.85, 0.86, 0.9), metal=1.0, rough=0.12, dirt=0.05, bump=0),
        "brass": M("brass", (0.75, 0.55, 0.25), metal=1.0, rough=0.35, rust=0.15, rust_color=(0.15, 0.25, 0.15)),
        "eye_black": M("eye_black", (0.01, 0.01, 0.01), rough=0.2, dirt=0.0, bump=0),
        "rope": M("rope_m", (0.6, 0.55, 0.45), rough=0.9),
        "gauge": M("gauge_face", (0.9, 0.88, 0.8), rough=0.5, dirt=0.3),
        "pipe": M("pipe_m", (0.35, 0.35, 0.36), metal=1.0, rough=0.4, rust=0.45),
        "beak": M("beak_m", (0.85, 0.6, 0.1), rough=0.4),
        "ink": M("ink_black", (0.01, 0.01, 0.01)),
    }


# --------------------------------------------------------------------------- scrap library
_LIB = {}


def scrap_library(coll):
    """Create template objects (hidden, in coll) used for instancing."""
    if _LIB:
        return _LIB
    m = mats()
    C.set_coll(coll)
    lib = {}
    lib["barrel_r"] = C.cyl("lib_barrel_r", 0.3, 0.88, m=m["paint_red"], verts=20, bevel=0.01)
    lib["barrel_b"] = C.cyl("lib_barrel_b", 0.3, 0.88, m=m["paint_blue"], verts=20, bevel=0.01)
    lib["barrel_rust"] = C.cyl("lib_barrel_rust", 0.3, 0.88, m=m["rust"], verts=20, bevel=0.01)
    lib["tire"] = C.torus("lib_tire", 0.32, 0.12, m=m["rubber"], seg=20, segr=8)
    lib["fridge"] = C.box("lib_fridge", (0.7, 0.65, 1.6), m=m["paint_white"], bevel=0.06)
    lib["crate"] = C.box("lib_crate", (0.6, 0.6, 0.5), m=m["wood"], bevel=0.01)
    lib["panel"] = C.box("lib_panel", (1.6, 0.05, 1.0), m=m["corr1"], bevel=0.0)
    lib["panel2"] = C.box("lib_panel2", (1.2, 0.04, 0.8), m=m["paint_green"], bevel=0.0)
    lib["pipe"] = C.cyl("lib_pipe", 0.08, 2.4, m=m["rust"], verts=12)
    lib["beam"] = C.box("lib_beam", (0.15, 0.15, 3.0), m=m["rust"], bevel=0.0)
    lib["drum"] = C.cyl("lib_drum", 0.45, 0.3, m=m["steel"], verts=24)
    lib["car_door"] = C.box("lib_cardoor", (1.1, 0.12, 0.8), m=m["paint_blue"], bevel=0.08)
    # old TV
    tv = C.box("lib_tv", (0.6, 0.5, 0.48), m=m["plastic"], bevel=0.05)
    lib["tv"] = tv
    lib["tv_screen"] = C.box("lib_tv_screen", (0.46, 0.02, 0.34), m=m["screen"], bevel=0.04)
    lib["washer"] = C.box("lib_washer", (0.6, 0.6, 0.85), m=m["paint_white"], bevel=0.04)
    lib["robot_arm"] = C.cyl("lib_rarm", 0.06, 1.2, m=m["paint_yel"], verts=12, bevel=0.0)
    lib["gear"] = C.cyl("lib_gear", 0.35, 0.08, m=m["rust"], verts=16)
    lib["sign"] = C.box("lib_sign", (1.4, 0.04, 0.6), m=m["paint_red"], bevel=0.0)
    for o in lib.values():
        o.hide_render = True
        o.hide_viewport = True
        o.location = (0, 0, -100)
    _LIB.update(lib)
    return _LIB


def scrap_item(kind, loc, rot, scale=1.0, coll=None):
    src = _LIB[kind]
    ob = C.instance("scrap_" + kind, src, loc, rot, scale, coll=coll)
    ob.hide_render = False
    ob.hide_viewport = False
    if kind == "tv":
        scr = C.instance("scrap_tvs", _LIB["tv_screen"], (0, -0.25, 0.02), (0, 0, 0), 1.0, parent=ob, coll=coll)
        scr.hide_render = scr.hide_viewport = False
    return ob


def mound(name, center, radius, height, m, coll=None, seed=0):
    """Earthy/junky mound (displaced squashed sphere)."""
    ob = C.sphere(name, 1.0, loc=center, scale=(radius, radius * 0.85, height), m=m, seg=32, rings=16, coll=coll)
    tex = bpy.data.textures.new(name + "_tex", "CLOUDS")
    tex.noise_scale = 0.4
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = 0.25
    d.texture_coords = "GLOBAL"
    ob.location.z = center[2] - height * 0.35
    return ob


def scrap_pile(name, center, radius=4.0, height=2.0, n=40, seed=0, coll=None):
    rnd = C.R.__class__(seed)
    m = mats()
    base = mound(name + "_mound", center, radius, height,
                 M("junk_earth", (0.2, 0.15, 0.11), rough=0.95, dirt=0.6, rust=0.5, scale=1.5, bump=0.5), coll, seed)
    kinds = ["barrel_r", "barrel_b", "barrel_rust", "tire", "tire", "fridge", "crate", "panel", "panel2", "pipe",
             "beam", "drum", "car_door", "tv", "tv", "washer", "robot_arm", "gear", "sign"]
    obs = [base]
    c = Vector(center)
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = math.sqrt(rnd.random()) * radius * 0.95
        x = c.x + math.cos(a) * rr
        y = c.y + math.sin(a) * rr * 0.85
        # surface height of squashed sphere (minus sink)
        t = min(1.0, rr / radius)
        z = c.z - height * 0.35 + height * math.sqrt(max(0.0, 1 - t * t)) - 0.1
        k = rnd.choice(kinds)
        rot = (rnd.uniform(-60, 60), rnd.uniform(-60, 60), rnd.uniform(0, 360))
        if k in ("tire", "panel", "panel2", "sign", "car_door"):
            rot = (rnd.uniform(-90, 90), rnd.uniform(-30, 30), rnd.uniform(0, 360))
        obs.append(scrap_item(k, (x, y, z), rot, rnd.uniform(0.8, 1.2), coll))
    return obs


# --------------------------------------------------------------------------- terrain
def terrain(name, size=300, res=120, strength=1.5, m=None, coll=None, loc=(0, 0, 0), flat_radius=0.0):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = C.new_obj(name, me, loc, mat_=m, coll=coll, smooth_=True)
    tex = bpy.data.textures.new(name + "_tex", "CLOUDS")
    tex.noise_scale = size / 6
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.mid_level = 0.5
    d.texture_coords = "GLOBAL"
    if flat_radius > 0:
        # vertex group fading displacement near the centre (the action area stays flat)
        vg = ob.vertex_groups.new(name="disp")
        for v in me.vertices:
            r = Vector((v.co.x, v.co.y)).length
            w = min(1.0, max(0.0, (r - flat_radius) / (flat_radius * 1.5)))
            vg.add([v.index], w, "REPLACE")
        d.vertex_group = "disp"
    return ob


def ground_mat(name, c1=(0.24, 0.19, 0.14), c2=(0.12, 0.1, 0.08)):
    if name in C._mats:
        return C._mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.95
    tc = N.new("ShaderNodeTexCoord")
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.15; n1.inputs["Detail"].default_value = 8
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 3.0; n2.inputs["Detail"].default_value = 10
    L.new(tc.outputs["Object"], n1.inputs[0]); L.new(tc.outputs["Object"], n2.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c2, 1)
    ramp.color_ramp.elements[1].color = (*c1, 1)
    mix = N.new("ShaderNodeMath"); mix.operation = "MULTIPLY_ADD"
    L.new(n1.outputs["Fac"], mix.inputs[0]); mix.inputs[1].default_value = 0.6
    L.new(n2.outputs["Fac"], mix.inputs[2])
    mix2 = N.new("ShaderNodeMath"); mix2.operation = "MULTIPLY"; mix2.inputs[1].default_value = 0.7
    L.new(mix.outputs[0], mix2.inputs[0])
    L.new(mix2.outputs[0], ramp.inputs[0])
    L.new(ramp.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4
    n3 = N.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 25
    L.new(tc.outputs["Object"], n3.inputs[0])
    L.new(n3.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(b.outputs[0], out.inputs[0])
    m.diffuse_color = (*c1, 1)
    C._mats[name] = m
    return m


# --------------------------------------------------------------------------- structures
def corrugated(name, w, h, loc, rot, m, coll=None, depth=0.03, waves=None):
    """Corrugated metal sheet (actual wavy geometry) in local XZ plane."""
    import bmesh
    waves = waves or max(4, int(w / 0.12))
    bm = bmesh.new()
    nx = waves * 4
    rows = []
    for zi in range(2):
        row = []
        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            y = depth * math.sin(2 * math.pi * i / 4)
            row.append(bm.verts.new((x, y, h * zi)))
        rows.append(row)
    for i in range(nx):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = C.new_obj(name, me, loc, rot, mat_=m, coll=coll)
    ob.modifiers.new("solid", "SOLIDIFY").thickness = 0.01
    C.smooth(me)
    return ob


def pylon(name, loc, h=12.0, coll=None, yaw=0):
    m = M("pylon_m", (0.3, 0.3, 0.3), metal=0.8, rough=0.5, rust=0.6, scale=2)
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    w0, w1 = 1.6, 0.4
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for i, (sx, sy) in enumerate(corners):
        C.limb(f"{name}_leg{i}", (sx * w0, sy * w0, 0), (sx * w1, sy * w1, h), 0.06, m=m, parent=root, coll=coll,
               verts=6)
    for k in range(6):
        z0 = h * k / 6; z1 = h * (k + 1) / 6
        wa = w0 + (w1 - w0) * k / 6; wb = w0 + (w1 - w0) * (k + 1) / 6
        for i in range(4):
            a = corners[i]; b = corners[(i + 1) % 4]
            C.limb(f"{name}_x{k}{i}", (a[0] * wa, a[1] * wa, z0), (b[0] * wb, b[1] * wb, z1), 0.025, m=m,
                   parent=root, coll=coll, verts=4)
    C.box(f"{name}_arm", (5.0, 0.2, 0.2), loc=(0, 0, h * 0.92), m=m, parent=root, coll=coll, bevel=0)
    C.box(f"{name}_arm2", (3.4, 0.2, 0.2), loc=(0, 0, h * 0.75), m=m, parent=root, coll=coll, bevel=0)
    ins = M("insulator", (0.25, 0.3, 0.25), rough=0.3)
    tips = []
    for x, z in ((-2.4, h * 0.92), (2.4, h * 0.92), (-1.6, h * 0.75), (1.6, h * 0.75)):
        C.cyl(f"{name}_ins{x}{z}", 0.06, 0.3, loc=(x, 0, z - 0.2), m=ins, parent=root, coll=coll, verts=8)
        tips.append((x, z - 0.35))
    return root, tips


def power_line(name, start, end, n=4, h=12, coll=None):
    """Row of pylons with sagging cables; returns list of cable sample functions."""
    s, e = Vector(start), Vector(end)
    d = (e - s)
    yaw = math.degrees(math.atan2(d.y, d.x)) + 90
    pyl = []
    for i in range(n):
        p = s.lerp(e, i / (n - 1))
        root, tips = pylon(f"{name}_{i}", p, h, coll, math.radians(yaw))
        pyl.append((p, tips))
    cable_m = M("cable_m", (0.02, 0.02, 0.02), rough=0.6)
    perp = Vector((-d.y, d.x, 0)).normalized()
    cables = []
    for k in range(4):
        for i in range(n - 1):
            p0, t0 = pyl[i]; p1, t1 = pyl[i + 1]
            # tip x is along the pylon's local X which is rotated by yaw
            a = p0 + perp * -t0[k][0] + Vector((0, 0, t0[k][1]))
            b = p1 + perp * -t1[k][0] + Vector((0, 0, t1[k][1]))
            pts = C.sag_points(a, b, sag=1.2, n=8)
            C.curve_tube(f"{name}_cab{k}_{i}", pts, radius=0.015, m=cable_m, coll=coll, bevel_res=1)
            cables.append(pts)
    return cables


def city_skyline(name, center, coll=None, n=70, seed=3, spread=(260, 60)):
    """Distant megacity: towers with emissive windows + beacons."""
    rnd = C.R.__class__(seed)
    win = window_mat("city_windows", (0.55, 0.75, 1.0), 1.2)
    win2 = window_mat("city_windows2", (1.0, 0.85, 0.6), 0.8)
    body = M("city_body", (0.05, 0.06, 0.08), rough=0.6, dirt=0.0, bump=0, emit=(0.32, 0.26, 0.34),
             emit_strength=0.5)
    beacon = C.emission("beacon_red", (1, 0.05, 0.02), 30)
    c = Vector(center)
    obs = []
    for i in range(n):
        x = c.x + rnd.gauss(0, spread[0] / 3)
        y = c.y + rnd.uniform(-spread[1] / 2, spread[1] / 2)
        dist = abs(x - c.x) / (spread[0] / 2)
        hgt = rnd.uniform(40, 140) * (1.4 - min(1, dist)) + 20
        w = rnd.uniform(8, 18)
        ob = C.box(f"{name}_t{i}", (w, w * rnd.uniform(0.7, 1.2), hgt), loc=(x, y, 0), origin="bottom",
                   m=[body, rnd.choice([win, win, win2])], bevel=0, coll=coll)
        # assign window material to side faces
        for p in ob.data.polygons:
            p.material_index = 1 if abs(p.normal.z) < 0.5 else 0
        obs.append(ob)
        if hgt > 120:
            C.cyl(f"{name}_sp{i}", 0.6, 25, loc=(x, y, hgt + 12), m=body, coll=coll, verts=6)
            C.sphere(f"{name}_bc{i}", 1.5, loc=(x, y, hgt + 25), m=beacon, coll=coll, seg=8, rings=4)
    return obs


def window_mat(name, color, strength):
    if name in C._mats:
        return C._mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.03, 0.035, 0.05, 1)
    haze = N.new("ShaderNodeEmission")
    haze.inputs[0].default_value = (0.32, 0.26, 0.34, 1)
    haze.inputs[1].default_value = 0.45
    b.inputs["Roughness"].default_value = 0.2
    b.inputs["Metallic"].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.25
    br.inputs["Brick Width"].default_value = 2.0
    br.inputs["Row Height"].default_value = 3.0
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (0.0, 0.0, 0.0, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    br.offset = 0.0
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8
    L.new(tc.outputs["Object"], nz.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
    L.new(nz.outputs["Fac"], gt.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(br.outputs["Color"], mul.inputs[0]); L.new(gt.outputs[0], mul.inputs[1])
    s2 = N.new("ShaderNodeMath"); s2.operation = "MULTIPLY"; s2.inputs[1].default_value = strength
    L.new(mul.outputs[0], s2.inputs[0])
    b.inputs["Emission Color"].default_value = (*color, 1)
    L.new(s2.outputs[0], b.inputs["Emission Strength"])
    add = N.new("ShaderNodeAddShader")
    L.new(b.outputs[0], add.inputs[0]); L.new(haze.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs[0])
    m.diffuse_color = (0.1, 0.12, 0.15, 1)
    C._mats[name] = m
    return m


def point_light(name, loc, energy=100, color=(1, 0.8, 0.6), radius=0.1, coll=None, kind="POINT", spot=None,
                rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind != "SUN":
        ld.shadow_soft_size = radius
    if kind == "SPOT" and spot:
        ld.spot_size = math.radians(spot)
        ld.spot_blend = 0.4
    if kind == "AREA":
        ld.size = radius
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    C.link(ob, coll)
    return ob


def string_lights(name, a, b, n=10, sag=0.4, colors=None, coll=None):
    pts = C.sag_points(a, b, sag, n=16)
    C.curve_tube(name + "_wire", pts, radius=0.006, m=M("cable_m"), coll=coll, bevel_res=1)
    colors = colors or [(1, 0.7, 0.3), (1, 0.3, 0.2), (0.4, 0.8, 1.0), (0.5, 1, 0.4)]
    bulbs = []
    for i in range(n):
        t = (i + 0.5) / n
        av, bv = Vector(a), Vector(b)
        p = av.lerp(bv, t)
        p.z -= sag * 4 * t * (1 - t) + 0.04
        col = colors[i % len(colors)]
        m = C.emission(f"bulb_{i % len(colors)}", col, 6)
        bulbs.append(C.sphere(f"{name}_b{i}", 0.035, loc=p, m=m, seg=8, rings=4, coll=coll))
    return bulbs


# --------------------------------------------------------------------------- vehicles
def reclamation_truck(name, loc, yaw, coll=None):
    """City collector truck with rear compactor. Returns dict of animatable parts."""
    C.set_coll(coll)
    navy = M("truck_navy", (0.04, 0.07, 0.15), metal=0.5, rough=0.3, dirt=0.25, rust=0.05, coat=0.5)
    stripe = M("truck_stripe", (0.8, 0.55, 0.05), metal=0.2, rough=0.4, dirt=0.2)
    chrome = M("chrome")
    rubber = M("tire")
    glass_ = C.glass("truck_glass", (0.3, 0.4, 0.5), 0.05)
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    # chassis along -Y (front at -Y)
    C.box(name + "_chassis", (2.2, 7.0, 0.4), loc=(0, 0, 0.9), m=M("dark_metal"), parent=root, bevel=0.02)
    cab = C.box(name + "_cab", (2.3, 2.0, 2.0), loc=(0, -2.6, 2.0), m=navy, parent=root, bevel=0.15)
    C.box(name + "_wind", (2.0, 0.05, 0.8), loc=(0, -3.61, 2.45), m=glass_, parent=root, bevel=0.02)
    C.box(name + "_grill", (1.8, 0.05, 0.6), loc=(0, -3.62, 1.4), m=chrome, parent=root, bevel=0.02)
    hl = C.emission("headlight", (1, 0.95, 0.8), 0.0)
    lights = []
    for sx in (-1, 1):
        lights.append(C.cyl(name + f"_hl{sx}", 0.15, 0.08, loc=(0.85 * sx, -3.63, 1.4), rot=(90, 0, 0), m=hl,
                            parent=root))
    body = C.box(name + "_body", (2.4, 4.2, 2.6), loc=(0, 0.9, 2.4), m=navy, parent=root, bevel=0.08)
    C.box(name + "_stripe1", (2.42, 4.0, 0.25), loc=(0, 0.9, 2.0), m=stripe, parent=root, bevel=0.0)
    for sx in (-1, 1):
        C.text(name + f"_txt{sx}", "CITY RECLAMATION", size=0.32, loc=(1.215 * sx, 0.9, 2.9),
               rot=(90, 0, 90 * sx), m=M("truck_text", (0.85, 0.8, 0.7), rough=0.4), parent=root)
        C.text(name + f"_txt2{sx}", "Out with the old.", size=0.18, loc=(1.215 * sx, 0.9, 2.55),
               rot=(90, 0, 90 * sx), m=M("truck_text"), parent=root)
    # rear hopper (pivot at top-back of body)
    hop_piv = C.empty(name + "_hopper_pivot", loc=(0, 3.0, 3.6), parent=root)
    C.box(name + "_hopper", (2.4, 1.2, 2.4), loc=(0, 0.6, -1.25), m=navy, parent=hop_piv, bevel=0.08)
    C.box(name + "_hopstripe", (2.42, 1.2, 0.15), loc=(0, 0.6, -0.4), m=stripe, parent=hop_piv, bevel=0.0)
    # hopper mouth (dark opening) + press plate
    C.box(name + "_mouth", (2.0, 0.05, 1.0), loc=(0, 1.21, -1.7), m=M("eye_back", (0.02, 0.02, 0.025)),
          parent=hop_piv, bevel=0.0)
    plate_piv = C.empty(name + "_plate_pivot", loc=(0, 1.0, -0.9), parent=hop_piv)
    C.box(name + "_plate", (1.9, 0.1, 1.1), loc=(0, 0, -0.55), m=chrome, parent=plate_piv, bevel=0.02)
    C.box(name + "_step", (2.2, 0.6, 0.06), loc=(0, 4.05, 0.75), m=chrome, parent=root, bevel=0.01)
    for sx in (-1, 1):
        C.box(name + f"_stepbr{sx}", (0.06, 0.6, 0.12), loc=(1.0 * sx, 4.05, 0.84), m=M("dark_metal"),
              parent=root, bevel=0.0)
    C.cyl(name + "_handle", 0.03, 1.4, loc=(0.95, 3.85, 1.6), m=chrome, parent=root)
    # the driver: a faceless city drone behind the windscreen, two cold eyes
    drv = M("driver_m", (0.08, 0.09, 0.11), metal=0.6, rough=0.35)
    C.box(name + "_drv_body", (0.45, 0.35, 0.55), loc=(-0.5, -2.95, 1.75), m=drv, parent=root, bevel=0.06)
    C.sphere(name + "_drv_head", 0.17, loc=(-0.5, -3.0, 2.25), scale=(1, 0.9, 1.1), m=drv, parent=root, seg=16, rings=8)
    eye_m = C.emission("driver_eye", (0.5, 0.85, 1.0), 6.0)
    for sx in (-1, 1):
        C.sphere(name + f"_drv_eye{sx}", 0.025, loc=(-0.5 + 0.06 * sx, -3.15, 2.28), m=eye_m, parent=root, seg=8,
                 rings=4)
    C.cyl(name + "_drv_wheel", 0.17, 0.03, loc=(-0.5, -3.25, 1.95), rot=(60, 0, 0), m=M("dark_metal"), parent=root,
          verts=16)
    # beacon on cab
    bm = C.emission("truck_beacon", (1.0, 0.45, 0.05), 0.0)
    beacon = C.cyl(name + "_beacon", 0.12, 0.15, loc=(0, -2.6, 3.1), m=bm, parent=root)
    wheels = []
    for (wy, sx) in ((-2.6, -1), (-2.6, 1), (1.4, -1), (1.4, 1), (2.6, -1), (2.6, 1)):
        w = C.empty(name + f"_w{wy}{sx}", loc=(1.1 * sx, wy, 0.55), parent=root)
        C.torus(name + f"_tire{wy}{sx}", 0.4, 0.17, loc=(0, 0, 0), rot=(0, 90, 0), m=rubber, parent=w, seg=20,
                segr=8)
        C.cyl(name + f"_rim{wy}{sx}", 0.25, 0.3, rot=(0, 90, 0), m=chrome, parent=w, verts=12)
        wheels.append(w)
    return {"root": root, "hopper": hop_piv, "plate": plate_piv, "wheels": wheels, "beacon_m": bm,
            "headlight_m": hl}


def drive(truck, f0, f1, p0, p1, yaw_deg):
    root = truck["root"]
    root.location = p0
    root.rotation_euler.z = math.radians(yaw_deg)
    root.keyframe_insert("location", frame=f0)
    root.keyframe_insert("rotation_euler", frame=f0)
    root.location = p1
    root.keyframe_insert("location", frame=f1)
    root.keyframe_insert("rotation_euler", frame=f1)
    # a key re-inserted on top of a CONSTANT hold keeps CONSTANT: the truck would teleport at f1
    A.set_interp(root, "location", f0, "BEZIER")
    A.set_interp(root, "rotation_euler", f0, "BEZIER")
    dist = (Vector(p1) - Vector(p0)).length
    for w in truck["wheels"]:
        w.keyframe_insert("rotation_euler", frame=f0, index=0)
        w.rotation_euler.x -= dist / 0.55
        w.keyframe_insert("rotation_euler", frame=f1, index=0)
        A.set_interp(w, "rotation_euler", f0, "BEZIER", index=0)
    A.event(f0, "truck", dur=f1 - f0)


# --------------------------------------------------------------------------- smoke puffs
def smoke(name, origin, f0, f1, coll=None, every=10, rise=3.0, life=60, size=0.25, color=(0.5, 0.5, 0.5),
          drift=(0.5, 0.2, 0), seed=0):
    rnd = C.R.__class__(seed)
    m = M(name + "_m", color, rough=1.0, dirt=0.0, bump=0, alpha=0.5)
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    o = Vector(origin)
    f = f0
    i = 0
    while f < f1:
        ob = C.sphere(f"{name}_{i}", size, loc=o, m=m, seg=10, rings=6, coll=coll)
        ob.scale = (0.2, 0.2, 0.2)
        A.show_between(ob, f, f + life)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("scale", frame=f)
        ob.location = o + Vector((drift[0] * rise + rnd.uniform(-0.3, 0.3), drift[1] * rise, rise))
        s = rnd.uniform(1.6, 2.4)
        ob.scale = (s, s, s)
        ob.keyframe_insert("location", frame=f + life)
        ob.keyframe_insert("scale", frame=f + life)
        f += every
        i += 1
