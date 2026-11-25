"""The Erfasser's eyes: a scanner POV with a HUD.

pov_shot() inserts a point-of-view shot into a sequence: the camera sits in the Erfasser's head,
the compositor turns the picture into a red monochrome scan (keyed per shot), and a HUD hangs in
front of the lens – corner brackets, scanlines, a reticle that locks on, data lines that type in,
and a verdict.
"""
import math
import bpy
from mathutils import Vector
import core as C
import anim as A

V = Vector
D = 0.1  # HUD distance in front of the lens


def _mat(name, col, s):
    return C.emission(name, col, s)


def pov_shot(ctx, idx, name, f0, f1, eye_fn, target_fn, lens=40, lines=(), verdict=None, verdict_col=(1, 0.08, 0.04),
             lock=None, step=3, jitter=0.004, hide=()):
    """eye_fn(f) / target_fn(f): world points. lines: [(frame, text, (r,g,b))]. verdict: (frame, text).
    lock: frame at which the reticle snaps onto the target."""
    s = ctx.seq[idx]
    sc = s["scene"]
    # remember which camera was cutting here, and take over the markers inside the POV
    mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
    resume = None
    for m in mk:
        if m.frame <= f1 and m.camera:
            resume = m.camera
    for m in list(sc.timeline_markers):
        if f0 <= m.frame <= f1:
            sc.timeline_markers.remove(m)
    cam = A.camera(name, s["cams"], lens=lens)
    rnd = C.R.__class__(f0)
    f = f0
    while f <= f1 + step:
        tgt = target_fn(f) + V((rnd.uniform(-1, 1) * jitter * 20, 0, rnd.uniform(-1, 1) * jitter * 20))
        eye = eye_fn(f)
        eye = eye + (tgt - eye).normalized() * 0.32  # in front of the face plate, never inside the head
        A.cam_key(cam, f, eye, tgt, lens)
        f += step
    m = sc.timeline_markers.new(name, frame=f0)
    m.camera = cam
    if resume and f1 + 1 <= sc.frame_end and not any(x.frame == f1 + 1 for x in sc.timeline_markers):
        m2 = sc.timeline_markers.new(name + "_back", frame=f1 + 1)
        m2.camera = resume
    # ---- compositor: red scan look between f0 and f1
    n = sc.node_tree.nodes.get("POVMix")
    if n:
        A.key_socket(n.inputs[0], f0 - 1, 0.0, "CONSTANT")
        A.key_socket(n.inputs[0], f0, 1.0, "CONSTANT")
        A.key_socket(n.inputs[0], f1 + 1, 0.0, "CONSTANT")
    # ---- HUD
    fw = cam.data.sensor_width / lens * D
    fh = fw * 9 / 16
    coll = s["cams"]
    red = _mat("hud_red", (1.0, 0.12, 0.06), 6.0)
    white = _mat("hud_white", (1.0, 0.85, 0.8), 4.0)
    dark = C.mat("hud_scan", (0.0, 0.0, 0.0), alpha=0.22)
    try:
        dark.surface_render_method = "BLENDED"
    except Exception:
        pass
    parts = []

    def P(u, v, z=0.0):  # u,v in -0.5..0.5 of the frame
        return (u * fw, v * fh, -D + z)

    def box(nm, u, v, w, h, m, z=0.0):
        o = C.box(f"{name}_{nm}", (w * fw, h * fh, 0.00001), loc=P(u, v, z), m=m, bevel=0, coll=coll, parent=cam)
        parts.append(o)
        return o

    def txt(nm, body, u, v, size, m, align="LEFT"):
        o = C.text(f"{name}_{nm}", body, size=size * fh, loc=P(u, v, 0.0001), rot=(0, 0, 0), m=m, parent=cam,
                   coll=coll, align=align)
        parts.append(o)
        return o
    # corner brackets
    for i, (u, v, su, sv) in enumerate(((-0.44, 0.4, 1, -1), (0.44, 0.4, -1, -1), (-0.44, -0.4, 1, 1), (0.44, -0.4, -1, 1))):
        box(f"br{i}a", u + su * 0.03, v, 0.06, 0.006, red)
        box(f"br{i}b", u, v + sv * 0.05, 0.0035, 0.1, red)
    # scanlines
    for i in range(36):
        box(f"sl{i}", 0, -0.5 + (i + 0.5) / 36, 1.02, 0.009, dark, z=0.00005)
    txt("hdr", "CITY RECLAMATION  /  SCAN MODE", -0.43, 0.43, 0.035, red)
    rec = txt("rec", "REC", 0.43, 0.43, 0.035, red, align="RIGHT")
    fr = f0
    A.hide(rec, 0, True)
    while fr < f1:  # blinking REC
        A.hide(rec, fr, False)
        A.hide(rec, fr + 12, True)
        fr += 24
    A.hide(rec, f1 + 1, True)
    # reticle
    ret = C.empty(f"{name}_ret", loc=P(0, 0), parent=cam, coll=coll)
    parts.append(ret)
    rt = C.torus(f"{name}_retring", 0.08 * fh, 0.0025 * fh, loc=(0, 0, 0), rot=(0, 0, 0), m=red, parent=ret, coll=coll,
                 seg=40, segr=4)
    parts.append(rt)
    for k in range(4):
        a = k * math.pi / 2
        t = C.box(f"{name}_tick{k}", (0.04 * fh, 0.004 * fh, 0.00001),
                  loc=(math.cos(a) * 0.11 * fh, math.sin(a) * 0.11 * fh, 0), rot=(0, 0, math.degrees(a)), m=red,
                  bevel=0, coll=coll, parent=ret)
        parts.append(t)
    lock = lock or (f0 + (f1 - f0) // 3)
    ret.scale = (2.2, 2.2, 1)
    ret.keyframe_insert("scale", frame=f0)
    ret.rotation_euler = (0, 0, 0)
    ret.keyframe_insert("rotation_euler", frame=f0)
    ret.scale = (1, 1, 1)
    ret.keyframe_insert("scale", frame=lock)
    ret.rotation_euler = (0, 0, math.radians(90))
    ret.keyframe_insert("rotation_euler", frame=lock)
    ret.scale = (0.85, 0.85, 1)
    ret.keyframe_insert("scale", frame=lock + 3)
    ret.scale = (1, 1, 1)
    ret.keyframe_insert("scale", frame=lock + 6)
    A.event(lock, "scan_lock")
    # data lines type in, bottom left
    for i, (lf, body, col) in enumerate(lines):
        m = white if col is None else _mat(f"hud_c{i}_{name}", col, 5.0)
        o = txt(f"ln{i}", body, -0.43, -0.22 - i * 0.055, 0.04, m)
        A.hide(o, 0, True)
        A.hide(o, lf, False)
        A.hide(o, f1 + 1, True)
        A.event(lf, "hud_tick")
    if verdict:
        vf, vt = verdict
        vb = box("vbox", 0, -0.33, 0.012 * len(vt) * 2.4 + 0.08, 0.1, _mat("hud_vbg", (0.25, 0.0, 0.0), 2.0), z=0.00002)
        vo = txt("verdict", vt, 0, -0.335, 0.075, _mat("hud_verdict", verdict_col, 8.0), align="CENTER")
        for o in (vb, vo):
            A.hide(o, 0, True)
            fr = vf
            k = 0
            while fr < f1 + 1:  # blink
                A.hide(o, fr, k % 2 == 1)
                fr += 6
                k += 1
            A.hide(o, f1 + 1, True)
        A.event(vf, "verdict_buzz")
    A.event(f0, "pov_in", dur=f1 - f0)
    for o in hide:  # its own equipment would only block the lens
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f0 - 1)
        A.set_interp(o, "hide_render", f0 - 1, "CONSTANT")
        A.hide(o, f0, True)
        A.hide(o, f1 + 1, False)
    # HUD only exists inside this shot
    for o in parts:
        if not o.name.endswith(("_rec", "_verdict", "_vbox")) and "_ln" not in o.name:
            A.hide(o, 0, True)
            A.hide(o, f0, False)
            A.hide(o, f1 + 1, True)
    return cam


def bone_pos(actor, bone, up=0.0):
    def fn(f):
        return A.world_matrix_at(actor.rig, f, bone).translation + V((0, 0, up))
    return fn


def erf_eye(e, up=0.12):
    """Eye point of the Erfasser at frame f (head bone, slightly up; pov_shot pushes it forward)."""
    return bone_pos(e, "head", up)
