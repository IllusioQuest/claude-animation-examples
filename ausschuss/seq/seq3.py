"""SEQ 3 – Village square by day: silence, the radio, everyone dances, the drone, the Erfasser."""
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
BEAT = 12  # frames per beat (120 bpm) – the soundtrack uses the same tempo


def Wv(x, y, z=0.0):
    return O + V((x, y, z))


def local_to_world(ob, p):
    bpy.context.view_layer.update()
    return ob.matrix_world @ V(p)


def idle_chat(a, f0, f1, seed=0):
    rnd = C.R.__class__(seed)
    f = f0
    while f < f1:
        r = rnd.random()
        if r < 0.4:
            a.pose(f, {"upper_arm_R": (rnd.uniform(30, 60), 0, rnd.uniform(10, 30)), "forearm_R": (rnd.uniform(40, 80), 0, 0),
                       "head": (rnd.uniform(-8, 5), rnd.uniform(-20, 20), 0)})
        elif r < 0.7:
            a.pose(f, {"upper_arm_R": (4, 0, 6), "forearm_R": (12, 0, 0), "head": (0, rnd.uniform(-25, 25), 0)})
        else:
            a.pose(f, {"spine": (rnd.uniform(-4, 6), 0, 0), "chest": (rnd.uniform(-4, 4), 0, 0)})
        f += rnd.randint(12, 30)


def dance(a, f0, f1, seed=0, style="dance", scale=1.0):
    rnd = C.R.__class__(seed)
    f = f0
    ph = rnd.choice([0.0, 0.5])
    yaw0 = a.yaw_at(f0)
    k = 0
    while f < f1:
        a.walk_cycle(f, ph % 1.0, style)
        if k % 8 == 4 and rnd.random() < 0.6:
            a.place(f, None, yaw0 + rnd.choice([-30, 30]))
        if k % 8 == 0:
            a.place(f, None, yaw0)
        ph += 0.25
        f += BEAT // 2
        k += 1


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(41)
    h, f, e = ctx.hedda, ctx.funke, ctx.erf
    vl = ctx.vil
    vg = ctx.vill
    wld = S.world("W_S3_day", horizon=(0.95, 0.82, 0.62), zenith=(0.35, 0.5, 0.72), ground=(0.2, 0.17, 0.13),
                  strength=0.75, sun_dir=(0.6, -0.4, 0.5), sun_color=(1, 0.9, 0.7), sun_glow=1.5)
    sc, L, cams = B.new_seq_scene(ctx, 3, "S3_Village_Day", F, END, wld, [ctx.chars, ctx.c_vil, ctx.c_props])
    S.sun("S3_sun", (48, 0, 140), 4.0, (1.0, 0.88, 0.7), L, angle=2)
    S.sun("S3_sky", (30, 0, -40), 0.6, (0.6, 0.7, 0.95), L, angle=40)
    S.fog_box("S3_fog", L, O, (300, 300, 50), 0.011, (0.95, 0.8, 0.6))
    keep = [h, f, e] + list(vg.values())
    B.offstage_all(ctx, F, keep=keep)
    e.offstage(F)
    # ------------------------------------------------------------------ placement of villagers
    st = vl["stalls"]
    radio_stall = vl["radio_stall"]
    vend_pos = local_to_world(radio_stall, (0.15, 0.95, 0))
    radio_pos = local_to_world(radio_stall, (0.5, 0.05, 0.98))
    stall_yaw = math.degrees(radio_stall.rotation_euler.z)
    vend = vg["Vendor"]
    vend.cut(F, vend_pos, stall_yaw)
    vend.pose(F, "stand")
    vend.pose(F, "sigh")
    vend.face(F, "sad")
    # vendor's dead radio
    C.set_coll(ctx.c_props)
    r2 = C.empty("radio2", loc=radio_pos, rot=(0, 0, stall_yaw + 10), coll=ctx.c_props)
    rm2 = C.mat("radio2_m", (0.2, 0.35, 0.3), rough=0.4, dirt=0.4, rust=0.25)
    C.box("radio2_body", (0.42, 0.2, 0.28), loc=(0, 0, 0.14), m=rm2, parent=r2, bevel=0.05)
    C.cyl("radio2_spk", 0.08, 0.01, loc=(-0.08, -0.103, 0.15), rot=(90, 0, 0), m=C.mat("radio_grill"), parent=r2)
    dial_m = C.emission("radio2_dial", (1.0, 0.7, 0.3), 0.0)
    C.box("radio2_dial", (0.12, 0.01, 0.05), loc=(0.11, -0.103, 0.18), m=dial_m, parent=r2, bevel=0)
    for k in range(2):
        C.cyl(f"radio2_knob{k}", 0.02, 0.02, loc=(0.07 + k * 0.08, -0.105, 0.08), rot=(90, 0, 0), m=C.mat("brass"),
              parent=r2)
    C.cyl("radio2_ant", 0.003, 0.4, loc=(0.16, 0.0, 0.45), rot=(0, -15, 0), m=C.mat("chrome"), parent=r2)
    # vendor fiddles with it
    for k, fr in enumerate(range(T(0.5), T(14), 26)):
        vend.pose(fr, {"upper_arm_R": (50, 0, 0), "forearm_R": (55, 0, -10), "spine": (14, 0, 0),
                       "head": (20, (8 if k % 2 else -8), 0)})
        vend.pose(fr + 6, {"upper_arm_R": (44, 0, 0), "forearm_R": (40, 0, -10), "hand_R": (15, 0, 0)}, interp="LINEAR")
        if k % 2 == 0:
            A.event(fr + 6, "knock_wood")
    vend.pose(T(12.5), "sigh")
    # old man asleep on the bench with the cat
    bench = vl["bench"]
    om = vg["OldMan"]
    om_pos = local_to_world(bench, (-0.3, -0.05, 0))
    om.cut(F, om_pos, math.degrees(bench.rotation_euler.z))
    om.pose(F, "stand")
    om.pose(F, "sit")
    om.pose(F, {"head": (35, 0, 12), "upper_arm_L": (20, 0, 20), "upper_arm_R": (20, 0, 20), "forearm_L": (70, 0, -30),
                "forearm_R": (70, 0, -30)})
    om.bone_loc(F, "root", (0, 0.02, -0.38 / 0.95))
    om.face(F, "closed")
    cat_root, cat_head, cat_body = CH.build_cat(ctx.c_props, "cat", local_to_world(bench, (0.45, 0.0, 0.48)),
                                                yaw=math.radians(100), color=(0.55, 0.35, 0.15))
    CH.animate_breathing(cat_body, F, END, period=50, amp=0.05)
    fr = F
    k = 0
    while fr < T(22):
        om.pose(fr, {"chest": (2 + (4 if k % 2 else 0), 0, 0)})
        if k % 2:
            A.event(fr, "snore_old")
        fr += 36
        k += 1
    # others
    w1, w2, w3 = vg["Woman1"], vg["Woman2"], vg["Woman3"]
    m2, m3, k1, k2 = vg["Man2"], vg["Man3"], vg["Kid1"], vg["Kid2"]
    p_m2 = Wv(-4.6, -1.0); p_m3 = Wv(-3.6, -1.7)
    m2.cut(F, p_m2, math.degrees(A.yaw_towards(p_m3 - p_m2)))
    m3.cut(F, p_m3, math.degrees(A.yaw_towards(p_m2 - p_m3)))
    for a, s_ in ((m2, 1), (m3, 2)):
        a.pose(F, "stand"); a.face(F, "neutral")
        idle_chat(a, F, T(21), seed=s_)
    p_w2 = local_to_world(st[0], (0.2, -1.0, 0))
    w2.cut(F, p_w2, math.degrees(st[0].rotation_euler.z) + 180)
    w2.pose(F, "stand"); w2.pose(F, {"spine": (18, 0, 0), "head": (15, 0, 0), "upper_arm_R": (40, 0, 5),
                                     "forearm_R": (40, 0, 0)})
    w2.face(F, "neutral")
    w1.cut(F, Wv(-4.6, -8.2), 0)
    w1.pose(F, "stand"); w1.face(F, "neutral")
    w1.walk(T(0), [Wv(-4.6, -8.2), Wv(-5.2, -6.2), Wv(-5, -4.5)], speed=0.5, stride=0.45, end_pose="stand")
    w3.cut(F, Wv(-6.5, 5.5), 160)
    w3.pose(F, "stand"); w3.face(F, "neutral")
    w3.pose(F, {"upper_arm_L": (150, 0, 10), "upper_arm_R": (150, 0, 10), "head": (-20, 0, 0)})  # hanging laundry
    # kids: idle, bored, sitting on the fountain rim
    # on the fountain rim (r=1.6, 0.5 high), facing outward, legs dangling over the edge
    kid_out = {}
    for a, ang in ((k1, -59), (k2, -119)):
        out_ = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        kid_out[a] = out_
        a.cut(F, Wv(0, 0) + out_ * 1.56, math.degrees(A.yaw_towards(out_)))
        a.pose(F, "stand")
        a.pose(F, "sit")
        a.bone_loc(F, "root", (0, 0, 0.2))
        a.pose(F, {"head": (20, 0, 0), "upper_arm_L": (30, 0, 10), "upper_arm_R": (30, 0, 10), "forearm_L": (90, 0, 0),
                   "forearm_R": (90, 0, 0)})
        a.face(F, "sad")
    # chickens & pigeons
    chickens = []
    for i, p in enumerate((Wv(2.5, -4), Wv(-2, 3), Wv(3.5, 1.2), Wv(-4, 6.5))):
        root, head = CH.build_chicken(ctx.c_props, f"chicken{i}", loc=p, yaw=math.radians(i * 80), seed=i)
        CH.animate_chicken(root, head, F, T(21), seed=i)
        chickens.append((root, head))
    pigeons = []
    wire = vl["pigeon_wire"]
    for i in range(4):
        pt = V(wire[3 + i * 2])
        root, head = CH.build_pigeon_drone(ctx.c_props, f"pigeon_v{i}", pt, yaw=math.radians(170 + i * 10))
        CH.animate_pigeon(head, F, T(30), seed=10 + i)
        pigeons.append((root, head))
    # hologram flicker
    hs = C.emit_socket(vl["holo_m"])
    rnd = C.R.__class__(8)
    fr = F
    while fr < END:
        A.key_socket(hs, fr, rnd.choice([2.0, 2.0, 0.2, 2.5, 0.0]), "CONSTANT")
        fr += rnd.randint(3, 20)
    # ------------------------------------------------------------------ Hedda arrives, Funke peeks from her coat
    hstart = Wv(0.8, -11.5)
    hstop = local_to_world(radio_stall, (-0.9, -1.4, 0))
    h.cut(F, hstart, 0)
    h.pose(F, "stand")
    h.face(F, "neutral")
    hw = h.walk(T(1.5), [hstart, Wv(1.6, -5.0), Wv(2.8, -0.2), hstop], speed=1.25, stride=0.5, end_pose=None)
    h.place(hw + 2, hstop, math.degrees(A.yaw_towards(radio_pos - hstop)))
    h.pose(hw + 4, "stand")
    h.pose(hw + 4, {"upper_arm_L": (35, 0, 6), "forearm_L": (75, 0, -25)})  # arm cradling Funke
    A.look(h, T(5.5), om_pos + V((0, 0, 1.0)))
    A.look(h, T(7.5), om_pos + V((0, 0, 1.0)))
    A.look(h, hw + 8, radio_pos)
    h.face(hw + 14, "sad")
    # Funke hidden in the coat, peeking out
    f.cut(F, (0, 0, 0), 0)
    f.pose(F, "stand")
    f.pose(F, "curl")
    f.pose(F, {"lid": (-95, 0, 0), "head": (-30, 0, 0), "body": (40, 0, 0)})
    f.glow(F, 4.0, "iris")
    f.glow(F, 2.0, "bulb")
    A.key(ctx.funke_light.data, "energy", F, 1.0)
    mw = A.world_matrix_at(h.rig, F, "chest")
    peek = mw @ V((0.02, 0.02, -0.17))
    f.place(F, h.pos_at(F) + V((0.02, -0.14, 0.92)), h.yaw_at(F))
    con_f = A.attach_to(f.rig, h.rig, F, bone="chest", name="in_coat")
    tout = max(T(17.0), hw + 36)
    for i, fr in enumerate(range(T(6), tout - 50, 30)):
        A.look(f, fr, Wv(rnd.uniform(-6, 6), rnd.uniform(-4, 6), 1.0), pitch=-10,
               extra={"lid": (-95, 0, 0), "body": (40, 0, 0)})
    f.blink(T(8))
    f.blink(tout - 60)
    A.look(f, tout - 40, radio_pos, extra={"lid": (-95, 0, 0), "body": (40, 0, 0)})
    # ------------------------------------------------------------------ Funke goes for the radio
    A.detach(f.rig, con_f, tout)
    f.pose(tout, "stand")
    f.pose(tout, {"lid": (-95, 0, 0)})
    fpos0 = f.pos_at(tout)
    hy = math.radians(h.yaw_at(tout))
    fpos1 = fpos0 + V((math.sin(hy), -math.cos(hy), 0)) * 0.3 + V((0, 0, 0.05))  # out of the coat first
    f.place(tout + 3, fpos1, None)
    table_spot = local_to_world(radio_stall, (0.05, 0.05, 0.89))
    A.arc(f.rig, tout + 4, tout + 18, fpos1, table_spot, height=0.4)
    f.place(tout + 18, table_spot, math.degrees(A.yaw_towards(radio_pos - table_spot)))
    A.event(tout + 16, "land_spring")
    f.pose(tout + 16, "happy")
    f.bone_scale(tout + 16, "body", (1.15, 1.15, 0.8))
    f.bone_scale(tout + 20, "body", (1, 1, 1))
    h.face(tout + 2, "surprised")
    h.pose(tout + 4, {"upper_arm_L": (60, 0, 20), "forearm_L": (20, 0, 0), "head": (5, 0, 0)})
    vend.face(tout + 18, "surprised")
    vend.pose(tout + 18, {"spine": (-6, 0, 0), "head": (-10, 0, 0)})
    tk = f.tap_twice(tout + 26)
    t_music = tk + 4
    A.event(t_music, "music_radio_start", beat=BEAT)
    A.key_socket(dial_m.node_tree.nodes["Emission"].inputs[1] if False else C.emit_socket(dial_m), t_music - 1, 0.0,
                 "CONSTANT")
    A.key_socket(C.emit_socket(dial_m), t_music, 6.0, "CONSTANT")
    # radio bounces to the beat
    t_stop = T(35.0)
    fr = t_music
    while fr < t_stop:
        r2.location = radio_pos + V((0, 0, 0.03))
        r2.keyframe_insert("location", frame=fr + 2)
        r2.location = radio_pos
        r2.keyframe_insert("location", frame=fr + BEAT // 2)
        fr += BEAT
    # ------------------------------------------------------------------ everyone dances
    td = t_music + 8
    vend.face(td, "happy")
    dance(vend, td + 6, t_stop, seed=1)
    for a, s_, d0 in ((m2, 2, 10), (m3, 3, 16), (w1, 4, 20), (w2, 5, 8), (w3, 6, 26)):
        a.hold(td + d0 - 2)
        a.face(td + d0, "happy")
        a.pose(td + d0, "stand")
        dance(a, td + d0, t_stop, seed=s_)
    for a, s_ in ((k1, 7), (k2, 8)):
        a.bone_loc(td - 2, "root", (0, 0, 0.2))
        a.pose(td + 2, "stand")
        a.bone_loc(td + 2, "root", (0, 0, 0))
        a.face(td + 2, "happy")
        a.place(td - 2, a.pos_at(td - 2), None)
        a.place(td + 2, a.pos_at(td) + kid_out[a] * 0.75, None)
        dance(a, td + 6, t_stop, seed=s_, style="dance")
    # old man wakes up and dances, the cat jumps off
    tw = td + C.sec(2.5)
    ctx.ground_skip += [("OldMan", F, tw + 16), ("Kid1", F, td + 2), ("Kid2", F, td + 2)]
    om.face(tw, "surprised")
    om.pose(tw, {"head": (-10, 0, 0)})
    om.bone_loc(tw + 10, "root", (0, 0.02, -0.38 / 0.95))
    om.pose(tw + 16, "stand")
    om.bone_loc(tw + 16, "root", (0, 0, 0))
    om.place(tw + 16, om_pos + V((0, -0.6, 0)), None)
    om.face(tw + 18, "happy")
    dance(om, tw + 20, t_stop, seed=9)
    cat_root.keyframe_insert("location", frame=tw + 2)
    A.arc(cat_root, tw + 3, tw + 15, V(cat_root.location), V(cat_root.location) + V((1.2, -0.8, -0.48)), height=0.5)
    A.event(tw + 3, "cat_meow")
    # Hedda: amused, sways with the music
    h.face(td + 4, "happy")
    h.pose(td + 4, "stand")
    dance(h, td + 20, t_stop, seed=11, style="dance")
    # Funke dances on the table
    fr = td
    k = 0
    while fr < t_stop:
        up = k % 2 == 0
        f.pose(fr, {"arm_L": (30 + (90 if up else 0), 0, 50), "arm_R": (30 + (0 if up else 90), 0, 50),
                    "body": (0, 0, 12 if up else -12), "head": (-10, 0, -10 if up else 10),
                    "antenna": (0, 0, 25 if up else -25), "leg_L": (20 if up else 0, 0, 0),
                    "leg_R": (0 if up else 20, 0, 0)})
        f.bone_loc(fr, "root", (0, 0, 0.04 if up else 0.0))
        f.glow(fr, 9.0 if up else 4.0, "bulb", "CONSTANT")
        fr += BEAT // 2
        k += 1
    # chickens hop to the beat
    for i, (root, head) in enumerate(chickens):
        fr = td + i * 3
        base = V(root.location)
        while fr < t_stop:
            root.location = base + V((0, 0, 0.15))
            root.keyframe_insert("location", frame=fr)
            root.location = base
            root.keyframe_insert("location", frame=fr + BEAT // 2)
            fr += BEAT
    # string lights brighter during the dance
    for i in range(4):
        m = bpy.data.materials.get(f"bulb_{i}")
        if m:
            A.key_socket(C.emit_socket(m), td - 1, 6.0)
            A.key_socket(C.emit_socket(m), td + 12, 14.0)
            A.key_socket(C.emit_socket(m), t_stop, 14.0)
            A.key_socket(C.emit_socket(m), t_stop + 1, 3.0, "CONSTANT")
    # ------------------------------------------------------------------ the drone-pigeon reports
    tp = T(31.0)
    proot, phead = pigeons[1]
    phead.rotation_euler = (0, 0, 0)
    phead.keyframe_insert("rotation_euler", frame=tp)
    phead.rotation_euler = (math.radians(30), 0, math.radians(-80))
    phead.keyframe_insert("rotation_euler", frame=tp + 8)
    eye_m = bpy.data.materials["drone_eye"]
    A.key_socket(C.emit_socket(eye_m), tp + 8, 6.0, "CONSTANT")
    for k in range(4):
        A.key_socket(C.emit_socket(eye_m), tp + 10 + k * 8, 40.0, "CONSTANT")
        A.key_socket(C.emit_socket(eye_m), tp + 14 + k * 8, 6.0, "CONSTANT")
        A.event(tp + 10 + k * 8, "drone_beep")
    # ------------------------------------------------------------------ the Erfasser arrives – freeze
    e.cut(T(32.5), Wv(0.3, -16), 0)
    e.pose(T(32.5), "stand")
    er = e.roll(T(32.6), [Wv(0.3, -16), Wv(0.3, -11.5)], speed=2.0)
    A.event(t_stop, "record_scratch")
    A.event(t_stop, "music_radio_stop")
    A.key_socket(C.emit_socket(dial_m), t_stop, 0.0, "CONSTANT")
    for a in [vend, m2, m3, w1, w2, w3, k1, k2, om, h]:
        a.hold(t_stop)
        a.hold_place(t_stop)
        a.face(t_stop + 3, "surprised")
    f.hold(t_stop)
    f.pose(t_stop + 4, {"lid": (-10, 0, 0), "antenna": (60, 0, 0)})
    f.glow(t_stop + 2, 0.5, "bulb", "CONSTANT")
    A.key(ctx.erf_beam.data, "energy", er, 0.0)
    A.key(ctx.erf_beam.data, "energy", er + 6, 600.0)
    e.scan(er + 4, er + C.sec(2.5), sweeps=2)
    for a in [vend, m2, m3, w1, w2, w3, k1, k2, om]:
        a.face(t_stop + 20, "worried")
    h.face(t_stop + 14, "worried")
    A.look(h, t_stop + 14, Wv(0.3, -11.5, 2.0))
    # ------------------------------------------------------------------ cameras
    B.shot(ctx, 3, "S3_c1_wide", F, [(F, Wv(0.5, -17.5, 4.5), Wv(0, 3, 1.4)), (T(4.5), Wv(0.0, -15.5, 3.8), Wv(0, 2, 1.4))],
           lens=26)
    wk = []
    for t_ in (T(4.5), T(7.5), T(11)):
        hp_ = h.pos_at(t_)
        wk.append((t_, hp_ + V((1.9, 3.6, 1.5)), hp_ + V((0, 0, 1.05))))
    B.shot(ctx, 3, "S3_c2_walk", T(4.5), wk, lens=30)
    B.shot(ctx, 3, "S3_c3_vendor", T(11), [(T(11), hstop + V((1.3, -2.1, 1.2)), radio_pos + V((-0.4, 0, 0.15))),
                                           (tout, hstop + V((1.2, -2.0, 1.2)), radio_pos + V((-0.6, -0.2, 0.1)))], lens=28)
    B.shot(ctx, 3, "S3_c4_radio", tout + 10, [(tout + 10, radio_pos + V((-0.9, -1.2, 0.35)), radio_pos + V((-0.2, 0, 0.1))),
                                              (td, radio_pos + V((-0.85, -1.1, 0.4)), radio_pos + V((-0.2, 0, 0.1)))],
           lens=32)
    B.shot(ctx, 3, "S3_c5_dance", td, [(td, Wv(-1.5, -13, 3.0), Wv(0, 1, 1.0)), (td + C.sec(4), Wv(1.0, -11, 2.6), Wv(0, 1, 1.0))],
           lens=24)
    B.shot(ctx, 3, "S3_c5b_kids", td + C.sec(4), [(td + C.sec(4), Wv(-1.6, -5.0, 1.0), Wv(0.2, -1.8, 0.7)),
                                                  (td + C.sec(6), Wv(-1.2, -5.2, 1.0), Wv(0.2, -2.0, 0.8))], lens=30)
    B.shot(ctx, 3, "S3_c5c_oldman", td + C.sec(6), [(td + C.sec(6), om_pos + V((2.0, -3.0, 1.3)), om_pos + V((0, -0.5, 0.95))),
                                                    (td + C.sec(8), om_pos + V((1.8, -2.8, 1.3)), om_pos + V((0, -0.6, 1.0)))],
           lens=24)
    side = (radio_pos - hstop).normalized()
    perp = V((-side.y, side.x, 0))
    to_c = (Wv(0, 0) - hstop)
    to_c.z = 0
    to_c.normalize()
    pc = V((-to_c.y, to_c.x, 0))
    B.shot(ctx, 3, "S3_c5d_hedda", td + C.sec(8), [(td + C.sec(8), hstop + to_c * 1.6 + pc * 2.3 + V((0, 0, 1.3)),
                                                    hstop + (radio_pos - hstop) * 0.35 + V((0, 0, 1.0))),
                                                   (tp, hstop + to_c * 1.5 + pc * 2.1 + V((0, 0, 1.25)),
                                                    hstop + (radio_pos - hstop) * 0.35 + V((0, 0, 1.0)))], lens=28)
    pw = V(proot.location)
    B.shot(ctx, 3, "S3_c6_drone", tp, [(tp, pw + V((0.9, -1.4, -0.2)), pw + V((0, 0, 0.05)))], lens=55)
    B.shot(ctx, 3, "S3_c7_erf", T(32.5), [(T(32.5), Wv(2.8, 1.4, 1.6), Wv(0.3, -12, 1.8)),
                                          (t_stop + 10, Wv(2.6, 0.6, 1.6), Wv(0.3, -12, 1.8))], lens=32)
    to_e = (Wv(0.3, -11.5) - hstop)
    to_e.z = 0
    to_e.normalize()
    B.shot(ctx, 3, "S3_c7b_freeze", t_stop + 12, [(t_stop + 12, hstop + to_e * 2.3 + pc * 0.5 + V((0, 0, 1.4)),
                                                   hstop + V((0, 0, 1.3))),
                                                  (END, hstop + to_e * 2.0 + pc * 0.45 + V((0, 0, 1.38)),
                                                   hstop + V((0, 0, 1.32)))], lens=26)
    ctx.s3 = {"hstop": hstop, "radio_pos": radio_pos, "table": table_spot, "erf_end": Wv(0.3, -11.5)}
    return END
