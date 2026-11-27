"""SEQ 5 – Reclamation depot at night: break-in, the press, OBSOLETE, the double knock, the uprising, escape."""
import math
import bpy
from mathutils import Vector, Matrix
import core as C
import anim as A
import characters as CH
import props as P
import sets as S
import sets2 as S2
import build as B

V = Vector
D = S2.DEPOT
H = S2.HALL
BELT_V = 0.6


def Hd(x, y, z=0.0):
    return H + V((x, y, z))


def Dd(x, y, z=0.0):
    return D + V((x, y, z))


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(47)
    h, f, e = ctx.hedda, ctx.funke, ctx.erf
    dep = ctx.dep
    wld = S.world("W_S5_night", horizon=(0.06, 0.07, 0.12), zenith=(0.01, 0.012, 0.03), ground=(0.02, 0.02, 0.02),
                  strength=0.5)
    sc, L, cams = B.new_seq_scene(ctx, 5, "S5_Depot_Night", F, END, wld, [ctx.chars, ctx.c_dep, ctx.c_props])
    S.sun("S5_moon", (60, 0, 30), 0.9, (0.45, 0.6, 1.0), L, angle=5)
    ext_key = P.point_light("S5_extkey", Dd(-3, -9, 6), 6000, (0.75, 0.85, 1.0), 2.0, coll=L, kind="SPOT", spot=60,
                            rot=(55, 0, -20))
    S.fog_box("S5_fog_out", L, D + V((0, -20, 0)), (200, 120, 40), 0.012, (0.6, 0.65, 0.8))
    S.fog_box("S5_fog_in", L, H, (43, 23, 11.5), 0.02, (0.9, 0.7, 0.5), height_falloff=False)
    fill_in = P.point_light("S5_hallfill", Hd(0, -6, 6), 4000, (1.0, 0.65, 0.35), 6.0, coll=L, kind="AREA",
                            rot=(30, 0, 0))
    fill_in.data.size = 12
    P.point_light("S5_exitlight", Hd(-19, -6, 4), 800, (0.5, 0.65, 1.0), 1.0, coll=L)
    B.offstage_all(ctx, F, keep=(h, f, e))
    for d in ctx.decal_funke:
        A.hide(d, F, True)
    # ------------------------------------------------------------------ cages on the belt
    t_jam = T(31.0)  # the STOP button (see 5.5) – Funke's beat is timed backwards from here
    S.key_sat(sc, F, 0.72)
    S.key_sat(sc, t_jam, 0.72)
    S.key_sat(sc, t_jam + 24, 1.15)  # the machines rise
    t0 = F
    bz = dep["belt_z"]
    by = H.y

    def belt_x(x_at_jam, t):
        return x_at_jam - BELT_V * (t_jam - t) / C.FPS

    C.set_coll(ctx.c_props)
    cages = {}
    spec = [("funke", 9.2, 0, (1.1, 1.1, 1.0)), ("hedda", 7.0, None, (1.4, 1.4, 1.65)),
            ("juke", 4.9, 1, (1.1, 1.1, 1.0)), ("quad", 2.9, 2, (1.1, 1.1, 1.0)), ("vac", 0.9, 0, (1.1, 1.1, 1.0))]
    for name, xj, kind, size in spec:
        if name in ("funke", "hedda"):
            root, door = S2.cage(f"belt_cage_{name}", (0, 0, 0), ctx.c_props, size=size, lid=(name == "hedda"))
            if name == "hedda":  # its lid stands open until she is dropped in
                door.rotation_euler.x = math.radians(-110)
                door.keyframe_insert("rotation_euler", frame=t0, index=0)
        else:
            root, door = S2.cage_with_machine(f"belt_cage_{name}", (0, 0, 0), ctx.c_props, kind=kind,
                                              seed=hash(name) % 7)
        for t in (t0, t_jam):
            root.location = H + V((belt_x(xj, t), 0, bz))
            root.keyframe_insert("location", frame=t)
            A.set_interp(root, "location", t, "LINEAR")
        cages[name] = (root, door, xj)
    # moving belt: dark slats travelling with the belt (cyclic, one spacing per cycle) until the jam
    slat_m = C.mat("belt_slat", (0.02, 0.02, 0.02), rough=0.6, dirt=0.2)
    sp = 0.5
    per = sp / BELT_V * C.FPS
    for i in range(56):
        x0 = -19.8 + i * sp
        sl = C.box(f"belt_slat{i}", (0.06, 1.78, 0.012), loc=H + V((x0, 0, bz + 0.006)), m=slat_m, bevel=0,
                   coll=ctx.c_props)
        sl.keyframe_insert("location", frame=t0, index=0)
        sl.location.x += sp
        sl.keyframe_insert("location", frame=t0 + per, index=0)
        fc = sl.animation_data.action.fcurves.find("location", index=0)
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        cyc = fc.modifiers.new("CYCLES")
        cyc.use_restricted_range = True
        cyc.frame_start = t0
        cyc.frame_end = t0 + per * int((t_jam - t0) / per)  # stop on a cycle boundary: no jump
    # junk stream ahead of Funke's cage, crushed one by one by the press
    ram = dep["ram"]
    ram_up_z = ram.location.z
    px = dep["press_x"] - H.x
    junk_kinds = ["crate", "tv", "drum", "washer", "crate", "tv", "barrel_rust", "crate", "tv", "drum", "washer",
                  "crate", "tv", "drum"]
    crush_frames = []
    for i, k in enumerate(junk_kinds):
        xj = 9.2 + 1.7 + 1.5 * i  # x at jam (if it still existed)
        # time when it reaches the press
        tc = t_jam - int((xj - px) / BELT_V * C.FPS)
        if tc < t0 - 200:
            continue
        o = P.scrap_item(k, (0, 0, 0), (0, 0, 20 * i), 0.8, ctx.c_props)
        for t in (t0 - 200, tc):
            o.location = H + V((belt_x(xj, t), 0, bz + 0.3))
            o.keyframe_insert("location", frame=t)
            A.set_interp(o, "location", t, "LINEAR")
        if tc < t_jam:
            o.scale = (0.8, 0.8, 0.8)
            o.keyframe_insert("scale", frame=tc - 2)
            o.scale = (1.1, 1.1, 0.15)
            o.location = H + V((px, 0, bz + 0.05))
            o.keyframe_insert("scale", frame=tc + 2)
            o.keyframe_insert("location", frame=tc + 2)
            A.hide(o, tc + 30, True)
            crush_frames.append(tc)
    # ram pounding synced to the crushes
    for tc in crush_frames:
        if tc + 30 > t_jam:
            break
        ram.location.z = ram_up_z
        ram.keyframe_insert("location", frame=tc - 14, index=2)
        ram.location.z = ram_up_z - 5.5
        ram.keyframe_insert("location", frame=tc, index=2)
        A.set_interp(ram, "location", tc, "LINEAR")
        ram.keyframe_insert("location", frame=tc + 6, index=2)
        ram.location.z = ram_up_z
        ram.keyframe_insert("location", frame=tc + 26, index=2)
        A.event(tc, "press_slam")
    # jam: ram stuck halfway, shaking
    ram.location.z = ram_up_z
    ram.keyframe_insert("location", frame=t_jam - 4, index=2)
    ram.location.z = ram_up_z - 2.6
    ram.keyframe_insert("location", frame=t_jam + 2, index=2)
    A.shake(ram, t_jam + 2, t_jam + 40, amp=0.06, freq=1.5)
    A.event(t_jam, "press_jam")
    # beacon + lamp flicker after jam
    bs = C.emit_socket(dep["beacon_m"])
    fr = t_jam
    while fr < END:
        A.key_socket(bs, fr, 30.0, "CONSTANT")
        A.key_socket(bs, fr + 6, 0.0, "CONSTANT")
        A.key(dep["beacon_light"].data, "energy", fr, 400.0, "CONSTANT")
        A.key(dep["beacon_light"].data, "energy", fr + 6, 0.0, "CONSTANT")
        fr += 12
    A.event(t_jam + 6, "alarm", dur=END - t_jam - 6)
    rnd = C.R.__class__(5)
    for lamp in dep["lamps"]:
        A.key(lamp.data, "energy", t_jam, 2500.0)
        fr = t_jam
        while fr < t_jam + 40:
            A.key(lamp.data, "energy", fr, rnd.choice([0, 800, 2500, 300]), "CONSTANT")
            fr += rnd.randint(2, 5)
        A.key(lamp.data, "energy", fr, 1200.0, "CONSTANT")
    for i, lm in enumerate(dep["cb_lights"]):
        fr = t_jam - 6
        while fr < t_jam + 50:
            A.key_socket(C.emit_socket(lm), fr, rnd.choice([0, 8, 2]), "CONSTANT")
            fr += rnd.randint(2, 6)
    # sparks at the press
    for i in range(10):
        sp = C.sphere(f"press_spark{i}", 0.03, loc=(0, 0, -300), m=C.emission("spark_m", (1, 0.7, 0.3), 40),
                      seg=6, rings=3, coll=ctx.c_props)
        sp.keyframe_insert("location", frame=t_jam + i * 3)
        A.set_interp(sp, "location", t_jam + i * 3, "CONSTANT")
        p0 = Hd(px - 1.2, -1.7, 3.6)
        A.arc(sp, t_jam + i * 3 + 1, t_jam + i * 3 + 14, p0, p0 + V((rnd.uniform(-1.5, 0.5), rnd.uniform(-2, -0.5), -3.5)),
              height=0.8)
        A.hide(sp, t_jam + i * 3 + 15, True)
    # cage doors pop open
    for name, (root, door, xj) in cages.items():
        dt = rnd.randint(2, 14)
        door.keyframe_insert("rotation_euler", frame=t_jam + dt)
        if name == "hedda":  # the lid
            door.rotation_euler.x = math.radians(-110)
        else:
            door.rotation_euler.z = math.radians(-115)
        door.keyframe_insert("rotation_euler", frame=t_jam + dt + 5)
        A.event(t_jam + dt, "cage_pop")
    waiting_doors = [o for o in bpy.data.objects if o.name.startswith("h_wait") and o.name.endswith("_doorpiv")]
    for i, door in enumerate(waiting_doors):
        door.keyframe_insert("rotation_euler", frame=t_jam + 8 + i * 2)
        door.rotation_euler.z = math.radians(-110)
        door.keyframe_insert("rotation_euler", frame=t_jam + 13 + i * 2)
    # ------------------------------------------------------------------ Funke in his cage
    c_f = cages["funke"][0]
    fpos_local = V((0.0, 0.0, 0.05))
    f.cut(F, H + V((belt_x(9.2, F), 0, bz)) + fpos_local, 0)
    f.pose(F, "stand")
    f.pose(F, "sad")
    f.glow(F, 0.8, "bulb")
    f.glow(F, 1.5, "iris")
    A.key(ctx.funke_light.data, "energy", F, 0.8)
    for d in ctx.decal_funke:
        A.hide(d, F, False)
    con_fc = A.attach_to(f.rig, c_f, F, name="in_cage")
    cage_lamp = P.point_light("S5_cagelamp", H + V((belt_x(9.2, F), -0.8, bz + 0.9)), 25, (1.0, 0.7, 0.4), 0.1,
                              coll=L)
    A.attach_to(cage_lamp, c_f, F, name="cagelamp")
    f.blink(T(10.5))
    # ------------------------------------------------------------------ 5.1 exterior: Hedda slips through the hole
    hole = dep["hole"]
    h.cut(F, Dd(-12, -3), -60)
    h.pose(F, "stand")
    h.face(F, "angry")
    for d in ctx.decal_hedda:
        A.hide(d, F, True)
    hw = h.walk(F + 6, [Dd(-12, -3), Dd(-6, -1.8), hole + V((0, -1.3, 0)), hole + V((0, 1.5, 0))], speed=1.5,
                stride=0.45, style="sneak", end_pose=None)
    e.cut(F, Hd(-14, 2.8, dep["catwalk_z"]), -90)
    e.pose(F, "stand")
    e.glow(F, 3.0, "iris")
    e.bone_loc(F, "neck", (0, 0, 0))
    # floodlights sweep
    floods = [o for o in bpy.data.objects if o.name.startswith("d_flood") and o.type == "LIGHT"]
    for i, fl in enumerate(floods):
        base = fl.rotation_euler.z
        for k, fr in enumerate(range(F, T(6), 36)):
            fl.rotation_euler.z = base + math.radians(25 if (k + i) % 2 else -25)
            fl.keyframe_insert("rotation_euler", frame=fr, index=2)
    for i, cp in enumerate(dep["chimneys"]):
        P.smoke(f"S5_smoke{i}", cp, F - 80, T(6), coll=ctx.c_props, every=10, rise=8.0, life=90, size=1.2,
                color=(0.25, 0.25, 0.28), seed=20 + i)
    B.shot(ctx, 5, "S5_c1_fence", F, [(F, Dd(5, -10, 1.6), Dd(-5, 1, 2.2)), (F + 40, Dd(4.4, -9.6, 1.6), Dd(-4.5, 0.5, 1.9))],
           lens=28)
    # then close on her: she sneaks along the fence towards the hole, the camera keeps pace on the outside
    sn = []
    for t_ in list(range(F + 40, T(5), 8)) + [T(5)]:
        hp_ = h.pos_at(min(t_, hw - 30))
        sn.append((t_, hp_ + V((1.4, -3.1, 1.25)), hp_ + V((0.3, 0, 0.95))))
    B.shot(ctx, 5, "S5_c1b_sneak", F + 40, sn, lens=32)
    # a cold fill keeps her readable against the black fence (the floodlights do the drama)
    fill = P.point_light("S5_hfill", h.pos_at(F) + V((1.2, -2.0, 2.2)), 45, (0.6, 0.7, 1.0), 0.6, coll=L)
    A.attach_to(fill, h.rig, F, name="fill")
    A.key(fill.data, "energy", F, 45.0)
    A.key(fill.data, "energy", T(5), 45.0, "CONSTANT")
    A.key(fill.data, "energy", T(5) + 1, 0.0, "CONSTANT")
    # ------------------------------------------------------------------ 5.2 interior: belt, press, Funke caged
    B.shot(ctx, 5, "S5_c2_hall", T(5), [(T(5), Hd(-19, -10, 7.5), Hd(6, 0, 2.0)), (T(9.5), Hd(-16, -10.5, 6.5), Hd(7, 0, 2.5))],
           lens=22)
    B.shot(ctx, 5, "S5_c2b_funke", T(9.5), [(T(9.5), Hd(belt_x(9.2, T(9.5)) - 0.3, -1.7, 1.6), Hd(belt_x(9.2, T(9.5)), 0, 1.3)),
                                            (T(12.5), Hd(belt_x(9.2, T(12.5)) - 0.2, -1.6, 1.6), Hd(belt_x(9.2, T(12.5)), 0, 1.3))],
           lens=45)
    # ------------------------------------------------------------------ 5.3 Hedda on the catwalk, netted, stamped
    cz = dep["catwalk_z"] + 0.04
    tcw = T(12.5)
    h.cut(tcw, Hd(-9.5, 2.75, cz), -90)
    h.pose(tcw, "stand")
    h.face(tcw, "angry")
    tgt_x = belt_x(9.2, T(19.5)) - 0.4
    hc = h.walk(tcw, [Hd(-9.5, 2.75, cz), Hd(tgt_x, 2.75, cz)], speed=1.7, stride=0.45, style="sneak",
                end_pose=None)
    h.place(hc + 2, Hd(tgt_x, 2.6, cz), 0)
    h.pose(hc + 6, "crouch")
    h.pose(hc + 6, {"upper_arm_R": (80, 0, 10), "forearm_R": (10, 0, 0), "head": (20, 0, 0)})
    h.face(hc + 6, "worried")
    # Erfasser rolls up behind her on the catwalk; the catch pole's ring (its net rolled up to a short frill)
    # comes down over her head and pins her arms
    hp = Hd(tgt_x, 2.6, cz)
    yaw_s = math.degrees(A.yaw_towards(V((1, 0, 0))))
    rz = Matrix.Rotation(math.radians(yaw_s), 3, "Z")
    E_s = hp - rz @ e.net_offset("net_shoulder")
    E_s.z = cz
    te = e.roll(T(14.0), [Hd(-14, 2.8, cz), E_s], speed=1.9, lean=6)
    e.place(te + 2, E_s, yaw_s)
    tn = max(te + 8, hc + 14)
    nm_ = e.extra["net"]
    for fr_, z_ in ((tn - 14, -1.0), (tn - 8, 0.18)):
        nm_.scale = (1, 1, z_)
        nm_.keyframe_insert("scale", frame=fr_, index=2)
    e.pose(tn - 12, "net_ready")
    e.pose(tn, "net_shoulder", interp="LINEAR")
    A.event(tn - 4, "whoosh")
    A.event(tn, "net_catch")
    hoop = bpy.data.objects["Erfasser_hoop"]
    h.face(tn - 6, "surprised")
    con_hn = A.attach_loc(h.rig, hoop, tn, name="netted")
    pinned = {"upper_arm_L": (5, 0, 4), "upper_arm_R": (5, 0, 4), "forearm_L": (30, 0, 0), "forearm_R": (30, 0, 0)}
    h.pose(tn + 3, pinned)
    # he hauls her up off the catwalk: she dangles in the ring, kicking
    tup = tn + 8
    e.pose(tup, "net_shoulder")
    e.pose(tup + 12, "net_up")
    h.pose(tup + 12, "stand")
    h.pose(tup + 12, pinned)
    for k in range(6):
        a_, b_ = (35, -10) if k % 2 else (-10, 35)
        h.pose(tup + 12 + k * 5, {"thigh_L": (a_, 0, 4), "thigh_R": (b_, 0, 4), "shin_L": (-40, 0, 0), "shin_R": (-40, 0, 0)})
    h.face(tup + 10, "angry")
    A.event(tup + 6, "struggle")
    # stamp on the forehead: she swings in to the stamp
    yaw_hf = math.degrees(A.yaw_towards(V((-1, 0, 0))))  # dangling, she turns to face him
    h.place(tup + 4, None, 0)
    h.place(tup + 16, None, yaw_hf)
    hit = e.stamp(tn + 34, keep_right=True)
    pad = E_s + rz @ e.stamp_offset()
    brow = A.world_matrix_at(h.rig, hit, "head").translation + V((0, 0, 0.13)) + \
        Matrix.Rotation(math.radians(yaw_hf), 3, "Z") @ V((0, -0.11, 0))
    swing = pad - brow
    print("seq5 stamp swing", round(swing.length, 2))
    h.place(hit - 9, hp)
    h.place(hit - 1, hp + swing)
    h.place(hit + 8, hp + swing * 0.6)
    for d in ctx.decal_hedda:
        A.hide(d, hit, False)
    h.face(hit, "closed")
    h.face(hit + 10, "angry")
    # he turns to the belt, holds her out over the railing - and lets go: she drops into the big cage, whose
    # lid stands open, and the lid slams shut
    c_h, lid_h = cages["hedda"][0], cages["hedda"][1]
    yaw_b = math.degrees(A.yaw_towards(V((0, -1, 0))))
    out_ = {"arm_R": (95, 0, 5), "fore_R": (0, 0, 0), "hand_R": (-75, 0, 0), "body": (-6, 0, 0)}
    off_out = Matrix.Rotation(math.radians(yaw_b), 3, "Z") @ e.net_offset(out_)
    # he rolls along the catwalk with her dangling until her cage (travelling on the belt) is below
    tr0 = hit + 18
    xd = E_s.x
    for _ in range(4):
        troll = tr0 + max(6, int(round(abs(xd - E_s.x) / 1.3 * C.FPS)))
        tdrop = troll + 22
        xd = A.world_matrix_at(c_h, tdrop + 14).translation.x - off_out.x
    E_d = V((xd, E_s.y, cz))
    troll = e.roll(tr0, [E_s, E_d], speed=1.3, lean=5)
    tdrop = troll + 22
    h.place(hit + 30, hp + swing * 0.2)
    # turns to the belt, holds her out over the railing - and lets go
    e.place(troll + 2, None, yaw_s)
    e.place(troll + 12, E_d, yaw_b)
    e.pose(troll + 4, "net_up")
    e.pose(troll + 16, out_)
    e.pose(tdrop, out_)
    A.detach(h.rig, con_hn, tdrop)
    nm_.scale = (1, 1, 0.18)
    nm_.keyframe_insert("scale", frame=tdrop + 6, index=2)
    nm_.scale = (1, 1, -1.0)
    nm_.keyframe_insert("scale", frame=tdrop + 14, index=2)
    cage_pos = A.world_matrix_at(c_h, tdrop + 14).translation
    A.arc(h.rig, tdrop + 1, tdrop + 14, A.world_matrix_at(h.rig, tdrop).translation, cage_pos + V((0, 0, 0.05)),
          height=0.5)
    h.pose(tdrop + 6, {"upper_arm_L": (150, 0, 30), "upper_arm_R": (150, 0, 30), "thigh_L": (30, 0, 4),
                       "thigh_R": (30, 0, 4)})
    A.event(tdrop + 14, "thud")
    h.pose(tdrop + 14, "crouch")
    h.place(tdrop + 15, cage_pos + V((0, 0, 0.05)), -90)
    con_hc = A.attach_to(h.rig, c_h, tdrop + 15, name="in_cage")
    lid_h.rotation_euler.x = math.radians(-110)
    lid_h.keyframe_insert("rotation_euler", frame=tdrop + 15, index=0)
    lid_h.rotation_euler.x = 0.0
    lid_h.keyframe_insert("rotation_euler", frame=tdrop + 19, index=0)
    A.event(tdrop + 19, "cage_slam")
    e.pose(tdrop + 20, "stand")
    # walking backwards ahead of her: we see her set face - and the Erfasser rolling up behind her before she does
    t_wide = tn - 26
    fk = []
    for t_ in list(range(tcw, t_wide, 8)) + [t_wide]:
        hp_ = h.pos_at(min(t_, hc))
        fk.append((t_, hp_ + V((2.9, 0.45, 2.3)), hp_ + V((-1.2, -0.1, 0.95))))
    B.shot(ctx, 5, "S5_c3a_ahead", tcw, fk, lens=34)
    B.shot(ctx, 5, "S5_c3_catwalk", t_wide, [(tcw, Hd(-12, 0.8, 5.2), Hd(-6, 2.8, 4.3)),
                                          (tn, Hd(tgt_x - 6.0, 0.4, 5.3), Hd(tgt_x - 1, 2.8, 4.4))], lens=28)
    B.shot(ctx, 5, "S5_c3b_stamp", tn + 10, [(tn + 10, Hd(tgt_x + 2.6, 0.2, 4.4), Hd(tgt_x - 1.4, 2.7, 5.5))], lens=24)
    B.shot(ctx, 5, "S5_c3c_drop", tdrop - 4, [(tdrop - 4, Hd(tgt_x + 1.5, -4.5, 2.6), Hd(tgt_x + 1.5, 0.5, 2.0))], lens=26)
    # ------------------------------------------------------------------ 5.4 Funke squeezes out
    # his whole beat is anchored to the jam: squeeze out, jump onto the platform, find the STOP button,
    # press it twice (the double knock) – and only then does the press jam
    plat = dep["control_box"]
    btn = dep["stop_button"]
    tk2 = t_jam - 6           # second press
    tk1 = tk2 - 14            # first press
    tlook = tk1 - 22          # he finds the button
    tj = tlook - 22           # jump (lands at tj + 14)
    tsq = tj - 28
    if tsq < tdrop + 22:
        print("WARNING seq5: Funke's beat starts", tdrop + 22 - tsq, "frames too early - move t_jam later")
    f.pose(tsq - 10, "stand")
    f.pose(tsq - 10, {"lid": (-95, 0, 0), "head": (-10, 0, 0)})
    f.glow(tsq - 10, 4.0, "iris")
    f.glow(tsq - 10, 4.0, "bulb")
    A.event(tsq - 10, "determined")
    A.detach(f.rig, con_fc, tsq)
    p_in = f.pos_at(tsq)
    yaw_out = 0.0  # face -Y (toward the control platform side)
    f.place(tsq + 1, p_in, yaw_out)
    p_bars = p_in + V((0, -0.55, 0))
    # stays with belt motion meanwhile (cheat: small x drift)
    f.place(tsq + 14, p_bars + V((BELT_V * 14 / C.FPS, 0, 0)), yaw_out)
    f.bone_scale(tsq + 4, "body", (1, 1, 1))
    f.bone_scale(tsq + 8, "body", (0.35, 1.3, 1.35))
    f.bone_scale(tsq + 14, "body", (0.35, 1.3, 1.35))
    f.bone_scale(tsq + 18, "body", (1.2, 0.9, 0.85))
    f.bone_scale(tsq + 22, "body", (1, 1, 1))
    A.event(tsq + 8, "squeeze")
    A.event(tsq + 16, "pop")
    p_out = p_bars + V((BELT_V * 22 / C.FPS, -0.25, 0))
    f.place(tsq + 22, p_out, yaw_out)
    h.face(tsq + 16, "surprised")
    # ------------------------------------------------------------------ 5.5 onto the platform: the STOP button
    yaw_btn = math.degrees(A.yaw_towards(V((1, 0, 0))))
    land = V((btn.location.x - 0.34, btn.location.y, plat.z))  # in front of the box, the button at arm's height
    A.arc(f.rig, tj, tj + 14, p_out + V((BELT_V * 6 / C.FPS, 0, 0)), land, height=0.9)
    f.pose(tj + 4, "happy")
    A.event(tj + 14, "land_spring")
    f.place(tj + 16, land, yaw_btn)
    f.pose(tj + 16, "stand")
    # looks around - up at the press, then at the button: there it is
    f.pose(tlook - 6, {"head": (-20, 0, 35)})
    f.pose(tlook, {"head": (-5, 0, 0)})
    f.glow(tlook + 2, 9.0, "iris")
    f.pose(tlook + 6, {"lid": (-95, 0, 0), "head": (5, 0, 0)})
    A.event(tlook + 2, "ping")
    bs0 = V(btn.location)
    btn.keyframe_insert("location", frame=F)
    for tp_ in (tk1, tk2):
        f.pose(tp_ - 6, {"arm_R": (70, 0, 0), "fore_R": (70, 0, 0), "body": (-6, 0, 0)})
        f.pose(tp_, {"arm_R": (92, 0, 0), "fore_R": (0, 0, 0), "body": (8, 0, 0)}, interp="LINEAR")
        f.pose(tp_ + 5, {"arm_R": (80, 0, 0), "fore_R": (25, 0, 0), "body": (0, 0, 0)})
        btn.location = bs0
        btn.keyframe_insert("location", frame=tp_ - 1)
        btn.location = bs0 + V((0.028, 0, 0))
        btn.keyframe_insert("location", frame=tp_)
        btn.keyframe_insert("location", frame=tp_ + 2)
        btn.location = bs0
        btn.keyframe_insert("location", frame=tp_ + 6)
        A.event(tp_, "knock_metal")
        for lm in dep["cb_lights"]:
            A.key_socket(C.emit_socket(lm), tp_ - 1, 4.0, "CONSTANT")
            A.key_socket(C.emit_socket(lm), tp_, 14.0, "CONSTANT")
            A.key_socket(C.emit_socket(lm), tp_ + 3, 4.0, "CONSTANT")
    f.pose(tk2 + 12, "happy")
    B.shot(ctx, 5, "S5_c4_squeeze", tsq - 12, [(tsq - 12, Hd(belt_x(9.2, tsq) + 0.4, -2.6, 1.5), Hd(belt_x(9.2, tsq), -0.3, 1.2)),
                                              (tj, Hd(belt_x(9.2, tj) + 0.2, -2.7, 1.5), Hd(belt_x(9.2, tj), -0.5, 1.2))],
           lens=32)
    B.shot(ctx, 5, "S5_c5_knock", tj, [(tj, Hd(4.0, -6.2, 2.4), V((plat.x - 0.4, plat.y, plat.z + 0.5))),
                                       (tlook, Hd(4.2, -6.0, 2.4), V((plat.x - 0.4, plat.y, plat.z + 0.5)))], lens=26)
    # close on Funke and the button: we see him find it and press it, twice
    bmid = V((btn.location.x - 0.17, btn.location.y, btn.location.z - 0.05))
    B.shot(ctx, 5, "S5_c5b_button", tlook - 4, [(tlook - 4, bmid + V((-0.55, -1.15, 0.12)), bmid),
                                                (tk2 + 8, bmid + V((-0.45, -0.95, 0.08)), bmid)], lens=35)
    # ... and the press, three seconds from crushing his empty cage, jams
    B.shot(ctx, 5, "S5_c5c_jam", tk2 + 8, [(tk2 + 8, Hd(px - 6.0, -7.5, 2.0), Hd(px, 0, 3.2)),
                                           (t_jam + 20, Hd(px - 5.6, -7.2, 2.1), Hd(px, 0, 3.0))], lens=28)
    # ------------------------------------------------------------------ 5.6 uprising
    tu = t_jam + 24
    # vacuum bot zooms in circles out of its cage
    vac_root = cages["vac"][0]
    vac = [o for o in vac_root.children if o.name.endswith("_vac")]
    juke_root = cages["juke"][0]
    jglow = bpy.data.materials.get("jb_glow")
    if jglow:
        A.key_socket(C.emit_socket(jglow), tu, 1.5)
        A.key_socket(C.emit_socket(jglow), tu + 6, 12.0)
    A.event(tu + 6, "jukebox_start", beat=12)
    # make a free-roaming vacuum (copy) that drives a loop on the floor
    vroot = C.empty("free_vac", loc=(0, 0, -300), coll=ctx.c_props)
    C.cyl("free_vac_body", 0.3, 0.25, loc=(0, 0, 0.15), m=C.mat("p_red"), parent=vroot, coll=ctx.c_props)
    C.sphere("free_vac_eye", 0.05, loc=(0, -0.28, 0.24), m=C.emission("happy_eye", (0.4, 1.0, 0.5), 4.0),
             parent=vroot, coll=ctx.c_props)
    vroot.keyframe_insert("location", frame=tu - 1)
    A.set_interp(vroot, "location", tu - 1, "CONSTANT")
    center = Hd(2.5, -3.0)
    for k in range(25):
        a = k / 6.0 * math.pi
        rr = 2.2 + 0.6 * math.sin(k)
        vroot.location = center + V((math.cos(a) * rr, math.sin(a) * rr * 0.7, 0))
        vroot.rotation_euler.z = a + math.pi
        vroot.keyframe_insert("location", frame=tu + k * 6)
        vroot.keyframe_insert("rotation_euler", frame=tu + k * 6)
    A.hide(vac[0], tu, True) if vac else None
    A.event(tu, "vacuum_zoom", dur=150)
    # Hedda climbs out of her cage
    A.detach(h.rig, con_hc, tu + 4)
    hp = h.pos_at(tu + 4)
    hfloor = Hd(5.0, -2.0)  # clear of the cage doors and the control platform
    A.arc(h.rig, tu + 6, tu + 22, hp, hfloor, height=2.1)  # up and out over the cage wall (the lid is open)
    h.pose(tu + 20, "stand")
    h.face(tu + 20, "happy")
    h.place(tu + 22, hfloor, math.degrees(A.yaw_towards(V((plat.x, plat.y)) - V((hfloor.x, hfloor.y)))))
    # Erfasser jumps down from the catwalk and charges
    tE = t_jam + 44  # the burst gets its moment before he leaps
    e.hold_all(tE - 1)
    ep = e.pos_at(tE)
    efloor = Hd(ep.x - H.x - 0.5, -1.9)  # leaps over the belt to the near side
    A.arc(e.rig, tE, tE + 16, ep, efloor, height=1.4)
    A.event(tE + 16, "heavy_land")
    e.pose(tE + 16, {"body": (20, 0, 0)})
    e.pose(tE + 22, "stand")
    e.glow(tE + 16, 15.0, "iris")
    tE2 = e.roll(tE + 24, [efloor, Hd(3.2, -2.6)], speed=2.2, lean=12)
    # the vacuum crosses his path: trip, spin, net over his own head, self-stamp
    ttr = tE2
    A.event(ttr, "bonk")
    epos = e.pos_at(ttr)
    y0 = e.yaw_at(ttr)
    for k, (dt, dy) in enumerate(((4, 150), (8, 320), (12, 470), (18, 560))):
        e.place(ttr + dt, epos + V((0.1 * k, -0.15 * k, 0)), y0 + dy)
    e.pose(ttr + 4, "tangled")
    e.pose(ttr + 10, {"arm_R": (170, 0, 0), "fore_R": (40, 0, 0), "hand_R": (120, 0, 0)})  # hoop over his own hat
    A.event(ttr + 10, "net_catch")
    e.pose(ttr + 16, {"arm_L": (120, 0, -30), "fore_L": (90, 0, 0), "hand_L": (-60, 0, 0)})
    e.pose(ttr + 21, {"arm_L": (95, 0, -40), "fore_L": (120, 0, 0), "hand_L": (-90, 0, 0)}, interp="LINEAR")
    A.event(ttr + 21, "stamp")
    for d in ctx.decal_erf:
        A.hide(d, ttr + 21, False)
    e.glow(ttr + 21, 0.5, "iris", "CONSTANT")
    e.glow(ttr + 30, 3.0, "iris", "CONSTANT")
    e.glow(ttr + 34, 0.5, "iris", "CONSTANT")
    # topples into Funke's (empty, open) cage – door slams
    c_root, c_door, _ = cages["funke"]
    cpos = A.world_matrix_at(c_root, ttr + 40).translation
    A.arc(e.rig, ttr + 28, ttr + 42, e.pos_at(ttr + 28), cpos + V((0, 0, 0.05)), height=2.6)  # sails over Hedda
    e.bone_scale(ttr + 40, "body", (1, 1, 1))
    e.bone_scale(ttr + 44, "body", (1.3, 1.3, 0.42))
    e.pose(ttr + 44, "tangled")
    c_door.keyframe_insert("rotation_euler", frame=ttr + 44)
    c_door.rotation_euler.z = 0
    c_door.keyframe_insert("rotation_euler", frame=ttr + 48)
    A.event(ttr + 48, "cage_slam")
    for d in ctx.decal_funke:
        A.hide(d, ttr + 30, True)
    # Funke hops down to Hedda; she scoops him up
    tf = ttr + 20
    f.hold_all(tf - 1)
    f_by_h = hfloor + V((-0.65, -0.3, 0))
    A.arc(f.rig, tf, tf + 16, f.pos_at(tf), f_by_h, height=1.1)
    A.event(tf + 16, "land_spring")
    f.pose(tf + 16, "happy")
    tsc = ttr + 52
    h.pose(tsc - 6, "bend_down")
    f.place(tsc, f_by_h, None)
    hm = A.world_matrix_at(h.rig, tsc + 8, "chest")
    f.place(tsc + 8, A.carry_spot(h, tsc + 8), h.yaw_at(tsc + 8))
    con_c = A.attach_to(f.rig, h.rig, tsc + 8, bone="chest", name="carried5")
    h.pose(tsc + 8, "carry")
    h.face(tsc + 10, "happy")
    # quadruped + jukebox roll off the belt and follow (simple hops)
    for nm, dx in (("quad", -1.0), ("juke", -2.0)):
        r_, _, _ = cages[nm]
        mach = [o for o in r_.children if not o.name.endswith(("_bars", "_floor", "_doorpiv"))]
        for o in mach:
            o.keyframe_insert("location", frame=tu + 10)
            lp = V(o.location)
            o.location = lp + V((0, 0.9, 0.35))  # hop off the far side of the belt
            o.keyframe_insert("location", frame=tu + 19)
            o.location = lp + V((0, 1.7, -0.95))
            o.keyframe_insert("location", frame=tu + 26)
            A.event(tu + 26, "clunk_land")
    # the uprising in three beats: cages burst and the vacuum zooms out under Hedda's feet,
    # the Erfasser's leap from the catwalk (from below), then the wide on the chaos
    B.shot(ctx, 5, "S5_c6a_burst", t_jam + 20, [(t_jam + 20, Hd(1.2, -6.6, 1.3), Hd(4.2, -1.6, 1.1)),
                                                (tE, Hd(1.8, -6.2, 1.25), Hd(4.6, -1.8, 1.0))], lens=30)
    B.shot(ctx, 5, "S5_c6a_leap", tE, [(tE, efloor + V((2.4, -3.4, 0.35)), ep + V((0, 0, 0.6))),
                                       (tE + 16, efloor + V((2.2, -3.1, 0.35)), efloor + V((0, 0, 1.3))),
                                       (tE + 22, efloor + V((2.1, -3.0, 0.4)), efloor + V((0, 0, 1.2)))], lens=24)
    B.shot(ctx, 5, "S5_c6_uprising", tE + 22, [(t_jam + 20, Hd(-3.5, -8.5, 2.2), Hd(4.0, -1.5, 1.2)),
                                                 (tsc + 20, Hd(-3.0, -8.0, 2.4), Hd(4.0, -1.5, 1.4))], lens=26)
    B.shot(ctx, 5, "S5_c6b_selfstamp", ttr + 8, [(ttr + 8, Hd(1.6, -5.4, 2.0), epos + V((0, 0, 1.6)))], lens=35)
    B.shot(ctx, 5, "S5_c6c_cage", ttr + 30, [(ttr + 30, Hd(belt_x(9.2, t_jam) - 1.0, -3.6, 1.6), cpos + V((0, 0, 0.7)))],
           lens=32)
    # ------------------------------------------------------------------ 5.7 escape
    tx = tsc + 26
    h.hold_place(tx - 1)
    hx = h.walk(tx, [hfloor, Hd(-6, -4.5), dep["exit"], dep["exit"] + V((-2.6, 0, 0))], speed=3.8, stride=0.85, style="run", end_pose=None)
    fr = tx
    while fr < hx:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    vroot.keyframe_insert("location", frame=tx + 20)
    vroot.location = dep["exit"] + V((1.5, 0.5, 0))
    vroot.keyframe_insert("location", frame=hx + 20)
    B.shot(ctx, 5, "S5_c7_run", tx, [(tx, Hd(-4, -8.5, 1.6), hfloor + V((0, 0, 1.0))),
                                     (hx, Hd(-12, -9.5, 1.6), dep["exit"] + V((0, 0, 1.0)))], lens=26)
    # mid-run: close on the two of them from the front, the vacuum bot tagging along behind
    run_cam = bpy.data.objects["S5_c7_run"]
    tm0 = tx + int((hx - tx) * 0.4)
    tm1 = tm0 + 40
    rk = []
    for t_ in range(tm0, tm1 + 1, 4):
        hp_ = h.pos_at(t_)
        fw = h.pos_at(t_ + 4) - hp_
        fw.z = 0
        fw = fw.normalized() if fw.length > 1e-4 else V((-1, 0, 0))
        sd_ = V((-fw.y, fw.x, 0))
        rk.append((t_, hp_ + fw * 2.4 + sd_ * 0.7 + V((0, 0, 1.25)), hp_ + V((0, 0, 1.15))))
    B.shot(ctx, 5, "S5_c7b_runclose", tm0, rk, lens=32)
    rf = P.point_light("S5_runfill", h.pos_at(tm0) + V((-1.5, -0.6, 1.9)), 0, (1.0, 0.75, 0.5), 0.5, coll=L)
    A.attach_to(rf, h.rig, tm0 - 1, name="fill")
    A.key(rf.data, "energy", F, 0.0, "CONSTANT")
    A.key(rf.data, "energy", tm0, 60.0, "CONSTANT")
    A.key(rf.data, "energy", tm1 + 1, 0.0, "CONSTANT")
    mk = sc.timeline_markers.new("S5_c7_run_back", frame=tm1 + 1)
    mk.camera = run_cam
    # exterior: out through the hole, sirens
    to = hx + 6
    h.cut(to, hole + V((0, 3.5, 0)), 180)
    h.pose(to, "carry")
    ho = h.walk(to, [hole + V((0, 3.5, 0)), hole + V((0, -1.2, 0)), Dd(-8, -8), Dd(-14, -16)], speed=3.8, stride=0.85,
                style="run", end_pose=None)
    fr = to
    while fr < ho:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    vroot.keyframe_insert("location", frame=to - 1)
    A.set_interp(vroot, "location", to - 1, "CONSTANT")
    vroot.location = hole + V((0.7, 4.6, 0))
    A.hold_obj(vroot, to - 1, ("rotation_euler",))
    vroot.rotation_euler = (0, 0, 0)
    vroot.keyframe_insert("location", frame=to)
    vroot.keyframe_insert("rotation_euler", frame=to)
    A.set_interp(vroot, "rotation_euler", to - 1, "CONSTANT")
    vroot.location = hole + V((0.2, -1.0, 0))
    vroot.keyframe_insert("location", frame=to + 22)
    vroot.keyframe_insert("rotation_euler", frame=to + 22)
    vroot.rotation_euler.z = math.radians(-30)
    vroot.keyframe_insert("rotation_euler", frame=to + 30)
    vroot.location = Dd(-12, -15)
    vroot.keyframe_insert("location", frame=ho + 20)
    siren = P.point_light("S5_siren", Dd(0, 4.5, 8.5), 0, (1, 0.05, 0.02), 1.0, coll=L)
    A.key(siren.data, "energy", F, 0.0, "CONSTANT")
    fr = to
    while fr < ho + 60:
        A.key(siren.data, "energy", fr, 20000.0, "CONSTANT")
        A.key(siren.data, "energy", fr + 8, 0.0, "CONSTANT")
        fr += 16
    END = min(ho + C.sec(1.5), to + C.sec(4.4))
    B.set_end(ctx, 5, END)
    B.shot(ctx, 5, "S5_c8_out", to, [(to, Dd(-2, -6, 1.4), hole + V((0, 0, 1.2))), (END, Dd(-4, -9, 1.5), Dd(-12, -14, 1.0))],
           lens=24)

    def sweep(base_fn, f0_, lock_, amp=1.6, z=0.0):
        """look around (decaying side-to-side search) until the lock, then sit on the target"""
        def fn(fr):
            b_ = base_fn(fr)
            k = max(0.0, 1.0 - (fr - f0_) / max(1, lock_ - f0_))
            return b_ + V((math.cos(fr * 0.11) * amp * k, math.sin(fr * 0.07) * amp * 0.4 * k, z * k))
        return fn
    # ---- the Erfasser's eyes: now it scans her
    import pov
    pf0, pf1 = tn + 6, hit - 3
    pov.pov_shot(ctx, 5, "S5_pov_hedda", pf0, pf1, pov.erf_eye(e),
                 sweep(pov.bone_pos(h, "head", 0.12), pf0, tn + 12, amp=0.6), lens=50, lock=tn + 12,
                 lines=[(tn + 12, "HUMAN", None), (tn + 17, "AGE       71", None),
                        (tn + 22, "OUTPUT    0 UNITS / DAY", (1, 0.6, 0.2))],
                 verdict=(tn + 27, "OBSOLETE"))
    return END
