"""SEQ 4 – The chase: village alley (laundry, bucket of bolts, barrel) and scrapyard (net, stamp, truck)."""
import math
import bpy
from mathutils import Vector
import core as C
import anim as A
import characters as CH
import props as P
import sets as S
import sets2 as S2
import build as B

V = Vector
O = S2.VILLAGE


def Wv(x, y, z=0.0):
    return O + V((x, y, z))


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(33)
    h, f, e = ctx.hedda, ctx.funke, ctx.erf
    tr = ctx.truck
    wld = S.world("W_S4_afternoon", horizon=(1.0, 0.7, 0.45), zenith=(0.3, 0.42, 0.65), ground=(0.15, 0.12, 0.1),
                  strength=0.8, sun_dir=(-0.6, 0.6, 0.35), sun_color=(1, 0.75, 0.45), sun_glow=2.0)
    sc, L, cams = B.new_seq_scene(ctx, 4, "S4_Chase", F, END, wld,
                                  [ctx.chars, ctx.c_vil, ctx.c_scrap, ctx.c_city, ctx.c_props])
    S.sun("S4_sun", (67, 0, -130), 4.8, (1.0, 0.74, 0.5), L, angle=2)
    S.sun("S4_sky", (30, 0, 40), 0.3, (0.6, 0.7, 0.95), L, angle=40)
    S.fog_box("S4_fogv", L, O, (300, 300, 50), 0.005, (0.95, 0.8, 0.6))
    S.fog_box("S4_fogs", L, (0, 120, 0), (520, 640, 70), 0.006, (0.9, 0.72, 0.55))
    # villagers stay frozen where seq3 left them; only the three principals move
    s3 = ctx.s3
    hstop = s3["hstop"]
    A.hold_obj(tr["root"], F - 1, ("location", "rotation_euler"))
    A.set_interp(tr["root"], "location", F - 1, "CONSTANT")
    # ------------------------------------------------------------------ 4.1 grab & run
    h.hold_all(F)
    f.hold_all(F)
    e.hold_all(F)
    tg = T(0.4)
    table = s3["table"]
    h.face(tg, "angry")
    h.pose(tg, {"upper_arm_L": (70, 0, 10), "upper_arm_R": (70, 0, 10), "forearm_L": (20, 0, 0), "forearm_R": (20, 0, 0),
                "spine": (20, 0, 0)})
    # Funke into her arms
    tgrab = tg + 8
    mw = A.world_matrix_at(h.rig, tgrab, "chest")
    hold_spot = mw @ V((0, 0.05, -0.32))
    f.place(tgrab, f.pos_at(tgrab), f.yaw_at(tgrab))
    f.place(tgrab + 6, A.carry_spot(h, tgrab + 6), h.yaw_at(tgrab))
    f.pose(tgrab + 6, "scared")
    con1 = A.attach_to(f.rig, h.rig, tgrab + 6, bone="chest", name="carried1")
    h.pose(tgrab + 6, "carry")
    A.event(tgrab + 2, "whoosh_small")
    # run to the east alley
    run1 = [hstop, Wv(7.0, 1.8), Wv(12.5, 0.2), Wv(18, 0.0)]
    tr1 = h.walk(tgrab + 10, run1, speed=4.2, stride=0.9, style="run", end_pose=None)
    # keep the carrying arms while running
    fr = tgrab + 10
    while fr < tr1:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    # Erfasser pursues
    te1 = e.roll(tgrab + 22, [s3["erf_end"], Wv(2.6, -5.5), Wv(3.4, -1.0), Wv(8.0, 0.4), Wv(12.5, 0.2), Wv(18, 0.0)],
                 speed=3.6, lean=14)
    A.event(tgrab + 22, "chase_start")
    B.shot(ctx, 4, "S4_c1_grab", F, [(F, hstop + V((-2.0, -2.3, 1.3)), hstop + V((0.6, 0.6, 1.0))),
                                     (tgrab + 14, hstop + V((-1.4, -2.6, 1.35)), hstop + V((1.2, -0.8, 1.0)))], lens=28)
    # she runs past the camera into the alley; the camera pans with her
    mouth = Wv(11.6, -1.6, 1.3)
    mk_keys = []
    for t_ in range(tgrab + 20, tr1 + 1, 6):
        hp_ = h.pos_at(t_) + V((0, 0, 1.0))
        mk_keys.append((t_, mouth, hp_ if (hp_ - mouth).length > 1.4 else hp_ + (hp_ - mouth).normalized() * 1.4))
    B.shot(ctx, 4, "S4_c1b_mouth", tgrab + 20, mk_keys, lens=26)
    # ------------------------------------------------------------------ 4.2 laundry
    # Hedda runs through the alley under the laundry; the Erfasser gets a sheet on his hat
    run2 = [Wv(18, 0.0), Wv(26, 0.4), Wv(34, -0.2)]
    tr2 = h.walk(tr1, run2, speed=4.2, stride=0.9, style="run", end_pose=None)
    fr = tr1
    while fr < tr2:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    laundry = ctx.vil["laundry"]
    # the sheet on line 2 (x≈21) catches on the Erfasser's hat
    sheet = min(laundry, key=lambda cl: abs(cl.location.x - Wv(21.5, 0).x) + abs(cl.location.y - O.y))
    xa, xb = 18.0, 28.5
    te2 = e.roll(te1, [Wv(xa, 0.0), Wv(xb, 0.2)], speed=3.4, lean=14)
    t_sheet = te1 + int((sheet.location.x - Wv(xa, 0).x) / (xb - xa) * (te2 - te1))
    e_head = A.world_matrix_at(e.rig, t_sheet, "head").translation
    sheet.keyframe_insert("location", frame=t_sheet - 1)
    sheet.keyframe_insert("rotation_euler", frame=t_sheet - 1)
    sheet.location = e_head + V((0, 0.0, 0.2))
    sheet.rotation_euler = (math.radians(-10), 0, math.radians(90))
    sheet.keyframe_insert("location", frame=t_sheet)
    sheet.keyframe_insert("rotation_euler", frame=t_sheet)
    A.set_interp(sheet, "location", t_sheet - 1, "CONSTANT")
    A.set_interp(sheet, "rotation_euler", t_sheet - 1, "CONSTANT")
    A.attach_to(sheet, e.rig, t_sheet, bone="head", name="on_hat")
    A.event(t_sheet, "cloth_flap")
    e.pose(t_sheet + 2, {"head": (-15, 0, 20), "arm_L": (90, 0, 40), "arm_R": (90, 0, 40), "fore_L": (90, 0, 0),
                         "fore_R": (90, 0, 0)})
    e.pose(t_sheet + 12, {"head": (10, 0, -20)})
    e.pose(t_sheet + 22, {"head": (-10, 0, 15), "arm_L": (8, 0, 8), "arm_R": (100, 0, 25), "fore_L": (30, 0, 0),
                          "fore_R": (20, 0, 0)})
    B.shot(ctx, 4, "S4_c2_alley", tr1, [(tr1, Wv(30, 1.3, 1.5), Wv(20, 0, 1.6)),
                                        (t_sheet + 20, Wv(31, 1.2, 1.6), Wv(23, 0, 1.6))], lens=28)
    # ------------------------------------------------------------------ 4.3 bucket of bolts
    bucket = bpy.data.objects.get("v_bucket")
    bp = Wv(28.0, -1.4)
    if bucket:
        bucket.location = bp + V((0, 0, 0.15))
    tb = tr1 + int((28.0 - 18.0) / 16.0 * (tr2 - tr1))
    if bucket:
        bucket.keyframe_insert("rotation_euler", frame=tb)
        bucket.rotation_euler = (math.radians(95), 0, 0)
        bucket.keyframe_insert("rotation_euler", frame=tb + 6)
    A.event(tb + 4, "bolts_spill")
    C.set_coll(ctx.c_props)
    for i in range(14):
        b_ = C.cyl(f"spillbolt{i}", 0.015, 0.05, loc=bp + V((0, 0, 0.2)), m=C.mat("steel"), verts=6, coll=ctx.c_props)
        b_.keyframe_insert("location", frame=tb + 3)
        rnd = C.R.__class__(i)
        A.arc(b_, tb + 4, tb + 14, bp + V((0, 0, 0.2)),
              bp + V((rnd.uniform(-0.6, 0.8), rnd.uniform(0.2, 1.8), 0.01)), height=0.25,
              spin=(rnd.uniform(-6, 6), rnd.uniform(-6, 6), 0))
    f.pose(tb - 6, {"arm_R": (90, 0, 60), "fore_R": (0, 0, 0)})
    f.pose(tb + 2, {"arm_R": (40, 0, 80), "fore_R": (0, 0, 0)})
    f.pose(tb + 8, "scared")
    # Erfasser hits the bolts: spin out (yaw spin + wobble) and recover
    ts = te2
    pos = e.pos_at(ts)
    yaw0 = e.yaw_at(ts)
    for k, (dt, dy) in enumerate(((4, 120), (8, 260), (12, 400), (16, 520), (22, 600), (30, 630))):
        e.place(ts + dt, pos + V((0.12 * k, 0.08 * math.sin(k), 0)), yaw0 + dy)
    e.pose(ts + 4, {"body": (0, 0, 25), "arm_L": (100, 0, 60), "arm_R": (100, 0, 60)})
    e.pose(ts + 12, {"body": (0, 0, -25)})
    e.pose(ts + 20, {"body": (0, 0, 15)})
    e.pose(ts + 30, {"body": (0, 0, 0), "arm_L": (8, 0, 8), "arm_R": (8, 0, 8)})
    A.event(ts + 2, "spin_out", dur=28)
    A.event(ts + 30, "boing")
    e.place(ts + 40, pos + V((0.7, 0.2, 0)), yaw0 + 720)
    e.pose(ts + 40, {"head": (0, 0, 0), "body": (-8, 0, 0)})
    ts_end = ts + 44
    B.shot(ctx, 4, "S4_c3_bolts", t_sheet + 20, [(t_sheet + 20, bp + V((2.4, 0.2, 0.9)), bp + V((-1.5, 1.0, 0.8))),
                                                 (ts_end, bp + V((2.5, 0.25, 1.0)), pos + V((0, 0, 1.0)))], lens=24)
    # ------------------------------------------------------------------ 4.4 the barrel
    barrel_spot = Wv(37.0, 1.4)
    barrel = P.scrap_item("barrel_rust", barrel_spot + V((0, 0, 0.704)), (0, 0, 0), 1.6, ctx.c_props)
    # she pauses at the alley's end, looks back at the spinning Erfasser, then dives for the barrel
    h.pose(tr2 + 3, "carry")
    A.look(h, tr2 + 8, pos + V((0, 0, 1.2)), extra={"spine": (-6, 0, 0)})
    h.face(tr2 + 8, "surprised")
    th = max(tr2 + 4, ts + 26)
    h.hold(th - 1)
    h.hold_place(th - 1)
    b_in = barrel_spot + V((0.1, -1.05, 0))
    hw = h.walk(th, [Wv(34, -0.2), b_in], speed=3.0, stride=0.8, style="run", end_pose=None)
    # hop in: she ducks into the barrel (lowered out of sight, only the goggles/Funke's antenna above the rim)
    h.place(hw + 2, b_in, 0)
    A.arc(h.rig, hw + 4, hw + 18, b_in, barrel_spot + V((0, 0, -0.2)), height=1.9)
    h.pose(hw + 6, {"thigh_L": (80, 0, 6), "thigh_R": (80, 0, 6), "shin_L": (-110, 0, 0), "shin_R": (-110, 0, 0)})
    h.pose(hw + 12, {"hips": (5, 0, 0), "spine": (18, 0, 0), "chest": (10, 0, 0), "head": (-10, 0, 0),
                     "thigh_L": (30, 0, 2), "thigh_R": (30, 0, 2), "shin_L": (-60, 0, 0), "shin_R": (-60, 0, 0),
                     "foot_L": (30, 0, 0), "foot_R": (30, 0, 0), "upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6),
                     "forearm_L": (80, 0, -25), "forearm_R": (80, 0, -25)})
    A.event(hw + 14, "barrel_thunk")
    h.face(hw + 16, "worried")
    # Erfasser rolls up and scans the alley
    tes = max(ts_end, hw + 20)
    e_scan = Wv(35.3, 0.3)
    te4 = e.roll(tes, [e.pos_at(tes), e_scan], speed=1.6, lean=6)
    e.place(te4 + 2, None, math.degrees(A.yaw_towards(barrel_spot - e_scan)))
    A.key(ctx.erf_beam.data, "energy", te4, 0.0)
    A.key(ctx.erf_beam.data, "energy", te4 + 4, 600.0)
    e.scan(te4 + 2, te4 + C.sec(2.2), sweeps=1)
    A.key(ctx.erf_beam.data, "energy", te4 + C.sec(2.4), 0.0)
    # Hedda peeks; the scan passes … then Funke's antenna lights up – betrayed
    tbet = te4 + C.sec(2.0)
    f.glow(tbet - 1, 0.5, "bulb", "CONSTANT")
    f.glow(tbet, 14.0, "bulb", "CONSTANT")
    f.pose(tbet, {"antenna": (-20, 0, 0)})
    A.event(tbet, "ping")
    e.pose(tbet + 4, {"head": (8, 0, 0), "neck": (0, 0, 0)})
    e.bone_loc(tbet + 2, "neck", (0, 0, 0))
    e.bone_loc(tbet + 8, "neck", (0, 0.35, 0))
    A.event(tbet + 6, "neck_extend")
    e.glow(tbet + 4, 20.0, "iris")
    f.pose(tbet + 6, {"lid": (-20, 0, 0)})
    h.face(tbet + 6, "surprised")
    B.shot(ctx, 4, "S4_c4_barrel", max(hw - 6, ts + 40), [(max(hw - 6, ts + 40), barrel_spot + V((2.2, -3.6, 1.4)), barrel_spot + V((-0.6, 0.2, 1.1))),
                                            (tbet + 16, barrel_spot + V((1.0, -3.4, 1.3)), barrel_spot + V((-0.9, -0.3, 1.25)))],
           lens=24)
    # ------------------------------------------------------------------ 4.5 scrapyard: net misses Hedda, catches Funke
    t5 = tbet + 24
    e.bone_loc(t5, "neck", (0, 0, 0))
    e.glow(t5, 3.0, "iris")
    # cut to scrapyard: running between piles
    p0 = V((-16, 8.3, 0)); p1 = V((-6, 7.9, 0)); p2 = V((1.5, 5.5, 0))  # along the side road
    h.cut(t5, p0, math.degrees(A.yaw_towards(p1 - p0)))
    h.pose(t5, "stand")
    h.face(t5, "angry")
    hr = h.walk(t5, [p0, p1, p2], speed=4.0, stride=0.9, style="run", end_pose=None)
    fr = t5
    while fr < hr:
        h.pose(fr, {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (80, 0, -25),
                    "forearm_R": (80, 0, -25)})
        fr += 6
    e.cut(t5, V((-27.0, 8.3, 0)), -90)
    e.pose(t5, "stand")
    e.glow(t5, 3.0, "iris")
    e.bone_loc(t5, "neck", (0, 0, 0))
    ter = e.roll(t5 + 6, [V((-27.0, 8.3, 0)), V((-6.5, 8.4, 0)), V((-0.5, 6.4, 0))], speed=6.0, lean=16)
    # remove sheet from hat at the cut
    for c in sheet.constraints:
        c.influence = 1.0
        c.keyframe_insert("influence", frame=t5 - 1)
        c.influence = 0.0
        c.keyframe_insert("influence", frame=t5)
    sheet.location = (0, 0, -300)
    sheet.keyframe_insert("location", frame=t5)
    A.set_interp(sheet, "location", t5 - 1, "CONSTANT")
    # net throw: Hedda trips forward, Funke flies from her arms into the net
    tn = hr - 8
    e.pose(tn - 10, "net_ready")
    e.pose(tn, "net_throw", interp="LINEAR")
    A.event(tn - 4, "whoosh")
    A.detach(f.rig, con1, tn + 2)
    net = e.extra["net"]
    hoop = A.world_matrix_at(net, tn + 10).translation
    A.arc(f.rig, tn + 2, tn + 10, f.pos_at(tn + 2), hoop - V((0, 0, 0.35)), height=0.6, spin=(2 * math.pi + 0.4, 0, 0))
    f.pose(tn + 6, "scared")
    con_n = A.attach_to(f.rig, net, tn + 10, name="netted")
    A.event(tn + 10, "net_catch")
    # Hedda trips and falls
    h.hold_place(hr)
    h.pose(hr, {"spine": (40, 0, 0), "upper_arm_L": (120, 0, 20), "upper_arm_R": (120, 0, 20)})
    h.place(hr + 8, p2 + (p2 - p1).normalized() * 1.2 + V((0, 0, 0.12)), h.yaw_at(hr))
    h.rig.keyframe_insert("rotation_euler", frame=hr, index=0)
    h.rig.rotation_euler.x = math.radians(80)
    h.rig.keyframe_insert("rotation_euler", frame=hr + 8, index=0)
    A.event(hr + 8, "thud")
    h.face(hr + 8, "closed")
    B.shot(ctx, 4, "S4_c5_scrap", t5, [(t5, V((3.4, 3.0, 1.3)), V((-12, 8.6, 1.3)), 34),
                                       (hr + 10, V((4.7, 1.7, 1.8)), V((1.0, 6.0, 0.6)), 24)], lens=34)
    # ------------------------------------------------------------------ 4.6 stamp, truck leaves, Hedda in the dust
    tst = hr + 24
    e.hold_all(tst - 1)
    e.pose(tst, {"arm_R": (80, 0, 30), "fore_R": (40, 0, 0), "hand_R": (-20, 0, 0)})
    hit = e.stamp(tst + 4)
    # the chase stays drained; the stamp takes the last of the colour
    S.key_sat(sc, F, 0.6)
    S.key_sat(sc, hit - 1, 0.62)
    S.key_sat(sc, hit + 1, 0.35, "CONSTANT")
    S.key_sat(sc, hit + 2, 0.35)
    for d in ctx.decal_funke:
        A.hide(d, hit, False)
    f.bone_scale(hit, "body", (1.15, 1.15, 0.8))
    f.bone_scale(hit + 4, "body", (1, 1, 1))
    f.pose(hit + 2, "sad")
    f.glow(hit + 2, 1.0, "bulb")
    # truck waiting at the road; Erfasser rolls to it with the net, climbs on the step
    tr["root"].location = (6, -1, 0)
    tr["root"].rotation_euler = (0, 0, 0)
    tr["root"].keyframe_insert("location", frame=F)
    tr["root"].keyframe_insert("rotation_euler", frame=F)
    A.key_socket(C.emit_socket(tr["headlight_m"]), F, 0.0)
    tgo = hit + 26
    e.pose(tgo, {"arm_R": (130, 0, 10), "fore_R": (10, 0, 0), "hand_R": (-10, 0, 0)})
    tstep = e.roll(tgo, [e.pos_at(tgo), V((3.2, 6.7, 0)), V((6.0, 4.6, 0))], speed=2.2, lean=6)
    e.place(tstep + 2, V((6.0, 4.6, 0)), 180)
    e.place(tstep + 8, V((6.0, 3.2, 0.78)), 180)
    A.event(tstep + 8, "clank")
    con_r = A.attach_to(e.rig, tr["root"], tstep + 9, name="ride_s4")
    tl = tstep + 16
    tr["root"].keyframe_insert("location", frame=tl)
    P.drive(tr, tl, tl + C.sec(5.5), (6, -1, 0), (6, -70, 0), 0)
    A.event(tl - 6, "engine_rev")
    A.key_socket(C.emit_socket(tr["beacon_m"]), F, 0.0)
    fr = F
    while fr < END + 200:
        A.key_socket(C.emit_socket(tr["beacon_m"]), fr, 12.0, "CONSTANT")
        A.key_socket(C.emit_socket(tr["beacon_m"]), fr + 7, 0.0, "CONSTANT")
        fr += 14
    # Hedda gets up on her knees, reaches out
    h.rig.keyframe_insert("rotation_euler", frame=tl - 30, index=0)
    h.rig.rotation_euler.x = 0
    h.rig.keyframe_insert("rotation_euler", frame=tl - 10, index=0)
    kp = h.pos_at(tl - 30)
    kp.z = 0.0
    h.place(tl - 10, V((kp.x, kp.y, 0)), math.degrees(A.yaw_towards(V((6.0, -14.0, 0)) - V((kp.x, kp.y, 0)))))
    h.pose(tl - 10, "crouch")
    h.pose(tl - 10, {"thigh_L": (90, 0, 4), "thigh_R": (90, 0, 4), "shin_L": (-150, 0, 0), "shin_R": (-150, 0, 0)})
    h.bone_loc(tl - 10, "root", (0, 0, -0.35))
    h.face(tl - 6, "sad")
    h.pose(tl + 10, {"upper_arm_R": (80, 0, 10), "forearm_R": (5, 0, 0), "head": (-8, 0, 0)})
    h.face(tl + 30, "sad")
    h.blink(tl + 50, "sad")
    # she gets up. Looks after the truck. And pulls the goggles down: she is going after them.
    tg = tl + 58
    h.pose(tg, "stand")
    h.bone_loc(tg, "root", (0, 0, 0))
    h.pose(tg, {"head": (-6, 0, 0), "upper_arm_R": (10, 0, 6), "forearm_R": (15, 0, 0)})
    h.face(tg + 6, "sad")
    h.blink(tg + 26, "sad")
    h.face(tg + 34, "angry")
    h.pose(tg + 34, {"head": (-10, 0, 0), "spine": (-4, 0, 0), "chest": (-4, 0, 0)})
    hands_up = {"upper_arm_L": (150, 0, 32), "forearm_L": (70, 0, -10), "upper_arm_R": (150, 0, 32),
                "forearm_R": (70, 0, -10), "head": (-12, 0, 0)}
    h.pose(tg + 46, hands_up)
    gpv = h.extra.get("goggles")
    if gpv:
        gpv.rotation_euler.x = 0
        gpv.keyframe_insert("rotation_euler", frame=tg + 50, index=0)
        gpv.rotation_euler.x = math.radians(26 + CH.GOGGLE_LIFT)
        gpv.keyframe_insert("rotation_euler", frame=tg + 55, index=0)
        A.set_interp(gpv, "rotation_euler", tg + 55, "CONSTANT", index=0)
    h.pose(tg + 55, {"upper_arm_L": (135, 0, 30), "forearm_L": (70, 0, -10), "upper_arm_R": (135, 0, 30),
                     "forearm_R": (70, 0, -10)})
    A.event(tg + 55, "click")
    h.pose(tg + 66, {"upper_arm_L": (8, 0, 6), "forearm_L": (20, 0, 0), "upper_arm_R": (8, 0, 6),
                     "forearm_R": (20, 0, 0), "head": (-8, 0, 0)})
    END = tg + 66 + C.sec(1.6)
    B.set_end(ctx, 4, END)
    A.event(END - 24, "wind")
    B.shot(ctx, 4, "S4_c6_stamp", tst - 4, [(tst - 4, V((-3.6, 8.8, 1.5)), V((-0.5, 6.0, 1.3))),
                                            (tgo, V((-3.4, 8.6, 1.5)), V((-0.5, 6.0, 1.4)))], lens=30)
    # over her shoulder: the truck shrinks down the road to the city, Hedda stays in the dust
    kq = V((kp.x, kp.y, 0))
    back = (kq - V((6.0, -14.0, 0))).normalized()
    side = V((-back.y, back.x, 0))
    # close on her face for the decision
    road_dir = (V((6.0, -14.0, 0)) - kq).normalized()
    hz = 1.5
    B.shot(ctx, 4, "S4_c7_resolve", tg + 24, [(tg + 24, kq + road_dir * 1.5 + V((0, 0, hz)), kq + V((0, 0, hz - 0.02))),
                                             (END, kq + road_dir * 1.25 + V((0, 0, hz - 0.02)), kq + V((0, 0, hz)))],
           lens=50)
    B.shot(ctx, 4, "S4_c6b_leave", tgo, [(tgo, kq + back * 3.4 + side * 1.0 + V((0, 0, 1.25)), V((6.0, -14.0, 0.9))),
                                         (END, kq + back * 2.9 + side * 0.8 + V((0, 0, 1.15)), V((6.0, -14.0, 1.1)))],
           lens=32)
    ctx.s4 = {"hedda_end": kp}

    def sweep(base_fn, f0_, lock_, amp=1.6, z=0.0):
        """look around (decaying side-to-side search) until the lock, then sit on the target"""
        def fn(fr):
            b_ = base_fn(fr)
            k = max(0.0, 1.0 - (fr - f0_) / max(1, lock_ - f0_))
            return b_ + V((math.cos(fr * 0.11) * amp * k, math.sin(fr * 0.07) * amp * 0.4 * k, z * k))
        return fn
    # ---- the Erfasser's eyes at the barrel: nothing ... nothing ... a blip
    import pov
    pf0, pf1 = te4 + 4, tbet + 14
    pov.pov_shot(ctx, 4, "S4_pov_barrel", pf0, pf1, pov.erf_eye(e),
                 sweep(lambda fr: (barrel_spot + V((0, 0, 1.25))) if fr < tbet else pov.bone_pos(f, "antenna")(fr),
                       pf0, tbet, amp=2.2), lens=40, lock=tbet + 2,
                 lines=[(te4 + 10, "SCANNING ALLEY ...", None), (te4 + 22, "NO MATCH", None),
                        (te4 + 34, "NO MATCH", None), (tbet + 1, "SIGNAL  ANTENNA  412 Hz", (1, 0.6, 0.2))],
                 verdict=(tbet + 6, "MATCH"),
                 hide=[bpy.data.objects[x] for x in ("Erfasser_pole", "Erfasser_hoop", "Erfasser_net")])
    return END
