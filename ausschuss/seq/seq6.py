"""SEQ 6 – New beginning at dawn: the hut is gone, the double knock, the freed machines arrive, iris-out."""
import math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import core as C
import anim as A
import characters as CH
import props as P
import sets as S
import build as B

V = Vector


def machine_vacuum(name, coll):
    r = C.empty(name, loc=(0, 0, -300), coll=coll)
    C.cyl(name + "_b", 0.3, 0.25, loc=(0, 0, 0.15), m=C.mat("p_red"), parent=r, coll=coll)
    C.sphere(name + "_e", 0.05, loc=(0, -0.28, 0.24), m=C.emission("happy_eye", (0.4, 1.0, 0.5), 4.0), parent=r,
             coll=coll)
    return r


def machine_juke(name, coll):
    r = C.empty(name, loc=(0, 0, -300), coll=coll)
    C.box(name + "_b", (0.6, 0.45, 0.85), loc=(0, 0, 0.47), m=C.mat("jb_m", (0.5, 0.2, 0.1), rough=0.4, rust=0.2),
          parent=r, bevel=0.1, coll=coll)
    C.box(name + "_g", (0.45, 0.02, 0.3), loc=(0, -0.23, 0.6), m=C.emission("jb_glow", (1, 0.6, 0.2), 6.0), parent=r,
          bevel=0.05, coll=coll)
    for sx in (-1, 1):
        C.cyl(name + f"_w{sx}", 0.06, 0.04, loc=(0.25 * sx, 0, 0.06), rot=(0, 90, 0), m=C.mat("tire"), parent=r,
              coll=coll)
    return r


def machine_quad(name, coll, paint="Bello_paint"):
    r = C.empty(name, loc=(0, 0, -300), coll=coll)
    C.box(name + "_q", (0.35, 0.5, 0.25), loc=(0, 0, 0.45), m=C.mat(paint), parent=r, bevel=0.05, coll=coll)
    C.box(name + "_qh", (0.2, 0.2, 0.18), loc=(0, -0.3, 0.6), m=C.mat(paint), parent=r, bevel=0.03, coll=coll)
    C.sphere(name + "_qe", 0.05, loc=(0, -0.41, 0.62), m=C.emission("happy_eye", (0.4, 1.0, 0.5), 4.0), parent=r, coll=coll)
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.cyl(name + f"_ql{sx}{sy}", 0.025, 0.35, loc=(0.13 * sx, 0.18 * sy, 0.17), m=C.mat("pipe_m"), parent=r,
                  coll=coll)
    return r


def trot(ob, f0, pts, speed=1.0, hop=0.08, period=8):
    pts = [V(p) for p in pts]
    total = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))
    dur = int(total / speed * C.FPS)
    ob.location = pts[0]
    ob.keyframe_insert("location", frame=f0 - 1)
    A.set_interp(ob, "location", f0 - 1, "CONSTANT")
    n = max(1, dur // (period // 2))
    for i in range(n + 1):
        t = i / n
        d = t * total
        acc = 0.0
        p = pts[-1]
        for k in range(len(pts) - 1):
            seg = (pts[k + 1] - pts[k]).length
            if acc + seg >= d:
                p = pts[k].lerp(pts[k + 1], (d - acc) / max(1e-6, seg))
                yaw = A.yaw_towards(pts[k + 1] - pts[k])
                break
            acc += seg
        ob.location = p + V((0, 0, hop if i % 2 else 0))
        ob.rotation_euler = (0, 0, yaw)
        ob.keyframe_insert("location", frame=f0 + int(t * dur))
        ob.keyframe_insert("rotation_euler", frame=f0 + int(t * dur))
    return f0 + dur


def iris(ctx, cam, f0, f1, target, coll, d=0.1):
    """Opaque black ring with a shrinking round hole, centred on target (world point)."""
    import bmesh
    sc = bpy.data.scenes[ctx.seq[6]["scene"].name]
    sc.frame_set(f0)
    u = world_to_camera_view(sc, cam, V(target))
    fw = cam.data.sensor_width / cam.data.lens * d
    fh = fw * 9 / 16
    cx, cy = (u.x - 0.5) * fw, (u.y - 0.5) * fh
    m = C.emission("iris_black", (0, 0, 0), 0.0)
    bm = bmesh.new()
    seg = 96
    inner = [bm.verts.new((math.cos(2 * math.pi * i / seg), math.sin(2 * math.pi * i / seg), 0)) for i in range(seg)]
    outer = [bm.verts.new((60 * math.cos(2 * math.pi * i / seg), 60 * math.sin(2 * math.pi * i / seg), 0))
             for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    me = bpy.data.meshes.new("iris_ring")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ring = bpy.data.objects.new("iris_ring", me)
    coll.objects.link(ring)
    ring.parent = cam
    ring.location = (cx, cy, -d)
    rmax = math.hypot(fw, fh) * 0.6 + math.hypot(cx, cy)
    for fr, r in ((f0, rmax), (f1 - 10, fw * 0.03), (f1 - 4, fw * 0.03), (f1, 0.00001)):
        ring.scale = (r, r, r)
        ring.keyframe_insert("scale", frame=fr)
    cap = C.box("iris_cap", (1.0, 1.0, 0.0001), loc=(0, 0, -d * 1.01), m=m, bevel=0, coll=coll)
    cap.parent = cam
    A.hide(cap, 0, True)
    A.hide(cap, f1, False)
    # the ring is only an object in front of the wink camera: keep it out of every other shot
    A.hide(ring, 0, True)
    A.hide(ring, f0, False)
    return ring


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(30)
    h, f = ctx.hedda, ctx.funke
    hut = ctx.scrap["hut"]
    wld = S.world("W_S6_sunrise", horizon=(1.0, 0.62, 0.35), zenith=(0.2, 0.32, 0.6), ground=(0.08, 0.06, 0.05),
                  strength=1.0, sun_dir=(0.7, 0.7, 0.05), sun_color=(1.0, 0.7, 0.35), sun_glow=5.0)
    sc, L, cams = B.new_seq_scene(ctx, 6, "S6_New_Beginning", F, END, wld,
                                  [ctx.chars, ctx.c_scrap, ctx.c_city, ctx.c_props])
    sun = S.sun("S6_sun", (88, 0, 135), 2.0, (1.0, 0.6, 0.3), L, angle=3)
    A.key(sun.data, "energy", F, 2.0)
    A.key(sun.data, "energy", END, 5.5)
    sun.rotation_euler.x = math.radians(88)
    sun.keyframe_insert("rotation_euler", frame=F)
    sun.rotation_euler.x = math.radians(80)
    sun.keyframe_insert("rotation_euler", frame=END)
    S.sun("S6_fill", (50, 0, -60), 0.8, (0.5, 0.6, 0.9), L, angle=30)
    fog6 = S.fog_box("S6_fog", L, (0, 120, 0), (520, 640, 70), 0.007, (0.95, 0.75, 0.6))
    B.offstage_all(ctx, F, keep=(h, f))
    # hut destroyed: parts hidden, remains shown (only from this sequence on)
    for ob in hut["parts"]:
        if ob.type in ("MESH", "CURVE", "FONT", "LIGHT"):
            A.hide(ob, 0, False)
            A.hide(ob, F, True)
    for ob in list(hut["mill_rotor"].children_recursive) + [hut["mill_rotor"]]:
        if ob.type == "MESH":
            A.hide(ob, 0, False)
            A.hide(ob, F, True)
    for ob in hut["remains"]:
        A.hide(ob, 0, True)
        A.hide(ob, F, False)
    for d in ctx.decal_hedda + ctx.decal_funke:
        A.hide(d, F, True)
    hr = hut["root"]
    bpy.context.view_layer.update()
    site = V(hr.location)

    def HL(x, y, z=0.0):
        return hr.matrix_world @ V((x, y, z))

    # ------------------------------------------------------------------ 6.1 arrival
    a0 = HL(2.0, -9.0)
    a1 = HL(0.9, -3.4)
    h.cut(F, a0, 0)
    h.pose(F, "stand")
    h.pose(F, "carry")
    h.face(F, "neutral")
    f.cut(F, (0, 0, 0), 0)
    f.pose(F, "stand")
    f.pose(F, {"lid": (-95, 0, 0)})
    f.glow(F, 4.0, "iris")
    f.glow(F, 3.0, "bulb")
    A.key(ctx.funke_light.data, "energy", F, 1.0)
    hm = A.world_matrix_at(h.rig, F, "chest")
    f.place(F, hm @ V((0, 0.05, -0.32)) - V((0, 0, 0.25)), 0)
    con = A.attach_to(f.rig, h.rig, F, bone="chest", name="carried6")
    hw = h.walk(F + 2, [a0, a1], speed=0.9, stride=0.45, end_pose=None)
    fr = F + 2
    while fr < hw:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    h.face(hw - 6, "surprised")
    h.pose(hw + 4, {"head": (0, 0, 0), "spine": (-4, 0, 0)})
    h.face(hw + 30, "sad")
    # set Funke down
    tset = hw + 40
    h.pose(tset, "bend_down")
    A.detach(f.rig, con, tset + 6)
    fpos = HL(1.6, -3.1)
    f.place(tset + 12, fpos, h.yaw_at(tset))
    f.pose(tset + 12, "stand")
    # Hedda sits down on a drum by the slab
    sit_yaw = math.degrees(hr.rotation_euler.z) + 180 + 20
    sd = V((math.sin(math.radians(sit_yaw)), -math.cos(math.radians(sit_yaw)), 0))
    seat_pos = HL(-0.8, -2.75)
    drum = P.scrap_item("crate", seat_pos - sd * 0.06 + V((0, 0, 0.25)), (0, 0, sit_yaw + 8), 1.0, ctx.c_props)
    A.hide(drum, 0, True)
    A.hide(drum, F, False)
    ts = tset + 20
    h.pose(ts, "stand")
    h.hold_place(ts)
    front = seat_pos + sd * 0.45
    tw_ = h.walk(ts, [a1, front], speed=0.6, stride=0.35, style="shuffle", end_pose=None)
    tsit = max(ts + 30, tw_ + 8)
    h.place(tw_ + 6, front, sit_yaw)
    h.place(tsit, seat_pos, sit_yaw)
    h.pose(tsit + 10, "sit")
    h.pose(tsit + 10, {"head": (30, 0, 0), "spine": (20, 0, 0), "upper_arm_L": (30, 0, 10), "upper_arm_R": (30, 0, 10),
                       "forearm_L": (80, 0, -20), "forearm_R": (80, 0, -20)})
    h.bone_loc(tsit, "root", (0, 0, 0))
    h.bone_loc(tsit + 10, "root", (0, 0.05, -0.32))
    h.face(tsit + 10, "sad")
    h.blink(tsit + 40, "sad")
    A.event(tsit + 10, "sigh")
    A.event(F, "dawn_wind", dur=C.sec(8))
    B.shot(ctx, 6, "S6_c1_arrive", F, [(F, HL(-3.5, -12, 1.7), HL(0.5, -1, 1.0)), (tsit, HL(-2.5, -9.5, 1.6), HL(0, -1.5, 0.9))],
           lens=30)
    # ------------------------------------------------------------------ 6.2 Funke brings a sheet, the double knock
    tf = tsit + 20
    f.hold_all(tf - 1)
    sheet_src = hut["remains"][3]
    sp = A.world_matrix_at(sheet_src, tf).translation
    spl = hr.matrix_world.inverted() @ sp
    edge = HL(max(-2.0, min(2.0, spl.x)), -2.65)  # at the slab's edge, not on it
    f1 = f.walk(tf, [fpos, edge], speed=0.8, stride=0.12, end_pose="stand")
    f.place(f1 + 2, None, math.degrees(A.yaw_towards(sp - edge)))
    f.pose(f1 + 6, "reach_up")
    A.event(f1 + 6, "metal_scrape")
    # a fresh sheet he drags (copy)
    C.set_coll(ctx.c_props)
    carry_sheet = P.corrugated("new_sheet", 0.9, 0.7, (0, 0, -300), (0, 0, 0), P.mats()["corr3"], coll=ctx.c_props)
    carry_sheet.keyframe_insert("location", frame=f1 + 7)
    A.set_interp(carry_sheet, "location", f1 + 7, "CONSTANT")
    hp = h.pos_at(tsit + 12)
    fdst = hp + (edge - hp).normalized() * 0.62
    fdst.z = 0
    f2 = f.walk(f1 + 12, [edge, fdst], speed=0.5, stride=0.1, end_pose=None)
    A.event(f1 + 12, "drag_metal", dur=f2 - f1 - 12)
    fr = f1 + 8
    while fr <= f2 + 2:
        fp = f.pos_at(fr)
        yw = math.radians(f.yaw_at(fr))
        back = V((-math.sin(yw), math.cos(yw), 0))
        carry_sheet.location = fp + back * 0.42 + V((0, 0, 0.14))
        carry_sheet.rotation_euler = (math.radians(-70), 0, yw)
        carry_sheet.keyframe_insert("location", frame=fr)
        carry_sheet.keyframe_insert("rotation_euler", frame=fr)
        fr += 4
    fr = f1 + 12
    while fr < f2:
        f.pose(fr, {"arm_L": (-40, 0, 20), "arm_R": (-40, 0, 20), "body": (15, 0, 0)})
        fr += 6
    f.place(f2 + 4, fdst, math.degrees(A.yaw_towards(hp - fdst)))
    f.pose(f2 + 6, "stand")
    tk = f2 + 14
    f.pose(tk - 4, {"arm_R": (120, 0, -20), "fore_R": (20, 0, 0), "head": (-20, 0, 0)})
    for k in range(2):
        f.pose(tk + k * 7, {"arm_R": (125, 0, -20), "fore_R": (25, 0, 0)})
        f.pose(tk + k * 7 + 3, {"arm_R": (110, 0, -20), "fore_R": (10, 0, 0)}, interp="LINEAR")
        A.event(tk + k * 7 + 3, "knock_soft")
    f.pose(tk + 18, "stand")
    f.pose(tk + 18, {"head": (-25, 0, 0)})
    # Hedda looks up – smiles
    h.pose(tk + 20, {"head": (-5, -25, 0), "spine": (6, 0, 0)})
    h.face(tk + 24, "surprised")
    h.face(tk + 40, "happy")
    h.blink(tk + 56, "happy")
    h.pose(tk + 44, {"upper_arm_R": (40, 0, -30), "forearm_R": (50, 0, 0)})
    f.pose(tk + 44, "happy")
    f.glow(tk + 44, 10.0, "bulb")
    A.event(tk + 40, "warm_chord")
    B.shot(ctx, 6, "S6_c2_sheet", tf, [(tf, HL(3.2, -5.5, 1.1), HL(0.2, -2.0, 0.5)), (f2, HL(2.8, -5.8, 1.0), HL(0, -2.6, 0.6))],
           lens=30)
    B.shot(ctx, 6, "S6_c2b_knock", f2 - 6, [(f2 - 6, HL(0.7, -0.5, 1.3), HL(-0.35, -2.7, 0.65)),
                                            (tk + 60, HL(0.6, -0.6, 1.25), HL(-0.4, -2.75, 0.7))], lens=28)
    # ------------------------------------------------------------------ the freed machines arrive
    tm = tk + 50
    road = [V((-25.5, 8.4, 0)), V((-21, 7.5, 0)), V((-20.6, 0.5, 0))]
    stops = [HL(1.5, -5.6), HL(2.6, -4.9), HL(0.4, -6.0), HL(3.4, -4.0)]
    machines = [machine_juke("free_juke", ctx.c_props), machine_quad("free_quad1", ctx.c_props),
                machine_vacuum("free_vac2", ctx.c_props), machine_quad("free_quad2", ctx.c_props)]
    for i, mc in enumerate(machines):
        A.hide(mc, 0, True)
        A.hide(mc, F, False)
        mc.location = (0, 0, -300)
        mc.keyframe_insert("location", frame=F)
        off = V(((i % 2) * 1.1 - 0.55, 0, 0))
        trot(mc, tm + i * 28, [p + off for p in road] + [stops[i]], speed=1.4, hop=0.06 if i != 0 else 0.02)
    A.event(tm, "jukebox_soft", beat=12)
    h.face(tm + 50, "surprised")
    A.look(h, tm + 50, road[1] + V((0, 0, 0.5)))
    h.pose(tm + 80, "stand")
    h.bone_loc(tm + 80, "root", (0, 0, 0))
    h.face(tm + 86, "happy")
    for k in range(3):
        h.pose(tm + 90 + k * 6, {"chest": (-6, 0, 0), "head": (-12, 0, 0)})
        h.pose(tm + 93 + k * 6, {"chest": (4, 0, 0), "head": (-4, 0, 0)})
    A.event(tm + 90, "laugh")
    B.shot(ctx, 6, "S6_c3_machines", tm + 20, [(tm + 20, V((-18.4, 4.6, 1.2)), V((-24.0, 8.3, 0.5))),
                                               (tm + 100, V((-18.3, 4.4, 1.25)), V((-21.6, 7.4, 0.5)))], lens=30)
    # ------------------------------------------------------------------ 6.3 building again, the wink, iris out
    tb = tm + 110
    h.pose(tb, "stand")
    h.hold_place(tb)
    h.place(tb + 4, None, math.degrees(hr.rotation_euler.z) + 180)
    h.pose(tb + 10, "arms_up")
    carry_sheet.keyframe_insert("location", frame=tb + 6)
    carry_sheet.keyframe_insert("rotation_euler", frame=tb + 6)
    hand_h = A.world_matrix_at(h.rig, tb + 14, "hand_R").translation
    carry_sheet.location = hand_h + V((-0.45, 0, -0.1))
    carry_sheet.rotation_euler = (0, 0, hr.rotation_euler.z)
    carry_sheet.keyframe_insert("location", frame=tb + 14)
    carry_sheet.keyframe_insert("rotation_euler", frame=tb + 14)
    A.event(tb + 14, "hammer_tiny")
    A.event(tb + 30, "hammer_tiny")
    A.event(tb + 46, "hammer_tiny")
    # Funke on top of the drum, waving
    f.hold_all(tb - 1)
    crate = P.scrap_item("crate", HL(1.7, -3.7, 0.25), (0, 0, 15), 1.0, ctx.c_props)
    A.hide(crate, 0, True)
    A.hide(crate, F, False)
    dpos = HL(1.7, -3.7, 0.5)
    A.arc(f.rig, tb, tb + 14, f.pos_at(tb), dpos, height=0.4)
    A.event(tb + 14, "land_spring")
    f.pose(tb + 14, "happy")
    tw = tb + C.sec(3.0)
    END = tw + C.sec(7.0)
    B.set_end(ctx, 6, END)
    B.shot(ctx, 6, "S6_c4_wide", tb, [(tb, HL(5, -12, 2.4), HL(0, -1, 1.2)), (tw, HL(6, -14, 3.0), HL(0, -1, 1.3))], lens=26)
    # close-up of Funke: wink + glint, iris-out on his eye
    cdir = V((0.62, 0.55, 0)).normalized()
    cam = B.shot(ctx, 6, "S6_c5_wink", tw, [(tw, dpos + cdir * 1.05 + V((0, 0, 0.5)), dpos + V((0, 0, 0.36))),
                                            (END, dpos + cdir * 0.9 + V((0, 0, 0.5)), dpos + V((0, 0, 0.4)))], lens=45)
    f.cut(tw, dpos, math.degrees(A.yaw_towards(cdir)))
    f.pose(tw, "stand")
    f.pose(tw, {"lid": (-95, 0, 0), "head": (-6, 0, 0)})
    tk2 = tw + 30
    f.pose(tk2, {"lid": (-95, 0, 0)})
    f.pose(tk2 + 4, {"lid": (-40, 0, 0), "head": (-6, 0, 12)})
    f.pose(tk2 + 12, {"lid": (-40, 0, 0), "head": (-6, 0, 12)})
    f.pose(tk2 + 16, {"lid": (-95, 0, 0), "head": (-6, 0, 0)})
    A.event(tk2 + 4, "wink")
    f.glow(tk2 + 18, 4.0, "iris")
    f.glow(tk2 + 21, 25.0, "iris")
    f.glow(tk2 + 26, 4.0, "iris")
    A.event(tk2 + 21, "glint")
    eye = A.world_matrix_at(f.rig, tk2 + 30, "head") @ V((0, -0.09, 0.1))
    card = iris(ctx, cam, tk2 + 30, END - C.sec(2.5), eye, cams)
    A.event(tk2 + 30, "iris_out")
    fs = S.fog_density_socket(fog6)
    fs.keyframe_insert("default_value", frame=tk2 + 40)
    fs.default_value = 0.0
    fs.keyframe_insert("default_value", frame=tk2 + 60)
    # end title
    title = C.text("end_title", "OBSOLETE?", size=0.006, loc=(0, 0.001, -0.099), rot=(0, 0, 0),
                   m=C.emission("title_m", (0.95, 0.9, 0.8), 3.0), parent=cam, coll=cams)
    title.parent = cam
    A.hide(title, 0, True)
    A.hide(title, END - C.sec(2.1), False)
    A.event(END - C.sec(2.1), "final_chord")
    return END
