"""Workshop interior, village square, reclamation depot."""
import bpy
import math
from mathutils import Vector
import core as C
import props as P
import anim as A
import sets as S

M = C.mat

WORKSHOP = Vector((0.0, 500.0, 0.0))
VILLAGE = Vector((300.0, 0.0, 0.0))
DEPOT = Vector((-300.0, 0.0, 0.0))
HALL = Vector((-300.0, 80.0, 0.0))


def _w(p, base):
    return tuple(Vector(p) + base)


# =========================================================================== WORKSHOP
def build_workshop(coll):
    """Interior. Local frame: x -3..3, y -2.5..2.5, back wall at +y. Returns dict of animatables."""
    C.set_coll(coll)
    O = WORKSHOP
    m = P.mats()
    w = lambda p: _w(p, O)
    out = {}
    floor = M("planks", (0.3, 0.2, 0.12), rough=0.75, dirt=0.6, scale=2, bump=0.25)
    for i in range(14):
        C.box(f"ws_plank{i}", (6.2, 0.36, 0.05), loc=w((0, -2.5 + 0.18 + i * 0.36, -0.025)),
              m=floor, bevel=0.01, coll=coll)
    walls = [m["corr1"], m["corr3"], m["corr2"], m["corr1"]]
    for i in range(6):  # back wall
        P.corrugated(f"ws_back{i}", 1.05, 2.8, w((-2.6 + i * 1.04, 2.55, 0)), (0, 0, 0), walls[i % 4], coll=coll)
    for s in (-1, 1):
        for i in range(5):
            P.corrugated(f"ws_side{s}{i}", 1.05, 2.8, w((3.05 * s, -2.1 + i * 1.04, 0)), (0, 0, math.radians(90)),
                         walls[(i + 1) % 4], coll=coll)
    for i in range(6):  # front wall
        P.corrugated(f"ws_front{i}", 1.05, 2.8, w((-2.6 + i * 1.04, -2.55, 0)), (0, 0, 0), walls[(i + 2) % 4],
                     coll=coll)
    for i in range(7):
        P.corrugated(f"ws_roof{i}", 6.4, 0.95, w((0, -2.6 + i * 0.85, 2.75)), (math.radians(-90), 0, 0),
                     m["corr1"], coll=coll)
    for i in range(4):
        C.box(f"ws_beam{i}", (6.2, 0.12, 0.16), loc=w((0, -1.9 + i * 1.3, 2.6)), m=m["wood"], bevel=0.01, coll=coll)
    # window on left wall (night outside)
    C.box("ws_window", (0.05, 1.0, 0.7), loc=w((-3.0, -0.8, 1.6)),
          m=C.emission("ws_night", (0.15, 0.25, 0.5), 1.2), bevel=0, coll=coll)
    for dz in (-0.37, 0.37):
        C.box(f"ws_wf{dz}", (0.1, 1.08, 0.06), loc=w((-2.98, -0.8, 1.6 + dz)), m=m["wood"], bevel=0, coll=coll)
    C.box("ws_wfv", (0.1, 0.06, 0.8), loc=w((-2.98, -0.8, 1.6)), m=m["wood"], bevel=0, coll=coll)
    # ---- workbench
    bench = M("bench_m", (0.36, 0.24, 0.13), rough=0.7, dirt=0.65, scale=2, bump=0.3)
    C.box("ws_benchtop", (3.2, 0.9, 0.08), loc=w((0, 1.95, 0.92)), m=bench, bevel=0.01, coll=coll)
    for x in (-1.5, 1.5):
        for y in (1.6, 2.3):
            C.box(f"ws_leg{x}{y}", (0.08, 0.08, 0.9), loc=w((x, y, 0.45)), m=bench, bevel=0.005, coll=coll)
    C.box("ws_benchshelf", (3.0, 0.7, 0.04), loc=w((0, 1.95, 0.25)), m=bench, bevel=0.005, coll=coll)
    # pegboard + tools
    C.box("ws_peg", (2.4, 0.03, 1.0), loc=w((0, 2.45, 1.65)), m=M("peg_m", (0.45, 0.38, 0.28), rough=0.8, dirt=0.4),
          bevel=0, coll=coll)
    tool_m = m["steel"]
    rnd = C.R.__class__(5)
    for i in range(9):
        x = -1.0 + i * 0.25
        k = i % 3
        if k == 0:
            C.box(f"ws_wrench{i}", (0.04, 0.015, 0.3), loc=w((x, 2.42, 1.65)), rot=(0, rnd.uniform(-8, 8), 0),
                  m=tool_m, bevel=0.005, coll=coll)
        elif k == 1:
            C.cyl(f"ws_screwh{i}", 0.018, 0.12, loc=w((x, 2.41, 1.75)), m=M("handle_red", (0.6, 0.08, 0.05)),
                  coll=coll)
            C.cyl(f"ws_screws{i}", 0.005, 0.14, loc=w((x, 2.41, 1.62)), m=tool_m, coll=coll)
        else:
            C.box(f"ws_hammerh{i}", (0.12, 0.04, 0.04), loc=w((x, 2.41, 1.8)), m=m["dark"], bevel=0.005, coll=coll)
            C.cyl(f"ws_hammers{i}", 0.012, 0.28, loc=w((x, 2.41, 1.65)), m=m["wood"], coll=coll)
    # items on bench: vise, parts tray, jars, soldering iron
    C.box("ws_vise", (0.2, 0.15, 0.15), loc=w((-1.25, 1.75, 1.04)), m=M("vise_m", (0.15, 0.25, 0.2), metal=0.5,
                                                                      rust=0.4), bevel=0.01, coll=coll)
    C.box("ws_tray", (0.4, 0.25, 0.05), loc=w((0.9, 2.0, 0.985)), m=m["steel"], bevel=0.005, coll=coll)
    for i in range(12):
        C.cyl(f"ws_nut{i}", 0.012, 0.01, loc=w((0.75 + rnd.uniform(0, 0.3), 1.92 + rnd.uniform(0, 0.15), 1.0)),
              m=M("brass"), verts=6, coll=coll)
    jar_m = C.glass("jar_glass", (0.8, 0.9, 0.85), 0.1)
    for i in range(4):
        C.cyl(f"ws_jar{i}", 0.06, 0.15, loc=w((1.2 + i * 0.14, 2.25, 1.04)), m=jar_m, coll=coll)
        C.cyl(f"ws_jarc{i}", 0.05, 0.08, loc=w((1.2 + i * 0.14, 2.25, 1.0)),
              m=[M("brass"), m["steel"], M("p_red"), M("dark_metal")][i], verts=8, coll=coll)
    # desk lamp (articulated) with warm spot
    lamp_m = M("lamp_green", (0.15, 0.3, 0.2), metal=0.6, rough=0.4, rust=0.25)
    C.cyl("ws_lampbase", 0.09, 0.03, loc=w((-0.6, 2.25, 0.975)), m=lamp_m, coll=coll)
    C.limb("ws_lamparm1", w((-0.6, 2.25, 0.98)), w((-0.5, 2.0, 1.5)), 0.012, m=m["steel"], coll=coll)
    C.limb("ws_lamparm2", w((-0.5, 2.0, 1.5)), w((-0.25, 1.7, 1.5)), 0.012, m=m["steel"], coll=coll)
    shade = C.cyl("ws_lampshade", 0.1, 0.14, loc=w((-0.22, 1.66, 1.45)), rot=(30, 0, 0), r2=0.04, m=lamp_m,
                  coll=coll)
    desk_bulb_m = C.emission("ws_deskbulb", (1.0, 0.8, 0.5), 20)
    desk_bulb = C.sphere("ws_deskbulb", 0.035, loc=w((-0.21, 1.64, 1.4)), m=desk_bulb_m, coll=coll)
    desk_light = P.point_light("ws_desklight", w((-0.21, 1.6, 1.38)), 60, (1.0, 0.75, 0.45), 0.05, coll=coll,
                               kind="SPOT", spot=95, rot=(30, 0, 0))
    out.update(desk_bulb=desk_bulb, desk_bulb_m=desk_bulb_m, desk_light=desk_light)
    # hanging bulb
    C.curve_tube("ws_cord", [w((0.3, 0.6, 2.6)), w((0.3, 0.6, 2.25))], radius=0.006, m=M("cable_m"), coll=coll)
    hb_m = C.emission("ws_hangbulb", (1.0, 0.7, 0.4), 15)
    C.sphere("ws_hangbulb", 0.045, loc=w((0.3, 0.6, 2.2)), m=hb_m, coll=coll)
    hang = P.point_light("ws_hanglight", w((0.3, 0.6, 2.15)), 90, (1.0, 0.65, 0.35), 0.1, coll=coll)
    out.update(hang_bulb_m=hb_m, hang_light=hang)
    # ---- stove (warm glow)
    st = M("stove_m", (0.06, 0.06, 0.06), metal=0.8, rough=0.5, rust=0.3)
    C.lathe("ws_stove", [(0.25, 0.0), (0.3, 0.3), (0.3, 0.7), (0.22, 0.85), (0.08, 0.9)], loc=w((-2.4, 1.9, 0.0)),
            m=st, coll=coll, cap_top=True)
    C.cyl("ws_stovepipe", 0.07, 1.9, loc=w((-2.4, 1.9, 1.85)), m=st, coll=coll)
    fire_m = C.emission("ws_fire", (1.0, 0.35, 0.08), 8)
    C.box("ws_stovewin", (0.16, 0.02, 0.12), loc=w((-2.4, 1.595, 0.45)), m=fire_m, bevel=0.01, coll=coll)
    fire_l = P.point_light("ws_firelight", w((-2.4, 1.4, 0.45)), 40, (1.0, 0.4, 0.1), 0.2, coll=coll)
    out.update(fire_light=fire_l)
    # ---- generator (right back corner)
    gen = C.empty("ws_gen", loc=w((2.35, 1.6, 0.0)), coll=coll)
    gm = M("gen_red", (0.5, 0.12, 0.06), metal=0.4, rough=0.5, rust=0.5)
    C.box("ws_genframe", (0.8, 0.55, 0.55), loc=(0, 0, 0.3), m=gm, parent=gen, bevel=0.03, coll=coll)
    C.cyl("ws_genengine", 0.18, 0.4, loc=(0.1, 0, 0.42), rot=(0, 90, 0), m=m["dark"], parent=gen, coll=coll)
    C.cyl("ws_gentank", 0.15, 0.5, loc=(0, 0, 0.72), rot=(0, 90, 0), m=gm, parent=gen, coll=coll)
    C.cyl("ws_genexhaust", 0.04, 1.6, loc=(-0.3, 0.2, 1.3), m=m["dark"], parent=gen, coll=coll)
    gen_lamp_m = C.emission("ws_genlamp", (0.2, 1.0, 0.2), 5)
    C.sphere("ws_genlamp", 0.025, loc=(0.3, -0.28, 0.5), m=gen_lamp_m, parent=gen, coll=coll)
    C.box("ws_gendial", (0.12, 0.02, 0.1), loc=(-0.1, -0.28, 0.45), m=M("gauge_face"), parent=gen, bevel=0.005,
          coll=coll)
    out.update(gen=gen, gen_lamp_m=gen_lamp_m)
    # ---- collapsing shelf (right wall), pivot at its foot
    shelf = C.empty("ws_shelf", loc=w((2.75, -0.4, 0.0)), coll=coll)
    sh_m = M("shelf_m", (0.3, 0.2, 0.12), rough=0.8, dirt=0.5)
    for z in (0.02, 0.6, 1.2, 1.8):
        C.box(f"ws_shelfb{z}", (0.4, 1.4, 0.03), loc=(0, 0, z), m=sh_m, parent=shelf, bevel=0.003, coll=coll)
    for y in (-0.68, 0.68):
        C.box(f"ws_shelfs{y}", (0.4, 0.03, 1.85), loc=(0, y, 0.92), m=sh_m, parent=shelf, bevel=0.003, coll=coll)
    shelf_items = []
    for i, (k, y, z) in enumerate((("tv", -0.3, 0.88), ("crate", 0.3, 0.29), ("drum", -0.3, 0.2),
                                   ("tv", 0.35, 1.48), ("crate", -0.35, 1.45), ("gear", 0.2, 1.85))):
        o = P.scrap_item(k, (0, 0, 0), (0, 0, 90), 0.5, coll)
        o.parent = shelf
        o.location = (0, y, z)
        shelf_items.append(o)
    out.update(shelf=shelf)
    # pot for the gag
    pot = C.lathe("ws_pot", [(0.12, 0.0), (0.14, 0.02), (0.14, 0.14), (0.15, 0.15)], m=m["steel"], coll=coll,
                  cap_bottom=True)
    pot.modifiers.new("s", "SOLIDIFY").thickness = 0.008
    pot.location = w((2.75, -0.1, 1.83))
    out.update(pot=pot)
    # ---- left wall shelves (static) with the radio
    for z in (1.0, 1.5):
        C.box(f"ws_lshelf{z}", (0.35, 1.6, 0.03), loc=w((-2.8, 0.9, z)), m=sh_m, bevel=0.003, coll=coll)
    out["radio_spot"] = Vector(w((-2.8, 0.7, 1.02)))
    for i in range(5):
        C.cyl(f"ws_can{i}", 0.05, 0.12, loc=w((-2.8, 0.25 + i * 0.12, 1.57)),
              m=[M("p_red"), M("p_blue"), m["steel"], M("p_yel"), M("p_green")][i], coll=coll)
    # ---- armchair + crate bed
    ch_m = M("chair_m", (0.35, 0.12, 0.1), rough=0.9, dirt=0.5, bump=0.2)
    chair = C.empty("ws_chair", loc=w((-1.9, -1.3, 0)), rot=(0, 0, 35), coll=coll)
    C.box("ws_chseat", (0.75, 0.7, 0.18), loc=(0, 0, 0.4), m=ch_m, parent=chair, bevel=0.06, coll=coll)
    C.box("ws_chback", (0.75, 0.2, 0.7), loc=(0, 0.32, 0.75), m=ch_m, parent=chair, bevel=0.06, coll=coll)
    for sx in (-1, 1):
        C.box(f"ws_charm{sx}", (0.15, 0.7, 0.3), loc=(0.36 * sx, 0, 0.6), m=ch_m, parent=chair, bevel=0.05,
              coll=coll)
    C.box("ws_chbase", (0.7, 0.65, 0.3), loc=(0, 0, 0.15), m=ch_m, parent=chair, bevel=0.03, coll=coll)
    out["chair"] = chair
    crate = C.empty("ws_bedcrate", loc=w((-0.6, -1.6, 0)), rot=(0, 0, -10), coll=coll)
    for (sx, sy, wx, wy) in ((0, -0.25, 0.6, 0.03), (0, 0.25, 0.6, 0.03), (-0.3, 0, 0.03, 0.5), (0.3, 0, 0.03, 0.5)):
        C.box(f"ws_crate{sx}{sy}", (wx, wy, 0.25), loc=(sx, sy, 0.125), m=m["wood"], parent=crate, bevel=0.003,
              coll=coll)
    C.box("ws_blanket", (0.55, 0.45, 0.06), loc=(0, 0, 0.1), m=M("blanket", (0.5, 0.25, 0.2), rough=0.95,
                                                             dirt=0.4, bump=0.3), parent=crate, bevel=0.03,
          coll=coll)
    out["crate"] = crate
    # ---- fascinating gadgets
    # orrery on the bench (right end)
    orr = C.empty("ws_orrery", loc=w((1.35, 1.75, 0.96)), coll=coll)
    C.cyl("ws_orrbase", 0.08, 0.04, loc=(0, 0, 0.02), m=M("brass"), parent=orr, coll=coll)
    C.cyl("ws_orrpole", 0.008, 0.3, loc=(0, 0, 0.17), m=M("brass"), parent=orr, coll=coll)
    sunb = C.emission("ws_orrsun", (1.0, 0.7, 0.3), 12)
    C.sphere("ws_orrsun", 0.045, loc=(0, 0, 0.34), m=sunb, parent=orr, coll=coll)
    orr_arms = []
    for k, (r, pm) in enumerate(((0.12, M("p_blue")), (0.2, M("p_red")), (0.28, m["steel"]))):
        arm = C.empty(f"ws_orrarm{k}", loc=(0, 0, 0.34 - 0.03 * (k + 1)), parent=orr, coll=coll)
        C.cyl(f"ws_orrrod{k}", 0.003, r, loc=(r / 2, 0, 0), rot=(0, 90, 0), m=M("brass"), parent=arm, coll=coll)
        C.sphere(f"ws_orrpl{k}", 0.02 + 0.006 * k, loc=(r, 0, 0), m=pm, parent=arm, coll=coll)
        orr_arms.append((arm, 1.2 / (k + 1)))
    out["orrery_arms"] = orr_arms
    # tesla coil (left bench end)
    tes = C.empty("ws_tesla", loc=w((-0.95, 2.2, 0.96)), coll=coll)
    C.cyl("ws_tesbase", 0.07, 0.05, loc=(0, 0, 0.025), m=M("dark_metal"), parent=tes, coll=coll)
    C.cyl("ws_tescoil", 0.035, 0.3, loc=(0, 0, 0.2), m=M("brass"), parent=tes, coll=coll)
    tesm = C.emission("ws_testop", (0.5, 0.7, 1.0), 3)
    C.torus("ws_testorus", 0.06, 0.025, loc=(0, 0, 0.37), m=M("chrome"), parent=tes, coll=coll)
    spark = C.sphere("ws_tesspark", 0.03, loc=(0, 0, 0.37), m=tesm, parent=tes, coll=coll)
    tes_l = P.point_light("ws_teslight", w((-0.95, 2.1, 1.4)), 0, (0.5, 0.7, 1.0), 0.05, coll=coll)
    out.update(tesla_m=tesm, tesla_light=tes_l)
    # caged tin bird (hanging near the window)
    cage = C.empty("ws_cage", loc=w((-2.3, -0.2, 1.9)), coll=coll)
    cg = C.lathe("ws_cagebars", [(0.15, 0.0), (0.15, 0.25), (0.08, 0.33), (0.001, 0.35)], m=M("brass"),
                 parent=cage, coll=coll, seg=12)
    cg.modifiers.new("wire", "WIREFRAME").thickness = 0.004
    C.curve_tube("ws_cagehook", [w((-2.3, -0.2, 2.25)), w((-2.3, -0.2, 2.6))], radius=0.004, m=M("cable_m"),
                 coll=coll)
    bird = C.empty("ws_bird", loc=(0, 0, 0.1), parent=cage, coll=coll)
    bm_ = M("bird_tin", (0.8, 0.6, 0.2), metal=0.9, rough=0.3, rust=0.15)
    C.sphere("ws_birdbody", 0.04, loc=(0, 0, 0.0), scale=(0.8, 1.3, 0.8), m=bm_, parent=bird, coll=coll)
    C.sphere("ws_birdhead", 0.025, loc=(0, -0.045, 0.03), m=bm_, parent=bird, coll=coll)
    C.cyl("ws_birdbeak", 0.008, 0.025, loc=(0, -0.075, 0.03), rot=(90, 0, 0), r2=0.001, m=M("beak_m"), parent=bird,
          coll=coll)
    wings = []
    for sx in (-1, 1):
        wp = C.empty(f"ws_wingp{sx}", loc=(0.025 * sx, 0, 0.01), parent=bird, coll=coll)
        C.box(f"ws_wing{sx}", (0.06, 0.04, 0.004), loc=(0.03 * sx, 0, 0), m=bm_, parent=wp, bevel=0.0, coll=coll)
        wings.append((wp, sx))
    out["bird_wings"] = wings
    out["bird"] = bird
    # ceiling mobile of tin fish
    mob = C.empty("ws_mobile", loc=w((-1.0, -0.3, 2.3)), coll=coll)
    for k in range(5):
        a = 2 * math.pi * k / 5
        C.curve_tube(f"ws_mobstr{k}", [(0.3 * math.cos(a), 0.3 * math.sin(a), 0),
                                       (0.3 * math.cos(a), 0.3 * math.sin(a), -0.2 - 0.05 * k)], radius=0.002,
                     m=M("cable_m"), parent=mob, coll=coll)
        C.sphere(f"ws_fish{k}", 0.04, loc=(0.3 * math.cos(a), 0.3 * math.sin(a), -0.22 - 0.05 * k),
                 scale=(0.4, 1.4, 0.8), m=[M("p_blue"), M("p_red"), M("p_yel"), m["steel"], M("p_green")][k],
                 parent=mob, coll=coll)
    C.cyl("ws_mobbar", 0.004, 0.65, loc=(0, 0, 0), rot=(0, 90, 0), m=M("brass"), parent=mob, coll=coll)
    out["mobile"] = mob
    # cables along ceiling
    for i in range(5):
        a = w((-2.8 + i * 1.2, -2.0, 2.55)); b = w((-2.4 + i * 1.1, 2.2, 2.5))
        C.curve_tube(f"ws_cable{i}", C.sag_points(a, b, 0.3, 6), radius=0.012, m=M("cable_m"), coll=coll)
    # door
    C.box("ws_door", (0.9, 0.05, 2.0), loc=w((1.6, -2.5, 1.0)), m=m["wood"], bevel=0.01, coll=coll)
    # junk on floor
    for i, (k, x, y) in enumerate((("tire", 2.5, -1.8), ("barrel_rust", -2.5, -2.0), ("crate", 1.0, -2.1),
                                   ("tv", 2.6, 0.9))):
        P.scrap_item(k, w((x, y, 0.1 if k == "tire" else (0.44 if k == "barrel_rust" else 0.25))),
                     (90 if k == "tire" else 0, 0, rnd.uniform(0, 360)), 0.8, coll)
    # build slots: where Funke's parts appear on the bench (montage)
    out["bench_spot"] = Vector(w((0.2, 1.8, 0.96)))
    out["moon"] = P.point_light("ws_moon", w((-3.5, -0.8, 1.6)), 30, (0.4, 0.55, 1.0), 0.5, coll=coll,
                                kind="AREA", rot=(0, -90, 0))
    out["moon"].data.size = 1.0
    return out


def animate_workshop_gadgets(ws, f0, f1):
    for arm, speed in ws["orrery_arms"]:
        S.spin(arm, f0, f1, axis=2, turns_per_sec=speed * 0.3)
    S.spin(ws["mobile"], f0, f1, axis=2, turns_per_sec=0.05)
    # bird flaps in bursts
    f = f0
    i = 0
    while f < f1:
        burst = (i % 3 == 0)
        for wp, sx in ws["bird_wings"]:
            wp.rotation_euler = (0, math.radians(40 * sx if burst else 0), 0)
            wp.keyframe_insert("rotation_euler", frame=f)
            wp.rotation_euler = (0, math.radians(-30 * sx if burst else 0), 0)
            wp.keyframe_insert("rotation_euler", frame=f + 2)
        f += 4 if burst else 30
        i += 1
    # tesla flicker
    sock = C.emit_socket(ws["tesla_m"])
    f = f0
    rnd = C.R.__class__(3)
    while f < f1:
        A.key_socket(sock, f, rnd.choice([2, 3, 4, 15, 3]))
        ws["tesla_light"].data.energy = rnd.choice([0, 0, 2, 8])
        ws["tesla_light"].data.keyframe_insert("energy", frame=f)
        f += rnd.randint(2, 7)


# =========================================================================== VILLAGE
def shack(name, loc, w, d, h, yaw, coll, rnd, door=True, window=True, lit=False):
    m = P.mats()
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    wall_m = rnd.choice([m["corr1"], m["corr2"], m["corr3"], M("v_plaster", (0.55, 0.48, 0.38), rough=0.9,
                                                                   dirt=0.6, bump=0.3),
                         M("v_plaster2", (0.4, 0.45, 0.42), rough=0.9, dirt=0.6, bump=0.3)])
    C.box(name + "_body", (w, d, h), loc=(0, 0, h / 2), m=wall_m, parent=root, bevel=0.02, coll=coll)
    roof = P.corrugated(name + "_roof", w + 0.5, d + 0.6, (0, -d / 2 - 0.3, h + 0.05), (0, 0, 0),
                        rnd.choice([m["corr1"], m["corr2"]]), coll=coll)
    roof.rotation_euler = (math.radians(-90 + rnd.uniform(4, 9)), 0, 0)
    roof.location = (0, d / 2 + 0.3, h + 0.05)
    roof.parent = root
    if door:
        C.box(name + "_door", (0.8, 0.06, 1.9), loc=(rnd.uniform(-w / 4, w / 4), -d / 2 - 0.01, 0.95),
              m=rnd.choice([m["wood"], M("p_blue"), M("p_green")]), parent=root, bevel=0.01, coll=coll)
    if window:
        wm = C.emission("v_winlit", (1.0, 0.7, 0.35), 2.0) if lit else M("v_windark", (0.05, 0.06, 0.07),
                                                                          rough=0.2)
        x = w / 3 if rnd.random() < 0.5 else -w / 3
        C.box(name + "_win", (0.6, 0.05, 0.5), loc=(x, -d / 2 - 0.01, 1.5), m=wm, parent=root, bevel=0.0,
              coll=coll)
        C.box(name + "_winf", (0.7, 0.07, 0.06), loc=(x, -d / 2 - 0.02, 1.22), m=m["wood"], parent=root, bevel=0,
              coll=coll)
    # awning made from a billboard fragment
    if rnd.random() < 0.5:
        aw = C.box(name + "_awning", (w * 0.8, 1.0, 0.03), loc=(0, -d / 2 - 0.45, 2.1), rot=(-15, 0, 0),
                   m=rnd.choice([M("p_red"), M("p_yel"), M("p_blue")]), parent=root, bevel=0, coll=coll)
    return root


def build_village(coll):
    C.set_coll(coll)
    O = VILLAGE
    w = lambda p: _w(p, O)
    m = P.mats()
    out = {}
    gm = P.ground_mat("village_ground", (0.36, 0.29, 0.2), (0.18, 0.14, 0.1))
    P.terrain("village_terrain", size=400, res=80, strength=4.0, m=gm, coll=coll, loc=O, flat_radius=40)
    rnd = C.R.__class__(21)
    # ring of shacks around square (radius ~11), with an alley gap at +X (east) and entrance at -Y (south)
    k = 0
    for i in range(16):
        a = 2 * math.pi * i / 16
        if abs(math.sin(a)) < 0.25 and math.cos(a) > 0:  # east alley
            continue
        if abs(math.cos(a)) < 0.25 and math.sin(a) < 0:  # south entrance
            continue
        r = 11.5 + rnd.uniform(-0.5, 1.0)
        pos = w((math.cos(a) * r, math.sin(a) * r, 0))
        yaw = math.atan2(math.sin(a), math.cos(a)) - math.pi / 2  # front faces the centre
        yaw = a + math.pi / 2
        shack(f"v_shack{k}", pos, rnd.uniform(3.5, 5.0), rnd.uniform(3, 4), rnd.uniform(2.4, 3.4), yaw, coll, rnd,
              lit=rnd.random() < 0.4)
        k += 1
    # second ring, taller / stacked
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        r = 17 + rnd.uniform(0, 3)
        pos = w((math.cos(a) * r, math.sin(a) * r, 0))
        if abs(math.sin(a)) < 0.2 and math.cos(a) > 0:
            continue
        shack(f"v_back{i}", pos, rnd.uniform(4, 6), rnd.uniform(3.5, 5), rnd.uniform(3.5, 5.5), a + math.pi / 2,
              coll, rnd, door=False)
    # alley to the east: two rows of shacks
    for i in range(5):
        for s in (-1, 1):
            shack(f"v_alley{i}{s}", w((15 + i * 4.5, s * 3.6, 0)), 4.0, 3.0, rnd.uniform(2.6, 3.4),
                  math.radians(0 if s > 0 else 180), coll, rnd, lit=False)
    out["alley_start"] = Vector(w((12, 0, 0)))
    out["alley_end"] = Vector(w((36, 0, 0)))
    # laundry lines in the alley and across the square
    cloth_cols = [(0.7, 0.2, 0.15), (0.2, 0.4, 0.6), (0.8, 0.75, 0.6), (0.3, 0.5, 0.25), (0.8, 0.6, 0.1)]
    laundry = []
    for i in range(4):
        x = 16 + i * 5
        a = w((x, -2.1, 3.0)); b = w((x + 1.0, 2.1, 3.0))
        pts = C.sag_points(a, b, 0.35, 8)
        C.curve_tube(f"v_line{i}", pts, radius=0.006, m=M("rope_m", (0.6, 0.55, 0.45)), coll=coll)
        for j in range(5):
            t = (j + 0.5) / 5
            p = Vector(a).lerp(Vector(b), t)
            p.z -= 0.35 * 4 * t * (1 - t)
            cl = C.box(f"v_cloth{i}{j}", (0.7, 0.02, rnd.uniform(0.6, 1.1)), loc=p - Vector((0, 0, 0.4)),
                       rot=(0, 0, 90 + math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90),
                       m=M(f"cloth{(i + j) % 5}", cloth_cols[(i + j) % 5], rough=0.95, dirt=0.3, bump=0.1),
                       bevel=0, coll=coll)
            cl.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]))
            laundry.append(cl)
    out["laundry"] = laundry
    # string lights across square
    for i in range(4):
        a1 = 2 * math.pi * i / 4 + 0.4
        p1 = w((math.cos(a1) * 10, math.sin(a1) * 10, 3.6))
        p2 = w((math.cos(a1 + math.pi) * 10, math.sin(a1 + math.pi) * 10, 3.6))
        P.string_lights(f"v_lights{i}", p1, p2, n=18, sag=1.0, coll=coll)
    for i in range(4):
        a1 = 2 * math.pi * i / 4 + 0.4
        C.cyl(f"v_pole{i}", 0.06, 4.0, loc=w((math.cos(a1) * 10, math.sin(a1) * 10, 2.0)), m=m["wood"], coll=coll)
        C.cyl(f"v_pole{i}b", 0.06, 4.0, loc=w((math.cos(a1 + math.pi) * 10, math.sin(a1 + math.pi) * 10, 2.0)),
              m=m["wood"], coll=coll)
    # dead fountain with a TV in it
    C.cyl("v_fountain", 1.6, 0.5, loc=w((0, 0, 0.25)), m=m["concrete"], coll=coll, verts=32)
    C.cyl("v_fountain_in", 1.45, 0.1, loc=w((0, 0, 0.46)), m=M("dry_mud", (0.2, 0.16, 0.1), rough=1.0), coll=coll,
          verts=32)
    C.cyl("v_fountain_col", 0.25, 1.4, loc=w((0, 0, 0.9)), m=m["concrete"], coll=coll)
    tv = P.scrap_item("tv", w((0, 0, 1.85)), (0, 0, 20), 1.0, coll)
    # market stalls
    stalls = []
    for i, (x, y, yaw, col) in enumerate(((-5, 4, 200, (0.6, 0.15, 0.1)), (5, 5, 160, (0.15, 0.35, 0.55)),
                                          (-6, -3, 290, (0.7, 0.55, 0.1)), (6, -3.5, 70, (0.25, 0.45, 0.25)))):
        yaw = math.degrees(math.atan2(-x, y))  # front (-Y local) faces the square centre
        st = C.empty(f"v_stall{i}", loc=w((x, y, 0)), rot=(0, 0, yaw), coll=coll)
        for sx in (-1, 1):
            for sy in (-1, 1):
                C.cyl(f"v_stallp{i}{sx}{sy}", 0.04, 2.3, loc=(1.1 * sx, 0.6 * sy, 1.15), m=m["wood"], parent=st,
                      coll=coll)
        C.box(f"v_stallt{i}", (2.3, 1.1, 0.06), loc=(0, 0, 0.85), m=m["wood"], parent=st, bevel=0.01, coll=coll)
        C.box(f"v_stallf{i}", (2.3, 0.04, 0.8), loc=(0, -0.55, 0.45), m=M(f"stallcloth{i}", col, rough=0.9,
                                                                        dirt=0.4), parent=st, bevel=0, coll=coll)
        aw = C.box(f"v_stalla{i}", (2.6, 1.6, 0.03), loc=(0, -0.1, 2.35), rot=(-12, 0, 0),
                   m=M(f"stallaw{i}", col, rough=0.9, dirt=0.3), parent=st, bevel=0, coll=coll)
        stalls.append(st)
        # goods
        for j in range(6):
            kind = ["tv", "crate", "drum", "gear", "barrel_b", "tire"][(i + j) % 6]
            o = P.scrap_item(kind, (0, 0, 0), (0, 0, rnd.uniform(0, 360)), 0.35, coll)
            o.parent = st
            o.location = (-0.9 + j * 0.36, rnd.uniform(-0.2, 0.2), 0.95)
    # billboard-text awning pieces
    C.text("v_bill1", "PROGRESS", size=0.35, loc=w((-5, 4.62, 2.5)), rot=(78, 0, 180), m=M("bill_white", (0.85, 0.8,
                                                                                                        0.7)),
           coll=coll)
    out["stalls"] = stalls
    out["radio_stall"] = stalls[1]
    # bench with sleeping old man spot + cat
    bench_root = C.empty("v_bench", loc=w((-3.0, -7.5, 0)), rot=(0, 0, 10), coll=coll)
    C.box("v_benchseat", (1.8, 0.45, 0.06), loc=(0, 0, 0.45), m=m["wood"], parent=bench_root, bevel=0.01,
          coll=coll)
    C.box("v_benchback", (1.8, 0.06, 0.4), loc=(0, 0.22, 0.75), rot=(-10, 0, 0), m=m["wood"], parent=bench_root,
          bevel=0.01, coll=coll)
    for sx in (-0.8, 0.8):
        C.box(f"v_benchleg{sx}", (0.06, 0.4, 0.45), loc=(sx, 0, 0.22), m=m["dark"], parent=bench_root, bevel=0,
              coll=coll)
    out["bench"] = bench_root
    # posters: REPORT OBSOLETE DEVICES (with the Erfasser silhouette)
    poster_wall = C.box("v_posterwall", (3.0, 0.3, 2.4), loc=w((-8.5, -7.0, 1.2)), rot=(0, 0, 40),
                        m=m["concrete"], bevel=0.02, coll=coll)
    for j in range(3):
        pr = C.empty(f"v_poster{j}", loc=w((-8.5, -7.0, 1.4)), rot=(0, 0, 40), coll=coll)
        x = -0.9 + j * 0.9
        C.box(f"v_posterp{j}", (0.75, 0.01, 1.05), loc=(x, -0.16, 0.05), rot=(0, j * 3 - 3, 0),
              m=M("poster_paper", (0.82, 0.78, 0.65), rough=0.9, dirt=0.5), parent=pr, bevel=0, coll=coll)
        C.text(f"v_postert{j}", "REPORT\nOBSOLETE\nDEVICES", size=0.09, loc=(x, -0.17, 0.35), rot=(90, 0, 0),
               m=M("poster_red", (0.6, 0.05, 0.03)), parent=pr, coll=coll)
        # tophat silhouette
        C.box(f"v_posterhat{j}", (0.18, 0.005, 0.2), loc=(x, -0.168, 0.0), m=M("ink_black", (0.01, 0.01, 0.01)),
              parent=pr, bevel=0, coll=coll)
        C.box(f"v_posterbrim{j}", (0.3, 0.005, 0.03), loc=(x, -0.168, -0.1), m=M("ink_black"), parent=pr, bevel=0,
              coll=coll)
        C.box(f"v_posterslit{j}", (0.14, 0.005, 0.025), loc=(x, -0.169, 0.03), m=M("poster_red"), parent=pr,
              bevel=0, coll=coll)
        C.text(f"v_postert2{j}", "IT'S THE LAW.", size=0.06, loc=(x, -0.17, -0.3), rot=(90, 0, 0),
               m=M("ink_black"), parent=pr, coll=coll)
    # broken hologram billboard (flickers) on a tall pole
    C.cyl("v_holopole", 0.12, 7.0, loc=w((6, 12, 3.5)), m=m["dark"], coll=coll)
    holo_m = C.emission("v_holo", (0.3, 0.9, 1.0), 2.0)
    holo = C.box("v_holo", (4.0, 0.02, 2.2), loc=w((6, 11.8, 7.5)), m=holo_m, bevel=0, coll=coll)
    C.text("v_holotxt", "THE CITY\nWANTS YOU\nNEW", size=0.45, loc=w((6, 11.75, 7.6)), rot=(90, 0, 0),
           m=C.emission("v_holotxt", (1.0, 1.0, 1.0), 4.0), coll=coll)
    out["holo_m"] = holo_m
    # water tower in the back
    wt = C.empty("v_watertower", loc=w((-14, 20, 0)), coll=coll)
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.limb(f"v_wtleg{sx}{sy}", (1.6 * sx, 1.6 * sy, 0), (1.1 * sx, 1.1 * sy, 8), 0.08, m=m["rust"], parent=wt,
                   coll=coll)
    C.cyl("v_wttank", 2.0, 2.6, loc=(0, 0, 9.3), m=M("wt_m", (0.5, 0.45, 0.4), metal=0.5, rust=0.6), parent=wt,
          coll=coll)
    C.cyl("v_wtroof", 2.2, 1.0, loc=(0, 0, 11.1), r2=0.1, m=m["rust"], parent=wt, coll=coll)
    # cable for drone pigeons across the square
    a = w((-12, 6, 5.0)); b = w((12, 8, 5.2))
    out["pigeon_wire"] = C.sag_points(a, b, 0.6, 12)
    C.curve_tube("v_pigeonwire", out["pigeon_wire"], radius=0.01, m=M("cable_m"), coll=coll)
    # bucket of bolts and barrel in alley
    out["bucket_spot"] = Vector(w((20, -1.5, 0)))
    C.cyl("v_bucket", 0.15, 0.3, loc=out["bucket_spot"] + Vector((0, 0, 0.15)), r2=0.18, m=m["steel"], coll=coll)
    out["barrel_spot"] = Vector(w((27, 1.6, 0)))
    for i in range(30):
        P.scrap_item(rnd.choice(["crate", "barrel_rust", "tire", "drum"]),
                     w((rnd.uniform(-30, 30), rnd.uniform(14, 30), 0.3)), (0, 0, rnd.uniform(0, 360)), 1.0, coll)
    return out


# =========================================================================== DEPOT
def build_depot(coll):
    C.set_coll(coll)
    m = P.mats()
    out = {}
    O = DEPOT
    w = lambda p: _w(p, O)
    gm = P.ground_mat("depot_ground", (0.2, 0.2, 0.2), (0.08, 0.08, 0.09))
    P.terrain("depot_terrain", size=400, res=60, strength=1.0, m=gm, coll=coll, loc=O, flat_radius=60)
    conc = M("depot_concrete", (0.32, 0.32, 0.33), rough=0.85, dirt=0.6, scale=0.8, bump=0.3)
    # exterior wall along X at y=+6 with gate sign
    C.box("d_wall", (80, 1.0, 9), loc=w((0, 6, 0)), origin="bottom", m=conc, bevel=0.05, coll=coll)
    for i in range(9):
        C.box(f"d_wallpillar{i}", (1.2, 1.4, 9.5), loc=w((-36 + i * 9, 5.8, 0)), origin="bottom", m=conc, bevel=0.05,
              coll=coll)
    sign = C.box("d_sign", (12, 0.2, 1.6), loc=w((0, 4.9, 7.0)), m=M("d_sign_m", (0.04, 0.07, 0.15), metal=0.4,
                                                                     rough=0.3), bevel=0.02, coll=coll)
    C.text("d_signtxt", "CITY RECLAMATION DEPOT 4", size=0.7, loc=w((0, 4.78, 7.15)), rot=(90, 0, 0),
           m=C.emission("d_signtxt", (0.9, 0.95, 1.0), 3.0), coll=coll)
    C.text("d_signtxt2", "Out with the old.", size=0.35, loc=w((0, 4.78, 6.5)), rot=(90, 0, 0),
           m=C.emission("d_signtxt2", (1.0, 0.7, 0.2), 2.0), coll=coll)
    # chain-link fence in front at y=0 with a hole at x=-4
    fence_m = M("fence_m", (0.4, 0.4, 0.42), metal=1.0, rough=0.4, rust=0.3)
    for i in range(14):
        x = -26 + i * 4
        C.cyl(f"d_fpost{i}", 0.05, 3.0, loc=w((x, 0, 1.5)), m=fence_m, coll=coll, verts=8)
        if abs(x + 4) < 1:
            continue
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=16, y_segments=12, size=1.0)
        me = bpy.data.meshes.new(f"d_fence{i}")
        bm.to_mesh(me); bm.free()
        ob = C.new_obj(f"d_fence{i}", me, w((x + 2, 0, 1.5)), (90, 45, 0), (1.4, 1.06, 1.0), mat_=fence_m,
                       coll=coll)
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.scale = (2.0, 1.5, 1)
        wf = ob.modifiers.new("wire", "WIREFRAME"); wf.thickness = 0.015
    # the hole: two bent half panels
    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=8, y_segments=12, size=1.0)
        me = bpy.data.meshes.new(f"d_hole{sx}")
        bm.to_mesh(me); bm.free()
        ob = C.new_obj(f"d_hole{sx}", me, w((-4 + 1.5 * sx, -0.3, 1.6)), (90, 0, 35 * sx), (0.5, 1.4, 1),
                       mat_=fence_m, coll=coll)
        ob.modifiers.new("wire", "WIREFRAME").thickness = 0.015
    out["hole"] = Vector(w((-4, 0, 0)))
    # floodlight towers
    for i, x in enumerate((-20, 14)):
        C.cyl(f"d_ftower{i}", 0.2, 14, loc=w((x, 3, 7)), m=m["dark"], coll=coll)
        C.box(f"d_fhead{i}", (1.4, 0.5, 0.8), loc=w((x, 2.6, 14)), m=m["dark"], bevel=0.05, coll=coll)
        C.box(f"d_flens{i}", (1.2, 0.05, 0.6), loc=w((x, 2.33, 14)),
              m=C.emission("d_flood", (0.85, 0.92, 1.0), 25), bevel=0.0, coll=coll)
        P.point_light(f"d_flood{i}", w((x, 2.0, 14)), 30000, (0.8, 0.9, 1.0), 0.5, coll=coll, kind="SPOT", spot=70,
                      rot=(60, 0, 180 + (20 if x < 0 else -20)))
    # chimneys with smoke behind wall
    for i, x in enumerate((-12, 0, 18)):
        C.cyl(f"d_chimney{i}", 1.4, 30, loc=w((x, 20, 15)), r2=1.1, m=conc, coll=coll)
        C.cyl(f"d_chimband{i}", 1.25, 1.0, loc=w((x, 20, 27)), m=M("p_red"), coll=coll)
    out["chimneys"] = [Vector(w((x, 20, 30.5))) for x in (-12, 0, 18)]
    # ------------------------------------------------------------------ hall interior
    H = HALL
    h = lambda p: _w(p, H)
    C.box("h_floor", (44, 24, 0.2), loc=h((0, 0, -0.1)), m=M("hall_floor", (0.25, 0.25, 0.26), rough=0.7,
                                                             dirt=0.6, scale=0.5, bump=0.2), bevel=0, coll=coll)
    for sy in (-12, 12):
        C.box(f"h_wall{sy}", (44, 0.5, 12), loc=h((0, sy, 0)), origin="bottom", m=conc, bevel=0, coll=coll)
    for sx in (-22, 22):
        C.box(f"h_walle{sx}", (0.5, 24, 12), loc=h((sx, 0, 0)), origin="bottom", m=conc, bevel=0, coll=coll)
    C.box("h_ceiling", (44, 24, 0.3), loc=h((0, 0, 12)), m=conc, bevel=0, coll=coll)
    # high windows (cold)
    for i in range(8):
        C.box(f"h_win{i}", (3.0, 0.1, 1.5), loc=h((-17 + i * 5, 11.7, 9.5)),
              m=C.emission("h_winm", (0.3, 0.45, 0.8), 1.5), bevel=0, coll=coll)
    # roof trusses
    for i in range(9):
        C.box(f"h_truss{i}", (0.3, 24, 0.6), loc=h((-20 + i * 5, 0, 11.4)), m=m["dark"], bevel=0, coll=coll)
    # conveyor along X (z top 1.0) from x=-20 to x=8
    conv_m = M("conveyor_belt", (0.05, 0.05, 0.05), rough=0.8, dirt=0.3, bump=0.5, scale=10)
    belt = C.box("h_belt", (28, 1.8, 0.1), loc=h((-6, 0, 0.95)), m=conv_m, bevel=0.01, coll=coll)
    C.box("h_beltframe", (28.4, 2.1, 0.3), loc=h((-6, 0, 0.75)), m=M("p_yel"), bevel=0.02, coll=coll)
    for i in range(10):
        C.box(f"h_beltleg{i}", (0.15, 1.8, 0.6), loc=h((-19 + i * 2.9, 0, 0.3)), m=m["dark"], bevel=0, coll=coll)
    out["belt_y"] = H.y
    out["belt_z"] = H.z + 1.0
    # giant press at x=+11
    press_m = M("press_m", (0.5, 0.38, 0.08), metal=0.6, rough=0.4, rust=0.35)
    for sy in (-2.0, 2.0):
        C.box(f"h_pressp{sy}", (1.2, 0.8, 9), loc=h((11, sy, 0)), origin="bottom", m=press_m, bevel=0.05, coll=coll)
    C.box("h_presstop", (2.0, 5.0, 1.5), loc=h((11, 0, 9.0)), m=press_m, bevel=0.05, coll=coll)
    C.box("h_pressbed", (3.0, 3.6, 1.0), loc=h((11, 0, 0.5)), m=m["dark"], bevel=0.02, coll=coll)
    ram = C.empty("h_ram", loc=h((11, 0, 8.2)), coll=coll)
    C.box("h_ramblock", (2.6, 3.4, 1.4), loc=(0, 0, -0.7), m=M("ram_m", (0.3, 0.3, 0.32), metal=0.9, rough=0.35,
                                                                   rust=0.2), parent=ram, bevel=0.03, coll=coll)
    for sy in (-0.8, 0.8):
        C.cyl(f"h_piston{sy}", 0.2, 3.0, loc=(0, sy, 1.5), m=M("chrome"), parent=ram, coll=coll)
    # hazard stripes on ram
    C.box("h_ramstripe", (2.62, 3.42, 0.2), loc=(0, 0, -1.3), m=M("hazard", (0.8, 0.6, 0.05), rough=0.5), parent=ram,
          bevel=0, coll=coll)
    beacon_m = C.emission("h_beacon", (1.0, 0.1, 0.02), 0.0)
    C.sphere("h_beacon", 0.25, loc=h((11, -2.5, 9.9)), m=beacon_m, coll=coll)
    beacon_l = P.point_light("h_beaconl", h((11, -3.0, 9.6)), 0, (1, 0.1, 0.02), 0.2, coll=coll)
    out.update(ram=ram, beacon_m=beacon_m, beacon_light=beacon_l)
    out["press_x"] = H.x + 11
    # crushed bales pile
    for i in range(14):
        rr = C.R.__class__(i)
        C.box(f"h_bale{i}", (1.0, 1.0, 0.8), loc=h((14.5 + rr.uniform(0, 4), rr.uniform(-4, 4), 0.4 + (i % 3) * 0.8)),
              rot=(0, 0, rr.uniform(0, 90)), m=m["rust"], bevel=0.05, coll=coll)
    # control box on platform at x=7, y=-3
    C.box("h_platform", (2.0, 1.6, 1.4), loc=h((7, -2.6, 0.7)), m=m["dark"], bevel=0.02, coll=coll)
    cb = C.box("h_controlbox", (0.8, 0.5, 1.0), loc=h((7, -2.6, 1.9)), m=M("cbox_m", (0.3, 0.35, 0.3), metal=0.5,
                                                                         rust=0.3), bevel=0.02, coll=coll)
    out["control_box"] = Vector(h((7, -2.6, 1.4)))
    cb_lights = []
    for i, col in enumerate(((1, 0.1, 0.05), (0.1, 1, 0.1), (1, 0.8, 0.1))):
        lm = C.emission(f"h_cbl{i}", col, 4.0)
        cb_lights.append(lm)
        C.sphere(f"h_cbl{i}", 0.04, loc=h((6.8 + i * 0.2, -2.86, 2.15)), m=lm, coll=coll)
    out["cb_lights"] = cb_lights
    # catwalk along conveyor at y=+2.6, z=3.5 with railing and stairs at x=-18
    C.box("h_catwalk", (26, 1.2, 0.1), loc=h((-5, 2.8, 3.5)), m=M("grate_m", (0.3, 0.3, 0.3), metal=0.8), bevel=0,
          coll=coll)
    for i in range(14):
        C.cyl(f"h_catpost{i}", 0.03, 1.0, loc=h((-17.5 + i * 1.9, 2.25, 4.05)), m=M("p_yel"), coll=coll, verts=6)
        C.cyl(f"h_catsup{i}", 0.06, 3.5, loc=h((-17.5 + i * 1.9, 3.3, 1.75)), m=m["dark"], coll=coll, verts=6)
    C.box("h_catrail", (26, 0.05, 0.05), loc=h((-5, 2.25, 4.55)), m=M("p_yel"), bevel=0, coll=coll)
    for i in range(10):
        C.box(f"h_stair{i}", (0.3, 1.0, 0.1), loc=h((-19 - i * 0.3, 2.8, 3.5 - i * 0.35)), m=M("grate_m"), bevel=0,
              coll=coll)
    out["catwalk_z"] = 3.55
    # sodium lamps
    lamps = []
    for i in range(5):
        p = h((-16 + i * 7, 0, 10.5))
        C.cyl(f"h_lampshade{i}", 0.5, 0.4, loc=p, r2=0.15, m=m["dark"], coll=coll)
        C.sphere(f"h_lampbulb{i}", 0.15, loc=Vector(p) - Vector((0, 0, 0.25)),
                 m=C.emission("h_sodium", (1.0, 0.55, 0.15), 20), coll=coll)
        lamps.append(P.point_light(f"h_lamp{i}", Vector(p) - Vector((0, 0, 0.4)), 2500, (1.0, 0.55, 0.2), 0.3,
                                   coll=coll, kind="SPOT", spot=100, rot=(0, 0, 0)))
    out["lamps"] = lamps
    # cages of old machines waiting along the far wall
    for i in range(6):
        cage_with_machine(f"h_wait{i}", h((-18 + i * 3, -8, 0)), coll, kind=i % 3, seed=i)
    # hole in the hall's back wall leading out (escape route)
    out["exit"] = Vector(h((-21, -6, 0)))
    return out


def cage(name, loc, coll, size=(1.1, 1.1, 1.0)):
    root = C.empty(name, loc=loc, coll=coll)
    cm = M("cage_m", (0.4, 0.4, 0.4), metal=1.0, rough=0.4, rust=0.3)
    me = C.mesh_box(name + "_bars", *size, origin="bottom")
    ob = C.new_obj(name + "_bars", me, (0, 0, 0), mat_=cm, parent=root, coll=coll)
    # subdivide to get bars then wireframe
    sd = ob.modifiers.new("sub", "SUBSURF"); sd.subdivision_type = "SIMPLE"; sd.levels = 2; sd.render_levels = 2
    wf = ob.modifiers.new("wire", "WIREFRAME"); wf.thickness = 0.025
    C.box(name + "_floor", (size[0], size[1], 0.04), loc=(0, 0, 0.02), m=M("grate_m"), parent=root, bevel=0,
          coll=coll)
    # door (front face) as separate pivot for popping open
    door_piv = C.empty(name + "_doorpiv", loc=(-size[0] / 2, -size[1] / 2 - 0.02, 0), parent=root, coll=coll)
    me2 = C.mesh_box(name + "_door", size[0], 0.02, size[2] * 0.95, origin="bottom")
    door = C.new_obj(name + "_door", me2, (size[0] / 2, 0, 0.02), mat_=cm, parent=door_piv, coll=coll)
    sd2 = door.modifiers.new("sub", "SUBSURF"); sd2.subdivision_type = "SIMPLE"; sd2.levels = 2
    door.modifiers.new("wire", "WIREFRAME").thickness = 0.025
    return root, door_piv


def cage_with_machine(name, loc, coll, kind=0, seed=0):
    root, door = cage(name, loc, coll)
    m = P.mats()
    rr = C.R.__class__(seed)
    if kind == 0:  # vacuum cleaner bot
        C.cyl(name + "_vac", 0.3, 0.25, loc=(0, 0, 0.2), m=M("p_red"), parent=root, coll=coll)
        C.sphere(name + "_vace", 0.05, loc=(0, -0.28, 0.28), m=C.emission("sad_eye", (0.4, 0.8, 1.0), 2.0),
                 parent=root, coll=coll)
    elif kind == 1:  # jukebox
        C.box(name + "_jb", (0.6, 0.45, 0.85), loc=(0, 0, 0.47), m=M("jb_m", (0.5, 0.2, 0.1), rough=0.4, rust=0.2),
              parent=root, bevel=0.1, coll=coll)
        C.box(name + "_jbg", (0.45, 0.02, 0.3), loc=(0, -0.23, 0.6), m=C.emission("jb_glow", (1, 0.6, 0.2), 1.5),
              parent=root, bevel=0.05, coll=coll)
    else:  # old quadruped (Bello's kin) - simplified
        C.box(name + "_q", (0.35, 0.5, 0.25), loc=(0, 0, 0.45), m=M("Bello_paint"), parent=root, bevel=0.05,
              coll=coll)
        C.box(name + "_qh", (0.2, 0.2, 0.18), loc=(0, -0.3, 0.6), m=M("Bello_paint"), parent=root, bevel=0.03,
              coll=coll)
        C.sphere(name + "_qe", 0.05, loc=(0, -0.41, 0.62), m=C.emission("sad_eye", (0.4, 0.8, 1.0), 2.0), parent=root, coll=coll)
        for sx in (-1, 1):
            for sy in (-1, 1):
                C.cyl(name + f"_ql{sx}{sy}", 0.025, 0.35, loc=(0.13 * sx, 0.18 * sy, 0.17), m=M("pipe_m"),
                      parent=root, coll=coll)
    return root, door
