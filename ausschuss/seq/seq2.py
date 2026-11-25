"""SEQ 2 – The workshop at night: building Funke, awakening, three attempts to help, sleep."""
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
O = S2.WORKSHOP


def W(x, y, z=0.0):
    return O + V((x, y, z))


def funke_groups(funke):
    g = {"legs": [], "body": [], "arms": [], "head": [], "eye": [], "ant": []}
    for ob in funke.rig.children:
        n = ob.name
        if any(k in n for k in ("foot", "_leg", "spring")):
            g["legs"].append(ob)
        elif "decal" in n:
            continue  # the OBSOLETE stamp only appears when it is stamped on
        elif any(k in n for k in ("_body", "rivet", "gauge", "needle")):
            g["body"].append(ob)
        elif any(k in n for k in ("_sh", "_ua", "uarm", "farm", "_fa", "wrist", "claw")):
            g["arms"].append(ob)
        elif "_eye_" in n:
            g["eye"].append(ob)
        elif any(k in n for k in ("ant_", "bulb")):
            g["ant"].append(ob)
        elif any(k in n for k in ("neck", "can", "label", "lid")):
            g["head"].append(ob)
    return g


def sparks(name, pos, f0, f1, coll, light=True, seed=0):
    rnd = C.R.__class__(seed)
    m = C.emission(name + "_m", (0.7, 0.85, 1.0), 40)
    sp = C.sphere(name, 0.012, loc=pos, m=m, seg=8, rings=4, coll=coll)
    lt = P.point_light(name + "_l", V(pos) + V((0, -0.05, 0.05)), 0, (0.6, 0.8, 1.0), 0.02, coll=coll)
    sp.scale = (0, 0, 0)
    sp.keyframe_insert("scale", frame=f0 - 1)
    A.key(lt.data, "energy", f0 - 1, 0.0)
    f = f0
    while f < f1:
        on = rnd.random() < 0.6
        s = rnd.uniform(0.6, 2.0) if on else 0.0
        sp.scale = (s, s, s)
        sp.keyframe_insert("scale", frame=f)
        A.key(lt.data, "energy", f, rnd.uniform(5, 25) if on else 0.0, "CONSTANT")
        f += rnd.randint(1, 3)
    sp.scale = (0, 0, 0)
    sp.keyframe_insert("scale", frame=f1)
    A.key(lt.data, "energy", f1, 0.0, "CONSTANT")
    A.event(f0, "solder", dur=f1 - f0)
    return sp, lt


def build(ctx, F):
    T = lambda s: F + C.sec(s)
    END = T(75)  # provisional, trimmed at the end
    h, f = ctx.hedda, ctx.funke
    wld = S.world("W_S2_night", horizon=(0.05, 0.07, 0.13), zenith=(0.008, 0.01, 0.03), ground=(0.01, 0.01, 0.01),
                  strength=0.6)
    sc, L, cams = B.new_seq_scene(ctx, 2, "S2_Workshop_Night", F, END, wld,
                                  [ctx.chars, ctx.c_ws, ctx.c_scrap, ctx.c_city, ctx.c_props])
    S.sun("S2_moon", (55, 0, -60), 0.7, (0.45, 0.6, 1.0), L, angle=5)
    fill = P.point_light("S2_fill", W(0.0, -1.2, 2.5), 140, (1.0, 0.72, 0.45), 2.5, coll=L, kind="AREA")
    fill.data.size = 2.5
    fill2 = P.point_light("S2_fill2", W(-1.5, -2.0, 1.6), 40, (0.5, 0.6, 1.0), 1.5, coll=L, kind="AREA",
                          rot=(80, 0, -30))
    S.fog_box("S2_fog", L, (0, 0, 0), (400, 400, 40), 0.004, (0.5, 0.6, 0.8))
    ws = ctx.ws
    B.offstage_all(ctx, F, keep=(h, f))
    S2.animate_workshop_gadgets(ws, F, END)
    hut = ctx.scrap["hut"]
    # ------------------------------------------------------------------ 2.1 exterior
    # welding flashes in the hut window, chimney smoke
    lamp = hut["lamp"]
    rnd = C.R.__class__(11)
    A.key(lamp.data, "energy", F, 120.0)
    fr = F + 10
    while fr < T(4):
        A.key(lamp.data, "energy", fr, rnd.choice([120, 120, 600, 900]), "CONSTANT")
        A.key(lamp.data, "color", fr, (0.6, 0.8, 1.0) if rnd.random() < 0.5 else (1.0, 0.6, 0.3), "CONSTANT")
        fr += rnd.randint(2, 6)
    A.event(F + 10, "weld_outside", dur=C.sec(3.5))
    top = hut["root"].matrix_world @ hut["chimney_top"] if False else None
    hroot = hut["root"]
    ch_top = V(S.SCRAP["hut"]) + V((math.cos(math.radians(-75)) * -1.5 - math.sin(math.radians(-75)) * 1.0,
                                   math.sin(math.radians(-75)) * -1.5 + math.cos(math.radians(-75)) * 1.0, 4.2))
    P.smoke("S2_smoke", ch_top, F - 40, T(4.5), coll=ctx.c_props, every=8, rise=3.0, life=70, size=0.22,
            color=(0.3, 0.3, 0.33), seed=2)
    S.spin(hut["mill_rotor"], F, T(4.5), axis=1, turns_per_sec=0.25)
    B.shot(ctx, 2, "S2_c1_hut", F, [(F, (-22.5, -7.5, 1.4), (-15, -3, 2.0)), (T(4), (-21.6, -7.0, 1.5), (-15, -3, 1.9))],
           lens=30)
    # ------------------------------------------------------------------ Funke on the bench (assembly)
    bench = ws["bench_spot"]
    grp = funke_groups(f)
    f.cut(F, bench, 0)
    f.pose(F, "stand")
    f.pose(F, "off")
    f.glow(F, 0.0, "bulb")
    f.glow(F, 0.0, "iris")
    A.key(ctx.funke_light.data, "energy", F, 0.0)
    for g in grp.values():
        for ob in g:
            A.hide(ob, F, True)
    stage_t = {"legs": T(4.0), "body": T(6.0), "arms": T(8.0), "head": T(10.0)}
    for k, t in stage_t.items():
        for ob in grp[k]:
            A.hide(ob, t, False)
    # Hedda at the bench
    hpos = W(0.2, 1.05)
    h.cut(F, hpos, 180)
    h.pose(F, "stand")
    h.pose(F, "work")
    h.face(F, "neutral")
    fr = T(4)
    k = 0
    while fr < T(14):
        h.pose(fr, {"forearm_R": (60 + (12 if k % 2 else -6), 0, -20), "forearm_L": (60 + (-8 if k % 2 else 8), 0, -20),
                    "head": (12 + (3 if k % 3 else 0), (6 if k % 4 == 0 else 0), 0)})
        fr += 9
        k += 1
    h.face(T(10.2), "neutral")
    # wipe brow
    h.pose(T(10.4), {"upper_arm_L": (120, 0, -10), "forearm_L": (100, 0, 0), "head": (-10, 0, 0)})
    h.pose(T(11.4), "work")
    h.blink(T(10.9))
    sparks("S2_sparkA", bench + V((0.0, -0.12, 0.1)), T(4.1), T(5.8), ctx.c_props, seed=1)
    sparks("S2_sparkB", bench + V((0.05, -0.1, 0.22)), T(8.1), T(9.6), ctx.c_props, seed=2)
    sparks("S2_sparkC", bench + V((0.0, -0.09, 0.42)), T(12.2), T(13.6), ctx.c_props, seed=3)
    A.event(T(6.2), "hammer_tiny")
    A.event(T(6.6), "hammer_tiny")
    A.event(T(7.0), "hammer_tiny")
    A.event(T(8.3), "screw")
    A.event(T(10.1), "clock_tick", dur=C.sec(4))
    B.shot(ctx, 2, "S2_m1_legs", T(4), [(T(4), W(0.75, 1.15, 1.25), bench + V((0, 0, 0.12))),
                                        (T(6), W(0.65, 1.2, 1.22), bench + V((0, 0, 0.12)))], lens=45)
    B.shot(ctx, 2, "S2_m2_body", T(6), [(T(6), W(-1.9, 0.5, 1.5), W(0.1, 1.6, 1.1)),
                                        (T(8), W(-1.8, 0.7, 1.5), W(0.1, 1.6, 1.15))], lens=30)
    B.shot(ctx, 2, "S2_m3_arms", T(8), [(T(8), W(0.95, 1.2, 1.45), bench + V((0, 0, 0.22))),
                                        (T(10), W(0.9, 1.25, 1.42), bench + V((0, 0, 0.22)))], lens=35)
    B.shot(ctx, 2, "S2_m4_bird", T(10), [(T(10), W(-1.75, -0.95, 1.9), W(-2.3, -0.2, 2.07), 50),
                                         (T(12), W(-1.65, -0.85, 1.95), W(-2.3, -0.2, 2.05), 55)], lens=50)
    B.shot(ctx, 2, "S2_m5_orrery", T(12), [(T(12), W(1.75, 1.15, 1.2), W(1.3, 1.8, 1.25)),
                                           (T(14), W(1.7, 1.05, 1.22), W(0.6, 1.8, 1.2))], lens=40)
    # ------------------------------------------------------------------ 2.3 the lens goes in
    lens = ctx.lens
    t_ins = T(15.0)
    h.pose(T(14.2), "work")
    h.pose(T(14.6), {"upper_arm_R": (75, 0, -20), "forearm_R": (55, 0, -10), "hand_R": (-20, 0, 0), "head": (16, 0, 0),
                     "spine": (12, 0, 0)})
    h.pose(t_ins, {"upper_arm_R": (70, 0, -12), "forearm_R": (40, 0, -5), "hand_R": (-10, 0, 0), "head": (20, 0, 0),
                   "spine": (14, 0, 0)})
    A.event(t_ins, "click")
    A.hide(lens, t_ins, True)
    for ob in grp["eye"] + grp["ant"]:
        A.hide(ob, t_ins, False)
    h.pose(t_ins + 8, "work")
    # tap twice -> nothing
    t1 = t_ins + 14
    h.tap_twice(t1)
    h.face(t1 + 18, "neutral")
    A.look(h, t1 + 20, f.pos_at(t1) + V((0, 0, 0.45)), pitch=20)
    t2 = t1 + 34
    h.tap_twice(t2)
    f.pose(t2 + 10, {"head": (30, 0, 8)})
    f.pose(t2 + 18, {"head": (25, 0, 0)})
    A.event(t2 + 12, "clunk_dead")
    h.face(t2 + 22, "sad")
    h.pose(t2 + 22, "sigh")
    A.event(t2 + 24, "sigh")
    # turn away and shuffle toward the chair
    t_away = t2 + 40
    h.hold_place(t_away)
    aw_end = h.walk(t_away, [W(0.2, 1.05), W(-0.4, 0.2), W(-1.0, -0.5)], speed=0.6, stride=0.4, style="shuffle",
                    end_pose="sigh")
    B.shot(ctx, 2, "S2_c3_insert", T(14), [(T(14), W(1.9, 0.95, 1.4), W(0.2, 1.5, 1.12)),
                                           (t_away, W(1.8, 0.9, 1.4), W(0.15, 1.45, 1.15))], lens=32)
    # ------------------------------------------------------------------ 2.4 awakening
    tw = T(21.0)
    f.glow(tw, 0.0, "iris")
    for i, (dt, v) in enumerate(((2, 1.5), (4, 0.0), (7, 2.5), (9, 0.3), (12, 4.0))):
        f.glow(tw + dt, v, "iris", "CONSTANT")
    A.key(ctx.funke_light.data, "energy", tw + 11, 0.0)
    A.key(ctx.funke_light.data, "energy", tw + 13, 3.0)
    A.event(tw + 2, "flicker_on")
    f.pose(tw + 12, {"lid": (0, 0, 0)})
    f.pose(tw + 20, {"lid": (-95, 0, 0), "head": (5, 0, 0), "body": (4, 0, 0)})
    A.event(tw + 18, "lid_open")
    f.blink(tw + 30)
    f.pose(tw + 36, {"head": (-8, 0, -30), "antenna": (-10, 0, 20)})
    f.pose(tw + 52, {"head": (-8, 0, 30), "antenna": (-10, 0, -20)})
    f.pose(tw + 66, {"head": (-12, 0, 8), "antenna": (0, 0, 0)})
    f.glow(tw + 30, 0.0, "bulb")
    f.glow(tw + 34, 5.0, "bulb")
    A.event(tw + 34, "ping")
    f.pose(tw + 36, {"needle": (0, 60, 0)})
    # Hedda stops, slowly turns
    tt = tw + 46
    h.place(tt, None, h.yaw_at(tt))
    h.place(tt + 18, None, math.degrees(A.yaw_towards(bench - W(-1.0, -0.5))))
    h.pose(tt + 18, {"head": (-4, 0, 0), "spine": (-6, 0, 0)})
    h.face(tt + 12, "surprised")
    f.blink(tt + 30)
    B.shot(ctx, 2, "S2_c4_eye", tw - 6, [(tw - 6, W(0.2, 1.2, 1.18), bench + V((0, 0, 0.44))),
                                         (tt, W(0.2, 1.28, 1.2), bench + V((0, 0, 0.44)))], lens=50)
    B.shot(ctx, 2, "S2_c4b_turn", tt, [(tt, W(1.3, 2.25, 1.45), W(-0.9, -0.5, 1.15)),
                                       (tt + 40, W(1.25, 2.2, 1.43), W(-0.9, -0.5, 1.2))], lens=30)
    # ------------------------------------------------------------------ 2.5 first steps, plop, imitation
    t5 = tt + 42
    f.pose(t5, "stand")
    f.pose(t5, {"lid": (-95, 0, 0), "needle": (0, 60, 0)})
    f.walk_cycle(t5 + 6, 0.0, "walk")
    f.walk_cycle(t5 + 12, 0.5, "walk")
    A.event(t5 + 6, "step_tiny")
    f.place(t5 + 14, bench, 0)
    floor = W(0.4, 0.55, 0.0)
    A.arc(f.rig, t5 + 16, t5 + 30, bench + V((0, -0.2, 0)), floor, height=0.35, steps=6)
    f.pose(t5 + 22, "happy")
    A.event(t5 + 30, "land_spring")
    f.pose(t5 + 30, "stand")
    f.bone_scale(t5 + 30, "body", (1.2, 1.2, 0.75))
    f.bone_scale(t5 + 34, "body", (0.95, 0.95, 1.08))
    f.bone_scale(t5 + 38, "body", (1, 1, 1))
    # wobble and fall backwards
    f.pose(t5 + 40, {"body": (-10, 0, 8)})
    f.pose(t5 + 46, {"body": (8, 0, -8)})
    f.pose(t5 + 52, {"body": (-20, 0, 4)})
    f.rig.rotation_euler.x = 0
    f.rig.keyframe_insert("rotation_euler", frame=t5 + 54, index=0)
    f.rig.rotation_euler.x = math.radians(-80)
    f.rig.keyframe_insert("rotation_euler", frame=t5 + 60, index=0)
    f.place(t5 + 60, floor + V((0, 0.12, 0.08)), None)
    A.event(t5 + 60, "plop")
    f.pose(t5 + 60, {"leg_L": (60, 0, 0), "leg_R": (50, 0, 0), "arm_L": (60, 0, 30), "arm_R": (60, 0, 30)})
    f.blink(t5 + 70)
    f.rig.keyframe_insert("rotation_euler", frame=t5 + 78, index=0)
    f.rig.rotation_euler.x = 0
    f.rig.keyframe_insert("rotation_euler", frame=t5 + 88, index=0)
    f.place(t5 + 78, floor + V((0, 0.12, 0.08)), None)
    f.place(t5 + 88, floor, None)
    f.pose(t5 + 88, "stand")
    A.event(t5 + 84, "boing")
    h.face(t5 + 60, "worried")
    h.pose(t5 + 62, {"spine": (12, 0, 0), "upper_arm_L": (40, 0, 20), "upper_arm_R": (40, 0, 20)})
    # Hedda walks closer, hands on hips
    hp2 = W(-0.35, -0.2)
    h.hold_place(t5 + 64)
    he = h.walk(t5 + 64, [h.pos_at(t5 + 64), hp2], speed=0.8, stride=0.4, end_pose=None)
    h.place(he + 2, hp2, math.degrees(A.yaw_towards(floor - hp2)))
    h.pose(he + 6, "stand")
    h.pose(he + 14, "hands_hips")
    h.face(he + 14, "neutral")
    f.place(he + 4, floor, math.degrees(A.yaw_towards(hp2 - floor)))
    A.look(f, he + 14, hp2 + V((0, 0, 1.6)), pitch=-25, extra={"lid": (-95, 0, 0)})
    f.pose(he + 30, "hands_hips")
    f.pose(he + 30, {"head": (-25, 0, 0)})
    A.event(he + 30, "imitate")
    h.face(he + 38, "happy")
    h.pose(he + 38, {"head": (-8, 12, 0)})
    t_imit_end = he + 52
    B.shot(ctx, 2, "S2_c5_steps", t5, [(t5, W(1.9, -1.9, 1.3), W(0.1, 0.8, 0.65)),
                                       (he, W(2.2, -2.0, 1.2), W(-0.1, 0.3, 0.65))], lens=24)
    B.shot(ctx, 2, "S2_c5b_imit", he + 10, [(he + 10, W(2.4, -2.0, 1.15), W(0.05, 0.2, 0.62)),
                                            (t_imit_end, W(2.3, -1.9, 1.1), W(0.05, 0.2, 0.65))], lens=26)
    # ------------------------------------------------------------------ 2.6a hammer smashes the desk lamp
    ta = t_imit_end + 4
    h.pose(ta, "stand")
    h.hold_place(ta)
    hb = W(-0.6, 1.0)
    he2 = h.walk(ta, [hp2, hb], speed=0.9, stride=0.45, end_pose=None)
    h.place(he2 + 2, hb, 180)
    h.pose(he2 + 8, "reach")
    h.pose(he2 + 8, {"upper_arm_R": (95, 0, 0), "head": (-15, 0, 0)})
    # Funke hops onto bench near the lamp with a hammer
    C.set_coll(ctx.c_props)
    hammer = C.empty("funke_hammer", loc=(0, 0, -300), coll=ctx.c_props)
    C.box("fh_head", (0.12, 0.04, 0.045), loc=(0, 0, 0.13), m=C.mat("dark_metal"), parent=hammer, bevel=0.005)
    C.cyl("fh_handle", 0.01, 0.2, loc=(0, 0, 0.03), m=C.mat("p_wood"), parent=hammer)
    f.hold_place(ta)
    fw = f.walk(ta + 2, [floor, W(-0.3, 1.25)], speed=0.9, stride=0.12, end_pose="stand")
    onb = W(-0.45, 1.75, 0.96)
    A.arc(f.rig, fw + 2, fw + 14, W(-0.3, 1.25), onb, height=0.5)
    A.event(fw + 14, "land_spring")
    f.place(fw + 16, onb, 170)
    tg = fw + 18
    hammer.location = A.world_matrix_at(f.rig, tg, "fore_R").translation
    hammer.keyframe_insert("location", frame=tg)
    A.set_interp(hammer, "location", tg - 1, "CONSTANT")
    hammer.location = (0, 0, -300)
    hammer.keyframe_insert("location", frame=tg - 1)
    A.set_interp(hammer, "location", tg - 1, "CONSTANT")
    con_h = A.attach_to(hammer, f.rig, tg, bone="fore_R")
    f.pose(tg, "happy")
    h.face(tg + 4, "surprised")
    A.look(h, tg + 4, onb + V((0, 0, 0.4)))
    # swing!
    tsw = tg + 16
    f.place(tsw - 4, onb, 210)
    f.pose(tsw, {"arm_R": (170, 0, 0), "fore_R": (20, 0, 0), "body": (-12, 0, 0), "head": (-10, 0, 0)})
    f.pose(tsw + 5, {"arm_R": (60, 0, 0), "fore_R": (10, 0, 0), "body": (15, 0, 0), "head": (6, 0, 0)},
           interp="LINEAR")
    A.event(tsw + 5, "glass_break")
    sock = C.emit_socket(ws["desk_bulb_m"])
    A.key_socket(sock, tsw + 4, 20.0)
    A.key_socket(sock, tsw + 5, 0.0, "CONSTANT")
    A.key(ws["desk_light"].data, "energy", tsw + 4, 60.0)
    A.key(ws["desk_light"].data, "energy", tsw + 5, 0.0, "CONSTANT")
    A.hide(ws["desk_bulb"], tsw + 5, True)
    bulbp = V(ws["desk_bulb"].location)
    for i in range(7):
        sh = C.cyl(f"shard{i}", 0.012, 0.004, loc=(0, 0, -300), m=C.glass("jar_glass"), verts=3, coll=ctx.c_props)
        sh.keyframe_insert("location", frame=tsw + 4)
        A.set_interp(sh, "location", tsw + 4, "CONSTANT")
        a = i / 7 * 6.28
        A.arc(sh, tsw + 5, tsw + 18, bulbp, bulbp + V((math.cos(a) * 0.5, math.sin(a) * 0.4 - 0.3, -0.42)), height=0.2,
              spin=(8, 5, 3))
    h.pose(tsw + 6, {"upper_arm_L": (60, 0, 40), "upper_arm_R": (60, 0, 40), "forearm_L": (90, 0, 0),
                     "forearm_R": (90, 0, 0), "head": (10, 0, 0), "spine": (-8, 0, 0)})
    h.face(tsw + 6, "closed")
    h.face(tsw + 26, "angry")
    f.pose(tsw + 16, {"arm_R": (40, 0, 0), "head": (15, 0, 0), "antenna": (40, 0, 0)})
    f.pose(tsw + 30, "sad")
    A.detach(hammer, con_h, tsw + 34)
    hammer.location = onb + V((0.1, 0, 0.02))
    hammer.rotation_euler = (0, math.radians(90), 0)
    hammer.keyframe_insert("location", frame=tsw + 40)
    hammer.keyframe_insert("rotation_euler", frame=tsw + 40)
    t6a_end = tsw + 48
    B.shot(ctx, 2, "S2_c6a_lamp", ta, [(ta, W(0.9, 0.3, 1.45), W(-0.4, 1.6, 1.15)),
                                       (t6a_end, W(0.95, 0.5, 1.4), W(-0.35, 1.6, 1.2))], lens=30)
    # ------------------------------------------------------------------ 2.6b the shelf
    tb = t6a_end + 2
    htv = W(2.0, -0.4)
    h.pose(tb, "stand")
    h.hold_place(tb)
    hw2 = h.walk(tb, [hb, W(1.0, 0.0), htv], speed=1.0, stride=0.45, end_pose=None)
    h.place(hw2 + 2, htv, 90)
    h.pose(hw2 + 8, "crouch")
    h.face(hw2 + 8, "neutral")
    fr = hw2 + 10
    for k in range(4):
        h.pose(fr, {"forearm_R": (60 + 15 * (k % 2), 0, 0), "forearm_L": (60 - 10 * (k % 2), 0, 0)})
        fr += 7
    A.event(hw2 + 10, "fiddle", dur=28)
    # Funke hops down and pulls a cable dangling from the shelf
    cable = C.curve_tube("shelf_cable", [W(2.62, -1.05, 1.85), W(2.35, -1.2, 1.0), W(2.15, -1.3, 0.25)],
                         radius=0.01, m=C.mat("p_red"), coll=ctx.c_props)
    bpy.context.view_layer.update()
    cable.parent = ws["shelf"]
    cable.matrix_parent_inverse = ws["shelf"].matrix_world.inverted()
    f.place(tb, onb, 210)
    A.arc(f.rig, tb + 4, tb + 18, onb, W(-0.2, 1.0), height=0.4)
    f.pose(tb + 4, "stand")
    A.event(tb + 18, "land_spring")
    FP = W(1.95, -1.55)  # beside the shelf, under the dangling cable
    fw2 = f.walk(tb + 20, [W(-0.2, 1.0), W(0.6, -1.5), FP], speed=1.0, stride=0.12, end_pose="stand")
    f.place(fw2 + 2, FP, -60)
    tpull = fw2 + 10
    f.pose(tpull, "reach_up")
    f.pose(tpull + 8, {"arm_L": (120, 0, 10), "arm_R": (120, 0, 10), "body": (-25, 0, 0), "head": (-30, 0, 0)})
    A.event(tpull + 6, "creak")
    # shelf topples onto Hedda (pivot at its foot, falls toward -X)
    shelf = ws["shelf"]
    shelf.keyframe_insert("rotation_euler", frame=tpull + 8)
    shelf.rotation_euler.y = math.radians(-9)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 14)
    shelf.rotation_euler.y = math.radians(-7)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 22)  # the hesitation
    shelf.rotation_euler.y = math.radians(-35)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 28)
    shelf.rotation_euler.y = math.radians(-90)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 32)
    A.set_interp(shelf, "rotation_euler", tpull + 28, "LINEAR")
    shelf.rotation_euler.y = math.radians(-86)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 34)
    shelf.rotation_euler.y = math.radians(-90)
    shelf.keyframe_insert("rotation_euler", frame=tpull + 37)
    A.event(tpull + 32, "crash")
    A.shake(shelf, tpull + 32, tpull + 38, amp=0.01, freq=1)
    h.pose(tpull + 14, {"head": (-30, 0, 0), "spine": (10, 0, 0)})
    h.face(tpull + 14, "surprised")
    # leap clear: back and to her left, landing on her bottom
    HD = W(1.0, 0.8)
    h.hold_place(tpull + 20)
    A.arc(h.rig, tpull + 21, tpull + 31, htv, HD, height=0.55)
    h.place(tpull + 31, HD, 105)
    h.pose(tpull + 24, {"spine": (-10, 0, 0), "chest": (-6, 0, 0), "head": (-10, 0, 0), "upper_arm_L": (150, 0, 30),
                        "upper_arm_R": (150, 0, 30), "forearm_L": (20, 0, 0), "forearm_R": (20, 0, 0),
                        "thigh_L": (60, 0, 8), "thigh_R": (40, 0, 8), "shin_L": (-70, 0, 0), "shin_R": (-50, 0, 0)})
    floor_sit = {"hips": (-10, 0, 0), "spine": (4, 0, 0), "chest": (4, 0, 0), "thigh_L": (82, 0, 10),
                 "thigh_R": (82, 0, 10), "shin_L": (-12, 0, 0), "shin_R": (-12, 0, 0), "foot_L": (-10, 0, 0),
                 "foot_R": (-10, 0, 0), "upper_arm_L": (-25, 0, 20), "upper_arm_R": (-25, 0, 20),
                 "forearm_L": (10, 0, 0), "forearm_R": (10, 0, 0), "head": (6, 0, 0)}
    h.pose(tpull + 31, floor_sit)
    h.bone_loc(tpull + 29, "root", (0, 0, 0))
    h.bone_loc(tpull + 31, "root", (0, 0, -0.74))
    h.face(tpull + 30, "closed")
    A.event(tpull + 31, "thud")
    h.face(tpull + 38, "surprised")
    A.look(h, tpull + 40, W(1.6, -0.4, 0.3), pitch=25, extra={"spine": (10, 0, 0)})
    # relief ...
    h.face(tpull + 50, "happy")
    h.pose(tpull + 50, {"chest": (-8, 0, 0), "head": (-6, 0, 0)})
    h.pose(tpull + 58, {"chest": (6, 0, 0), "head": (8, 0, 0)})
    A.event(tpull + 52, "sigh")
    # ... then the pot, catapulted up by the crash, comes down on her head
    pot = ws["pot"]
    tp_land = tpull + 66
    head_m = A.world_matrix_at(h.rig, tp_land, "head")
    headtop = head_m.translation + V((0, 0, 0.31))
    pot.keyframe_insert("location", frame=tpull + 27)
    pot.keyframe_insert("rotation_euler", frame=tpull + 27)
    A.arc(pot, tpull + 28, tp_land, V(pot.location) + V((-0.4, 0, 0)), headtop + V((0, 0, 0.02)), height=2.0,
          spin=(0, 3 * 6.28 + math.pi, 0), steps=10)
    pot.location = headtop
    pot.rotation_euler = (0, math.radians(180), 0)
    pot.keyframe_insert("location", frame=tp_land)
    pot.keyframe_insert("rotation_euler", frame=tp_land)
    con_pot = A.attach_to(pot, h.rig, tp_land, bone="head")
    A.event(tp_land, "pot_bong")
    h.face(tp_land, "closed")
    h.bone_scale(tp_land, "head", (1.1, 1.1, 0.85))
    h.bone_scale(tp_land + 4, "head", (1, 1, 1))
    tp_land -= 20  # (later beats are timed from here)
    # Hedda gets up, pot on head
    h.bone_loc(tp_land + 26, "root", (0, 0, -0.74))
    h.bone_loc(tp_land + 34, "root", (0, 0, 0))
    h.pose(tp_land + 34, "stand")
    h.pose(tp_land + 34, {"head": (6, 0, -8), "spine": (4, 0, 6)})
    h.face(tp_land + 34, "angry")
    h.blink(tp_land + 46, "angry")
    f.pose(tp_land + 24, {"arm_L": (140, 0, 30), "arm_R": (140, 0, 30), "fore_L": (80, 0, 0), "fore_R": (80, 0, 0),
                         "lid": (-10, 0, 0), "head": (20, 0, 0)})
    A.event(tp_land + 32, "pop_up")
    t6b_end = tp_land + 64
    B.shot(ctx, 2, "S2_c6b_shelf", tb, [(tb, W(-0.4, -1.9, 1.3), W(1.5, -0.6, 0.8)),
                                        (tpull + 12, W(-0.3, -1.95, 1.3), W(1.7, -0.6, 0.85))], lens=30)
    B.shot(ctx, 2, "S2_c6b2_leap", tpull + 12, [(tpull + 12, W(-1.3, -1.5, 1.7), W(1.5, 0.1, 0.55)),
                                                (t6b_end, W(-1.2, -1.4, 1.65), W(1.3, 0.4, 0.6))], lens=24)
    # ------------------------------------------------------------------ 2.6c generator dies; the double knock
    tc = t6b_end + 2
    A.event(tc, "gen_sputter")
    gen = ws["gen"]
    A.shake(gen, F, tc + 10, amp=0.004, freq=6)
    hang_s = C.emit_socket(ws["hang_bulb_m"])
    for i, (dt, v) in enumerate(((0, 15), (4, 3), (7, 15), (12, 1), (15, 10), (22, 0))):
        A.key_socket(hang_s, tc + dt, v, "CONSTANT")
        A.key(ws["hang_light"].data, "energy", tc + dt, v * 6.0, "CONSTANT")
    A.key_socket(C.emit_socket(ws["gen_lamp_m"]), tc + 20, 5.0, "CONSTANT")
    A.key_socket(C.emit_socket(ws["gen_lamp_m"]), tc + 22, 0.0, "CONSTANT")
    A.key(ws["fire_light"].data, "energy", tc + 20, 40.0)
    A.key(ws["fire_light"].data, "energy", tc + 26, 12.0)
    A.key(fill.data, "energy", tc + 21, 140.0, "CONSTANT")
    A.key(fill.data, "energy", tc + 22, 4.0, "CONSTANT")
    A.key(ctx.funke_light.data, "energy", tc + 21, 3.0, "CONSTANT")
    A.key(ctx.funke_light.data, "energy", tc + 22, 12.0, "CONSTANT")
    A.event(tc + 22, "gen_die")
    h.face(tc + 24, "worried")
    A.look(h, tc + 24, W(0.3, 0.6, 2.2), pitch=-20)
    # in the dark only Funke's eye glows; he goes to the generator
    tg0 = tc + 40
    f.pose(tg0 - 10, "stand")
    f.pose(tg0 - 10, {"head": (-20, 0, 0)})
    f.hold_place(tg0)
    A.arc(f.rig, tg0, tg0 + 16, FP, W(1.8, 0.6), height=0.9)
    f.place(tg0, FP, 0)
    f.place(tg0 + 16, W(1.8, 0.6), 20)
    A.event(tg0 + 16, "land_spring")
    fg = f.walk(tg0 + 18, [W(1.8, 0.6), W(2.0, 1.05)], speed=0.6, stride=0.12, end_pose="stand")
    f.place(fg + 2, W(2.0, 1.05), math.degrees(A.yaw_towards(W(2.35, 1.6) - W(2.0, 1.05))))
    f.pose(fg + 6, {"head": (-25, 0, 0)})
    tk = fg + 14
    f.pose(tk - 4, {"arm_R": (95, 0, -5), "fore_R": (35, 0, 0)})
    for kk in range(2):
        f.pose(tk + kk * 6, {"arm_R": (95, 0, -5), "fore_R": (35, 0, 0)})
        f.pose(tk + kk * 6 + 3, {"arm_R": (80, 0, -5), "fore_R": (20, 0, 0)}, interp="LINEAR")
        A.event(tk + kk * 6 + 3, "knock_small")
    f.pose(tk + 16, "stand")
    tr_on = tk + 20
    A.event(tr_on, "gen_roar")
    A.shake(gen, tr_on, END, amp=0.006, freq=6)
    for dt, v in ((0, 2), (3, 15), (5, 6), (8, 15)):
        A.key_socket(hang_s, tr_on + dt, v, "CONSTANT")
        A.key(ws["hang_light"].data, "energy", tr_on + dt, v * 6.0, "CONSTANT")
    A.key_socket(C.emit_socket(ws["gen_lamp_m"]), tr_on, 5.0, "CONSTANT")
    A.key(fill.data, "energy", tr_on + 3, 140.0, "CONSTANT")
    A.key(ctx.funke_light.data, "energy", tr_on + 3, 3.0, "CONSTANT")
    f.pose(tr_on + 6, "happy")
    f.glow(tr_on + 6, 8.0, "bulb")
    f.pose(tr_on + 6, {"needle": (0, -70, 0)})
    # Hedda: pot off, laughs, taps Funke twice on the head
    h.face(tr_on + 4, "surprised")
    h.pose(tr_on + 14, {"upper_arm_R": (150, 0, 10), "forearm_R": (60, 0, 0), "head": (0, 0, 0)})
    A.detach(pot, con_pot, tr_on + 20)
    pot.location = h.pos_at(tr_on + 20) + V((-0.4, 0.35, 0.06))
    pot.rotation_euler = (0, 0, 0)
    pot.keyframe_insert("location", frame=tr_on + 30)
    pot.keyframe_insert("rotation_euler", frame=tr_on + 30)
    A.event(tr_on + 30, "pot_bong_small")
    h.face(tr_on + 22, "happy")
    for kk in range(3):
        h.pose(tr_on + 24 + kk * 6, {"chest": (-6, 0, 0), "head": (-10, 0, 0), "upper_arm_L": (10, 0, 15),
                                     "upper_arm_R": (10, 0, 15)})
        h.pose(tr_on + 27 + kk * 6, {"chest": (4, 0, 0), "head": (-4, 0, 0)})
    A.event(tr_on + 24, "laugh")
    hk = W(1.55, 0.55)
    h.hold_place(tr_on + 44)
    hw3 = h.walk(tr_on + 44, [HD, hk], speed=0.9, stride=0.45, end_pose=None)
    h.place(hw3 + 2, hk, math.degrees(A.yaw_towards(W(2.0, 1.05) - hk)))
    f.place(hw3 + 2, W(2.0, 1.05), math.degrees(A.yaw_towards(hk - W(2.0, 1.05))))
    h.pose(hw3 + 6, "bend_down")
    h.pose(hw3 + 6, {"upper_arm_R": (60, 0, 0), "forearm_R": (40, 0, 0)})
    for kk in range(2):
        h.pose(hw3 + 10 + kk * 6, {"upper_arm_R": (66, 0, 0), "forearm_R": (40, 0, 0), "hand_R": (-20, 0, 0)})
        h.pose(hw3 + 13 + kk * 6, {"upper_arm_R": (58, 0, 0), "forearm_R": (35, 0, 0), "hand_R": (10, 0, 0)},
               interp="LINEAR")
        A.event(hw3 + 13 + kk * 6, "knock_soft")
        f.bone_scale(hw3 + 13 + kk * 6, "head", (1.08, 1.08, 0.85))
        f.bone_scale(hw3 + 16 + kk * 6, "head", (1, 1, 1))
    f.pose(hw3 + 26, {"head": (-28, 0, 0), "antenna": (-25, 0, 0)})
    f.glow(hw3 + 26, 14.0, "bulb")
    f.pose(hw3 + 26, {"needle": (0, -90, 0)})
    A.event(hw3 + 26, "ping_happy")
    h.pose(hw3 + 30, "stand")
    h.face(hw3 + 30, "happy")
    t6c_end = hw3 + 50
    B.shot(ctx, 2, "S2_c6c_dark", tc, [(tc, W(-1.1, -1.7, 1.5), W(1.4, 0.4, 0.9)),
                                       (tr_on + 40, W(-0.9, -1.6, 1.45), W(1.6, 0.5, 0.8))], lens=28)
    B.shot(ctx, 2, "S2_c6c_knock", tr_on + 40, [(tr_on + 40, W(2.65, -0.6, 1.7), W(1.75, 0.8, 0.65), 22),
                                               (t6c_end, W(2.6, -0.55, 1.65), W(1.8, 0.85, 0.65), 22)], lens=22)
    # ------------------------------------------------------------------ 2.7 later: both asleep
    ts = t6c_end + 2
    ctx.ground_skip.append(("Hedda", ts, ts + C.sec(6)))
    END = ts + C.sec(5.5)
    B.set_end(ctx, 2, END)
    chair = ws["chair"]
    cfwd = V((math.sin(chair.rotation_euler.z), -math.cos(chair.rotation_euler.z), 0))
    cpos = V(chair.location) + V((0.05, 0.06, 0)) + cfwd * 0.14
    h.cut(ts, cpos, 35)
    h.pose(ts, "stand")
    h.pose(ts, "sit")
    h.pose(ts, {"head": (25, 0, -15), "spine": (-6, 0, 0), "chest": (-4, 0, 0), "upper_arm_L": (25, 0, 25),
                "forearm_L": (60, 0, -20), "upper_arm_R": (25, 0, 25), "forearm_R": (60, 0, -20)})
    h.bone_loc(ts, "root", (0, 0.05, -0.33))
    h.face(ts, "closed")
    crate = ws["crate"]
    f.cut(ts, V(crate.location) + V((0, 0, 0.12)), 20)
    f.pose(ts, "stand")
    f.pose(ts, "curl")
    f.glow(ts, 0.6, "iris")
    f.glow(ts, 0.6, "bulb")
    A.key(ctx.funke_light.data, "energy", ts, 0.6)
    A.key(ws["hang_light"].data, "energy", ts, 10.0, "CONSTANT")
    A.key_socket(hang_s, ts, 2.0, "CONSTANT")
    A.key(ws["fire_light"].data, "energy", ts, 35.0, "CONSTANT")
    A.key(fill.data, "energy", ts, 35.0, "CONSTANT")
    fr = ts
    k = 0
    while fr < END:
        h.pose(fr, {"chest": (-4 + (3 if k % 2 else 0), 0, 0)})
        f.bone_scale(fr, "body", (1, 1, 1.0 + (0.04 if k % 2 else 0)))
        if k % 2:
            A.event(fr, "snore")
        fr += 30
        k += 1
    B.shot(ctx, 2, "S2_c7_sleep", ts, [(ts, W(0.6, -0.1, 1.4), W(-1.2, -1.5, 0.45)),
                                       (END, W(0.3, -0.3, 1.25), W(-1.2, -1.5, 0.45))], lens=26)
    ctx.pot = pot
    return END
