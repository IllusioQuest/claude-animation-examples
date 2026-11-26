"""Set dressing: the small things that make the places feel lived in.

Static details are added right after the sets are built (they never touch the action paths);
animated details (smoke, fire, CCTV, moths, steam) are added once the sequence frame ranges are known.
Every detail uses its own RNG (seeded from a name), so the layout of the sets themselves is unchanged.
"""
import math
import zlib
import random
import bpy
from mathutils import Vector
import core as C
import anim as A
import props as P

M = C.mat
V = Vector
CHIMNEYS = []        # (world point, set) – smoke is added later, per sequence
SHOP_SIGNS = ["REPAIRS", "SOUP", "WATER", "PARTS", "BOOTS FIXED", "TEA", "SCRAP BOUGHT", "RADIO DOC"]
GRAFFITI = ["STILL WORKS", "FIX IT.", "MADE TO LAST", "OLD IS GOLD", "WE REMEMBER", "NO NEW!"]


def rng(name):
    return random.Random(zlib.crc32(name.encode()))


def plant(name, loc, coll, parent=None, s=1.0, rnd=None):
    rnd = rnd or rng(name)
    pot = C.cyl(name + "_pot", 0.09 * s, 0.14 * s, loc=loc, r2=0.11 * s, m=M("terracotta", (0.55, 0.25, 0.14),
                                                                            rough=0.9, dirt=0.5), parent=parent,
                coll=coll, verts=10)
    leaf = M("leaf_m", (0.12, 0.3, 0.08), rough=0.7, dirt=0.2)
    for i in range(3):
        C.sphere(f"{name}_lf{i}", 0.07 * s, loc=V(loc) + V((rnd.uniform(-0.05, 0.05) * s, rnd.uniform(-0.05, 0.05) * s,
                                                            (0.12 + rnd.uniform(0, 0.06)) * s)),
                 scale=(1, 1, 1.3), m=leaf, parent=parent, coll=coll, seg=8, rings=5)
    return pot


# =========================================================================== VILLAGE

def _face(root, name, side, w, d, fo, coll):
    """Pivot empty on a wall face: side 0 front (-y), 1 back, 2 +x, 3 -x. Its local -y points outward."""
    loc, rz = {0: ((0, -d / 2 - fo, 0), 0), 1: ((0, d / 2 + fo, 0), 180), 2: ((w / 2 + fo, 0, 0), 90),
               3: ((-w / 2 - fo, 0, 0), -90)}[side]
    return C.empty(f"{name}_face{side}", loc=loc, rot=(0, 0, rz), parent=root, coll=coll, size=0.05)


def stain(parent, name, x, z, sw, sh, m, coll, y=-0.012):
    """Soft decal on a wall (pivot space): a flattened disc with a ragged feathered edge."""
    o = C.cyl(name, 0.5, 0.002, loc=(x, y, z), rot=(90, 0, 0), m=m, parent=parent, coll=coll, verts=16)
    o.scale = (sw, sh, 1)
    o.visible_shadow = False
    return o


def window(parent, name, x, z, rnd, coll, lit=False, ww=0.55, wh=0.6, shutters=None):
    """A proper window in pivot space: frame, cross bars, glass, sill, maybe shutters and a curtain."""
    m = P.mats()
    fr = m["wood"]
    t, dp = 0.05, 0.07
    y = -dp / 2 + 0.01
    glass = C.emission("v_winlit", (1.0, 0.7, 0.35), 2.0) if lit else M("v_glass_dark", (0.04, 0.05, 0.06), rough=0.08,
                                                                       dirt=0.3, bump=0, spec=0.8)
    C.box(name + "_gl", (ww, 0.02, wh), loc=(x, 0.0, z), m=glass, parent=parent, bevel=0, coll=coll)
    for k, (sx, sz, px, pz) in enumerate(((ww + 2 * t, t, 0, wh / 2 + t / 2), (ww + 2 * t, t, 0, -wh / 2 - t / 2),
                                          (t, wh, -ww / 2 - t / 2, 0), (t, wh, ww / 2 + t / 2, 0),
                                          (0.025, wh, 0, 0), (ww, 0.025, 0, 0.04))):
        C.box(f"{name}_fr{k}", (sx, dp, sz), loc=(x + px, y, z + pz), m=fr, parent=parent, bevel=0.004, coll=coll)
    C.box(name + "_sill", (ww + 0.2, 0.13, 0.04), loc=(x, -0.06, z - wh / 2 - t - 0.02), rot=(-4, 0, 0), m=fr,
          parent=parent, bevel=0.006, coll=coll)
    if lit and rnd.random() < 0.7:  # curtain half drawn
        cm = M(f"curtain{rnd.randint(0, 2)}", [(0.6, 0.2, 0.15), (0.75, 0.65, 0.4), (0.3, 0.4, 0.55)][rnd.randint(0, 2)],
               rough=0.9, dirt=0.2)
        C.box(name + "_cur", (ww * 0.45, 0.01, wh * 0.95), loc=(x - ww * 0.27 * rnd.choice((-1, 1)), 0.03, z),
              m=cm, parent=parent, bevel=0, coll=coll)
    if shutters is None:
        shutters = rnd.random() < 0.55
    if shutters:
        sm = rnd.choice([m["paint_green"], m["paint_blue"], m["wood"], m["paint_red"]])
        for sx in (-1, 1):
            if rnd.random() < 0.15:
                continue  # one shutter lost long ago
            hinge = C.empty(f"{name}_hinge{sx}", loc=(x + sx * (ww / 2 + t), -0.04, z), parent=parent, coll=coll,
                            size=0.03)
            ang = sx * rnd.uniform(95, 165) if rnd.random() < 0.85 else sx * rnd.uniform(20, 40)
            hinge.rotation_euler = (0, math.radians(rnd.uniform(-2, 2)), math.radians(-ang))
            C.box(f"{name}_sh{sx}", (ww / 2 + 0.02, 0.025, wh + 0.08), loc=(sx * (ww / 4 + 0.01), 0, 0), m=sm,
                  parent=hinge, bevel=0.005, coll=coll)
            for b in range(3):  # slats
                C.box(f"{name}_shs{sx}{b}", (ww / 2 - 0.02, 0.012, 0.03),
                      loc=(sx * (ww / 4 + 0.01), -0.016, -wh / 3 + b * wh / 3), m=fr, parent=hinge, bevel=0, coll=coll)


def weather(root, name, w, d, h, fo, coll, rnd, plaster, door_x, win_x, lit, back, alley=False):
    """Side windows, rain streaks under sills and roof edge, a splash band at the base, bare brick where the
    plaster fell off – the walls read as old and lived-in instead of flat boxes."""
    if plaster:
        streak = M("stain_plaster", (0.09, 0.075, 0.06), rough=0.95, dirt=0.0, bump=0)
        C.soft_alpha(streak, alpha=0.55)
    else:
        streak = M("stain_rust", (0.3, 0.1, 0.03), rough=0.9, dirt=0.0, bump=0)
        C.soft_alpha(streak, alpha=0.7)
    splash = C.soft_alpha(M("stain_splash", (0.08, 0.065, 0.05), rough=1.0, dirt=0.0, bump=0), alpha=0.6)
    for side in range(4):
        L_ = w if side < 2 else d
        if side == 1 and not back and rnd.random() < 0.6:
            continue  # back walls mostly unseen
        pv = _face(root, name, side, w, d, fo, coll)
        # splash band along the base (rain hitting the mud)
        nb = max(1, int(L_ / 1.2))
        for k in range(nb):
            stain(pv, f"{name}_spl{side}{k}", -L_ / 2 + (k + 0.5) * L_ / nb, 0.18,
                  rnd.uniform(1.3, 1.8), rnd.uniform(0.35, 0.55), splash, coll)
        # streaks running down from the roof edge
        for k in range(rnd.randint(1, 3)):
            sx_ = rnd.uniform(-L_ / 2 + 0.3, L_ / 2 - 0.3)
            hh = rnd.uniform(0.6, 1.3)
            stain(pv, f"{name}_str{side}{k}", sx_, h - hh / 2 - 0.05, rnd.uniform(0.15, 0.3), hh, streak, coll)
        if side >= 2 and L_ > 1.6 and rnd.random() < 0.7:
            wx = rnd.uniform(-L_ / 4, L_ / 4)
            window(pv, f"{name}_sw{side}", wx, 1.45, rnd, coll, lit=lit and rnd.random() < 0.5, shutters=False if alley else None)
            stain(pv, f"{name}_sws{side}", wx, 0.85, 0.35, 0.7, streak, coll)
        if side == 0 and win_x is not None:
            for suf in ("_win", "_winf"):  # replace the flat placeholder window
                o = bpy.data.objects.get(name + suf)
                if o:
                    bpy.data.objects.remove(o, do_unlink=True)
            window(pv, f"{name}_fw", win_x, 1.5, rnd, coll, lit=lit, ww=0.6, wh=0.5, shutters=False if alley else None)
            stain(pv, f"{name}_fws", win_x, 0.85, 0.4, 0.7, streak, coll)
        # bare brick under fallen plaster
        if plaster and rnd.random() < 0.5:
            bx = rnd.uniform(-L_ / 2 + 0.4, L_ / 2 - 0.4)
            if side == 0 and abs(bx - door_x) < 0.8:
                continue
            bz = rnd.uniform(0.5, h - 0.6)
            brick = M("brick_m", (0.42, 0.17, 0.1), rough=0.9, dirt=0.5, bump=0.4)
            for r_ in range(rnd.randint(2, 4)):
                for c_ in range(rnd.randint(2, 4)):
                    if rnd.random() < 0.25:
                        continue
                    C.box(f"{name}_brk{side}{r_}{c_}", (0.2, 0.02, 0.075),
                          loc=(bx + c_ * 0.215 + (0.1 if r_ % 2 else 0) - 0.3, -0.006, bz + r_ * 0.09),
                          m=brick, parent=pv, bevel=0.006, coll=coll)


def shack_details(root, name, w, d, h, tilt, coll, door_x, win_x, lit, alley=False, back=False):
    """root: shack empty (front faces local -y, origin on the ground in the middle)."""
    rnd = rng(name)
    m = P.mats()
    out = 0.25 if alley else 0.4  # how far things may stick out in front (alley: the chase runs there)
    # ---- cladding: corrugated shacks get real sheets (a patchwork of panels), plaster ones trims
    body = bpy.data.objects.get(name + "_body")
    wm = body.active_material if body else None
    fo = 0.0
    if wm is not None and wm.name.startswith("p_corr"):
        fo = 0.06
        corr = [m["corr1"], m["corr2"], m["corr3"], m["rust"]]
        k = 0
        for side, (L_, place) in enumerate(((w, lambda x, j: ((x, -d / 2 - 0.025 - 0.007 * (j % 2), 0), 0.0)),
                                            (w, lambda x, j: ((-x, d / 2 + 0.025 + 0.007 * (j % 2), 0), math.pi)),
                                            (d, lambda x, j: ((w / 2 + 0.025 + 0.007 * (j % 2), x, 0), math.pi / 2)),
                                            (d, lambda x, j: ((-w / 2 - 0.025 - 0.007 * (j % 2), -x, 0), -math.pi / 2)))):
            n_ = max(1, int(round(L_ / 1.05)))
            pw = L_ / n_
            for j in range(n_):
                x = -L_ / 2 + pw * (j + 0.5)
                mat_ = wm if rnd.random() < 0.72 else rnd.choice(corr)
                hh = h - rnd.uniform(0.0, 0.12)
                (px, py, pz), rz = place(x, j)
                sh = P.corrugated(f"{name}_clad{k}", pw + 0.06, hh, (0, 0, 0), (0, 0, 0), mat_, coll=coll,
                                  depth=0.022)
                sh.parent = root
                sh.location = (px, py, rnd.uniform(-0.02, 0.06))
                sh.rotation_euler = (0, math.radians(rnd.uniform(-1.2, 1.2)), rz)
                k += 1
        for o in (bpy.data.objects.get(name + s) for s in ("_door", "_win", "_winf", "_awning")):
            if o:
                o.location.y -= fo
    else:
        # plaster: a dirty base band, corner pilasters and a cornice
        base = M("plaster_base", (0.18, 0.15, 0.12), rough=0.95, dirt=0.6, bump=0.3)
        C.box(name + "_base", (w + 0.04, d + 0.04, 0.32), loc=(0, 0, 0.16), m=base, parent=root, bevel=0.01, coll=coll)
        C.box(name + "_cornice", (w + 0.08, d + 0.08, 0.1), loc=(0, 0, h - 0.05), m=body.active_material if body else base,
              parent=root, bevel=0.02, coll=coll)
        crack = M("seam_dark", (0.03, 0.025, 0.02), rough=0.9, dirt=0.0, bump=0.0)
        for c_ in range(rnd.randint(1, 3)):
            cx = rnd.uniform(-w / 2 + 0.3, w / 2 - 0.3)
            if abs(cx - door_x) < 0.6:
                continue
            pts = [V((cx, -d / 2 - 0.005, h - 0.1))]
            for s_ in range(4):
                pts.append(pts[-1] + V((rnd.uniform(-0.12, 0.12), 0, -rnd.uniform(0.15, 0.3))))
            C.curve_tube(f"{name}_crack{c_}", pts, radius=0.006, m=crack, parent=root, coll=coll, res=2)
    # wooden corner posts on every shack
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.box(f"{name}_post{sx}{sy}", (0.09, 0.09, h + 0.05), loc=(sx * (w / 2 + fo * 0.5), sy * (d / 2 + fo * 0.5),
                                                                       (h + 0.05) / 2),
                  m=m["wood"], parent=root, bevel=0.01, coll=coll)
    front = -d / 2 - fo

    def roof_z(y):  # roof underside at local y
        return h + 0.05 + (y - (front - 0.3)) * math.sin(math.radians(tilt))
    # stovepipe through the roof (most shacks), some smoking
    if rnd.random() < 0.6:
        x = rnd.choice((-1, 1)) * rnd.uniform(0.25, 0.4) * w
        y = rnd.uniform(0.0, 0.3) * d
        z0 = roof_z(y)
        hh = rnd.uniform(0.7, 1.3)
        pm = m["pipe"]
        C.cyl(name + "_stove", 0.07, hh, loc=(x, y, z0 + hh / 2 - 0.05), m=pm, parent=root, coll=coll, verts=10)
        C.cyl(name + "_stovecap", 0.14, 0.1, loc=(x, y, z0 + hh + 0.06), r2=0.02, m=pm, parent=root, coll=coll,
              verts=10)
        if not back or rnd.random() < 0.5:
            CHIMNEYS.append((root, V((x, y, z0 + hh + 0.15))))
    # TV antenna or a little dish
    r = rnd.random()
    if r < 0.3:
        x = rnd.uniform(-0.3, 0.3) * w
        y = d * 0.2
        z0 = roof_z(y)
        C.cyl(name + "_ant", 0.012, 1.4, loc=(x, y, z0 + 0.7), m=m["steel"], parent=root, coll=coll, verts=6)
        for k in range(3):
            C.cyl(f"{name}_antx{k}", 0.008, 0.7 - k * 0.15, loc=(x, y, z0 + 1.0 + k * 0.17), rot=(0, 90, rnd.uniform(-20, 20)),
                  m=m["steel"], parent=root, coll=coll, verts=5)
    elif r < 0.42:
        x = rnd.choice((-1, 1)) * 0.35 * w
        C.lathe(name + "_dish", [(0.0, 0.0), (0.2, 0.04), (0.33, 0.12)], loc=(x, front - 0.05, h - 0.35),
                rot=(70, 0, rnd.uniform(-30, 30)), m=m["paint_white"], parent=root, coll=coll, seg=16)
    # patch panels on the front wall
    for k in range(rnd.randint(0, 2)):
        pw, ph = rnd.uniform(0.5, 1.2), rnd.uniform(0.4, 0.9)
        x = rnd.uniform(-w / 2 + pw / 2 + 0.1, w / 2 - pw / 2 - 0.1)
        if abs(x - door_x) < 0.4 + pw / 2:
            continue
        C.box(f"{name}_patch{k}", (pw, 0.015, ph), loc=(x, front - 0.015, rnd.uniform(0.4, h - 0.6)),
              rot=(0, rnd.uniform(-6, 6), 0), m=rnd.choice([m["rust"], m["corr3"], m["paint_yel"], m["corr2"]]),
              parent=root, bevel=0, coll=coll)
    # rain barrel at a front corner (never in the alley lane)
    sx = rnd.choice((-1, 1))
    if not alley and rnd.random() < 0.45:
        C.cyl(name + "_barrel", 0.28, 0.85, loc=(sx * (w / 2 - 0.35), front - 0.32, 0.425),
              m=rnd.choice([m["paint_blue"], m["rust"], m["paint_green"]]), parent=root, coll=coll, verts=14)
        C.cyl(name + "_water", 0.26, 0.01, loc=(sx * (w / 2 - 0.35), front - 0.32, 0.8),
              m=M("water_dark", (0.03, 0.04, 0.05), rough=0.05, dirt=0.0, bump=0), parent=root, coll=coll, verts=14)
        # gutter pipe feeding it
        C.cyl(name + "_gutter", 0.035, h - 0.6, loc=(sx * (w / 2 - 0.35), front - 0.05, 0.85 + (h - 0.6) / 2),
              m=m["pipe"], parent=root, coll=coll, verts=8)
    elif rnd.random() < 0.4:
        # crates stacked by the wall
        for k in range(rnd.randint(1, 3)):
            C.box(f"{name}_crate{k}", (0.45, 0.4, 0.38), loc=(sx * (w / 2 - 0.4), front - min(out, 0.22),
                                                           0.19 + k * 0.38),
                  rot=(0, 0, rnd.uniform(-12, 12)), m=m["wood"], parent=root, bevel=0.01, coll=coll)
    # window box with plants, or a plant pot on the sill
    if win_x is not None and rnd.random() < 0.55:
        C.box(name + "_wbox", (0.66, 0.16, 0.12), loc=(win_x, front - 0.1, 1.17), m=m["wood"], parent=root,
              bevel=0.005, coll=coll)
        leaf = M("leaf_m", (0.12, 0.3, 0.08), rough=0.7, dirt=0.2)
        flower = M(f"flower{rnd.randint(0, 2)}", [(0.8, 0.2, 0.15), (0.9, 0.75, 0.2), (0.85, 0.85, 0.9)][rnd.randint(0, 2)],
                   rough=0.6, dirt=0.1)
        for k in range(5):
            C.sphere(f"{name}_wleaf{k}", 0.06, loc=(win_x - 0.25 + k * 0.125, front - 0.1, 1.27 + rnd.uniform(0, 0.04)),
                     scale=(1, 1, 1.4), m=leaf if k % 2 else flower, parent=root, coll=coll, seg=8, rings=5)
    # shop sign above the door (houses facing the square)
    if not back and not alley and rnd.random() < 0.35:
        txt = rnd.choice(SHOP_SIGNS)
        sw = 0.16 * len(txt) + 0.3
        C.box(name + "_sign", (sw, 0.04, 0.34), loc=(door_x, front - 0.06, 2.25), rot=(0, rnd.uniform(-3, 3), 0),
              m=rnd.choice([m["paint_white"], m["wood"], m["paint_yel"]]), parent=root, bevel=0.01, coll=coll)
        C.text(name + "_signtxt", txt, size=0.2, loc=(door_x, front - 0.085, 2.24), rot=(90, 0, 0),
               m=M("ink_black"), parent=root, coll=coll)
    # lantern by the door
    if lit or rnd.random() < 0.25:
        lx = door_x + rnd.choice((-1, 1)) * 0.6
        C.box(name + "_lbr", (0.03, 0.22, 0.03), loc=(lx, front - 0.11, 2.05), m=m["dark"], parent=root, bevel=0,
              coll=coll)
        C.cyl(name + "_lamp", 0.06, 0.16, loc=(lx, front - 0.2, 1.95), m=C.emission("lantern_m", (1.0, 0.65, 0.3), 3.0),
              parent=root, coll=coll, verts=8)
    # graffiti in the alley and on back walls
    if (alley or back) and rnd.random() < 0.45:
        txt = rnd.choice(GRAFFITI)
        C.text(name + "_graf", txt, size=rnd.uniform(0.28, 0.4), loc=(rnd.uniform(-0.6, 0.6), front - 0.02,
                                                                     rnd.uniform(1.0, 1.7)),
               rot=(90, rnd.uniform(-6, 6), 0),
               m=M(f"spray{rnd.randint(0, 3)}", [(0.85, 0.85, 0.85), (0.8, 0.25, 0.1), (0.15, 0.45, 0.7),
                                                 (0.9, 0.7, 0.1)][rnd.randint(0, 3)], rough=0.7, dirt=0.3),
               parent=root, coll=coll)
    weather(root, name, w, d, h, fo, coll, rnd, fo == 0.0, door_x, win_x, lit, back, alley)
    # a pipe running down a side wall
    if rnd.random() < 0.35:
        C.cyl(name + "_spipe", 0.04, h, loc=(sx * (w / 2 + 0.05), rnd.uniform(-0.3, 0.6) * d / 2, h / 2),
              m=m["pipe"], parent=root, coll=coll, verts=8)


def village(vil, coll, O):
    C.set_coll(coll)
    rnd = rng("village")
    m = P.mats()
    w = lambda p: O + V(p)
    puddle = C.soft_alpha(M("puddle_m", (0.2, 0.22, 0.25), metal=0.5, rough=0.05, dirt=0.0, bump=0))
    # puddles: away from the shacks, partly in the alley (the chase splashes through)
    spots = [(3.5, -6.5, 1.2), (-6.5, 1.5, 0.9), (2.0, 8.0, 1.0), (-3.5, -10.5, 0.8), (22, 0.6, 0.7), (31, -0.5, 0.9),
             (8.5, -1.5, 0.6)]
    for i, (x, y, r) in enumerate(spots):
        C.cyl(f"v_puddle{i}", r, 0.004, loc=w((x, y, 0.004)), m=puddle, coll=coll, verts=20).scale = (1.0, 0.65, 1)
    # scattered paper and leaflets (some are the REPORT OBSOLETE DEVICES flyer)
    paper = M("paper_m", (0.82, 0.8, 0.72), rough=0.9, dirt=0.4)
    for i in range(22):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(3.0, 10.0)
        C.box(f"v_paper{i}", (0.21, 0.29, 0.002), loc=w((math.cos(a) * r, math.sin(a) * r, 0.003)),
              rot=(rnd.uniform(-4, 4), rnd.uniform(-4, 4), rnd.uniform(0, 360)), m=paper, bevel=0, coll=coll)
    # weeds along the bases of the shack ring
    weed = M("weed_m", (0.22, 0.28, 0.1), rough=0.9, dirt=0.4)
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(9.6, 10.4)
        p = w((math.cos(a) * r, math.sin(a) * r, 0))
        for k in range(3):
            C.cyl(f"v_weed{i}_{k}", 0.012, rnd.uniform(0.12, 0.3), loc=p + V((rnd.uniform(-0.06, 0.06),
                                                                          rnd.uniform(-0.06, 0.06), 0.1)),
                  rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), 0), r2=0.002, m=weed, coll=coll, verts=4)
    # power/phone wires from shack to shack around the square
    roots = sorted([o for o in bpy.data.objects if o.name.startswith("v_shack") and o.type == "EMPTY"],
                   key=lambda o: math.atan2(o.location.y - O.y, o.location.x - O.x))
    bpy.context.view_layer.update()
    for i in range(len(roots)):
        a, b = roots[i], roots[(i + 1) % len(roots)]
        if (a.location - b.location).length > 9:
            continue
        pa = a.matrix_world @ V((0, -1.0, 2.7))
        pb = b.matrix_world @ V((0, -1.0, 2.7))
        C.curve_tube(f"v_wire{i}", C.sag_points(pa, pb, 0.5, 8), radius=0.008, m=m["cable"], coll=coll)
    # chickens' feeding trough and a hand cart near the south entrance
    C.box("v_trough", (1.2, 0.3, 0.2), loc=w((-6.8, -5.8, 0.1)), rot=(0, 0, 30), m=m["wood"], bevel=0.01, coll=coll)
    cart = C.empty("v_cart", loc=w((7.5, -8.0, 0)), rot=(0, 0, -30), coll=coll)
    C.box("v_cartbed", (1.2, 0.8, 0.3), loc=(0, 0, 0.55), rot=(-8, 0, 0), m=m["wood"], parent=cart, bevel=0.01, coll=coll)
    for sx in (-0.65, 0.65):
        C.cyl(f"v_cartw{sx}", 0.3, 0.05, loc=(sx, 0.1, 0.3), rot=(0, 90, 0), m=m["wood"], parent=cart, coll=coll)
    C.cyl("v_carth", 0.025, 1.2, loc=(0, -0.9, 0.55), rot=(80, 0, 0), m=m["wood"], parent=cart, coll=coll)
    for k in range(3):
        it = P.scrap_item(["tv", "gear", "drum"][k], (0, 0, 0), (0, 0, k * 70), 0.35, coll)
        it.parent = cart  # (cart.matrix_world is not evaluated yet – parent instead of baking a world position)
        it.location = (-0.35 + k * 0.35, 0, 0.82)
    # sleeping cat on a roof edge
    cat = C.empty("v_cat", loc=w((-7.6, 8.6, 2.75)), rot=(0, 0, 200), coll=coll)
    fur = M("cat_fur", (0.55, 0.35, 0.18), rough=0.9, dirt=0.2)
    C.sphere("v_catbody", 0.16, loc=(0, 0, 0.1), scale=(1.6, 1, 0.8), m=fur, parent=cat, coll=coll, seg=12, rings=8)
    C.sphere("v_cathead", 0.09, loc=(0.25, 0.02, 0.15), m=fur, parent=cat, coll=coll, seg=10, rings=6)
    for sy in (-0.04, 0.05):
        C.cyl(f"v_catear{sy}", 0.03, 0.05, loc=(0.27, sy, 0.24), r2=0.0, m=fur, parent=cat, coll=coll, verts=4)
    C.curve_tube("v_cattail", [V((-0.22, 0, 0.06)), V((-0.32, 0.12, 0.03)), V((-0.2, 0.25, 0.02))], radius=0.025,
                 m=fur, parent=cat, coll=coll)
    vil["cat"] = cat


# =========================================================================== SCRAPYARD
def scrapyard(scrap, coll):
    C.set_coll(coll)
    rnd = rng("scrapyard")
    m = P.mats()

    def free(x, y, r=1.0):
        if -4 - r < x < 10 + r and -4 - r < y < 15 + r:
            return False
        if abs(x - 6) < 3.6 + r or (abs(y - 8) < 3.2 + r and x < 9 + r):
            return False
        if (V((x, y)) - V((-17.5, -3.5))).length < 7.5 + r:
            return False
        return True
    puddle = C.soft_alpha(M("puddle_m", (0.2, 0.22, 0.25), metal=0.5, rough=0.05, dirt=0.0, bump=0))
    n = 0
    for i in range(60):
        x, y = rnd.uniform(-30, 30), rnd.uniform(-25, 30)
        if not free(x, y, 0.5):
            continue
        r = rnd.uniform(0.5, 1.4)
        C.cyl(f"s_puddle{n}", r, 0.004, loc=(x, y, 0.02), m=puddle, coll=coll, verts=18).scale = (1, rnd.uniform(0.5, 0.8), 1)
        n += 1
        if n >= 10:
            break
    # puddles in the tyre ruts of the side road (lovely in the dawn light)
    for i, x in enumerate((-18, -9, -3)):
        C.cyl(f"s_rutpuddle{i}", 0.7, 0.004, loc=(x, 7.2 + (i % 2) * 1.6, 0.05), m=puddle, coll=coll,
              verts=18).scale = (1.8, 0.35, 1)
    # dry grass tufts
    grass = M("drygrass_m", (0.42, 0.36, 0.18), rough=0.95, dirt=0.3)
    n = 0
    for i in range(400):
        x, y = rnd.uniform(-28, 28), rnd.uniform(-22, 28)
        if not free(x, y, 0.2):
            continue
        p = V((x, y, 0.0))
        for k in range(4):
            C.cyl(f"s_grass{n}_{k}", 0.01, rnd.uniform(0.15, 0.35), loc=p + V((rnd.uniform(-0.07, 0.07),
                                                                           rnd.uniform(-0.07, 0.07), 0.1)),
                  rot=(rnd.uniform(-30, 30), rnd.uniform(-30, 30), 0), r2=0.001, m=grass, coll=coll, verts=4)
        n += 1
        if n >= 90:
            break
    # stones and pebbles (low-poly, slightly squashed), off the paths
    stone = M("stone_m", (0.32, 0.29, 0.26), rough=0.9, dirt=0.6, bump=0.5, scale=6)
    n = 0
    for i in range(600):
        x, y = rnd.uniform(-26, 26), rnd.uniform(-20, 26)
        if not free(x, y, 0.15):
            continue
        s = rnd.uniform(0.05, 0.22)
        st = C.sphere(f"s_stone{n}", s, loc=(x, y, s * 0.25), scale=(1.0, rnd.uniform(0.7, 1.1), rnd.uniform(0.45, 0.7)),
                      rot=(0, 0, rnd.uniform(0, 360)), m=stone, coll=coll, seg=7, rings=5)
        for p in st.data.polygons:
            p.use_smooth = False
        n += 1
        if n >= 160:
            break
    # a car wreck on its belly, a bathtub, a shopping trolley, a mattress, a fridge on its back
    car = C.empty("s_car", loc=(-24.0, 2.5, 0), rot=(0, 3, 35), coll=coll)
    body = M("car_paint", (0.25, 0.42, 0.45), metal=0.5, rough=0.5, rust=0.65, scale=2)
    C.box("s_carbody", (3.8, 1.7, 0.7), loc=(0, 0, 0.55), m=body, parent=car, bevel=0.15, coll=coll)
    C.box("s_carcab", (2.0, 1.5, 0.6), loc=(-0.2, 0, 1.15), m=body, parent=car, bevel=0.2, coll=coll)
    C.box("s_carwin", (2.02, 1.3, 0.4), loc=(-0.2, 0, 1.17), m=M("glass_dark", (0.02, 0.03, 0.03), rough=0.1),
          parent=car, bevel=0.1, coll=coll)
    for sx in (-1.2, 1.2):
        C.cyl(f"s_carwheel{sx}", 0.33, 0.25, loc=(sx, 0.86, 0.25), rot=(90, 0, 0), m=m["rubber"], parent=car, coll=coll)
    C.cyl("s_carweed", 0.4, 0.5, loc=(1.3, 0, 1.05), r2=0.05, m=grass, parent=car, coll=coll, verts=8)
    tub = C.lathe("s_tub", [(0.0, 0.0), (0.3, 0.02), (0.35, 0.45), (0.38, 0.5)], loc=(15.5, -10.5, 0.0),
                  m=M("enamel", (0.85, 0.85, 0.8), rough=0.3, rust=0.35), coll=coll, seg=20, cap_bottom=True)
    tub.scale = (2.2, 1.0, 1.0)
    tub.rotation_euler.z = math.radians(20)
    trolley = C.empty("s_trolley", loc=(-13.5, -14.5, 0), rot=(0, 0, 70), coll=coll)
    tm = m["chrome"]
    for k in range(6):
        C.box(f"s_trol{k}", (0.9, 0.012, 0.012), loc=(0, -0.28 + k * 0.11, 0.55), m=tm, parent=trolley, bevel=0, coll=coll)
        C.box(f"s_trolz{k}", (0.012, 0.6, 0.012), loc=(-0.45 + k * 0.18, 0, 0.55), m=tm, parent=trolley, bevel=0,
              coll=coll)
    for sx in (-0.4, 0.4):
        for sy in (-0.25, 0.25):
            C.cyl(f"s_troll{sx}{sy}", 0.012, 0.5, loc=(sx, sy, 0.3), m=tm, parent=trolley, coll=coll, verts=6)
            C.sphere(f"s_trolw{sx}{sy}", 0.05, loc=(sx, sy, 0.05), m=m["rubber"], parent=trolley, coll=coll, seg=8, rings=4)
    trolley.rotation_euler = (math.radians(75), 0, math.radians(70))  # tipped over
    trolley.location.z = 0.3
    C.box("s_mattress", (1.9, 1.3, 0.2), loc=(18.5, 9.5, 0.6), rot=(0, 18, 50),
          m=M("mattress_m", (0.6, 0.55, 0.45), rough=0.95, dirt=0.7, bump=0.4), bevel=0.06, coll=coll)
    # road signs: the city is far, dumping is forbidden (on the biggest dump in the land)
    for i, (loc, rot, t1, t2) in enumerate((((9.0, 1.0, 0), 200, "CITY", "12 km ->"),
                                             ((-9.5, 11.6, 0), 170, "NO", "DUMPING"))):
        C.cyl(f"s_signpole{i}", 0.04, 2.2, loc=V(loc) + V((0, 0, 1.1)), m=m["steel"], coll=coll, verts=8)
        sg = C.empty(f"s_sign{i}", loc=V(loc) + V((0, 0, 2.0)), rot=(0, rnd.uniform(-8, 8), rot), coll=coll)
        C.box(f"s_signp{i}", (0.9, 0.04, 0.55), loc=(0, -0.04, 0), m=m["paint_white"], parent=sg, bevel=0.01, coll=coll)
        C.text(f"s_signt{i}", t1 + "\n" + t2, size=0.17, loc=(0, -0.065, 0), rot=(90, 0, 0),
               m=M("sign_red", (0.6, 0.06, 0.04)), parent=sg, coll=coll)
    # burning oil drum (lit in S1, embers in S6)
    drum = C.cyl("s_firedrum", 0.3, 0.9, loc=(-11.5, 3.2, 0.45), m=m["rust"], coll=coll, verts=16)
    fire_m = C.emission("s_fire", (1.0, 0.4, 0.08), 6.0)
    flames = []
    for k in range(4):
        fl = C.cyl(f"s_flame{k}", 0.12 - k * 0.015, 0.35 + k * 0.05, loc=(-11.5 + rnd.uniform(-0.1, 0.1),
                                                                          3.2 + rnd.uniform(-0.1, 0.1), 1.02),
                   r2=0.0, m=fire_m, coll=coll, verts=8)
        flames.append(fl)
    fire_l = P.point_light("s_firelight", (-11.5, 3.2, 1.4), 80, (1.0, 0.45, 0.12), 0.3, coll=coll)
    scrap["fire"] = {"drum": drum, "m": fire_m, "flames": flames, "light": fire_l}
    # crows on the pylons' cross arms
    crows = []
    cm = M("crow_m", (0.02, 0.02, 0.025), rough=0.6)
    for i, x in enumerate((-31.5, -30.6, 29.4)):
        cr = C.empty(f"s_crow{i}", loc=(x, 24.0, 12.2), rot=(0, 0, rnd.uniform(0, 360)), coll=coll)
        C.sphere(f"s_crowb{i}", 0.13, loc=(0, 0, 0.1), scale=(1.4, 0.9, 1), m=cm, parent=cr, coll=coll, seg=10, rings=6)
        C.sphere(f"s_crowh{i}", 0.07, loc=(0.16, 0, 0.2), m=cm, parent=cr, coll=coll, seg=8, rings=5)
        C.cyl(f"s_crowbk{i}", 0.02, 0.08, loc=(0.25, 0, 0.19), rot=(0, 90, 0), r2=0.0, m=m["dark"], parent=cr,
              coll=coll, verts=5)
        crows.append(cr)
    scrap["crows"] = crows
    # the flower: one small bloom pushing out of the rubble by the hut (only shown in the last sequence)
    fl = C.empty("s_flower", loc=(-19.6, -4.2, 0), coll=coll)
    C.curve_tube("s_flowerstem", [V((0, 0, 0)), V((0.02, 0.01, 0.12)), V((-0.01, 0.0, 0.24))], radius=0.006,
                 m=M("leaf_m"), parent=fl, coll=coll)
    for k in range(6):
        a = k * math.pi / 3
        C.sphere(f"s_petal{k}", 0.025, loc=(math.cos(a) * 0.03 - 0.01, math.sin(a) * 0.03, 0.245), scale=(1.4, 0.8, 0.4),
                 rot=(0, 0, math.degrees(a)), m=M("petal_m", (0.95, 0.85, 0.2), rough=0.5), parent=fl, coll=coll,
                 seg=8, rings=4)
    C.sphere("s_flowerc", 0.014, loc=(-0.01, 0, 0.25), m=M("petal_c", (0.5, 0.25, 0.05)), parent=fl, coll=coll,
             seg=8, rings=4)
    C.sphere("s_flowerleaf", 0.03, loc=(0.03, 0, 0.08), scale=(1.8, 0.6, 0.3), rot=(0, -30, 0), m=M("leaf_m"),
             parent=fl, coll=coll, seg=8, rings=4)
    fl.scale = (1.6, 1.6, 1.6)
    scrap["flower"] = fl


# =========================================================================== WORKSHOP
def workshop(ws, coll, O):
    C.set_coll(coll)
    m = P.mats()
    w = lambda p: O + V(p)
    rnd = rng("workshop")
    paper = M("paper_m", (0.82, 0.8, 0.72), rough=0.9, dirt=0.4)
    blue = M("blueprint_m", (0.08, 0.2, 0.45), rough=0.8, dirt=0.3)
    ink_w = M("chalk_m", (0.85, 0.88, 0.9), rough=0.8)
    # blueprints of Funke pinned on the left wall (between window and stove)
    for i, (y, z, rz) in enumerate(((0.35, 1.6, -3), (1.05, 1.75, 4), (0.75, 1.15, -6))):
        bp = C.empty(f"ws_bp{i}", loc=w((-3.0, y, z)), rot=(0, rz, 90), coll=coll)
        C.box(f"ws_bpp{i}", (0.55, 0.004, 0.4), loc=(0, 0, 0), m=blue if i < 2 else paper, parent=bp, bevel=0, coll=coll)
        lm = ink_w if i < 2 else M("ink_black")
        # a can on legs, the lens, an antenna – drawn with a few strokes
        C.torus(f"ws_bpeye{i}", 0.06, 0.004, loc=(-0.08, -0.004, 0.06), rot=(90, 0, 0), m=lm, parent=bp, coll=coll,
                seg=16, segr=4)
        C.box(f"ws_bpcan{i}", (0.18, 0.002, 0.004), loc=(-0.08, -0.004, -0.02), m=lm, parent=bp, bevel=0, coll=coll)
        C.box(f"ws_bpcan2{i}", (0.18, 0.002, 0.004), loc=(-0.08, -0.004, 0.14), m=lm, parent=bp, bevel=0, coll=coll)
        for sx in (-0.17, 0.01):
            C.box(f"ws_bpside{i}{sx}", (0.004, 0.002, 0.16), loc=(sx, -0.004, 0.06), m=lm, parent=bp, bevel=0, coll=coll)
            C.box(f"ws_bpleg{i}{sx}", (0.004, 0.002, 0.12), loc=(sx * 0.6 - 0.03, -0.004, -0.09), rot=(0, 15, 0), m=lm,
                  parent=bp, bevel=0, coll=coll)
        C.text(f"ws_bpt{i}", ["FUNKE  MK I", "EYE: OLD LENS", "SPRINGS x4 ?"][i], size=0.04, loc=(0.13, -0.004, -0.13),
               rot=(90, 0, 0), m=lm, parent=bp, coll=coll)
        C.sphere(f"ws_bppin{i}", 0.008, loc=(0, -0.006, 0.18), m=M("p_red"), parent=bp, coll=coll, seg=6, rings=4)
    # calendar on the right wall, days crossed out
    cal = C.empty("ws_cal", loc=w((3.0, -1.1, 1.65)), rot=(0, 0, -90), coll=coll)
    C.box("ws_calp", (0.32, 0.004, 0.42), loc=(0, 0, 0), m=paper, parent=cal, bevel=0, coll=coll)
    C.box("ws_calpic", (0.28, 0.003, 0.14), loc=(0, -0.003, 0.11), m=M("calpic", (0.3, 0.5, 0.35), rough=0.8),
          parent=cal, bevel=0, coll=coll)
    for r in range(4):
        for c in range(7):
            if r * 7 + c < 19:
                C.box(f"ws_calx{r}{c}", (0.03, 0.002, 0.004), loc=(-0.12 + c * 0.04, -0.004, -0.02 - r * 0.045),
                      rot=(0, 45, 0), m=M("p_red"), parent=cal, bevel=0, coll=coll)
    # framed photo on the bench shelf: two figures, one tall, one small (her and someone she misses)
    ph = C.empty("ws_photo", loc=w((1.75, 2.35, 1.07)), rot=(-12, 0, 8), coll=coll)
    C.box("ws_photof", (0.16, 0.015, 0.2), loc=(0, 0, 0), m=m["wood"], parent=ph, bevel=0.003, coll=coll)
    C.box("ws_photop", (0.13, 0.003, 0.17), loc=(0, -0.008, 0), m=M("photo_m", (0.6, 0.52, 0.38), rough=0.4),
          parent=ph, bevel=0, coll=coll)
    for k, (x, s) in enumerate(((-0.03, 1.0), (0.035, 0.65))):
        C.sphere(f"ws_photoh{k}", 0.012 * s + 0.004, loc=(x, -0.011, -0.01 + 0.06 * s), m=M("ink_black"), parent=ph,
                 coll=coll, seg=8, rings=4)
        C.box(f"ws_photob{k}", (0.02 * s + 0.006, 0.002, 0.07 * s), loc=(x, -0.011, -0.04 + 0.025 * s - 0.03 * (1 - s)),
              m=M("ink_black"), parent=ph, bevel=0, coll=coll)
    # mug of cold tea, oil can, cable coil, sketches on the floor
    C.cyl("ws_mug", 0.04, 0.09, loc=w((-1.0, 1.65, 1.005)), m=M("mug_m", (0.7, 0.2, 0.12), rough=0.3, rust=0.0),
          coll=coll, verts=12)
    C.torus("ws_mugh", 0.025, 0.008, loc=w((-0.955, 1.65, 1.005)), rot=(90, 0, 0), m=M("mug_m"), coll=coll, seg=10,
            segr=5)
    C.cyl("ws_oilcan", 0.06, 0.12, loc=w((1.45, 1.7, 1.02)), m=m["paint_red"], coll=coll, verts=10)
    C.cyl("ws_oilspout", 0.008, 0.2, loc=w((1.5, 1.7, 1.12)), rot=(0, 50, 0), r2=0.004, m=m["paint_red"], coll=coll,
          verts=6)
    for k in range(4):
        C.torus(f"ws_coil{k}", 0.22 - k * 0.01, 0.012, loc=w((-2.55, -2.05, 0.012 + k * 0.022)), m=m["cable"],
                coll=coll, seg=20, segr=5)
    for k in range(5):
        a = rnd.uniform(0, 360)
        C.box(f"ws_sketch{k}", (0.21, 0.29, 0.002), loc=w((rnd.uniform(-1.4, -0.4), rnd.uniform(1.0, 1.4), 0.003)),
              rot=(0, 0, a), m=paper, bevel=0, coll=coll)
    # drip bucket under a leak in the roof (front right corner)
    C.cyl("ws_dripbucket", 0.14, 0.24, loc=w((2.55, -2.1, 0.12)), r2=0.16, m=m["steel"], coll=coll, verts=14)
    C.cyl("ws_dripwater", 0.135, 0.005, loc=w((2.55, -2.1, 0.17)), m=M("water_dark", (0.03, 0.04, 0.05), rough=0.05),
          coll=coll, verts=14)
    ws["drip_from"] = w((2.55, -2.1, 2.7))
    # cobwebs in the upper corners
    web = M("web_m", (0.8, 0.8, 0.8), rough=0.6, alpha=0.35)
    try:
        web.surface_render_method = "BLENDED"
    except Exception:
        pass
    for i, (x, y) in enumerate(((-2.95, 2.45), (2.95, 2.45), (-2.95, -2.45))):
        me = bpy.data.meshes.new(f"ws_web{i}")
        sx, sy = (-1 if x > 0 else 1), (-1 if y > 0 else 1)
        me.from_pydata([(0, 0, 0), (sx * 0.4, 0, 0), (0, sy * 0.4, 0), (0, 0, -0.35)], [], [(0, 1, 3), (0, 2, 3), (0, 1, 2)])
        ob = C.new_obj(f"ws_web{i}", me, w((x, y, 2.58)), mat_=web, coll=coll)
    # string of sockets/plugs along the back wall, a bundle of wires to the generator
    C.curve_tube("ws_wire1", [w((2.2, 2.5, 0.9)), w((1.6, 2.5, 1.2)), w((0.4, 2.5, 2.3)), w((0.3, 0.6, 2.6))],
                 radius=0.008, m=m["cable"], coll=coll)
    C.curve_tube("ws_wire2", [w((2.35, 1.4, 0.6)), w((2.8, 0.8, 0.05)), w((2.9, -0.5, 0.05)), w((2.95, -1.4, 1.2))],
                 radius=0.01, m=m["cable"], coll=coll)


# =========================================================================== DEPOT
def depot(dep, coll, O, H):
    C.set_coll(coll)
    m = P.mats()
    w = lambda p: O + V(p)
    h = lambda p: H + V(p)
    rnd = rng("depot")
    # warning signs on the fence (outside face, y<0)
    signs = [(-14, "KEEP OUT", "PROPERTY OF THE CITY"), (2, "VIOLATORS", "WILL BE RECYCLED"),
             (12, "NO ENTRY", "AFTER CURFEW"), (-22, "DANGER", "PRESS IN USE")]
    for i, (x, t1, t2) in enumerate(signs):
        sg = C.empty(f"d_wsign{i}", loc=w((x, -0.06, 1.7)), rot=(0, rnd.uniform(-5, 5), 0), coll=coll)
        C.box(f"d_wsignp{i}", (1.2, 0.02, 0.6), loc=(0, 0, 0), m=M("sign_yel", (0.75, 0.6, 0.08), rough=0.5, rust=0.4),
              parent=sg, bevel=0.005, coll=coll)
        C.text(f"d_wsignt{i}", t1, size=0.16, loc=(0, -0.012, 0.11), rot=(90, 0, 0), m=M("ink_black"), parent=sg,
               coll=coll)
        C.text(f"d_wsignt2{i}", t2, size=0.08, loc=(0, -0.012, -0.12), rot=(90, 0, 0), m=M("ink_black"), parent=sg,
               coll=coll)
    # barbed wire along the top of the fence (a helix)
    bw = M("barbed_m", (0.35, 0.35, 0.36), metal=1.0, rough=0.4, rust=0.4)
    for seg in range(2):
        x0, x1 = (-26, -6.2) if seg == 0 else (-1.8, 26)
        pts = []
        n = int((x1 - x0) * 3)
        for k in range(n + 1):
            t = k / n
            a = t * (x1 - x0) * 2.2 * math.pi
            pts.append(w((x0 + t * (x1 - x0), math.sin(a) * 0.18, 3.15 + math.cos(a) * 0.18)))
        C.curve_tube(f"d_barbed{seg}", pts, radius=0.006, m=bw, coll=coll, res=2, bevel_res=1)
    # puddles in front of the fence reflecting the floodlights
    puddle = C.soft_alpha(M("puddle_night", (0.13, 0.14, 0.16), metal=0.0, rough=0.1, dirt=0.0, bump=0, spec=0.7))
    for i, (x, y, r) in enumerate(((-9, -4, 1.4), (-1, -6.5, 1.0), (6, -3, 1.6), (-16, -7, 1.2))):
        C.cyl(f"d_puddle{i}", r, 0.004, loc=w((x, y, 0.02)), m=puddle, coll=coll, verts=20).scale = (1, 0.6, 1)
    # CCTV cameras on the wall pillars (they pan; see animate)
    cams = []
    for i, x in enumerate((-18, 0, 18)):
        root = C.empty(f"d_cctv{i}", loc=w((x, 5.05, 7.6)), rot=(0, 0, 180), coll=coll)
        C.box(f"d_cctvarm{i}", (0.08, 0.5, 0.08), loc=(0, 0.25, 0), m=m["dark"], parent=root, bevel=0, coll=coll)
        head = C.empty(f"d_cctvhead{i}", loc=(0, 0.5, 0), parent=root, coll=coll)
        C.box(f"d_cctvbody{i}", (0.22, 0.45, 0.2), loc=(0, 0.15, -0.05), rot=(-20, 0, 0), m=m["paint_white"],
              parent=head, bevel=0.02, coll=coll)
        C.sphere(f"d_cctvled{i}", 0.025, loc=(0.07, 0.38, -0.08), m=C.emission("cctv_led", (1, 0.05, 0.02), 6.0),
                 parent=head, coll=coll, seg=6, rings=4)
        cams.append(head)
    dep["cctv"] = cams
    # ---- inside the hall
    hz = M("hazard", (0.8, 0.6, 0.05), rough=0.5)
    for i in range(12):
        C.box(f"h_floorstripe{i}", (0.5, 0.14, 0.004), loc=h((-19 + i * 2.4, -1.6, 0.003)), rot=(0, 0, 45), m=hz,
              bevel=0, coll=coll)
    # propaganda boards
    for i, (x, t1, t2) in enumerate(((-12, "TODAY'S QUOTA", "400 UNITS"), (2, "NEW IS BETTER", "BETTER IS NEW"))):
        C.box(f"h_board{i}", (4.0, 0.08, 1.4), loc=h((x, 11.7, 6.5)), m=M("d_sign_m"), bevel=0.02, coll=coll)
        C.text(f"h_boardt{i}", t1, size=0.45, loc=h((x, 11.64, 6.75)), rot=(90, 0, 0),
               m=C.emission("h_boardtxt", (0.9, 0.95, 1.0), 2.5), coll=coll)
        C.text(f"h_boardt2{i}", t2, size=0.35, loc=h((x, 11.64, 6.15)), rot=(90, 0, 0),
               m=C.emission("h_boardtxt2", (1.0, 0.7, 0.2), 2.5), coll=coll)
    # chains hanging from the trusses (with hooks)
    chain_m = m["dark"]
    for i, (x, y, L_) in enumerate(((-15, -5, 5.0), (-7.5, -6, 6.5), (0, 5.5, 4.0), (5, -7, 5.5), (-11, 6, 3.5))):
        for k in range(int(L_ / 0.12)):
            C.torus(f"h_chain{i}_{k}", 0.05, 0.012, loc=h((x, y, 11.1 - k * 0.12)), rot=(90 * (k % 2), 0, 90 * (k % 2)),
                    m=chain_m, coll=coll, seg=8, segr=4)
        C.torus(f"h_hook{i}", 0.1, 0.022, loc=h((x, y + 0.08, 11.1 - L_ - 0.1)), rot=(90, 0, 0), m=chain_m, coll=coll,
                seg=12, segr=5)
    # pallets and stacked crates near the walls
    for i in range(6):
        x = -20 + i * 1.3
        for k in range(2 if i % 2 else 3):
            C.box(f"h_pallet{i}_{k}", (1.2, 1.0, 0.14), loc=h((x, 10.6, 0.07 + k * 0.15)), rot=(0, 0, rnd.uniform(-4, 4)),
                  m=m["wood"], bevel=0.005, coll=coll)
    # steel columns along the long walls, under every truss
    colm = M("column_m", (0.22, 0.2, 0.18), metal=0.7, rough=0.5, rust=0.35, scale=2)
    for i in range(9):
        x = -20 + i * 5
        for sy in (-1, 1):
            y = sy * 11.55
            C.box(f"h_colweb{i}{sy}", (0.06, 0.3, 11.4), loc=h((x, y, 5.7)), m=colm, bevel=0, coll=coll)
            for fx in (-0.13, 0.13):
                C.box(f"h_colfl{i}{sy}{fx}", (0.02, 0.32, 11.4), loc=h((x + fx, y, 5.7)), m=colm, bevel=0, coll=coll)
            C.box(f"h_colbase{i}{sy}", (0.4, 0.45, 0.25), loc=h((x, y, 0.125)), m=bpy.data.materials.get("depot_concrete"),
                  bevel=0.02, coll=coll)
    # oil stains under the conveyor
    oil = M("oil_m", (0.02, 0.02, 0.02), rough=0.1, dirt=0.0, bump=0)
    for i in range(7):
        C.cyl(f"h_oil{i}", rnd.uniform(0.3, 0.8), 0.003, loc=h((rnd.uniform(-18, 6), rnd.uniform(-0.8, 0.8), 0.003)),
              m=oil, coll=coll, verts=14).scale = (1, rnd.uniform(0.5, 0.9), 1)
    # steam pipe along the far wall with valves
    C.cyl("h_steampipe", 0.18, 40, loc=h((0, -11.5, 6.0)), rot=(0, 90, 0), m=m["pipe"], coll=coll, verts=14)
    for i in range(5):
        C.torus(f"h_flange{i}", 0.2, 0.04, loc=h((-16 + i * 8, -11.5, 6.0)), rot=(0, 90, 0), m=m["pipe"], coll=coll,
                seg=16, segr=6)
    dep["steam_vents"] = [h((-12 + i * 8, -11.3, 6.1)) for i in range(4)]
    # ---- the escape hole in the back wall (x=-22, around y=-6)
    hw_ = bpy.data.objects.get("h_walle-22")
    if hw_:
        bpy.data.objects.remove(hw_, do_unlink=True)
        conc = bpy.data.materials.get("depot_concrete")
        for i, (y0, y1) in enumerate(((-12, -6.9), (-5.1, 12))):
            C.box(f"h_wallw{i}", (0.5, y1 - y0, 12), loc=h((-22, (y0 + y1) / 2, 0)), origin="bottom", m=conc, bevel=0,
                  coll=coll)
        C.box("h_wallw_top", (0.5, 1.8, 9.6), loc=h((-22, -6, 2.4)), origin="bottom", m=conc, bevel=0, coll=coll)
        # torn sheet edges and a bit of moonlight outside
        for k, (y, z, ry) in enumerate(((-6.85, 1.0, 20), (-5.15, 1.4, -25), (-6.0, 2.35, 0))):
            C.box(f"h_tear{k}", (0.04, 0.35 if k < 2 else 1.6, 0.9 if k < 2 else 0.25), loc=h((-22.3, y, z)),
                  rot=(ry * 0.3, 0, ry), m=m["corr1"], bevel=0, coll=coll)
        P.point_light("h_moonout", h((-24.5, -6, 1.6)), 250, (0.5, 0.65, 1.0), 0.6, coll=coll)


# =========================================================================== animated details
def animate(ctx):
    sq = ctx.seq
    # village chimneys smoke during S3/S4 (day: pale)
    if 3 in sq:
        f0 = sq[3]["f0"] - 60
        f1 = sq.get(4, sq[3])["f1"]
        bpy.context.view_layer.update()
        n = 0
        for root, p in CHIMNEYS:
            if n >= 3:
                break
            wp = root.matrix_world @ p
            P.smoke(f"v_chsmoke{n}", wp, f0, f1, coll=ctx.c_vil, every=6, rise=2.2, life=70, size=0.16,
                    color=(0.8, 0.78, 0.75), drift=(0.5, 0.2, 0), seed=40 + n, alpha=0.12)
            n += 1
    # oil-drum fire flickers through S1; embers in S6
    fire = ctx.scrap.get("fire")
    if fire:
        rnd = random.Random(7)
        if 1 in sq:
            fr = sq[1]["f0"]
            while fr < sq[1]["f1"]:
                v = rnd.uniform(0.6, 1.3)
                A.key(fire["light"].data, "energy", fr, 80 * v)
                A.key_socket(C.emit_socket(fire["m"]), fr, 6.0 * v)
                for k, fl in enumerate(fire["flames"]):
                    fl.scale = (1, 1, rnd.uniform(0.6, 1.4))
                    fl.keyframe_insert("scale", frame=fr)
                fr += rnd.randint(2, 4)
        if 6 in sq:
            A.key(fire["light"].data, "energy", sq[6]["f0"], 12.0, "CONSTANT")
            A.key_socket(C.emit_socket(fire["m"]), sq[6]["f0"], 1.2, "CONSTANT")
            for fl in fire["flames"]:
                fl.scale = (0.6, 0.6, 0.25)
                fl.keyframe_insert("scale", frame=sq[6]["f0"])
            P.smoke("s_drumsmoke", V((-11.5, 3.2, 1.0)), sq[6]["f0"] - 60, sq[6]["f1"], coll=ctx.c_scrap, every=6,
                    rise=1.6, life=60, size=0.1, color=(0.6, 0.55, 0.52), drift=(0.4, 0.1, 0), seed=66, alpha=0.12)
    # the flower is only there at the new beginning
    fl = ctx.scrap.get("flower")
    if fl:
        kids = [fl] + list(fl.children_recursive)
        for o in kids:
            A.hide(o, 0, True)
            if 6 in sq:
                A.hide(o, sq[6]["f0"], False)
    # crows shuffle and turn their heads now and then
    for i, cr in enumerate(ctx.scrap.get("crows", [])):
        rnd = random.Random(20 + i)
        for s in (1, 6):
            if s not in sq:
                continue
            fr = sq[s]["f0"]
            while fr < sq[s]["f1"]:
                cr.rotation_euler.z += math.radians(rnd.uniform(-60, 60))
                cr.keyframe_insert("rotation_euler", frame=fr, index=2)
                A.set_interp(cr, "rotation_euler", fr, "CONSTANT", index=2)
                fr += rnd.randint(30, 90)
    # depot CCTV pans slowly during S5
    if 5 in sq:
        f0, f1 = sq[5]["f0"], sq[5]["f1"]
        for i, head in enumerate(ctx.dep.get("cctv", [])):
            fr = f0 + i * 20
            k = 0
            while fr < f1:
                head.rotation_euler.z = math.radians(35 if k % 2 else -35)
                head.keyframe_insert("rotation_euler", frame=fr, index=2)
                fr += 72
                k += 1
        # steam puffs from the pipe valves in the hall
        for i, p in enumerate(ctx.dep.get("steam_vents", [])):
            rnd = random.Random(80 + i)
            fr = f0 + rnd.randint(0, 60)
            while fr < f1:
                P.smoke(f"h_steam{i}_{fr}", p, fr, fr + 18, coll=ctx.c_dep, every=3, rise=1.2, life=30, size=0.16,
                        color=(0.85, 0.85, 0.85), drift=(0.2, 0.6, 0), seed=fr, alpha=0.18)
                A.event(fr, "steam_hiss")
                fr += rnd.randint(110, 200)
    # S2: moths circling the hanging bulb, a drip into the bucket
    if 2 in sq:
        f0, f1 = sq[2]["f0"], sq[2]["f1"]
        W = ctx.ws
        import sets2 as S2
        bulb = S2.WORKSHOP + V((0.3, 0.6, 2.2))
        mm = M("moth_m", (0.75, 0.68, 0.55), rough=0.8)
        for i in range(2):
            mo = C.sphere(f"ws_moth{i}", 0.012, loc=bulb, scale=(1.6, 0.6, 0.4), m=mm, coll=ctx.c_ws, seg=6, rings=4)
            rnd = random.Random(90 + i)
            fr = f0
            while fr < f1:
                a = rnd.uniform(0, 2 * math.pi)
                r = rnd.uniform(0.08, 0.25)
                mo.location = bulb + V((math.cos(a) * r, math.sin(a) * r, rnd.uniform(-0.15, 0.08)))
                mo.keyframe_insert("location", frame=fr)
                fr += rnd.randint(3, 7)
        drop = C.sphere("ws_drop", 0.008, loc=W["drip_from"], m=M("water_dark"), coll=ctx.c_ws, seg=6, rings=4)
        fr = f0 + 10
        top = V(W["drip_from"])
        bot = V((top.x, top.y, 0.18))
        while fr < f1:
            drop.location = top
            drop.keyframe_insert("location", frame=fr)
            drop.location = bot
            drop.keyframe_insert("location", frame=fr + 9)
            A.set_interp(drop, "location", fr + 9, "CONSTANT")
            A.event(fr + 9, "drip")
            fr += 48
