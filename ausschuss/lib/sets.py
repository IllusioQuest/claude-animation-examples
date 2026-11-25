"""Sets, worlds and render setup."""
import bpy
import math
from mathutils import Vector
import core as C
import props as P
import anim as A

M = C.mat

# =========================================================================== RENDER / WORLD


def setup_render(sc, preview=True):
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.fps = C.FPS
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 25 if preview else 100
    ee = sc.eevee
    ee.taa_render_samples = 1 if preview else 64
    ee.use_shadows = True
    ee.shadow_ray_count = 1
    ee.shadow_step_count = 4 if preview else 6
    ee.shadow_resolution_scale = 0.25 if preview else 1.0
    ee.shadow_pool_size = "256" if preview else "512"
    ee.volumetric_tile_size = "16" if preview else "4"
    ee.volumetric_samples = 32 if preview else 128
    ee.use_volumetric_shadows = True
    ee.volumetric_end = 250
    try:
        ee.use_raytracing = not preview
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    compositor(sc)


def compositor(sc, glare=True, vignette=0.35, grain=0.04):
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    rl = N.new("CompositorNodeRLayers"); rl.location = (-600, 0)
    rl.scene = sc
    last = rl.outputs["Image"]
    if glare:
        g = N.new("CompositorNodeGlare"); g.location = (-400, 0)
        g.glare_type = "FOG_GLOW"
        g.quality = "MEDIUM"
        g.threshold = 1.2
        g.size = 7
        g.mix = -0.6
        L.new(last, g.inputs["Image"])
        last = g.outputs["Image"]
    if vignette:
        el = N.new("CompositorNodeEllipseMask"); el.location = (-400, -300)
        el.width = 0.95; el.height = 0.9
        bl = N.new("CompositorNodeBlur"); bl.location = (-200, -300)
        bl.filter_type = "FAST_GAUSS"; bl.use_relative = True
        bl.factor_x = 25; bl.factor_y = 25
        L.new(el.outputs[0], bl.inputs[0])
        mr = N.new("CompositorNodeMapRange"); mr.location = (0, -300)
        mr.inputs[3].default_value = 1 - vignette; mr.inputs[4].default_value = 1.0
        L.new(bl.outputs[0], mr.inputs[0])
        mu = N.new("CompositorNodeMixRGB"); mu.blend_type = "MULTIPLY"; mu.location = (200, 0)
        L.new(last, mu.inputs[1]); L.new(mr.outputs[0], mu.inputs[2])
        last = mu.outputs[0]
    g = GRADES.get(sc.name[:2])
    if g:
        cb = N.new("CompositorNodeColorBalance"); cb.location = (300, 150)
        cb.correction_method = "LIFT_GAMMA_GAIN"
        cb.lift = g["lift"]; cb.gamma = g["gamma"]; cb.gain = g["gain"]
        L.new(last, cb.inputs["Image"])
        last = cb.outputs["Image"]
        hs = N.new("CompositorNodeHueSat"); hs.location = (400, 150)
        hs.name = "GradeSat"
        hs.inputs["Saturation"].default_value = g["sat"]
        L.new(last, hs.inputs["Image"])
        last = hs.outputs["Image"]
        if g.get("contrast"):
            bc = N.new("CompositorNodeBrightContrast"); bc.location = (450, 150)
            bc.inputs["Contrast"].default_value = g["contrast"]
            L.new(last, bc.inputs["Image"])
            last = bc.outputs["Image"]
    if g:
        # the Erfasser's scanner view: red monochrome, mixed in per POV shot (factor keyed by pov.py)
        bw = N.new("CompositorNodeRGBToBW"); bw.location = (550, 300)
        L.new(last, bw.inputs[0])
        tint = N.new("CompositorNodeMixRGB"); tint.blend_type = "MULTIPLY"; tint.location = (700, 300)
        tint.inputs[0].default_value = 1.0
        tint.inputs[2].default_value = (1.6, 0.28, 0.2, 1)
        L.new(bw.outputs[0], tint.inputs[1])
        pm = N.new("CompositorNodeMixRGB"); pm.name = "POVMix"; pm.location = (850, 150)
        pm.inputs[0].default_value = 0.0
        L.new(last, pm.inputs[1]); L.new(tint.outputs[0], pm.inputs[2])
        last = pm.outputs[0]
    comp = N.new("CompositorNodeComposite"); comp.location = (1000, 0)
    L.new(last, comp.inputs["Image"])
    sc["comp_last"] = 1


def key_sat(sc, f, v, interp=None):
    """Colour as dramaturgy: key the saturation of a sequence's grade."""
    n = sc.node_tree.nodes.get("GradeSat")
    if n:
        A.key_socket(n.inputs["Saturation"], f, v, interp)


# per-sequence grade: every place gets its own palette (shadows / mids / highlights)
GRADES = {
    "S1": dict(lift=(0.98, 0.985, 1.04), gamma=(1.0, 0.99, 1.0), gain=(1.05, 0.99, 0.95), sat=1.08),
    "S2": dict(lift=(0.97, 1.0, 1.035), gamma=(1.01, 1.0, 0.985), gain=(1.06, 1.0, 0.92), sat=1.06),
    "S3": dict(lift=(1.015, 1.005, 0.985), gamma=(1.015, 1.01, 0.99), gain=(1.02, 1.01, 0.975), sat=0.92),
    "S4": dict(lift=(0.985, 0.985, 1.01), gamma=(1.01, 1.0, 0.98), gain=(1.05, 1.01, 0.95), sat=1.12),
    "S5": dict(lift=(0.96, 0.995, 1.05), gamma=(1.0, 0.995, 1.0), gain=(1.05, 0.99, 0.93), sat=1.06),
    "S6": dict(lift=(0.995, 0.985, 1.02), gamma=(1.015, 1.0, 0.98), gain=(1.06, 1.015, 0.94), sat=1.12),
}


def world(name, horizon, zenith, ground=(0.05, 0.04, 0.03), strength=1.0, fog_density=0.0,
          fog_color=(0.6, 0.65, 0.7), fog_aniso=0.3, sun_dir=None, sun_color=(1, 0.6, 0.3), sun_glow=0.0):
    w = bpy.data.worlds.new(name)
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputWorld")
    bg = N.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.47
    cr.elements[0].color = (*ground, 1)
    cr.elements[1].position = 0.5
    cr.elements[1].color = (*horizon, 1)
    e = cr.elements.new(0.75)
    e.color = (*zenith, 1)
    # generated coords for world are direction based: z in [-1,1] -> map to [0,1]
    mr = N.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = -1; mr.inputs[2].default_value = 1
    L.new(sep.outputs["Z"], mr.inputs[0])
    L.new(mr.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if sun_dir is not None and sun_glow > 0:
        # soft glow around the sun direction
        dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
        L.new(tc.outputs["Generated"], dot.inputs[0])
        dot.inputs[1].default_value = Vector(sun_dir).normalized()
        pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 12
        cl = N.new("ShaderNodeMath"); cl.operation = "MAXIMUM"; cl.inputs[1].default_value = 0
        L.new(dot.outputs["Value"], cl.inputs[0])
        L.new(cl.outputs[0], pw.inputs[0])
        sc_ = N.new("ShaderNodeMath"); sc_.operation = "MULTIPLY"; sc_.inputs[1].default_value = sun_glow
        L.new(pw.outputs[0], sc_.inputs[0])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "ADD"
        L.new(sc_.outputs[0], mix.inputs["Factor"])
        L.new(col, mix.inputs["A"])
        mix.inputs["B"].default_value = (*sun_color, 1)
        col = mix.outputs["Result"]
    L.new(col, bg.inputs[0])
    L.new(bg.outputs[0], out.inputs["Surface"])
    if fog_density > 0:
        vol = N.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (*fog_color, 1)
        vol.inputs["Density"].default_value = fog_density
        vol.inputs["Anisotropy"].default_value = fog_aniso
        L.new(vol.outputs[0], out.inputs["Volume"])
    w["fog"] = fog_density
    return w


def fog_socket(w):
    for n in w.node_tree.nodes:
        if n.type == "PRINCIPLED_VOLUME":
            return n.inputs["Density"]


def sun(name, rot, energy, color, coll, angle=2.0):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, ld)
    ob.rotation_euler = [math.radians(a) for a in rot]
    coll.objects.link(ob)
    return ob


# =========================================================================== SCRAPYARD
SCRAP = {
    "hut": Vector((-15.0, -3.0, 0.0)),
    "dump": Vector((2.0, 8.0, 0.0)),
}


def build_scrapyard(coll, lib_coll):
    C.set_coll(coll)
    P.scrap_library(lib_coll)
    C.set_coll(coll)
    gm = P.ground_mat("scrap_ground", (0.26, 0.2, 0.15), (0.1, 0.08, 0.06))
    P.terrain("scrap_terrain", size=600, res=160, strength=3.0, m=gm, coll=coll, flat_radius=30)
    # road (tyre-tracked dirt) toward the city
    road = M("road_m", (0.12, 0.1, 0.08), rough=0.95, dirt=0.6, scale=0.5, bump=0.4)
    C.box("road1", (5.0, 300.0, 0.04), loc=(6.0, 150 + 8, 0.0), m=road, bevel=0, coll=coll)
    C.box("road2", (40.0, 5.0, 0.04), loc=(-12.0, 8.0, 0.01), m=road, bevel=0, coll=coll)
    # piles near action area
    # (kept clear of the truck road x=6±4 and the side road y=8±3.5)
    piles = [((-3.4, 12.0, 0), 3.0, 2.2, 40), ((-3, -7, 0), 3.0, 1.6, 30), ((13, -4, 0), 4.0, 2.5, 50),
             ((-8, 3.4, 0), 2.5, 1.5, 25),
             ((-14, 15.5, 0), 4.5, 3.2, 55), ((15, 15, 0), 6.0, 4.0, 60), ((20, -10, 0), 5.0, 3.0, 50),
             ((-25, -20, 0), 6.0, 3.5, 50), ((-9, 23.5, 0), 4.0, 2.5, 40), ((-36, -14, 0), 7, 5, 60),
             ((30, 4, 0), 7, 5, 60), ((-7, 36, 0), 8, 6, 70), ((-28, 30, 0), 10, 7, 60), ((28, 32, 0), 10, 8, 60),
             ((-45, -20, 0), 10, 6, 50), ((45, -18, 0), 12, 7, 50), ((24, 62, 0), 12, 9, 60),
             ((-40, 60, 0), 16, 10, 60), ((50, 55, 0), 16, 12, 60)]
    for i, (c, r, h, n) in enumerate(piles):
        P.scrap_pile(f"pile{i}", c, r, h, n, seed=10 + i, coll=coll)
    # loose items on the ground near the action
    rnd = C.R.__class__(99)
    kinds = ["tire", "barrel_rust", "crate", "tv", "panel", "pipe", "gear", "drum"]
    for i in range(40):
        x = rnd.uniform(-20, 20); y = rnd.uniform(-15, 20)
        if -4 < x < 10 and -4 < y < 15:
            continue
        if abs(x - 6) < 3.6 or (abs(y - 8) < 3.2 and x < 9):
            continue
        if (Vector((x, y)) - Vector((-17.5, -3.5))).length < 7.5:  # the hut and the space in front of it
            continue
        if Vector((x, y)).length < 3:
            continue
        k = rnd.choice(kinds)
        rot = (90 if k == "tire" and rnd.random() < 0.6 else 0, 0, rnd.uniform(0, 360))
        z = 0.1 if k == "tire" else 0.3
        P.scrap_item(k, (x, y, z), rot, rnd.uniform(0.7, 1.1), coll)
    cables = P.power_line("pline", (-90, 24, 0), (90, 24, 0), n=4, h=13, coll=coll)
    city = C.collection("City")
    P.city_skyline("city", (0, 650, 0), coll=city, n=80, spread=(700, 120))
    # giant city wall & gate glow
    C.box("citywall", (900, 6, 25), loc=(0, 560, 0), origin="bottom",
          m=M("citywall_m", (0.08, 0.09, 0.1), metal=0.4, rough=0.4, dirt=0.3), coll=city, bevel=0)
    for i in range(18):
        P.point_light(f"citywall_l{i}", (-400 + i * 47, 555, 24), 4000, (0.6, 0.8, 1.0), 2.0, coll=city)
    hut = build_hut(coll, SCRAP["hut"], yaw=-75)
    return {"cables": cables, "hut": hut, "city": city}


def build_hut(coll, loc, yaw=0):
    """Hedda's corrugated shack. Front (door) faces local -Y."""
    C.set_coll(coll)
    m = P.mats()
    root = C.empty("hut", loc=loc, rot=(0, 0, yaw), coll=coll)
    parts = [root]
    W, D, H = 4.4, 3.6, 2.5
    cols = [m["corr1"], m["corr2"], m["corr3"], m["corr1"]]
    # walls from sheets (front has door + window gaps)
    def sheet(name, w, h, lp, rot, mm):
        o = P.corrugated(name, w, h, lp, rot, mm, coll=coll)
        o.parent = root
        parts.append(o)
        return o
    # back wall
    for i in range(4):
        sheet(f"hut_back{i}", 1.15, H + 0.1, (-W / 2 + 0.55 + i * 1.1, D / 2, 0), (0, 0, 0), cols[i % 4])
    for s in (-1, 1):
        for i in range(3):
            sheet(f"hut_side{s}{i}", 1.25, H + (0.25 if s < 0 else 0.0), (s * W / 2, -D / 2 + 0.6 + i * 1.2, 0),
                  (0, 0, 90), cols[(i + (s > 0)) % 4])
    # front: left of door, window section, right
    sheet("hut_front0", 1.2, H + 0.3, (-1.6, -D / 2, 0), (0, 0, 0), cols[2])
    sheet("hut_front_low", 1.6, 0.9, (0.6, -D / 2, 0), (0, 0, 0), cols[0])
    sheet("hut_front_high", 1.6, 0.6, (0.6, -D / 2, 1.95), (0, 0, 0), cols[1])
    sheet("hut_front2", 0.8, H + 0.3, (1.8, -D / 2, 0), (0, 0, 0), cols[3])
    # window: warm glowing glass with frame
    warm = C.emission("hut_window_glow", (1.0, 0.62, 0.28), 10.0)
    win = C.box("hut_window", (1.5, 0.04, 1.0), loc=(0.6, -D / 2 + 0.06, 1.42), m=warm, parent=root, bevel=0,
                coll=coll)
    parts.append(win)
    for (x, z, w_, h_) in ((0.6, 1.42, 0.06, 1.05), (0.6, 1.42, 1.55, 0.06)):
        parts.append(C.box("hut_wframe", (w_, 0.08, h_), loc=(x, -D / 2 - 0.02, z), m=m["wood"], parent=root,
                           bevel=0, coll=coll))
    # door (wood planks)
    door = C.box("hut_door", (0.9, 0.06, 2.0), loc=(-0.55, -D / 2, 1.0), m=m["wood"], parent=root, bevel=0.01,
                 coll=coll)
    parts.append(door)
    for z in (0.4, 1.6):
        parts.append(C.box("hut_doorbar", (0.92, 0.04, 0.1), loc=(-0.55, -D / 2 - 0.04, z), m=m["wood"],
                           parent=root, bevel=0, coll=coll))
    # roof (slanted), overhang, weights (tyres/stones)
    roof = P.corrugated("hut_roof", W + 0.8, D + 1.0, (0, -D / 2 - 0.5, H + 0.25), (0, 0, 0), m["corr1"],
                        coll=coll)
    roof.rotation_euler = (math.radians(90 - 8), 0, 0)
    roof.location = (0, D / 2 + 0.5, H + 0.05)
    roof.rotation_euler = (math.radians(-90 + 4), 0, 0)
    roof.parent = root
    parts.append(roof)
    roof2 = P.corrugated("hut_roofpatch", 1.4, 1.5, (0.9, 0.6, H + 0.3), (-90 + 4, 0, 0),
                         m["corr2"], coll=coll)
    roof2.parent = root
    parts.append(roof2)
    for i, (x, y) in enumerate(((-1.4, 0.5), (1.5, -0.6), (0.2, 1.2))):
        t = P.scrap_item("tire", (x, y, H + 0.42), (0, 0, 0), 0.7, coll)
        t.parent = root
        parts.append(t)
    # stove pipe chimney
    pipe = C.cyl("hut_chimney", 0.12, 1.4, loc=(-1.5, 1.0, H + 0.9), m=m["dark"], parent=root, coll=coll)
    parts.append(pipe)
    parts.append(C.cyl("hut_chimcap", 0.22, 0.05, loc=(-1.5, 1.0, H + 1.66), r2=0.02, m=m["dark"], parent=root,
                       coll=coll))
    # satellite dish + antenna + windmill made from a fan
    dish = C.lathe("hut_dish", [(0.01, 0.0), (0.25, 0.04), (0.45, 0.14)], loc=(1.6, 1.2, H + 0.6),
                   rot=(-50, 0, 30), m=m["paint_white"], parent=root, coll=coll)
    dish.modifiers.new("s", "SOLIDIFY").thickness = 0.02
    parts.append(dish)
    parts.append(C.cyl("hut_antenna", 0.015, 2.2, loc=(1.9, 0.6, H + 1.2), m=m["steel"], parent=root, coll=coll))
    for z in (0.6, 0.9, 1.2):
        parts.append(C.cyl(f"hut_ant_x{z}", 0.01, 0.6 - z * 0.3, loc=(1.9, 0.6, H + 0.2 + z * 1.4),
                           rot=(0, 90, 0), m=m["steel"], parent=root, coll=coll))
    mill = C.empty("hut_windmill", loc=(-2.6, 0.9, H + 1.9), rot=(0, 0, 0), parent=root, coll=coll)
    parts.append(C.cyl("hut_millpole", 0.04, 2.0, loc=(-2.6, 1.0, H + 0.9), m=m["steel"], parent=root, coll=coll))
    rotor = C.empty("hut_millrotor", loc=(0, -0.12, 0), parent=mill, coll=coll)
    for k in range(4):
        b = C.box(f"hut_blade{k}", (0.12, 0.02, 0.55), loc=(0, 0, 0.3), rot=(0, 0, 0),
                  m=[m["paint_red"], m["paint_yel"], m["paint_blue"], m["paint_white"]][k], parent=None, bevel=0,
                  coll=coll)
        piv = C.empty(f"hut_bladepiv{k}", rot=(0, k * 90, 0), parent=rotor, coll=coll)
        b.parent = piv
        b.rotation_euler = (math.radians(20), 0, 0)
    C.cyl("hut_millhub", 0.06, 0.1, loc=(0, -0.05, 0), rot=(90, 0, 0), m=m["dark"], parent=rotor, coll=coll)
    parts += [mill]
    # sign
    sign = C.box("hut_sign", (1.3, 0.04, 0.4), loc=(-0.3, -D / 2 - 0.06, H + 0.0), rot=(0, 3, 0),
                 m=M("sign_wood", (0.5, 0.42, 0.3), rough=0.9, dirt=0.6), parent=root, bevel=0, coll=coll)
    parts.append(sign)
    parts.append(C.text("hut_signtxt", "REPAIRS", size=0.24, loc=(-0.3, -D / 2 - 0.085, H + 0.0), rot=(90, 3, 0),
                        m=M("paint_text", (0.6, 0.1, 0.05), rough=0.8), parent=root, coll=coll))
    parts.append(C.text("hut_signtxt2", "anything. almost.", size=0.07, loc=(-0.3, -D / 2 - 0.085, H - 0.15),
                        rot=(90, 3, 0), m=M("paint_text"), parent=root, coll=coll))
    # junk around hut: barrel rain catcher, crates, gas bottle
    for i, (k, x, y, rz) in enumerate((("barrel_rust", 2.6, -1.0, 0), ("crate", 2.5, 0.3, 20),
                                         ("crate", 2.55, 0.35, 50), ("tire", -2.8, -1.2, 0),
                                         ("drum", -2.8, 0.2, 0))):
        o = P.scrap_item(k, (x, y, 0.44 if k == "barrel_rust" else 0.25 + (0.5 if i == 2 else 0)),
                         (90 if k == "tire" else 0, 0, rz), 1.0, coll)
        o.parent = root
        parts.append(o)
    lamp = P.point_light("hut_inner_light", (0.6, -2.4, 1.8), 120, (1.0, 0.6, 0.3), 0.3, coll=coll)
    lamp.parent = root
    parts.append(lamp)
    # flattened remains (for sequence 6) – hidden by default
    remains = []
    slab = C.box("hut_remains_slab", (W + 0.4, D + 0.4, 0.12), loc=(0, 0, 0.06),
                 m=P.mats()["concrete"], parent=root, bevel=0.02, coll=coll)
    remains.append(slab)
    for i in range(7):
        rr = C.R.__class__(i)
        o = P.corrugated(f"hut_rem{i}", rr.uniform(0.8, 1.4), rr.uniform(0.6, 1.2),
                         (rr.uniform(-2, 2), rr.uniform(-1.6, 1.6), 0.16), (-88 + rr.uniform(-6, 6), 0,
                                                                              rr.uniform(0, 180)),
                         cols[i % 4], coll=coll)
        o.parent = root
        remains.append(o)
    return {"root": root, "parts": parts, "remains": remains, "mill_rotor": rotor, "window": win, "lamp": lamp,
            "door": door, "chimney_top": Vector((-1.5, 1.0, H + 1.7))}


def spin(ob, f0, f1, axis=1, turns_per_sec=0.5):
    ob.keyframe_insert("rotation_euler", frame=f0, index=axis)
    r = list(ob.rotation_euler)
    r[axis] += 2 * math.pi * turns_per_sec * (f1 - f0) / C.FPS
    ob.rotation_euler = r
    ob.keyframe_insert("rotation_euler", frame=f1, index=axis)
    A.set_interp(ob, "rotation_euler", f0, "LINEAR", axis)


def fog_box(name, coll, center=(0, 0, 0), size=(300, 300, 60), density=0.01, color=(0.7, 0.7, 0.75),
            aniso=0.35, height_falloff=True):
    """Volume box for atmospheric haze (EEVEE Next friendly). Density falls off with height."""
    m = bpy.data.materials.new(name + "_m")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Anisotropy"].default_value = aniso
    val = N.new("ShaderNodeValue"); val.outputs[0].default_value = density
    val.label = "density"
    if height_falloff:
        tc = N.new("ShaderNodeTexCoord")
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(tc.outputs["Generated"], sep.inputs[0])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.6
        mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.15
        L.new(sep.outputs["Z"], mr.inputs[0])
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        L.new(mr.outputs[0], mul.inputs[0]); L.new(val.outputs[0], mul.inputs[1])
        L.new(mul.outputs[0], vol.inputs["Density"])
    else:
        L.new(val.outputs[0], vol.inputs["Density"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    me = C.mesh_box(name, *size, origin="bottom")
    ob = bpy.data.objects.new(name, me)
    me.materials.append(m)
    ob.location = (center[0], center[1], center[2] - 1)
    coll.objects.link(ob)
    ob["density_node"] = val.name
    return ob


def fog_density_socket(fog_ob):
    m = fog_ob.data.materials[0]
    return m.node_tree.nodes[fog_ob["density_node"]].outputs[0]
