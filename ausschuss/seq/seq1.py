"""SEQ 1 – Scrapyard at dawn: the radio, Bello, the Erfasser, the press, the lens."""
import math
import bpy
from mathutils import Vector
import core as C
import anim as A
import characters as CH
import props as P
import sets as S
import build as B

V = Vector


def flash(sock, f0, f1, on=8.0, period=12):
    f = f0
    while f < f1:
        A.key_socket(sock, f, on, "CONSTANT")
        A.key_socket(sock, f + period // 2, 0.0, "CONSTANT")
        f += period


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(44)
    h, b, e, f = ctx.hedda, ctx.bello, ctx.erf, ctx.funke
    tr = ctx.truck
    wld = S.world("W_S1_dawn", horizon=(1.0, 0.5, 0.3), zenith=(0.1, 0.14, 0.32), ground=(0.06, 0.05, 0.05),
                  strength=1.1, sun_dir=(0.15, 1, 0.06), sun_color=(1.0, 0.55, 0.25), sun_glow=4.0)
    sc, L, cams = B.new_seq_scene(ctx, 1, "S1_Scrapyard_Dawn", F, END, wld,
                                  [ctx.chars, ctx.c_scrap, ctx.c_city, ctx.c_props])
    S.sun("S1_sun", (86, 0, 172), 4.2, (1.0, 0.62, 0.38), L, angle=3)
    S.sun("S1_fill", (55, 0, -25), 0.9, (0.5, 0.58, 0.85), L, angle=30)
    S.fog_box("S1_fog", L, (0, 120, 0), (520, 640, 70), 0.006, (0.85, 0.68, 0.62))
    B.offstage_all(ctx, F, keep=(h, b, e))
    # ------------------------------------------------------------------ props for this sequence
    C.set_coll(ctx.c_props)
    radio = C.empty("radio", loc=(0, 0, -300), coll=ctx.c_props)
    rm = C.mat("radio_m", (0.45, 0.25, 0.12), rough=0.5, dirt=0.5, rust=0.2)
    C.box("radio_body", (0.26, 0.12, 0.17), loc=(0, 0, 0), m=rm, parent=radio, bevel=0.03)
    C.cyl("radio_speaker", 0.05, 0.01, loc=(-0.05, -0.062, 0), rot=(90, 0, 0),
          m=C.mat("radio_grill", (0.7, 0.6, 0.4), rough=0.8), parent=radio)
    C.cyl("radio_knob", 0.018, 0.02, loc=(0.07, -0.065, 0.02), rot=(90, 0, 0), m=C.mat("brass"), parent=radio)
    C.cyl("radio_ant", 0.003, 0.25, loc=(0.1, 0.0, 0.2), rot=(0, 20, 0), m=C.mat("chrome"), parent=radio)
    ctx.radio = radio
    bolt = C.cyl("bolt", 0.015, 0.06, loc=(0, 0, -300), m=C.mat("steel"), verts=6, coll=ctx.c_props)
    lens = C.empty("bello_lens", loc=(0, 0, -300), coll=ctx.c_props)
    lens_iris = CH.iris_material("lens_iris", (1.0, 0.55, 0.12), 3.0)
    for o in CH.lens_eye("lensprop", ctx.c_props, (0, 0, 0), 0.05, lens_iris):
        o.parent = lens
    ctx.lens, ctx.lens_iris = lens, lens_iris
    # fresh junk heap (appears with the dump)
    J = V((5.4, 9.3, 0))
    heap = P.mound("dump_heap", J, 1.8, 1.1, C.mat("junk_earth"), ctx.c_props)
    heap.scale = (0.01, 0.01, 0.01)
    heap.keyframe_insert("scale", frame=T(5.8))
    heap.scale = (1.8, 1.53, 1.1)
    heap.keyframe_insert("scale", frame=T(6.25))
    rnd = C.R.__class__(4)
    junk = []
    for i, k in enumerate(["tv", "tire", "crate", "drum", "panel2", "barrel_b", "tv", "gear", "crate", "washer"]):
        o = P.scrap_item(k, (0, 0, -300), (0, 0, 0), 0.7, ctx.c_props)
        a = rnd.uniform(0, 6.28)
        rr = rnd.uniform(0.2, 1.2)
        dx, dy = math.cos(a) * rr, math.sin(a) * rr * 0.8
        zs = -0.385 + 1.1 * math.sqrt(max(0.0, 1 - (dx / 1.8) ** 2 - (dy / 1.53) ** 2))
        dst = J + V((dx, dy, zs + 0.15))
        f0 = T(5.9 + i * 0.08)
        o.location = (6, 5.6, 2.0)
        o.keyframe_insert("location", frame=f0 - 1)
        A.set_interp(o, "location", f0 - 1, "CONSTANT")
        o.location = (0, 0, -300)
        o.keyframe_insert("location", frame=f0 - 2)
        A.set_interp(o, "location", f0 - 2, "CONSTANT")
        A.arc(o, f0, f0 + 10, (6, 5.9, 2.0), dst, height=0.6,
              spin=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(-3, 3)))
        junk.append(o)
    A.event(T(5.9), "junk_dump")
    # ------------------------------------------------------------------ truck
    tr["root"].location = (6, 80, 0)
    tr["root"].keyframe_insert("location", frame=F - 1)
    P.drive(tr, T(0), T(5.0), (6, 80, 0), (6, 2, 0), 0)
    A.set_interp(tr["root"], "location", T(0), "LINEAR")
    for fr, on in ((F, 10.0),):
        A.key_socket(C.emit_socket(tr["headlight_m"]), fr, on)
    flash(C.emit_socket(tr["beacon_m"]), F, END, on=12.0, period=14)
    A.shake(tr["root"], T(5.0), T(40), amp=0.008, freq=8)
    # hopper dump
    hp = tr["hopper"]
    hp.keyframe_insert("rotation_euler", frame=T(5.4))
    hp.rotation_euler.x = math.radians(65)
    hp.keyframe_insert("rotation_euler", frame=T(6.0))
    hp.keyframe_insert("rotation_euler", frame=T(7.2))
    hp.rotation_euler.x = 0
    hp.keyframe_insert("rotation_euler", frame=T(8.0))
    A.event(T(5.4), "hydraulic")
    A.event(T(7.4), "hydraulic")
    # ------------------------------------------------------------------ Erfasser rides in on the rear step
    step_world = V((6, 80 + 4.2, 0.78))
    e.cut(F, step_world, 180)
    e.pose(F, "stand")
    con_e = A.attach_to(e.rig, tr["root"], F, name="ride")
    A.detach(e.rig, con_e, T(5.1))
    # hop down to the side before the hopper tips (and out of the junk's way)
    e.place(T(5.1), (6, 6.2, 0.78), 180)
    A.arc(e.rig, T(5.1) + 1, T(5.45), (6, 6.2, 0.78), (7.7, 6.7, 0.0), height=0.35)
    e.place(T(5.45), (7.7, 6.7, 0.0), 230)
    e.pose(T(5.45), {"body": (12, 0, 0)})
    e.pose(T(5.8), {"body": (0, 0, 0), "head": (10, 0, 25)})
    A.event(T(5.45), "clank")
    e.place(T(6.6), None, 210)
    fe = e.roll(T(7.0), [(7.7, 6.7, 0), (8.7, 5.0, 0), (9.0, -3.0, 0)], speed=2.6)
    # ------------------------------------------------------------------ Hedda sneaks to the heap
    cover = P.scrap_item("fridge", (-1.0, 14.3, 0.33), (0, 90, 4), 1.0, ctx.c_props)
    A.hide(cover, 0, True)
    A.hide(cover, F, False)
    A.hide(cover, END + 1, True)
    HS = V((3.95, 10.89, 0))  # rummage spot at the foot of the fresh heap
    h.cut(F, (-1.8, 15.2, 0), 30)
    h.pose(F, "stand")
    h.pose(F, "crouch")
    h.face(F, "neutral")
    h.pose(T(8.0), "crouch")
    A.look(h, T(8.3), (6, 2, 1.5), extra={"spine": (25, 0, 0)})
    A.look(h, T(8.8), (6, 2, 1.5), extra={"spine": (25, 0, 0)})
    h.pose(T(9.0), "crouch")
    h.pose(T(9.3), "stand")
    hw = h.walk(T(9.3), [(-1.8, 15.2, 0), (0.3, 14.9, 0), (1.6, 12.9, 0), HS], speed=1.1, stride=0.45,
                style="sneak", end_pose=None)
    h.face(T(9), "worried")
    # rummage
    yaw_heap = math.degrees(A.yaw_towards(J - HS))
    h.place(hw + 2, HS, yaw_heap)
    h.pose(hw + 2, "stand")
    h.pose(hw + 8, "bend_down")
    h.face(hw + 8, "neutral")
    fr = hw + 12
    for k in range(4):
        h.pose(fr, {"upper_arm_R": (70 + 15 * (k % 2), 0, 10), "upper_arm_L": (60 - 15 * (k % 2), 0, 10),
                    "forearm_R": (20, 0, 0), "forearm_L": (25, 0, 0)})
        A.event(fr, "rummage")
        fr += 6
    t_radio = fr + 2  # ~T(15.6)
    radio.location = (0, 0, -300)
    radio.keyframe_insert("location", frame=t_radio - 1)
    mw = A.world_matrix_at(h.rig, t_radio, "hand_R")
    radio.location = mw.translation + V((0, 0, -0.06))
    radio.keyframe_insert("location", frame=t_radio)
    A.set_interp(radio, "location", t_radio - 1, "CONSTANT")
    con_r = A.attach_to(radio, h.rig, t_radio, bone="hand_R")
    h.pose(t_radio + 8, "stand")
    h.pose(t_radio + 8, {"upper_arm_R": (50, 0, 5), "forearm_R": (60, 0, -10), "head": (14, 0, 0)})
    h.face(t_radio + 8, "surprised")
    h.blink(t_radio + 16, "surprised")
    # transfer radio to left hand by simply holding it with right and tapping with left
    h.pose(t_radio + 22, {"upper_arm_L": (55, 0, -5), "forearm_L": (55, 0, 0), "hand_L": (-25, 0, 0)})
    for k in range(2):
        h.pose(t_radio + 26 + k * 6, {"upper_arm_L": (48, 0, -5), "forearm_L": (40, 0, 0), "hand_L": (10, 0, 0)},
               interp="LINEAR")
        A.event(t_radio + 26 + k * 6, "knock")
        h.pose(t_radio + 29 + k * 6, {"upper_arm_L": (55, 0, -5), "forearm_L": (55, 0, 0), "hand_L": (-25, 0, 0)})
    A.event(t_radio + 40, "radio_crackle")
    h.face(t_radio + 40, "happy")
    h.pose(t_radio + 48, {"upper_arm_L": (4, 0, 6), "forearm_L": (12, 0, 0), "hand_L": (0, 0, 0)})
    # pocket the radio
    h.pose(t_radio + 56, {"upper_arm_R": (-10, 0, 25), "forearm_R": (60, 0, 0), "head": (10, 0, 0)})
    A.detach(radio, con_r, t_radio + 58)
    radio.location = (0, 0, -300)
    radio.keyframe_insert("location", frame=t_radio + 59)
    A.set_interp(radio, "location", t_radio + 58, "CONSTANT")
    h.pose(t_radio + 64, "stand")
    A.event(t_radio + 58, "pocket")
    # ------------------------------------------------------------------ Bello arrives
    b.cut(F, (-9.5, 7.4, 0), -90)
    b.pose(F, "stand")
    bw = b.walk(T(13.2), [(-9.5, 7.4, 0), (-3, 7.6, 0), (2.5, 8.7, 0)], speed=1.2, stride=0.3, style="limp",
                end_pose="stand")
    b.pose(bw + 4, "sniff")
    b.pose(bw + 14, "stand")
    b.pose(bw + 20, "sniff")
    A.event(bw + 4, "sniff")
    A.event(bw + 20, "sniff")
    # Hedda notices (after pocketing radio, ~T(18.3))
    tn = max(t_radio + 66, bw + 6)
    A.look(h, tn, V((2.5, 8.7, 0.5)), pitch=10)
    h.pose(tn, {"spine": (-6, 0, 0)})
    h.face(tn, "surprised")
    A.event(tn, "startle")
    h.face(tn + 14, "happy")
    h.place(tn + 10, None, math.degrees(A.yaw_towards(V((2.5, 8.7, 0)) - HS)))
    h.pose(tn + 10, {"head": (10, 0, 0), "spine": (6, 0, 0)})
    b.pose(tn + 4, {"neck": (-20, 0, 0), "head": (-10, 0, 0)})
    # toss the bolt
    ttoss = tn + 22
    h.pose(ttoss - 6, {"upper_arm_R": (-20, 0, 15), "forearm_R": (40, 0, 0)})
    h.pose(ttoss, {"upper_arm_R": (70, 0, 5), "forearm_R": (10, 0, 0)})
    hand = A.world_matrix_at(h.rig, ttoss, "hand_R").translation
    bolt.location = (0, 0, -300)
    bolt.keyframe_insert("location", frame=ttoss - 1)
    A.set_interp(bolt, "location", ttoss - 1, "CONSTANT")
    A.arc(bolt, ttoss, ttoss + 12, hand, (2.2, 8.4, 0.02), height=0.7, spin=(9, 4, 0))
    A.event(ttoss + 12, "bolt_land")
    h.pose(ttoss + 10, "stand")
    b.pose(ttoss + 14, "sniff")
    b.pose(ttoss + 24, "stand")
    b.pose(ttoss + 24, {"neck": (-10, 0, 0)})
    b.wag(ttoss + 24, ttoss + 64, speed=3)
    b.glow(ttoss + 22, 2.0, "bulb")
    b.glow(ttoss + 26, 8.0, "bulb")
    b.glow(ttoss + 60, 2.0, "bulb")
    h.face(ttoss + 20, "happy")
    # ------------------------------------------------------------------ Erfasser returns (T(21)…)
    t4 = T(20.5)
    E2 = V((4.1, 7.2, 0))
    er = e.roll(t4, [(9.0, -3.0, 0), (8.8, 1.0, 0), (8.4, 7.3, 0), (5.4, 7.7, 0), E2], speed=3.0)
    A.event(t4, "squeak")
    # Hedda hears, ducks behind the heap
    tduck = T(22.4)
    A.look(h, tduck - 4, V((8, 0, 1.5)))
    h.face(tduck - 4, "worried")
    h.hold_place(tduck)
    tcr = h.walk(tduck, [HS, (5.0, 11.75, 0), (5.9, 11.5, 0)], speed=1.6, stride=0.4, style="sneak",
                 end_pose=None) + 2
    h.place(tcr, (5.9, 11.5, 0), math.degrees(A.yaw_towards(V((0, -1)))))
    h.pose(tcr, "crouch")
    h.face(tcr, "worried")
    b.pose(T(23.5), {"neck": (-15, 0, 0), "head": (0, 0, -25)})
    b.pose(T(24.6), "cower")
    b.glow(T(24.6), 1.0, "bulb")
    # scanning
    yaw_eb = math.degrees(A.yaw_towards(V((2.5, 8.7, 0)) - E2))
    e.place(er + 2, None, yaw_eb)
    ts = max(T(25.6), er + 6)
    A.key(ctx.erf_beam.data, "energy", ts - 2, 0.0)
    A.key(ctx.erf_beam.data, "energy", ts + 2, 300.0)
    e.scan(ts, ts + C.sec(2.0), sweeps=1)
    A.key(ctx.erf_beam.data, "energy", ts + C.sec(2.2), 300.0)
    A.key(ctx.erf_beam.data, "energy", ts + C.sec(2.5), 0.0)
    A.event(ts + C.sec(2.0), "verdict_buzz")
    e.glow(ts + C.sec(2.0), 20.0, "iris")
    e.glow(ts + C.sec(2.6), 3.0, "iris")
    # stamp
    tst = ts + C.sec(2.6)
    hit = e.stamp(tst)
    for d in ctx.decal_bello:
        A.hide(d, hit, False)
    b.pose(hit, {"body": (10, 0, 0)})
    b.bone_scale(hit, "body", (1.1, 0.85, 1.0))
    b.bone_scale(hit + 4, "body", (1, 1, 1))
    b.pose(hit + 6, "cower")
    # net
    tn2 = hit + C.sec(1.2)
    e.pose(tn2, "net_ready")
    e.pose(tn2 + 8, "net_ready")
    e.pose(tn2 + 14, "net_throw", interp="LINEAR")
    A.event(tn2 + 10, "whoosh")
    A.event(tn2 + 14, "net_catch")
    con_b = A.attach_to(b.rig, e.extra["net"], tn2 + 14, name="netted")
    b.pose(tn2 + 14, "cower")
    # carry to hopper
    tc = tn2 + 24
    e.pose(tc, {"arm_R": (130, 0, 10), "fore_R": (10, 0, 0), "hand_R": (-10, 0, 0), "body": (-5, 0, 0)})
    tcarry = e.roll(tc + 4, [E2, (5.1, 7.7, 0), (6.0, 7.5, 0)], speed=1.0, lean=4)
    e.place(tcarry + 2, None, 0)
    e.pose(tcarry + 6, {"arm_R": (150, 0, 0), "fore_R": (-10, 0, 0), "hand_R": (30, 0, 0), "body": (-10, 0, 0)})
    tdrop = tcarry + 14
    e.pose(tdrop, {"arm_R": (120, 0, 0), "fore_R": (0, 0, 0), "hand_R": (70, 0, 0), "body": (6, 0, 0)})
    A.event(tdrop, "drop_in")
    b.offstage(tdrop + 1)
    for d in ctx.decal_bello:
        A.hide(d, tdrop + 1, True)
    e.pose(tdrop + 10, "stand")
    # press
    pl = tr["plate"]
    tp = tdrop + 16
    pl.keyframe_insert("rotation_euler", frame=tp)
    pl.rotation_euler.x = math.radians(-100)
    pl.keyframe_insert("rotation_euler", frame=tp + 18)
    pl.rotation_euler.x = 0
    pl.keyframe_insert("rotation_euler", frame=tp + 40)
    A.event(tp, "press_start")
    A.event(tp + 16, "crunch")
    A.shake(tr["root"], tp + 14, tp + 24, amp=0.05, freq=1.5)
    h.face(tp + 18, "closed")
    h.pose(tp + 18, {"head": (35, 0, 0), "spine": (35, 0, 0)})
    # lens pops out and rolls to Hedda
    tpop = tp + 22
    lens.location = (0, 0, -300)
    lens.keyframe_insert("location", frame=tpop - 1)
    A.set_interp(lens, "location", tpop - 1, "CONSTANT")
    A.event(tpop, "pop")
    A.arc(lens, tpop, tpop + 20, (6.0, 6.4, 1.9), (5.1, 12.1, 0.05), height=2.0, spin=(14, 3, 0), steps=8)
    A.event(tpop + 20, "lens_land")
    lens.rotation_euler = (math.radians(90), 0, 0)
    lens.keyframe_insert("rotation_euler", frame=tpop + 21)
    lens.location = (5.6, 11.9, 0.05)
    lens.keyframe_insert("location", frame=tpop + 34)
    lens.rotation_euler = (math.radians(90), math.radians(-200), 0)
    lens.keyframe_insert("rotation_euler", frame=tpop + 34)
    A.event(tpop + 21, "roll", dur=13)
    A.key_socket(C.emit_socket(lens_iris), tpop + 30, 3.0)
    A.key_socket(C.emit_socket(lens_iris), tpop + 50, 0.15)
    h.face(tpop + 24, "worried")
    h.pose(tpop + 24, "crouch")
    h.pose(tpop + 36, {"head": (40, 0, 0)})
    # Erfasser back onto the step, truck leaves
    tback = tp + 30
    tb2 = e.roll(tback, [(6.0, 7.5, 0), (6.0, 6.9, 0)], speed=1.0, lean=3)
    e.place(tb2 + 2, (6, 6.9, 0), 180)
    e.place(tb2 + 8, (6, 6.2, 0.78), 180)
    A.event(tb2 + 8, "clank")
    e.pose(tb2 + 8, "stand")
    con_e2 = A.attach_to(e.rig, tr["root"], tb2 + 9, name="ride2")
    tleave = max(tb2 + 14, T(40.5))
    tr["root"].keyframe_insert("location", frame=tleave)
    P.drive(tr, tleave, tleave + C.sec(5), (6, 2, 0), (6, -60, 0), 0)
    A.event(tleave - 6, "engine_rev")
    # Hedda picks up the lens
    tpick = tpop + C.sec(2.6)
    h.pose(tpick - 6, {"upper_arm_R": (60, 0, 10), "forearm_R": (30, 0, 0), "spine": (30, 0, 0), "head": (30, 0, 0)})
    mw = A.world_matrix_at(h.rig, tpick, "hand_R")
    lens.location = mw.translation + V((0, 0, -0.05))
    lens.keyframe_insert("location", frame=tpick)
    lens.keyframe_insert("rotation_euler", frame=tpick)
    A.set_interp(lens, "location", tpick - 1, "CONSTANT")
    con_l = A.attach_to(lens, h.rig, tpick, bone="hand_R")
    lens.keyframe_insert("scale", frame=tpick)
    lens.scale = (1.5, 1.5, 1.5)  # reads at a distance; it is THE prop of the film
    lens.keyframe_insert("scale", frame=tpick + 6)
    A.key_socket(C.emit_socket(lens_iris), tpick + 10, 0.8)
    h.pose(tpick + 16, "stand")
    h.pose(tpick + 16, {"upper_arm_R": (62, 0, -18), "forearm_R": (95, 0, -10), "hand_R": (-30, 0, 0),
                        "head": (12, -10, 0), "spine": (4, 0, 0)})
    h.face(tpick + 16, "sad")
    h.blink(tpick + 40, "sad")
    h.pose(tpick + 40, {"upper_arm_L": (45, 0, -10), "forearm_L": (75, 0, -15)})
    # she looks after the truck, then back at the lens and rubs the dust off it with her thumb
    h.pose(tpick + 58, {"head": (6, 34, 0), "spine": (2, 8, 0)})
    h.face(tpick + 58, "worried")
    h.blink(tpick + 72, "worried")
    h.pose(tpick + 84, {"head": (16, -6, 6), "spine": (6, 0, 0)})
    h.face(tpick + 84, "sad")
    for i, fw in enumerate(range(tpick + 90, END - 34, 7)):
        h.pose(fw, {"upper_arm_L": (48, 0, -18 if i % 2 else -4), "hand_L": (0, 0, 12 if i % 2 else -12)})
    h.pose(END - 32, {"upper_arm_L": (45, 0, -10), "hand_L": (0, 0, 0)})
    # ... and the eye answers: a flicker. Surprise, then the tiniest smile.
    h.pose(END - 24, {"head": (-4, -4, 0), "spine": (-3, 0, 0), "upper_arm_L": (30, 0, -20)})
    h.face(END - 24, "surprised")
    h.pose(END - 10, {"head": (10, -4, -8), "spine": (3, 0, 0)})
    h.face(END - 10, "happy")
    A.key_socket(C.emit_socket(lens_iris), END - 30, 0.8)
    A.key_socket(C.emit_socket(lens_iris), END - 26, 4.0)
    A.key_socket(C.emit_socket(lens_iris), END - 23, 0.8)
    A.event(END - 26, "tiny_flicker")
    ctx.lens_con = con_l
    # background life: pigeons on the power line, windmill
    C.set_coll(ctx.c_props)
    pigeons = []
    cab = ctx.scrap["cables"][1]
    for i in range(5):
        pt = V(cab[2 + i % 4]) + V((i * 0.6, 0, 0.02))
        root, head = CH.build_pigeon_drone(ctx.c_props, f"pigeon_s{i}", pt, yaw=math.radians(180 + i * 13))
        CH.animate_pigeon(head, F, END, seed=i)
        pigeons.append(root)
    S.spin(ctx.scrap["hut"]["mill_rotor"], F, END, axis=1, turns_per_sec=0.4)
    # ------------------------------------------------------------------ cameras
    B.shot(ctx, 1, "S1_c1_wide", F, [(F, (-13, -15, 2.3), (6, 40, 7), 26), (T(8), (-10, -10.5, 2.0), (5, 9, 2.5), 28)],
           lens=26)
    B.shot(ctx, 1, "S1_c2_sneak", T(8), [(T(8), (-3.6, 17.3, 1.05), (2.2, 12.2, 0.7)),
                                         (T(14), (-2.4, 16.9, 1.15), (4.0, 10.6, 0.9))], lens=32)
    B.shot(ctx, 1, "S1_c3_bello", T(14), [(T(14), (0.4, 6.0, 1.05), (3.6, 9.6, 0.7)),
                                          (T(21.5), (0.2, 5.8, 1.0), (3.4, 9.6, 0.6))], lens=30)
    B.shot(ctx, 1, "S1_c4_erf", T(21.5), [(T(21.5), (7.6, 14.6, 1.0), (6.0, 3, 1.5)),
                                          (T(26), (7.4, 14.4, 0.95), (4.8, 6.0, 1.4))], lens=32)
    B.shot(ctx, 1, "S1_c5_scan", T(26), [(T(26), (0.9, 4.6, 1.3), (3.5, 8.0, 1.0)),
                                         (hit - 6, (1.0, 4.8, 1.25), (3.5, 8.2, 0.9))], lens=32)
    B.shot(ctx, 1, "S1_c5b_stamp", hit - 6, [(hit - 6, (1.2, 6.9, 0.95), (2.7, 8.8, 0.6))], lens=35)
    B.shot(ctx, 1, "S1_c5c_net", hit + 14, [(hit + 14, (0.5, 4.4, 1.4), (3.8, 7.8, 1.4)),
                                            (tpop, (0.2, 2.8, 1.9), (5.5, 7.0, 1.8))], lens=28)
    B.shot(ctx, 1, "S1_c6_lens", tpop + 6, [(tpop + 6, (3.3, 13.9, 0.5), (5.4, 11.8, 0.35)),
                                            (tpick - 4, (3.4, 13.9, 0.6), (5.6, 11.7, 0.45))], lens=30)
    B.shot(ctx, 1, "S1_c7_hold", tpick - 4, [(tpick - 4, (4.5, 9.0, 1.2), (5.9, 11.5, 0.75), 30),
                                             (tpick + 20, (4.6, 9.2, 1.35), (5.9, 11.5, 1.2), 32),
                                             (END, (4.95, 9.75, 1.45), (5.9, 11.5, 1.38), 40)], lens=30)
    return END
