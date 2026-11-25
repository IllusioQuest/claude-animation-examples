"""Procedural characters. Every builder returns an anim.Actor subclass instance."""
import bpy
import math
from mathutils import Vector
import core as C
import rig as RG
import anim as A

M = C.mat


def _mirror_x(p):
    return (-p[0], p[1], p[2])


# =========================================================================== HUMANS
HUMAN_POSES = {
    "stand": {"hips": (0, 0, 0), "spine": (2, 0, 0), "chest": (2, 0, 0), "neck": (0, 0, 0), "head": (-2, 0, 0),
              "upper_arm_L": (4, 0, 6), "upper_arm_R": (4, 0, 6), "forearm_L": (12, 0, 0), "forearm_R": (12, 0, 0),
              "hand_L": (0, 0, 0), "hand_R": (0, 0, 0), "thigh_L": (0, 0, 0), "thigh_R": (0, 0, 0),
              "shin_L": (0, 0, 0), "shin_R": (0, 0, 0), "foot_L": (0, 0, 0), "foot_R": (0, 0, 0)},
    "hands_hips": {"upper_arm_L": (-10, 80, 45), "upper_arm_R": (-10, 80, 45), "forearm_L": (100, 0, 0),
                   "forearm_R": (100, 0, 0), "chest": (-4, 0, 0), "head": (-6, 0, 0)},
    "reach": {"upper_arm_R": (70, 0, 5), "forearm_R": (15, 0, 0), "spine": (12, 0, 0), "chest": (8, 0, 0)},
    "bend_down": {"hips": (25, 0, 0), "spine": (25, 0, 0), "chest": (15, 0, 0), "head": (-25, 0, 0),
                  "upper_arm_L": (45, 0, 8), "upper_arm_R": (45, 0, 8), "forearm_L": (20, 0, 0),
                  "forearm_R": (20, 0, 0), "thigh_L": (-20, 0, 0), "thigh_R": (-20, 0, 0),
                  "shin_L": (-35, 0, 0), "shin_R": (-35, 0, 0), "foot_L": (15, 0, 0), "foot_R": (15, 0, 0)},
    "crouch": {"hips": (10, 0, 0), "spine": (25, 0, 0), "chest": (15, 0, 0), "head": (-30, 0, 0),
               "thigh_L": (70, 0, 4), "thigh_R": (70, 0, 4), "shin_L": (-120, 0, 0), "shin_R": (-120, 0, 0),
               "foot_L": (50, 0, 0), "foot_R": (50, 0, 0), "upper_arm_L": (40, 0, 10), "upper_arm_R": (40, 0, 10),
               "forearm_L": (60, 0, 0), "forearm_R": (60, 0, 0)},
    "work": {"spine": (14, 0, 0), "chest": (10, 0, 0), "head": (10, 0, 0),
             "upper_arm_L": (40, 0, 14), "upper_arm_R": (40, 0, 14), "forearm_L": (60, 0, -20),
             "forearm_R": (60, 0, -20), "hand_L": (0, 0, 0), "hand_R": (0, 0, 0)},
    "sit": {"hips": (-5, 0, 0), "spine": (8, 0, 0), "chest": (6, 0, 0), "thigh_L": (88, 0, 6),
            "thigh_R": (88, 0, 6), "shin_L": (-88, 0, 0), "shin_R": (-88, 0, 0), "foot_L": (0, 0, 0),
            "foot_R": (0, 0, 0), "upper_arm_L": (25, 0, 8), "upper_arm_R": (25, 0, 8),
            "forearm_L": (50, 0, -10), "forearm_R": (50, 0, -10)},
    "sigh": {"spine": (14, 0, 0), "chest": (12, 0, 0), "head": (16, 0, 0), "upper_arm_L": (2, 0, 3),
             "upper_arm_R": (2, 0, 3), "forearm_L": (5, 0, 0), "forearm_R": (5, 0, 0)},
    "surprise": {"spine": (-8, 0, 0), "chest": (-8, 0, 0), "head": (-10, 0, 0), "upper_arm_L": (20, 0, 35),
                 "upper_arm_R": (20, 0, 35), "forearm_L": (70, 0, 0), "forearm_R": (70, 0, 0)},
    "arms_up": {"upper_arm_L": (160, 0, 20), "upper_arm_R": (160, 0, 20), "forearm_L": (10, 0, 0),
                "forearm_R": (10, 0, 0), "chest": (-6, 0, 0), "head": (-12, 0, 0)},
    "shield": {"upper_arm_L": (60, 0, 50), "upper_arm_R": (60, 0, 50), "forearm_L": (10, 0, 0),
               "forearm_R": (10, 0, 0), "chest": (-4, 0, 0), "head": (-4, 0, 0)},
    "carry": {"upper_arm_L": (35, 0, 6), "upper_arm_R": (35, 0, 6), "forearm_L": (75, 0, -25),
              "forearm_R": (75, 0, -25), "spine": (-4, 0, 0)},
    "tap": {"upper_arm_R": (55, 0, 0), "forearm_R": (55, 0, 0), "hand_R": (-25, 0, 0), "spine": (8, 0, 0),
            "head": (12, 0, 0)},
    "tap_hit": {"upper_arm_R": (48, 0, 0), "forearm_R": (40, 0, 0), "hand_R": (10, 0, 0), "spine": (9, 0, 0),
                "head": (14, 0, 0)},
}

FACE = {
    "neutral": {"eye": (1, 1, 1), "brow": (0, 0, 0), "brow_z": 0.0},
    "happy": {"eye": (1, 1, 0.35), "brow": (0, 12, 0), "brow_z": 0.01},
    "sad": {"eye": (1, 1, 0.75), "brow": (0, -18, 0), "brow_z": 0.0},
    "angry": {"eye": (1, 1, 0.7), "brow": (0, 22, 0), "brow_z": -0.012},
    "surprised": {"eye": (1.15, 1, 1.25), "brow": (0, -6, 0), "brow_z": 0.02},
    "closed": {"eye": (1, 1, 0.08), "brow": (0, 0, 0), "brow_z": -0.004},
    "worried": {"eye": (1.05, 1, 1.05), "brow": (0, -24, 0), "brow_z": 0.012},
}


class Human(A.Actor):
    def __init__(self, rig, h=1.0):
        super().__init__(rig, dict(HUMAN_POSES))
        self.h = h

    def face(self, f, name, interp=None):
        d = FACE[name]
        for s in ("L", "R"):
            self.bone_scale(f, "eye_" + s, d["eye"], interp)
            self.pose(f, {"brow_" + s: d["brow"]}, interp)
            self.bone_loc(f, "brow_" + s, (0, 0, d["brow_z"] / self.h), interp)

    def blink(self, f, cur="neutral"):
        d = FACE[cur]["eye"]
        for s in ("L", "R"):
            self.bone_scale(f - 2, "eye_" + s, d)
            self.bone_scale(f, "eye_" + s, (d[0], d[1], 0.08))
            self.bone_scale(f + 3, "eye_" + s, d)

    def dance_cycle(self, f, phase):
        tw = 2 * math.pi * phase
        s1 = math.sin(tw)
        c2 = math.cos(2 * tw)
        up = 1 if s1 > 0 else -1
        pose = {
            "hips": (0, 0, 12 * s1), "spine": (-4, 10 * s1, 6 * s1), "chest": (-4, -14 * s1, 0),
            "head": (-6, 12 * s1, -10 * s1),
            "upper_arm_L": (90 + 50 * s1, 0, 50 - 20 * s1), "upper_arm_R": (90 - 50 * s1, 0, 50 + 20 * s1),
            "forearm_L": (50 + 20 * s1, 0, 0), "forearm_R": (50 - 20 * s1, 0, 0),
            "thigh_L": (14 * max(0, s1) + 6, 0, 4), "thigh_R": (14 * max(0, -s1) + 6, 0, 4),
            "shin_L": (-30 * max(0, s1) - 10 * (1 - c2) / 2, 0, 0), "shin_R": (-30 * max(0, -s1) - 10 * (1 - c2) / 2, 0, 0),
            "foot_L": (8 * max(0, s1), 0, 0), "foot_R": (8 * max(0, -s1), 0, 0),
        }
        self.pose(f, pose)
        self.bone_loc(f, "root", (0, 0, (0.03 * (1 + c2) / 2 - 0.03) / self.h))

    STYLE = {"walk": (24, 40, 0.7, 4, 0.02, 0), "run": (45, 85, 1.0, 14, 0.05, 1),
             "sneak": (30, 70, 0.3, 18, 0.0, 2), "shuffle": (14, 25, 0.4, 8, 0.01, 0),
             "dance": (20, 50, 1.2, -4, 0.04, 3)}

    def leg_len(self):
        b = self.rig.data.bones
        return (b["thigh_L"].length + b["shin_L"].length) * self.rig.scale.z

    def fit_stride(self, stride, style):
        """Step length (half a cycle) = foot travel during stance = 2*L*sin(A). Keep steps at
        least ~80 % of the style's natural length and set the swing amplitude to match."""
        self.extra["amp"] = None
        if style not in self.STYLE or style == "dance":
            return stride
        A_ = self.STYLE[style][0]
        L = self.leg_len() * (0.85 if style == "sneak" else 1.0)
        nat = 2 * L * math.sin(math.radians(A_))
        s = max(stride, 0.8 * nat)
        self.extra["amp"] = math.degrees(math.asin(min(0.95, s / (2 * L))))
        return s

    def walk_cycle(self, f, phase, style):
        if style == "dance":
            return self.dance_cycle(f, phase)
        A_, B, armk, lean, bob, kind = self.STYLE[style]
        if self.extra.get("amp"):
            k = self.extra["amp"] / A_
            A_, B = self.extra["amp"], B * min(1.3, max(0.7, k))
        tw = 2 * math.pi * phase
        pose = {}
        for side, ph in (("L", 0.0), ("R", math.pi)):
            c = math.cos(tw + ph)
            s_ = math.sin(tw + ph)
            pose["thigh_" + side] = (A_ * c + (25 if kind == 2 else 0), 0, 2)
            pose["shin_" + side] = (-B * max(0.0, -s_) - (30 if kind == 2 else 4), 0, 0)
            pose["foot_" + side] = (10 * max(0.0, -s_) + (20 if kind == 2 else 0), 0, 0)
            if kind == 2:
                pose["upper_arm_" + side] = (55, 0, 12)
                pose["forearm_" + side] = (70, 0, -15)
                pose["hand_" + side] = (-40, 0, 0)
            elif kind == 3:
                pose["upper_arm_" + side] = (60 + 40 * s_, 0, 40)
                pose["forearm_" + side] = (60, 0, 0)
            else:
                pose["upper_arm_" + side] = (-A_ * armk * c, 0, 6)
                pose["forearm_" + side] = (15 + (35 if kind == 1 else 0) + 10 * max(0, c), 0, 0)
        pose["spine"] = (lean, 4 * math.cos(tw), 0)
        pose["chest"] = (2 + (6 if kind == 1 else 0), -6 * math.cos(tw) * armk, 0)
        pose["head"] = (-lean * 0.8, 3 * math.cos(tw), 0)
        pose["hips"] = (0, 0, 3 * math.cos(tw) if kind != 3 else 8 * math.cos(tw))
        self.pose(f, pose)
        z = -bob * math.cos(2 * tw) - (0.12 if kind == 2 else 0)
        self.bone_loc(f, "root", (0, 0, z / self.h))

    def tap_twice(self, f, side="R"):
        """Heddas Doppelklopfen. Returns frame after the gesture."""
        self.pose(f, "tap")
        self.pose(f + 4, "tap_hit", interp="LINEAR")
        A.event(f + 4, "knock")
        self.pose(f + 7, "tap")
        self.pose(f + 10, "tap_hit", interp="LINEAR")
        A.event(f + 10, "knock")
        self.pose(f + 15, "tap")
        return f + 15


def build_human(name, coll, h=1.0, girth=1.0, palette=None, style="hedda", seed=0):
    """Generic stylised human. style: 'hedda', 'man', 'woman', 'kid', 'oldman'."""
    C.set_coll(coll)
    rnd = C.R.__class__(seed)
    pal = {"skin": (0.78, 0.48, 0.36), "coat": (0.33, 0.27, 0.15), "coat2": (0.25, 0.3, 0.4),
           "trousers": (0.18, 0.2, 0.24), "boots": (0.16, 0.1, 0.06), "scarf": (0.55, 0.16, 0.1),
           "hair": (0.72, 0.72, 0.7), "glove": (0.3, 0.2, 0.12), "hat": (0.3, 0.25, 0.2)}
    if style == "kid":
        pal["hair"] = (0.3, 0.18, 0.08)
    if palette:
        pal.update(palette)
    S = lambda v: tuple(x * h for x in v)
    g = girth
    bones = [
        ("root", (0, 0, 0), (0, 0.2 * h, 0), None, 0),
        ("hips", S((0, 0, 0.86)), S((0, 0, 1.0)), "root", 0),
        ("spine", S((0, 0, 1.0)), S((0, 0, 1.18)), "hips", 0),
        ("chest", S((0, 0, 1.18)), S((0, 0, 1.36)), "spine", 0),
        ("neck", S((0, 0, 1.36)), S((0, 0, 1.43)), "chest", 0),
        ("head", S((0, 0, 1.43)), S((0, 0, 1.76)), "neck", 0),
    ]
    for s, sx in (("L", 1), ("R", -1)):
        bones += [
            ("eye_" + s, S((0.055 * sx, -0.128, 1.625)), S((0.055 * sx, -0.2, 1.625)), "head", 0),
            ("brow_" + s, S((0.06 * sx, -0.15, 1.685)), S((0.06 * sx, -0.21, 1.685)), "head", 0),
            ("upper_arm_" + s, S((0.2 * g * sx, 0, 1.33)), S((0.215 * g * sx, 0, 1.06)), "chest", 180),
            ("forearm_" + s, S((0.215 * g * sx, 0, 1.06)), S((0.225 * g * sx, 0, 0.8)), "upper_arm_" + s, 180),
            ("hand_" + s, S((0.225 * g * sx, 0, 0.8)), S((0.225 * g * sx, 0, 0.7)), "forearm_" + s, 180),
            ("thigh_" + s, S((0.09 * sx, 0, 0.86)), S((0.09 * sx, 0, 0.48)), "hips", 180),
            ("shin_" + s, S((0.09 * sx, 0, 0.48)), S((0.09 * sx, 0, 0.09)), "thigh_" + s, 180),
            ("foot_" + s, S((0.09 * sx, 0, 0.09)), S((0.09 * sx, -0.14, 0.04)), "shin_" + s, 0),
        ]
    rig = RG.build_armature(name, bones, coll)
    P = RG.Parts(name, coll)
    n = lambda s: f"{name}_{s}"
    import humanparts as HP
    skin = C.skin(n("skin"), pal["skin"])
    coat = C.fabric(n("coat"), pal["coat"], dirt=0.5, weave=70, bump=0.35)
    coat2 = C.fabric(n("coat2"), pal["coat2"], dirt=0.4, weave=70, bump=0.35)
    trou = C.fabric(n("trousers"), pal["trousers"], dirt=0.35, weave=110, bump=0.3)
    trim = C.fabric(n("trim"), tuple(c * 0.75 for c in pal["coat"]), dirt=0.4, weave=70, bump=0.35)
    boots = M(n("boots"), pal["boots"], rough=0.5, dirt=0.4, bump=0.2)
    hair = M(n("hair"), pal["hair"], rough=0.8, dirt=0.15, scale=20, bump=0.4)
    glove = M(n("glove"), pal["glove"], rough=0.6, dirt=0.3)
    white = M("eye_white", (0.92, 0.9, 0.85), rough=0.3, dirt=0.0, bump=0)
    black = M("eye_black", (0.01, 0.01, 0.01), rough=0.2, dirt=0.0, bump=0)
    brass = M("brass", (0.75, 0.55, 0.25), metal=1.0, rough=0.35, rust=0.15, rust_color=(0.15, 0.25, 0.15))
    is_kid = style == "kid"
    hr = (0.16 if not is_kid else 0.19) * h  # head radius
    hc = Vector(S((0, 0, 1.6)))
    # ---- head
    P.add("head", HP.head_mesh(n("head"), hr, hc, style, skin, coll))
    nose_r = (0.055 if style in ("hedda", "oldman", "man") else 0.04) * h
    P.add("head", C.sphere(n("nose"), nose_r, loc=hc + Vector((0, -hr - nose_r * 0.3, -0.03 * h)),
                           scale=(1, 1, 0.92), m=M(n("nose_m"), tuple(min(1, c * 1.06) for c in pal["skin"]),
                                                 rough=0.45, dirt=0.1, bump=0), coll=coll))
    for s, sx in (("L", 1), ("R", -1)):
        ec = Vector(S((0.055 * sx, -0.128, 1.625)))
        er = (0.037 if not is_kid else 0.045) * h
        for o in HP.eye(n, s, ec, er, pal.get("iris", (0.28, 0.16, 0.08)), skin, coll,
                        lid=0.05 if is_kid else (0.3 if style in ("oldman", "hedda") else 0.2)):
            P.add("eye_" + s, o)
        P.add("brow_" + s, HP.brow(n, s, sx, Vector(S((0.06 * sx, -0.152, 1.685))), h, hair, coll))
        P.add("head", C.sphere(n("ear" + s), 0.032 * h, loc=hc + Vector((hr * 0.97 * sx, 0.01, 0)),
                               scale=(0.5, 1, 1.3), m=skin, coll=coll))
    # hair cap
    prof = []
    for i in range(9):
        a = math.radians(0 + i * 90 / 8)
        prof.append(((hr + 0.008 * h) * math.cos(a), (hr + 0.008 * h) * math.sin(a)))
    prof[-1] = (0.001, prof[-1][1])
    cap = C.lathe(n("haircap"), prof, loc=hc + Vector((0, 0.012 * h, 0.01 * h)), rot=(-32, 0, 0), m=hair,
                  coll=coll)
    if style in ("hedda", "woman", "kid", "oldman"):
        P.add("head", cap)
    else:
        bpy.data.objects.remove(cap)
    if style == "hedda":
        P.add("head", C.sphere(n("bun"), 0.072 * h, loc=hc + Vector((0, 0.11 * h, 0.12 * h)), m=hair, coll=coll))
        for i in range(5):
            a = rnd.uniform(-1.2, 1.2)
            P.add("head", C.sphere(n(f"wisp{i}"), 0.02 * h, loc=hc + Vector(
                (math.sin(a) * hr, -math.cos(a) * hr * 0.3 + 0.05 * h, 0.1 * h + rnd.uniform(0, 0.05) * h)),
                                   scale=(1, 0.5, 2), m=hair, coll=coll))
        # goggles on forehead
        strap = C.torus(n("strap"), hr * 1.02, 0.012 * h, loc=hc + Vector((0, 0, 0.075 * h)), rot=(-14, 0, 0),
                        m=M(n("strap_m"), (0.12, 0.08, 0.05), rough=0.7), coll=coll)
        P.add("head", strap)
        for s, sx in (("L", 1), ("R", -1)):
            gp = hc + Vector((0.055 * sx * h, -hr * 0.9, 0.105 * h))
            P.add("head", C.cyl(n("gcup" + s), 0.036 * h, 0.04 * h, loc=gp, rot=(80, 0, 0), m=brass, coll=coll))
            P.add("head", C.torus(n("grim" + s), 0.036 * h, 0.008 * h, loc=gp + Vector((0, -0.02 * h, 0.004 * h)),
                                  rot=(80, 0, 0), m=brass, coll=coll))
            P.add("head", C.cyl(n("glens" + s), 0.03 * h, 0.006 * h, loc=gp + Vector((0, -0.021 * h, 0.004 * h)),
                                rot=(80, 0, 0), m=C.glass("amber_glass", (1.0, 0.6, 0.25), 0.1), coll=coll))
        # scarf over mouth
        sc = C.fabric(n("scarf_m"), pal["scarf"], dirt=0.35, weave=55, bump=0.6, knit=True, sheen=0.6)
        for bone, o in HP.scarf(n, h, hc, sc, coll):
            P.add(bone, o)
    elif style in ("man", "oldman"):
        # moustache + cap
        P.add("head", C.sphere(n("moust"), 0.05 * h, loc=hc + Vector((0, -hr * 0.95, -0.07 * h)),
                               scale=(1.4, 0.45, 0.45), m=hair, coll=coll))
        hatm = M(n("hat_m"), pal["hat"], rough=0.9, dirt=0.4)
        if style == "man":
            P.add("head", C.lathe(n("flatcap"), [(hr * 1.04, 0), (hr * 1.0, 0.06 * h), (hr * 0.6, 0.11 * h),
                                                 (0.001, 0.12 * h)], loc=hc + Vector((0, 0.01 * h, 0.06 * h)),
                                  rot=(-10, 0, 0), m=hatm, coll=coll))
            P.add("head", C.box(n("visor"), S((0.2, 0.1, 0.015)), loc=hc + Vector((0, -hr * 0.95, 0.07 * h)),
                                rot=(15, 0, 0), m=hatm, bevel=0.01, coll=coll))
        else:
            P.add("head", C.lathe(n("beanie"), [(hr * 1.03, 0), (hr * 0.95, 0.09 * h), (hr * 0.5, 0.16 * h),
                                                (0.001, 0.17 * h)], loc=hc + Vector((0, 0.0, 0.04 * h)),
                                  m=hatm, coll=coll))
            P.add("head", C.sphere(n("pompom"), 0.03 * h, loc=hc + Vector((0, 0, 0.22 * h)), m=hatm, coll=coll))
    elif style == "woman":
        P.add("head", C.lathe(n("headscarf"), [(hr * 1.06, -0.05 * h), (hr * 1.07, 0.05 * h),
                                               (hr * 0.75, 0.15 * h), (0.001, 0.18 * h)],
                              loc=hc + Vector((0, 0.03 * h, 0.0)), rot=(-20, 0, 0),
                              m=M(n("hs_m"), pal["scarf"], rough=0.9, dirt=0.3), coll=coll))
    if style != "hedda":
        P.add("head", C.sphere(n("mouth"), 0.03 * h, loc=hc + Vector((0, -hr * 0.92, -0.095 * h)),
                               scale=(1.2, 0.3, 0.5), m=M("mouth_m", (0.25, 0.05, 0.05), dirt=0, bump=0),
                               coll=coll))
    # ---- torso
    tz = S((0, 0, 0))
    torso_prof = [(0.17 * g, 0.98), (0.2 * g, 1.1), (0.215 * g, 1.24), (0.205 * g, 1.33), (0.15, 1.39),
                  (0.07, 1.43)]
    if style == "oldman":
        torso_prof = [(0.2 * g, 0.98), (0.24 * g, 1.1), (0.22 * g, 1.24), (0.2 * g, 1.33), (0.15, 1.39),
                      (0.07, 1.43)]
    tor = C.lathe(n("torso"), [(r * h, z * h) for r, z in torso_prof], m=coat, coll=coll)
    tor.scale = (1, 0.8, 1)
    P.add("spine", tor)
    if style in ("hedda", "oldman", "man"):
        skirt_prof = [(0.33 * g, 0.38), (0.29 * g, 0.55), (0.23 * g, 0.82), (0.195 * g, 1.02)]
        if style != "hedda":
            skirt_prof = [(0.22 * g, 0.72), (0.2 * g, 0.85), (0.19 * g, 1.02)]
        sk = C.lathe(n("skirt"), [(r * h, z * h) for r, z in skirt_prof], m=coat, coll=coll)
        sk.scale = (1, 0.85, 1)
        P.add("hips", sk)
    elif style in ("woman",):
        sk = C.lathe(n("skirt"), [(r * h, z * h) for r, z in [(0.3, 0.42), (0.25, 0.7), (0.19, 1.02)]],
                     m=coat2, coll=coll)
        sk.scale = (1, 0.85, 1)
        P.add("hips", sk)
    else:
        sk = C.lathe(n("skirt"), [(r * h, z * h) for r, z in [(0.17, 0.8), (0.18, 0.9), (0.18, 1.02)]],
                     m=trou, coll=coll)
        P.add("hips", sk)
    P.add("chest", C.torus(n("collar"), 0.1 * h, 0.035 * h, loc=S((0, 0.005, 1.39)), m=coat, coll=coll))
    if style in ("hedda", "oldman", "man", "woman"):
        long_coat = style == "hedda"
        for bone, o in HP.coat_details(n, h, g, coat, trim, coll, long_coat=long_coat,
                                       hem_z=0.385, hem_r=0.325):
            P.add(bone, o)
    belt = M("belt_m", (0.14, 0.09, 0.05), rough=0.6, dirt=0.3)
    bt = C.torus(n("belt"), 0.19 * h * g, 0.022 * h, loc=S((0, 0, 0.99)), m=belt, coll=coll)
    bt.scale = (1, 0.82, 0.7)
    P.add("hips", bt)
    if style == "hedda":
        P.add("hips", C.box(n("pouch"), S((0.08, 0.06, 0.1)), loc=S((0.19, -0.05, 0.92)), rot=(0, 0, 20),
                            m=belt, bevel=0.012, coll=coll))
        P.add("hips", C.cyl(n("wrench_h"), 0.008 * h, 0.2 * h, loc=S((-0.19, -0.04, 0.9)), rot=(0, 10, 0),
                            m=M("steel", (0.6, 0.6, 0.62), metal=1, rough=0.35, rust=0.25), coll=coll))
        # patches
        for i, (pz, px, pc) in enumerate([(0.62, 0.12, (0.3, 0.38, 0.5)), (0.8, -0.1, (0.55, 0.25, 0.18)),
                                          (1.18, 0.1, (0.35, 0.3, 0.2))]):
            rr = 0.27 if pz < 1.0 else 0.205
            bone = "hips" if pz < 1.0 else "spine"
            pm = M(n(f"patch{i}"), pc, rough=0.95, dirt=0.4, bump=0.4, scale=10)
            ang = math.asin(max(-1, min(1, px / rr)))
            P.add(bone, C.box(n(f"patch{i}"), S((0.09, 0.012, 0.08)),
                              loc=(px * h, -math.cos(ang) * rr * h * 0.83, pz * h), rot=(rnd.uniform(-8, 8) - 6, 0,
                                                                                          math.degrees(ang)),
                              m=pm, bevel=0.004, coll=coll))
    for i in range(4):
        P.add("spine" if i < 2 else "hips", C.cyl(n(f"button{i}"), 0.012 * h, 0.01 * h,
                                                  loc=S((0, -0.172 * g + (0.0 if i < 2 else -0.0), 1.25 - i * 0.12)),
                                                  rot=(90, 0, 0), m=M("button_m", (0.1, 0.08, 0.06)), coll=coll))
    # ---- arms
    for s, sx in (("L", 1), ("R", -1)):
        sh = Vector(S((0.2 * g * sx, 0, 1.33)))
        el = Vector(S((0.215 * g * sx, 0, 1.06)))
        wr = Vector(S((0.225 * g * sx, 0, 0.8)))
        hd = Vector(S((0.225 * g * sx, 0, 0.74)))
        P.add("upper_arm_" + s, C.sphere(n("shoulder" + s), 0.064 * h, loc=sh - Vector((0.012 * sx * h, 0, 0.015 * h)), m=coat, coll=coll))
        P.add("upper_arm_" + s, C.limb(n("uarm" + s), sh, el, 0.066 * h, 0.058 * h, m=coat, coll=coll))
        P.add("forearm_" + s, C.sphere(n("elbow" + s), 0.058 * h, loc=el, m=coat, coll=coll))
        P.add("forearm_" + s, C.limb(n("farm" + s), el, wr, 0.058 * h, 0.052 * h, m=coat, coll=coll))
        P.add("forearm_" + s, C.torus(n("cuff" + s), 0.05 * h, 0.014 * h, loc=wr + Vector((0, 0, 0.01 * h)),
                                      m=coat, coll=coll))
        gm = glove if style == "hedda" else skin
        for o in HP.glove(n, s, sx, hd, h, gm, coll, bare=style != "hedda"):
            P.add("hand_" + s, o)
    # ---- legs
    for s, sx in (("L", 1), ("R", -1)):
        hp = Vector(S((0.09 * sx, 0, 0.88)))
        kn = Vector(S((0.09 * sx, 0, 0.48)))
        an = Vector(S((0.09 * sx, 0, 0.12)))
        P.add("thigh_" + s, C.limb(n("thigh" + s), hp, kn, 0.075 * h * g, 0.062 * h, m=trou, coll=coll))
        P.add("shin_" + s, C.sphere(n("knee" + s), 0.062 * h, loc=kn, m=trou, coll=coll))
        P.add("shin_" + s, C.limb(n("shin" + s), kn, an, 0.062 * h, 0.055 * h, m=trou, coll=coll))
        for o in HP.boot(n, s, sx, h, boots, coll):
            P.add("foot_" + s, o)
    P.attach_all(rig)
    act = Human(rig, h)
    act.pose(0, "stand")
    act.face(0, "neutral")
    return act


# =========================================================================== FUNKE
FUNKE_POSES = {
    "stand": {"body": (0, 0, 0), "head": (0, 0, 0), "antenna": (0, 0, 0), "lid": (-95, 0, 0),
              "arm_L": (0, 0, 10), "arm_R": (0, 0, 10), "fore_L": (20, 0, 0), "fore_R": (20, 0, 0),
              "leg_L": (0, 0, 0), "leg_R": (0, 0, 0), "foot_L": (0, 0, 0), "foot_R": (0, 0, 0)},
    "off": {"body": (10, 0, 0), "head": (25, 0, 0), "antenna": (30, 0, 0), "lid": (0, 0, 0),
            "arm_L": (0, 0, 2), "arm_R": (0, 0, 2), "fore_L": (0, 0, 0), "fore_R": (0, 0, 0)},
    "curious": {"head": (-8, 0, -22), "antenna": (-10, 0, 20), "body": (-4, 0, 0)},
    "hands_hips": {"arm_L": (-15, 80, 40), "arm_R": (-15, 80, 40), "fore_L": (110, 0, 0),
                   "fore_R": (110, 0, 0), "head": (-12, 0, 0), "body": (-6, 0, 0)},
    "reach_up": {"arm_L": (160, 0, 10), "arm_R": (160, 0, 10), "fore_L": (10, 0, 0), "fore_R": (10, 0, 0),
                 "head": (-20, 0, 0), "body": (-8, 0, 0)},
    "tap": {"arm_R": (75, 0, -5), "fore_R": (40, 0, 0), "head": (5, 0, 0)},
    "tap_hit": {"arm_R": (60, 0, -5), "fore_R": (25, 0, 0), "head": (8, 0, 0)},
    "happy": {"arm_L": (20, 0, 60), "arm_R": (20, 0, 60), "fore_L": (40, 0, 0), "fore_R": (40, 0, 0),
              "head": (-15, 0, 0), "antenna": (-20, 0, 0), "body": (-8, 0, 0)},
    "sad": {"head": (25, 0, 0), "antenna": (60, 0, 0), "body": (12, 0, 0), "arm_L": (5, 0, 2),
            "arm_R": (5, 0, 2), "fore_L": (0, 0, 0), "fore_R": (0, 0, 0)},
    "curl": {"body": (60, 0, 0), "head": (40, 0, 0), "leg_L": (90, 0, 0), "leg_R": (90, 0, 0),
             "arm_L": (60, 0, 20), "arm_R": (60, 0, 20), "fore_L": (90, 0, 0), "fore_R": (90, 0, 0),
             "lid": (0, 0, 0), "antenna": (70, 0, 0)},
    "scared": {"body": (-10, 0, 0), "head": (-5, 0, 0), "arm_L": (90, 0, 40), "arm_R": (90, 0, 40),
               "fore_L": (90, 0, 0), "fore_R": (90, 0, 0), "antenna": (-30, 0, 0)},
}


class Robot(A.Actor):
    def __init__(self, rig, poses, bulb_mat=None, iris_mat=None):
        super().__init__(rig, dict(poses))
        self.bulb = bulb_mat
        self.iris = iris_mat

    def glow(self, f, v, which="bulb", interp=None):
        m = self.bulb if which == "bulb" else self.iris
        if m is not None:
            A.key_socket(C.emit_socket(m), f, v, interp)

    def blink(self, f, open_deg=-95):
        self.pose(f - 2, {"lid": (open_deg, 0, 0)})
        self.pose(f, {"lid": (-5, 0, 0)})
        self.pose(f + 3, {"lid": (open_deg, 0, 0)})

    def walk_cycle(self, f, phase, style):
        tw = 2 * math.pi * phase
        big = 1.4 if style == "run" else 1.0
        pose = {}
        for side, ph in (("L", 0.0), ("R", math.pi)):
            c = math.cos(tw + ph)
            s_ = math.sin(tw + ph)
            pose["leg_" + side] = (35 * big * c, 0, 0)
            pose["foot_" + side] = (20 * max(0, -s_), 0, 0)
            pose["arm_" + side] = (-30 * big * c, 0, 12)
            pose["fore_" + side] = (30, 0, 0)
        pose["body"] = (4 * big, 0, 6 * math.cos(tw))
        pose["head"] = (-2, 0, -4 * math.cos(tw))
        pose["antenna"] = (12 * math.sin(2 * tw), 0, 8 * math.cos(tw))
        self.pose(f, pose)
        self.bone_loc(f, "root", (0, 0, 0.025 * big * abs(math.sin(tw))))

    def tap_twice(self, f):
        self.pose(f, "tap")
        self.pose(f + 3, "tap_hit", interp="LINEAR")
        A.event(f + 3, "knock_small")
        self.pose(f + 6, "tap")
        self.pose(f + 9, "tap_hit", interp="LINEAR")
        A.event(f + 9, "knock_small")
        self.pose(f + 13, "tap")
        return f + 13


def lens_eye(prefix, coll, center, r, iris_mat, facing=(90, 0, 0)):
    """Brass-ringed lens eye (shared design of Bello and Funke). Returns objects."""
    brass = M("brass_eye", (0.7, 0.5, 0.22), metal=1.0, rough=0.3, rust=0.2, rust_color=(0.12, 0.22, 0.15))
    c = Vector(center)
    obs = []
    obs.append(C.torus(prefix + "_ring", r, r * 0.22, loc=c, rot=facing, m=brass, coll=coll, segr=10))
    obs.append(C.cyl(prefix + "_back", r * 0.98, r * 0.3, loc=c + Vector((0, r * 0.15, 0)), rot=facing,
                     m=M("eye_back", (0.02, 0.02, 0.025), rough=0.4), coll=coll))
    obs.append(C.cyl(prefix + "_iris", r * 0.5, r * 0.06, loc=c + Vector((0, -r * 0.0, 0)), rot=facing,
                     m=iris_mat, coll=coll, verts=24))
    obs.append(C.cyl(prefix + "_pupil", r * 0.2, r * 0.07, loc=c + Vector((0, -r * 0.02, 0)), rot=facing,
                     m=M("eye_black"), coll=coll, verts=16))
    lens = C.sphere(prefix + "_lens", r * 0.95, loc=c + Vector((0, -r * 0.02, 0)), scale=(1, 0.38, 1),
                    m=C.glass("lens_glass", (0.85, 0.92, 1.0), 0.02), coll=coll)
    obs.append(lens)
    return obs


def iris_material(name, color=(1.0, 0.55, 0.12), strength=4.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    em.inputs[1].default_value = strength
    # radial pattern for a 'camera iris' look
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    sc = nt.nodes.new("ShaderNodeMapping"); sc.inputs["Scale"].default_value = (12, 12, 12)
    nt.links.new(tc.outputs["Object"], sc.inputs[0])
    nt.links.new(sc.outputs[0], gr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (color[0] * 0.3, color[1] * 0.3, color[2] * 0.3, 1)
    ramp.color_ramp.elements[1].color = (min(1, color[0] * 1.2), min(1, color[1] * 1.3), min(1, color[2] * 1.5), 1)
    nt.links.new(gr.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, 1)
    return m


def build_funke(coll, name="Funke"):
    C.set_coll(coll)
    bones = [
        ("root", (0, 0, 0), (0, 0.1, 0), None, 0),
        ("body", (0, 0, 0.17), (0, 0, 0.36), "root", 0),
        ("head", (0, 0, 0.36), (0, 0, 0.55), "body", 0),
        ("lid", (0, -0.0, 0.455), (0, -0.1, 0.455), "head", 0),
        ("antenna", (0.03, 0.03, 0.53), (0.03, 0.03, 0.66), "head", 0),
        ("needle", (0, -0.1, 0.28), (0, -0.14, 0.28), "body", 0),
    ]
    for s, sx in (("L", 1), ("R", -1)):
        bones += [
            ("arm_" + s, (0.105 * sx, 0, 0.32), (0.12 * sx, 0, 0.23), "body", 180),
            ("fore_" + s, (0.12 * sx, 0, 0.23), (0.125 * sx, 0, 0.15), "arm_" + s, 180),
            ("leg_" + s, (0.05 * sx, 0, 0.18), (0.05 * sx, 0, 0.06), "root", 180),
            ("foot_" + s, (0.05 * sx, 0, 0.06), (0.05 * sx, -0.07, 0.03), "leg_" + s, 0),
        ]
    rig = RG.build_armature(name, bones, coll)
    P = RG.Parts(name, coll)
    n = lambda s: f"{name}_{s}"
    teal = M(n("paint"), (0.2, 0.45, 0.45), metal=0.6, rough=0.45, rust=0.35, scale=6)
    tin = M(n("tin"), (0.7, 0.7, 0.68), metal=1.0, rough=0.3, rust=0.2, scale=8)
    label = M(n("label"), (0.75, 0.18, 0.1), rough=0.7, dirt=0.5, scale=10)
    rubber = M("rubber_red", (0.55, 0.08, 0.05), rough=0.6, dirt=0.3)
    dark = M("dark_metal", (0.08, 0.08, 0.09), metal=0.8, rough=0.5, rust=0.2)
    iris = iris_material(n("iris"), (1.0, 0.55, 0.12), 4.0)
    bulb = iris_material(n("bulb"), (1.0, 0.75, 0.3), 3.0)
    # body (boiler)
    body = C.lathe(n("body"), [(0.07, 0.165), (0.095, 0.18), (0.102, 0.22), (0.102, 0.32), (0.09, 0.35),
                               (0.06, 0.365), (0.001, 0.37)], m=teal, coll=coll, cap_bottom=True)
    P.add("body", body)
    for i in range(10):
        a = 2 * math.pi * i / 10
        P.add("body", C.sphere(n(f"rivet{i}"), 0.007, loc=(0.103 * math.cos(a), 0.103 * math.sin(a), 0.335),
                               m=tin, seg=8, rings=4, coll=coll))
    # chest gauge
    P.add("body", C.cyl(n("gauge"), 0.034, 0.02, loc=(0, -0.1, 0.27), rot=(90, 0, 0), m=tin, coll=coll))
    P.add("body", C.cyl(n("gauge_face"), 0.029, 0.004, loc=(0, -0.111, 0.27), rot=(90, 0, 0),
                        m=M("gauge_face", (0.9, 0.88, 0.8), rough=0.5, dirt=0.3), coll=coll))
    P.add("needle", C.box(n("needle_m"), (0.004, 0.003, 0.024), loc=(0, -0.114, 0.28), m=label, bevel=0, coll=coll))
    # neck
    P.add("head", C.cyl(n("neck"), 0.03, 0.04, loc=(0, 0, 0.37), m=dark, coll=coll))
    # head (tin can)
    P.add("head", C.cyl(n("can"), 0.085, 0.14, loc=(0, 0, 0.455), m=tin, coll=coll, verts=32))
    for z in (0.388, 0.522):
        P.add("head", C.torus(n(f"canrim{z}"), 0.085, 0.006, loc=(0, 0, z), m=tin, coll=coll))
    lab = C.cyl(n("label"), 0.0865, 0.05, loc=(0, 0, 0.415), m=label, coll=coll, verts=32)
    P.add("head", lab)
    for o in lens_eye(n("eye"), coll, (0, -0.088, 0.462), 0.048, iris):
        P.add("head", o)
    # eyelid: hemisphere shell in front of eye, rotates up to open
    prof = [(0.058 * math.cos(math.radians(a)), 0.058 * math.sin(math.radians(a))) for a in range(-90, 91, 15)]
    lid = C.lathe(n("lid"), [(max(0.001, r), z) for r, z in prof], loc=(0, -0.085, 0.462), rot=(0, 90, 0),
                  m=tin, coll=coll, seg=24)
    # lathe around local Z; rotated so its axis is X: becomes a half shell? we keep full sphere but scale y
    lid.scale = (1, 1, 1)
    bpy.data.objects.remove(lid)
    # build proper half-dome (front half of a sphere) covering the eye
    import bmesh
    bm = bmesh.new()
    rings, segs, rr = 8, 16, 0.06
    vs = []
    for i in range(rings + 1):
        th = math.pi * i / rings  # top->bottom
        row = []
        for j in range(segs + 1):
            ph = math.pi * j / segs  # 0..pi : half around -Y
            x = rr * math.sin(th) * math.cos(ph)
            y = -rr * math.sin(th) * math.sin(ph) * 0.75
            z = rr * math.cos(th)
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for i in range(rings):
        for j in range(segs):
            bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    me = bpy.data.meshes.new(n("lid"))
    bm.to_mesh(me); bm.free()
    lid = C.new_obj(n("lid"), me, loc=(0, -0.083, 0.462), mat_=tin, coll=coll, smooth_=True)
    sol = lid.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.004
    P.add("lid", lid)
    # antenna
    P.add("antenna", C.cyl(n("ant_base"), 0.012, 0.02, loc=(0.03, 0.03, 0.535), m=dark, coll=coll))
    P.add("antenna", C.cyl(n("ant_rod"), 0.004, 0.11, loc=(0.03, 0.03, 0.6), m=tin, coll=coll, verts=8))
    P.add("antenna", C.sphere(n("bulb"), 0.02, loc=(0.03, 0.03, 0.67), m=bulb, coll=coll))
    # arms (accordion tubes) + claws
    for s, sx in (("L", 1), ("R", -1)):
        P.add("arm_" + s, C.sphere(n("sh" + s), 0.022, loc=(0.105 * sx, 0, 0.32), m=dark, coll=coll))
        for k in range(4):
            t = k / 4
            p = Vector((0.105 * sx, 0, 0.32)).lerp(Vector((0.12 * sx, 0, 0.23)), t + 0.12)
            P.add("arm_" + s, C.torus(n(f"ua{s}{k}"), 0.014, 0.006, loc=p, m=dark, coll=coll, seg=12, segr=6))
        P.add("arm_" + s, C.limb(n("uarm" + s), (0.105 * sx, 0, 0.32), (0.12 * sx, 0, 0.23), 0.011, 0.011, m=tin,
                                 coll=coll))
        P.add("fore_" + s, C.limb(n("farm" + s), (0.12 * sx, 0, 0.23), (0.125 * sx, 0, 0.15), 0.011, 0.01, m=tin,
                                  coll=coll))
        for k in range(3):
            p = Vector((0.12 * sx, 0, 0.23)).lerp(Vector((0.125 * sx, 0, 0.15)), 0.2 + k * 0.3)
            P.add("fore_" + s, C.torus(n(f"fa{s}{k}"), 0.013, 0.005, loc=p, m=dark, coll=coll, seg=12, segr=6))
        P.add("fore_" + s, C.sphere(n("wrist" + s), 0.016, loc=(0.125 * sx, 0, 0.148), m=dark, coll=coll))
        for fy in (-1, 1):
            P.add("fore_" + s, C.box(n(f"claw{s}{fy}"), (0.008, 0.01, 0.04), loc=(0.125 * sx, 0.012 * fy, 0.125),
                                     rot=(-14 * fy, 0, 0), m=tin, bevel=0.003, coll=coll))
    # legs (springs) + rubber feet
    for s, sx in (("L", 1), ("R", -1)):
        P.add("leg_" + s, C.limb(n("leg" + s), (0.05 * sx, 0, 0.18), (0.05 * sx, 0, 0.06), 0.008, m=tin,
                                 coll=coll))
        for k in range(5):
            P.add("leg_" + s, C.torus(n(f"spring{s}{k}"), 0.018, 0.004, loc=(0.05 * sx, 0, 0.07 + k * 0.022),
                                      rot=(8, 0, 0), m=M("spring_m", (0.5, 0.48, 0.45), metal=1, rough=0.4,
                                                          rust=0.3), coll=coll, seg=12, segr=6))
        P.add("foot_" + s, C.sphere(n("foot" + s), 0.04, loc=(0.05 * sx, -0.02, 0.03), scale=(0.95, 1.5, 0.75),
                                    m=rubber, coll=coll))
    P.attach_all(rig)
    act = Robot(rig, FUNKE_POSES, bulb, iris)
    act.pose(0, "stand")
    return act


# =========================================================================== ERFASSER
ERF_POSES = {
    "stand": {"body": (0, 0, 0), "neck": (0, 0, 0), "head": (0, 0, 0), "arm_L": (8, 0, 8), "arm_R": (8, 0, 8),
              "fore_L": (30, 0, 0), "fore_R": (45, 0, 0), "hand_L": (0, 0, 0), "hand_R": (-45, 0, 0)},
    "stamp_up": {"arm_L": (110, 0, 5), "fore_L": (40, 0, 0), "hand_L": (-50, 0, 0), "body": (-6, 0, 0),
                 "head": (-8, 0, 0)},
    "stamp_down": {"arm_L": (70, 0, 5), "fore_L": (20, 0, 0), "hand_L": (-90, 0, 0), "body": (12, 0, 0),
                   "head": (10, 0, 0)},
    "net_ready": {"arm_R": (100, 0, 25), "fore_R": (20, 0, 0), "hand_R": (-20, 0, 0), "body": (-4, 0, 0)},
    "net_throw": {"arm_R": (60, 0, 5), "fore_R": (0, 0, 0), "hand_R": (40, 0, 0), "body": (14, 0, 0)},
    "scan": {"head": (8, 0, 0), "body": (6, 0, 0), "neck": (0, 0, 0)},
    "lean_fwd": {"body": (18, 0, 0), "head": (6, 0, 0)},
    "tangled": {"arm_L": (40, 0, 60), "arm_R": (40, 0, 60), "fore_L": (90, 0, 0), "fore_R": (90, 0, 0),
                "body": (-10, 0, 15), "head": (10, 0, -20)},
}


class Erfasser(Robot):
    def roll(self, f0, pts, speed=1.6, lean=8):
        """Roll along polyline; spins wheel. Returns end frame."""
        pts = [Vector(p) for p in pts]
        total = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1))
        dur = max(2, int(round(total / speed * C.FPS)))
        acc = 0.0
        self.place(f0, pts[0], math.degrees(A.yaw_towards(pts[1] - pts[0])))
        self.pose(f0, {"body": (0, 0, 0)})
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            acc += (b - a).length
            f = f0 + int(round(acc / total * dur))
            yaw = math.degrees(A.yaw_towards(b - a))
            if i > 0:
                fs = f0 + int(round((acc - (b - a).length) / total * dur))
                self.place(fs, None, yaw)
            self.place(f, b, yaw, interp="LINEAR" if i < len(pts) - 2 else None, hold=False)
        f1 = f0 + dur
        self.pose(f0 + 6, {"body": (lean, 0, 0)})
        self.pose(f1 - 4, {"body": (lean, 0, 0)})
        self.pose(f1 + 6, {"body": (-lean * 0.6, 0, 0)})
        self.pose(f1 + 14, {"body": (0, 0, 0)})
        # wheel spin: angle = distance / radius
        pb = self.rig.pose.bones["wheel"]
        fc = None
        start = 0.0
        ad = self.rig.animation_data
        if ad and ad.action:
            fc = ad.action.fcurves.find(pb.path_from_id("rotation_euler"), index=1)
            if fc:
                start = fc.evaluate(f0)
        pb.rotation_euler = (0, start, 0)
        pb.keyframe_insert("rotation_euler", frame=f0, index=1)
        pb.rotation_euler = (0, start - total / 0.27, 0)
        pb.keyframe_insert("rotation_euler", frame=f1, index=1)
        A.event(f0, "unicycle", dur=dur)
        return f1

    def stamp(self, f, target_face=True):
        self.pose(f, "stamp_up")
        self.pose(f + 8, "stamp_up")
        self.pose(f + 11, "stamp_down", interp="LINEAR")
        A.event(f + 11, "stamp")
        self.pose(f + 18, "stamp_down")
        self.pose(f + 26, "stand")
        return f + 11

    def scan(self, f0, f1, sweeps=2):
        """Head sweep left/right with red slit brightening."""
        n = sweeps * 2
        for i in range(n + 1):
            fr = f0 + int((f1 - f0) * i / n)
            self.pose(fr, {"head": (8, 0, (28 if i % 2 else -28) if 0 < i < n else 0)})
        self.glow(f0 - 1, 3.0, "iris")
        self.glow(f0 + 3, 9.0, "iris")
        self.glow(f1, 9.0, "iris")
        self.glow(f1 + 4, 3.0, "iris")
        A.event(f0, "scan", dur=f1 - f0)


def build_erfasser(coll, name="Erfasser"):
    C.set_coll(coll)
    bones = [
        ("root", (0, 0, 0), (0, 0.2, 0), None, 0),
        ("wheel", (0, 0, 0.27), (0.15, 0, 0.27), "root", 0),
        ("body", (0, 0, 0.27), (0, 0, 1.5), "root", 0),
        ("neck", (0, 0, 1.5), (0, 0, 1.78), "body", 0),
        ("head", (0, 0, 1.78), (0, 0, 2.1), "neck", 0),
    ]
    for s, sx in (("L", 1), ("R", -1)):
        bones += [
            ("arm_" + s, (0.2 * sx, 0, 1.44), (0.22 * sx, 0, 1.06), "body", 180),
            ("fore_" + s, (0.22 * sx, 0, 1.06), (0.23 * sx, 0, 0.7), "arm_" + s, 180),
            ("hand_" + s, (0.23 * sx, 0, 0.7), (0.23 * sx, 0, 0.6), "fore_" + s, 180),
        ]
    rig = RG.build_armature(name, bones, coll)
    P = RG.Parts(name, coll)
    n = lambda s: f"{name}_{s}"
    navy = M(n("navy"), (0.035, 0.055, 0.12), metal=0.55, rough=0.32, dirt=0.3, rust=0.06, scale=6, bump=0.04,
             coat=0.45, rust_color=(0.25, 0.18, 0.1))
    felt = C.fabric(n("felt"), (0.025, 0.035, 0.08), rough=0.8, dirt=0.2, weave=160, bump=0.15, sheen=0.6)
    seam = M("seam_dark", (0.03, 0.025, 0.02), rough=0.9, dirt=0.0, bump=0.0)
    chrome = M("chrome", (0.85, 0.86, 0.9), metal=1.0, rough=0.12, dirt=0.05, bump=0)
    gold = M("gold", (0.9, 0.65, 0.2), metal=1.0, rough=0.25, dirt=0.05, bump=0)
    white = M("collar_white", (0.85, 0.86, 0.88), rough=0.4, dirt=0.05, bump=0)
    redtie = M("tie_red", (0.5, 0.02, 0.03), rough=0.4, dirt=0.05, bump=0)
    rubber = M("tire", (0.02, 0.02, 0.02), rough=0.8, dirt=0.2)
    slit = iris_material(n("slit"), (1.0, 0.05, 0.03), 3.0)
    # wheel
    P.add("wheel", C.torus(n("tire"), 0.22, 0.05, loc=(0, 0, 0.27), rot=(0, 90, 0), m=rubber, coll=coll))
    P.add("wheel", C.cyl(n("hub"), 0.05, 0.08, loc=(0, 0, 0.27), rot=(0, 90, 0), m=chrome, coll=coll))
    for k in range(8):
        a = math.pi * k / 8
        P.add("wheel", C.cyl(n(f"spoke{k}"), 0.006, 0.4, loc=(0, 0, 0.27), rot=(math.degrees(a), 0, 0), m=chrome,
                             coll=coll, verts=6))
    # fork
    for fx in (-1, 1):
        P.add("body", C.limb(n(f"fork{fx}"), (0.065 * fx, 0, 0.27), (0.04 * fx, 0, 0.62), 0.014, 0.018, m=chrome,
                             coll=coll))
    # body: tall frock-coat shape
    bd = C.lathe(n("body"), [(0.06, 0.58), (0.12, 0.62), (0.14, 0.8), (0.15, 1.1), (0.19, 1.35), (0.2, 1.42),
                             (0.12, 1.49), (0.04, 1.51)], m=navy, coll=coll, cap_bottom=True)
    bd.scale = (1, 0.7, 1)
    C.subsurf(bd, 1)
    P.add("body", bd)
    # riveted panel seams (it is a machine in a uniform, not a man)
    for z, r in ((0.8, 0.14), (1.12, 0.152)):
        ring = C.torus(n(f"seam{z}"), r, 0.004, loc=(0, 0, z), m=seam, coll=coll, seg=48)
        ring.scale = (1, 0.7, 1)
        P.add("body", ring)
        for k in range(14):
            a = 2 * math.pi * k / 14
            P.add("body", C.sphere(n(f"rivet{z}_{k}"), 0.006, loc=(math.cos(a) * r, math.sin(a) * r * 0.7, z + 0.012),
                                   m=chrome, seg=6, rings=4, coll=coll))
    # frock-coat tails at the back
    for tx in (-1, 1):
        tail = C.box(n(f"coattail{tx}"), (0.11, 0.025, 0.42), loc=(0.06 * tx, 0.105, 0.86), rot=(12, 0, 6 * tx),
                     m=navy, bevel=0.012, coll=coll)
        C.subsurf(tail, 1)
        P.add("body", tail)
        P.add("body", C.box(n(f"tailtrim{tx}"), (0.112, 0.027, 0.02), loc=(0.06 * tx, 0.13, 0.655), rot=(12, 0, 6 * tx),
                            m=gold, bevel=0.004, coll=coll))
    # coat tails + gold trim + buttons + collar + tie + badge
    P.add("body", C.torus(n("trim"), 0.12, 0.012, loc=(0, 0, 0.62), m=gold, coll=coll))
    for i in range(5):
        P.add("body", C.sphere(n(f"btn{i}"), 0.014, loc=(0.0, -0.1 - 0.004 * i, 0.82 + i * 0.12), m=gold, seg=10,
                               rings=6, coll=coll))
    col = C.lathe(n("collar"), [(0.075, 1.46), (0.085, 1.52), (0.065, 1.56)], m=white, coll=coll)
    P.add("body", col)
    P.add("body", C.box(n("tie"), (0.04, 0.012, 0.16), loc=(0, -0.1, 1.38), rot=(-10, 0, 0), m=redtie, bevel=0.005,
                        coll=coll))
    P.add("body", C.box(n("badge"), (0.08, 0.01, 0.05), loc=(0.09, -0.115, 1.22), rot=(-8, 0, 20), m=gold,
                        bevel=0.004, coll=coll))
    P.add("body", C.text(n("badgetxt"), "E-07", size=0.025, loc=(0.0905, -0.122, 1.22), rot=(82, 0, 20),
                         m=M("ink_black", (0.01, 0.01, 0.01)), coll=coll))
    # epaulettes
    for s, sx in (("L", 1), ("R", -1)):
        P.add("body", C.cyl(n("epau" + s), 0.06, 0.02, loc=(0.18 * sx, 0, 1.47), rot=(0, 15 * sx, 0), m=gold,
                            coll=coll))
    # neck (telescopic)
    P.add("neck", C.cyl(n("neck1"), 0.03, 0.18, loc=(0, 0, 1.6), m=chrome, coll=coll))
    P.add("neck", C.cyl(n("neck2"), 0.024, 0.18, loc=(0, 0, 1.72), m=chrome, coll=coll))
    # head: top hat with scanner slit + monocle
    brim = C.lathe(n("brim"), [(0.125, 1.79), (0.185, 1.79), (0.205, 1.805), (0.212, 1.825), (0.2, 1.815),
                                (0.125, 1.81)], m=felt, coll=coll, seg=48, cap_top=False)
    P.add("head", brim)
    P.add("head", C.cyl(n("hat"), 0.13, 0.32, loc=(0, 0, 1.97), r2=0.14, m=felt, coll=coll, verts=40))
    P.add("head", C.cyl(n("hatband"), 0.1315, 0.05, loc=(0, 0, 1.84), m=redtie, coll=coll, verts=40))
    P.add("head", C.cyl(n("hattop"), 0.141, 0.01, loc=(0, 0, 2.13), m=felt, coll=coll, verts=40))
    # slit: curved strip in front
    import bmesh
    bm = bmesh.new()
    segs = 12
    vs = []
    for j in range(segs + 1):
        a = math.radians(-50 + 100 * j / segs)
        r = 0.137
        x, y = r * math.sin(a), -r * math.cos(a)
        vs.append((bm.verts.new((x, y, 1.935)), bm.verts.new((x, y, 1.965))))
    for j in range(segs):
        bm.faces.new((vs[j][0], vs[j + 1][0], vs[j + 1][1], vs[j][1]))
    me = bpy.data.meshes.new(n("slit"))
    bm.to_mesh(me); bm.free()
    so = C.new_obj(n("slit"), me, mat_=slit, coll=coll)
    so.modifiers.new("solid", "SOLIDIFY").thickness = 0.006
    P.add("head", so)
    P.add("head", C.torus(n("monocle"), 0.04, 0.007, loc=(-0.05, -0.142, 1.95), rot=(90, 0, 0), m=gold, coll=coll))
    P.add("head", C.cyl(n("monoglass"), 0.036, 0.004, loc=(-0.05, -0.143, 1.95), rot=(90, 0, 0),
                        m=C.glass("mono_glass", (0.9, 0.95, 1.0), 0.0), coll=coll))
    P.add("head", C.curve_tube(n("chain"), [(-0.09, -0.135, 1.94), (-0.12, -0.11, 1.86), (-0.12, -0.08, 1.8)],
                               radius=0.003, m=gold, coll=coll))
    # arms
    for s, sx in (("L", 1), ("R", -1)):
        sh = Vector((0.2 * sx, 0, 1.44)); el = Vector((0.22 * sx, 0, 1.06)); wr = Vector((0.23 * sx, 0, 0.7))
        P.add("arm_" + s, C.sphere(n("sh" + s), 0.045, loc=sh, m=chrome, coll=coll))
        P.add("arm_" + s, C.limb(n("ua" + s), sh, el, 0.034, 0.028, m=navy, coll=coll))
        P.add("arm_" + s, C.torus(n("uacuff" + s), 0.03, 0.006, loc=el + Vector((0, 0, 0.05)), m=gold, coll=coll))
        # hydraulic piston along the forearm
        P.add("fore_" + s, C.limb(n("piston" + s), el + Vector((0, 0.03, -0.04)), wr + Vector((0, 0.025, 0.08)), 0.007,
                                  m=M("dark_metal"), coll=coll))
        P.add("fore_" + s, C.sphere(n("el" + s), 0.032, loc=el, m=chrome, coll=coll))
        P.add("fore_" + s, C.limb(n("fa" + s), el, wr, 0.02, 0.018, m=chrome, coll=coll))
        P.add("hand_" + s, C.sphere(n("wr" + s), 0.028, loc=wr, m=chrome, coll=coll))
        P.add("hand_" + s, C.cyl(n("cuffw" + s), 0.03, 0.04, loc=wr + Vector((0, 0, 0.03)), m=white, coll=coll))
        import humanparts as HP
        for o in HP.glove(n, "g" + s, sx, wr - Vector((0, 0, 0.055)), 0.85, white, coll, bare=True):
            P.add("hand_" + s, o)
    # stamp on left hand
    P.add("hand_L", C.cyl(n("stamp_handle"), 0.018, 0.12, loc=(0.23, 0, 0.62), m=M("wood", (0.4, 0.22, 0.1),
                                                                                   rough=0.6), coll=coll))
    P.add("hand_L", C.box(n("stamp_block"), (0.14, 0.09, 0.05), loc=(0.23, 0, 0.545), m=gold, bevel=0.008,
                          coll=coll))
    P.add("hand_L", C.box(n("stamp_pad"), (0.13, 0.08, 0.012), loc=(0.23, 0, 0.515), m=M("stamp_ink",
                                                                                         (0.6, 0.02, 0.02),
                                                                                         rough=0.7), bevel=0.003,
                          coll=coll))
    # net on right hand: pole + hoop + mesh
    pole_top = Vector((-0.23, 0, 0.7 + 1.1))
    P.add("hand_R", C.limb(n("pole"), (-0.23, 0, 0.55), pole_top, 0.012, m=chrome, coll=coll))
    P.add("hand_R", C.torus(n("hoop"), 0.24, 0.01, loc=pole_top + Vector((0, 0, 0.24)), rot=(0, 90, 0), m=chrome,
                            coll=coll))
    netm = C.lathe(n("net"), [(0.24, 0.0), (0.2, 0.18), (0.12, 0.32), (0.02, 0.38)],
                   loc=pole_top + Vector((0, 0, 0.24)), rot=(0, 90, 0), m=M("net_m", (0.3, 0.3, 0.28), rough=0.8),
                   coll=coll, seg=16)
    wf = netm.modifiers.new("wire", "WIREFRAME"); wf.thickness = 0.006
    P.add("hand_R", netm)
    P.attach_all(rig)
    act = Erfasser(rig, ERF_POSES, None, slit)
    act.pose(0, "stand")
    act.extra["net"] = netm
    return act


# =========================================================================== BELLO
BELLO_POSES = {
    "stand": {"body": (0, 0, 0), "neck": (0, 0, 0), "head": (0, 0, 0), "tail": (-20, 0, 0),
              "fl_L": (0, 0, 0), "fl_R": (0, 0, 0), "bl_L": (0, 0, 0), "bl_R": (0, 0, 0),
              "fl2_L": (0, 0, 0), "fl2_R": (0, 0, 0), "bl2_L": (0, 0, 0), "bl2_R": (0, 0, 0)},
    "sniff": {"neck": (35, 0, 0), "head": (20, 0, 0), "body": (6, 0, 0), "fl_L": (-10, 0, 0), "fl_R": (-10, 0, 0),
              "fl2_L": (10, 0, 0), "fl2_R": (10, 0, 0)},
    "sit": {"body": (-25, 0, 0), "bl_L": (70, 0, 0), "bl_R": (70, 0, 0), "bl2_L": (-110, 0, 0),
            "bl2_R": (-110, 0, 0), "fl_L": (25, 0, 0), "fl_R": (25, 0, 0), "neck": (-15, 0, 0), "head": (5, 0, 0)},
    "cower": {"body": (8, 0, 0), "neck": (40, 0, 0), "head": (20, 0, 0), "tail": (40, 0, 0),
              "fl_L": (-20, 0, 0), "fl_R": (-20, 0, 0), "fl2_L": (40, 0, 0), "fl2_R": (40, 0, 0),
              "bl_L": (30, 0, 0), "bl_R": (30, 0, 0), "bl2_L": (-60, 0, 0), "bl2_R": (-60, 0, 0)},
    "look_up": {"neck": (-25, 0, 0), "head": (-15, 0, 0)},
}


class Quadruped(Robot):
    def walk_cycle(self, f, phase, style):
        tw = 2 * math.pi * phase
        limp = 0.6 if style == "limp" else 1.0
        pose = {}
        for leg, ph in (("fl_L", 0), ("bl_R", 0.3), ("fl_R", math.pi), ("bl_L", math.pi + 0.3)):
            c = math.cos(tw + ph); s_ = math.sin(tw + ph)
            amp = 22 * (limp if leg == "bl_L" else 1.0)
            pose[leg] = (amp * c, 0, 0)
            pose[leg.replace("l_", "l2_")] = ((25 if leg[0] == "f" else -25) * max(0, -s_), 0, 0)
        pose["body"] = (0, 0, 3 * math.cos(tw))
        pose["neck"] = (6 + 4 * math.sin(2 * tw), 0, 0)
        pose["tail"] = (-20, 0, 25 * math.sin(tw * 2))
        self.pose(f, pose)
        bob = 0.012 + (0.02 if style == "limp" and math.cos(tw) > 0.5 else 0)
        self.bone_loc(f, "root", (0, 0, bob * abs(math.sin(tw))))

    def wag(self, f0, f1, speed=4, amp=35):
        f = f0
        i = 0
        while f < f1:
            self.pose(f, {"tail": (-35, 0, amp if i % 2 else -amp)})
            f += speed
            i += 1
        self.pose(f1, {"tail": (-20, 0, 0)})
        A.event(f0, "wag", dur=f1 - f0)


def build_bello(coll, name="Bello"):
    C.set_coll(coll)
    bones = [
        ("root", (0, 0, 0), (0, 0.2, 0), None, 0),
        ("body", (0, 0.16, 0.42), (0, -0.16, 0.42), "root", 0),
        ("neck", (0, -0.16, 0.48), (0, -0.24, 0.6), "body", 0),
        ("head", (0, -0.24, 0.6), (0, -0.36, 0.62), "neck", 0),
        ("tail", (0, 0.17, 0.5), (0, 0.22, 0.62), "body", 0),
    ]
    for s, sx in (("L", 1), ("R", -1)):
        for lg, y in (("fl", -0.12), ("bl", 0.12)):
            bones += [(f"{lg}_{s}", (0.12 * sx, y, 0.38), (0.12 * sx, y, 0.2), "body", 180),
                      (f"{lg}2_{s}", (0.12 * sx, y, 0.2), (0.12 * sx, y, 0.03), f"{lg}_{s}", 180)]
    rig = RG.build_armature(name, bones, coll)
    P = RG.Parts(name, coll)
    n = lambda s: f"{name}_{s}"
    yel = M(n("paint"), (0.75, 0.55, 0.1), metal=0.5, rough=0.5, rust=0.38, scale=3)
    dark = M("dark_metal")
    pipe = M("pipe_m", (0.35, 0.35, 0.36), metal=1.0, rough=0.4, rust=0.45)
    iris = iris_material(n("iris"), (1.0, 0.55, 0.12), 3.0)
    P.add("body", C.box(n("body"), (0.26, 0.38, 0.2), loc=(0, 0, 0.44), m=yel, bevel=0.05))
    P.add("body", C.text(n("num"), "SV-12", size=0.05, loc=(0.132, 0.02, 0.45), rot=(90, 0, 90),
                         m=M("stencil", (0.08, 0.07, 0.06), rough=0.8)))
    P.add("body", C.box(n("vent"), (0.12, 0.1, 0.02), loc=(0, 0.04, 0.545), m=dark, bevel=0.01))
    P.add("neck", C.limb(n("neck"), (0, -0.15, 0.47), (0, -0.25, 0.6), 0.03, 0.025, m=pipe))
    P.add("head", C.box(n("head"), (0.17, 0.15, 0.13), loc=(0, -0.3, 0.63), m=yel, bevel=0.03))
    for o in lens_eye(n("eye"), coll, (0, -0.378, 0.635), 0.05, iris):
        P.add("head", o)
    for s, sx in (("L", 1), ("R", -1)):
        P.add("head", C.cyl(n("ear" + s), 0.04, 0.012, loc=(0.1 * sx, -0.28, 0.7), rot=(0, 60 * sx, 0), r2=0.02,
                            m=pipe))
        for lg, y in (("fl", -0.12), ("bl", 0.12)):
            P.add(f"{lg}_{s}", C.sphere(n(f"hip{lg}{s}"), 0.035, loc=(0.12 * sx, y, 0.38), m=dark))
            P.add(f"{lg}_{s}", C.limb(n(f"ul{lg}{s}"), (0.12 * sx, y, 0.38), (0.12 * sx, y, 0.2), 0.022, m=pipe))
            P.add(f"{lg}2_{s}", C.sphere(n(f"kn{lg}{s}"), 0.027, loc=(0.12 * sx, y, 0.2), m=dark))
            P.add(f"{lg}2_{s}", C.limb(n(f"ll{lg}{s}"), (0.12 * sx, y, 0.2), (0.12 * sx, y, 0.03), 0.02, 0.016,
                                       m=pipe))
            P.add(f"{lg}2_{s}", C.cyl(n(f"ft{lg}{s}"), 0.035, 0.025, loc=(0.12 * sx, y - 0.01, 0.013), m=dark))
    P.add("tail", C.cyl(n("tailrod"), 0.005, 0.16, loc=(0, 0.2, 0.58), rot=(-25, 0, 0), m=pipe, verts=8))
    tb = iris_material(n("tailbulb"), (1.0, 0.3, 0.1), 2.0)
    P.add("tail", C.sphere(n("tailbulb"), 0.016, loc=(0, 0.235, 0.655), m=tb))
    P.attach_all(rig)
    act = Quadruped(rig, BELLO_POSES, tb, iris)
    act.pose(0, "stand")
    return act


# =========================================================================== CRITTERS
def build_chicken(coll, name, loc=(0, 0, 0), yaw=0, seed=0):
    """Tin chicken: object hierarchy, returns (root, head) for animation."""
    rnd = C.R.__class__(seed)
    body_m = M("chick_body%d" % (seed % 3), [(0.75, 0.73, 0.7), (0.6, 0.35, 0.2), (0.3, 0.32, 0.35)][seed % 3],
               metal=0.8, rough=0.35, rust=0.3)
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    body = C.sphere(name + "_b", 0.09, loc=(0, 0, 0.16), scale=(0.85, 1.25, 0.9), m=body_m, parent=root, coll=coll)
    C.cyl(name + "_tail", 0.035, 0.12, loc=(0, 0.12, 0.22), rot=(-35, 0, 0), r2=0.01, m=body_m, parent=root,
          coll=coll)
    head = C.empty(name + "_neck", loc=(0, -0.08, 0.2), parent=root, coll=coll)
    C.sphere(name + "_h", 0.045, loc=(0, -0.03, 0.06), m=body_m, parent=head, coll=coll)
    C.cyl(name + "_beak", 0.015, 0.04, loc=(0, -0.08, 0.055), rot=(90, 0, 0), r2=0.001,
          m=M("beak_m", (0.85, 0.6, 0.1), rough=0.4), parent=head, coll=coll)
    comb = M("comb_m", (0.7, 0.05, 0.04), rough=0.5)
    for k in range(3):
        C.sphere(name + f"_comb{k}", 0.015, loc=(0, -0.05 + k * 0.022, 0.1 + 0.01 * (k == 1)), m=comb,
                 parent=head, coll=coll)
    C.sphere(name + "_eye", 0.008, loc=(0.03, -0.055, 0.075), m=M("eye_black"), parent=head, coll=coll)
    C.sphere(name + "_eye2", 0.008, loc=(-0.03, -0.055, 0.075), m=M("eye_black"), parent=head, coll=coll)
    for sx in (-1, 1):
        C.limb(name + f"_leg{sx}", (0.03 * sx, 0, 0.1), (0.03 * sx, -0.01, 0.0), 0.005,
               m=M("wire_m", (0.3, 0.3, 0.3), metal=1, rough=0.4), parent=root, coll=coll)
    return root, head


def animate_chicken(root, head, f0, f1, seed=0, wander=0.6):
    rnd = C.R.__class__(seed)
    f = f0
    base = Vector(root.location)
    yaw = root.rotation_euler.z
    while f < f1:
        action = rnd.random()
        if action < 0.55:  # peck
            for k in range(rnd.randint(1, 3)):
                head.rotation_euler = (0, 0, 0); head.keyframe_insert("rotation_euler", frame=f)
                head.rotation_euler = (math.radians(70), 0, 0); head.keyframe_insert("rotation_euler", frame=f + 3)
                head.rotation_euler = (0, 0, 0); head.keyframe_insert("rotation_euler", frame=f + 7)
                f += 8
        elif action < 0.8:  # hop to a new spot
            root.keyframe_insert("location", frame=f)
            root.keyframe_insert("rotation_euler", frame=f)
            yaw += rnd.uniform(-1.5, 1.5)
            d = Vector((math.sin(yaw), -math.cos(yaw), 0)) * rnd.uniform(0.1, 0.3)
            nl = Vector(root.location) + d
            if (nl - base).length > wander:
                nl = base + (nl - base).normalized() * wander
            root.location = (Vector(root.location) + nl) / 2 + Vector((0, 0, 0.12))
            root.keyframe_insert("location", frame=f + 3)
            root.location = nl
            root.rotation_euler.z = yaw
            root.keyframe_insert("location", frame=f + 6)
            root.keyframe_insert("rotation_euler", frame=f + 6)
            f += 10
        else:  # look around
            head.rotation_euler = (0, 0, math.radians(rnd.choice([-50, 50])))
            head.keyframe_insert("rotation_euler", frame=f + 2)
            head.rotation_euler = (0, 0, 0)
            head.keyframe_insert("rotation_euler", frame=f + 14)
            f += 16


def build_pigeon_drone(coll, name, loc, yaw=0):
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    gm = M("drone_m", (0.12, 0.13, 0.15), metal=0.7, rough=0.35, rust=0.1)
    C.sphere(name + "_b", 0.06, loc=(0, 0, 0.06), scale=(0.8, 1.3, 0.75), m=gm, parent=root, coll=coll)
    head = C.empty(name + "_neck", loc=(0, -0.06, 0.09), parent=root, coll=coll)
    C.sphere(name + "_h", 0.035, loc=(0, -0.02, 0.02), m=gm, parent=head, coll=coll)
    eye = C.emission("drone_eye", (1.0, 0.05, 0.02), 6.0)
    C.sphere(name + "_e", 0.012, loc=(0, -0.05, 0.025), m=eye, parent=head, coll=coll)
    for sx in (-1, 1):
        for sy in (-1, 1):
            C.cyl(name + f"_rot{sx}{sy}", 0.035, 0.004, loc=(0.07 * sx, 0.06 * sy, 0.08),
                  m=M("rotor_m", (0.05, 0.05, 0.05), rough=0.5), parent=root, coll=coll, verts=12)
    C.cyl(name + "_tail", 0.02, 0.06, loc=(0, 0.08, 0.06), rot=(-70, 0, 0), r2=0.005, m=gm, parent=root, coll=coll)
    return root, head


def animate_pigeon(head, f0, f1, seed=0):
    rnd = C.R.__class__(seed)
    f = f0 + rnd.randint(0, 20)
    while f < f1:
        a = math.radians(rnd.choice([-70, -35, 0, 35, 70]))
        head.rotation_euler = (0, 0, a)
        head.keyframe_insert("rotation_euler", frame=f)
        head.keyframe_insert("rotation_euler", frame=f + rnd.randint(10, 40))
        f += rnd.randint(25, 60)


def build_cat(coll, name, loc, yaw=0, color=(0.15, 0.12, 0.1), sleeping=True):
    root = C.empty(name, loc=loc, rot=(0, 0, yaw), coll=coll)
    fur = M(name + "_fur", color, rough=0.9, dirt=0.3, scale=15, bump=0.4)
    body = C.sphere(name + "_b", 0.12, loc=(0, 0, 0.08), scale=(1.0, 1.6, 0.7), m=fur, parent=root, coll=coll)
    head = C.empty(name + "_neck", loc=(0, -0.17, 0.1), parent=root, coll=coll)
    C.sphere(name + "_h", 0.07, loc=(0, -0.02, 0.0), scale=(1.1, 1, 0.9), m=fur, parent=head, coll=coll)
    for sx in (-1, 1):
        C.cyl(name + f"_ear{sx}", 0.025, 0.05, loc=(0.04 * sx, -0.02, 0.07), r2=0.002, m=fur, parent=head, coll=coll)
        C.box(name + f"_eye{sx}", (0.025, 0.005, 0.004 if sleeping else 0.018), loc=(0.03 * sx, -0.083, 0.01),
              m=M("eye_black"), parent=head, coll=coll, bevel=0.0)
    tail = C.curve_tube(name + "_tail", [(0.05, 0.15, 0.05), (0.15, 0.1, 0.03), (0.18, -0.05, 0.03),
                                         (0.12, -0.12, 0.04)], radius=0.02, m=fur, parent=root, coll=coll)
    return root, head, body


def animate_breathing(ob, f0, f1, period=60, amp=0.04):
    f = f0
    base = Vector(ob.scale)
    while f < f1:
        ob.scale = base; ob.keyframe_insert("scale", frame=f)
        ob.scale = base * (1 + amp); ob.keyframe_insert("scale", frame=f + period // 2)
        f += period
