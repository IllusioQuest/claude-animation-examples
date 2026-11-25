"""Animation helpers: keying, easing, holds, walk cycles, actors."""
import bpy
import math
from mathutils import Vector
import core as C

EVENTS = []  # (frame, kind, extra) – used by the sound pipeline


def event(frame, kind, **kw):
    EVENTS.append({"frame": int(frame), "kind": kind, **kw})


def _fcurve(id_data, path, index):
    ad = id_data.animation_data
    if ad is None or ad.action is None:
        return None
    return ad.action.fcurves.find(path, index=index)


def set_interp(id_data, path, frame, interp, index=-1):
    ad = id_data.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == path and (index < 0 or fc.array_index == index):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.01:
                    kp.interpolation = interp
                    if interp == "BEZIER":
                        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def key(owner, prop, frame, value=None, interp=None, index=-1, id_data=None):
    """Set owner.prop = value and insert a keyframe."""
    if value is not None:
        if index >= 0:
            getattr(owner, prop)[index] = value
        else:
            setattr(owner, prop, value)
    owner.keyframe_insert(prop, frame=frame, index=index)
    if interp:
        idd = id_data or getattr(owner, "id_data", owner)
        path = owner.path_from_id(prop) if hasattr(owner, "path_from_id") and owner != idd else prop
        set_interp(idd, path, frame, interp, index)


def key_socket(sock, frame, value, interp=None):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)
    if interp:
        idd = sock.id_data
        set_interp(idd, sock.path_from_id("default_value"), frame, interp)


def hide(ob, frame, hidden):
    """Visibility key (render + viewport), constant interpolation."""
    ob.hide_render = hidden
    ob.hide_viewport = hidden
    ob.keyframe_insert("hide_render", frame=frame)
    ob.keyframe_insert("hide_viewport", frame=frame)
    set_interp(ob, "hide_render", frame, "CONSTANT")
    set_interp(ob, "hide_viewport", frame, "CONSTANT")


def show_between(ob, f0, f1):
    hide(ob, 0, True)
    hide(ob, f0, False)
    hide(ob, f1, True)


def hold_obj(ob, frame, paths=("location", "rotation_euler", "scale")):
    """Key the currently evaluated value of animated channels at frame (a 'hold')."""
    ad = ob.animation_data
    for p in paths:
        vals = list(getattr(ob, p))
        for i in range(len(vals)):
            fc = _fcurve(ob, p, i)
            if fc is not None:
                vals[i] = fc.evaluate(frame)
        setattr(ob, p, vals)
        ob.keyframe_insert(p, frame=frame)


def ease(t, kind="inout"):
    t = max(0.0, min(1.0, t))
    if kind == "in":
        return t * t
    if kind == "out":
        return 1 - (1 - t) * (1 - t)
    if kind == "linear":
        return t
    return t * t * (3 - 2 * t)


def yaw_towards(d):
    return math.atan2(d[0], -d[1])


def wrap_angle_near(a, ref):
    while a - ref > math.pi:
        a -= 2 * math.pi
    while a - ref < -math.pi:
        a += 2 * math.pi
    return a


class Actor:
    """Wraps an armature object. Poses are dicts bone -> (x, y, z) degrees.
    Bones ending in _R get Y/Z mirrored so poses can be written symmetrically."""

    def __init__(self, rig, poses=None, mirror=True):
        self.rig = rig
        self.poses = poses or {}
        self.mirror = mirror
        self.extra = {}

    # ----------------------------------------------------------------- placement
    def place(self, f, loc=None, yaw=None, interp=None):
        ob = self.rig
        if loc is not None:
            key(ob, "location", f, Vector(loc), interp)
        if yaw is not None:
            r = ob.rotation_euler.copy()
            fc = _fcurve(ob, "rotation_euler", 2)
            yaw_r = math.radians(yaw)
            if fc is not None:
                yaw_r = wrap_angle_near(yaw_r, fc.evaluate(f))
            r.z = yaw_r
            ob.rotation_euler = r
            ob.keyframe_insert("rotation_euler", frame=f, index=2)
            if interp:
                set_interp(ob, "rotation_euler", f, interp, 2)

    def cut(self, f, loc, yaw):
        """Teleport at a cut: hold previous at f-1, jump at f."""
        ob = self.rig
        if ob.animation_data and ob.animation_data.action:
            hold_obj(ob, f - 1, ("location", "rotation_euler"))
        self.place(f, loc, yaw)
        set_interp(ob, "location", f - 1, "CONSTANT")
        set_interp(ob, "rotation_euler", f - 1, "CONSTANT")

    def offstage(self, f):
        self.cut(f, (0, 0, -300), 0)

    def hold_place(self, f):
        hold_obj(self.rig, f, ("location", "rotation_euler"))

    def pos_at(self, f):
        ob = self.rig
        v = Vector(ob.location)
        for i in range(3):
            fc = _fcurve(ob, "location", i)
            if fc:
                v[i] = fc.evaluate(f)
        return v

    def yaw_at(self, f):
        fc = _fcurve(self.rig, "rotation_euler", 2)
        return math.degrees(fc.evaluate(f)) if fc else math.degrees(self.rig.rotation_euler.z)

    # ----------------------------------------------------------------- posing
    def _pb(self, bone):
        return self.rig.pose.bones[bone]

    def pose(self, f, p, interp=None, scale=None, loc=None, blend=1.0):
        """p: name of stored pose or dict. Also accepts extra dicts for scale/loc."""
        if isinstance(p, str):
            p = self.poses[p]
        for bone, rot in p.items():
            if bone.startswith("@"):
                continue
            pb = self._pb(bone)
            x, y, z = rot
            if self.mirror and bone.endswith("_R"):
                y, z = -y, -z
            pb.rotation_euler = (math.radians(x) * blend, math.radians(y) * blend, math.radians(z) * blend)
            pb.keyframe_insert("rotation_euler", frame=f)
            if interp:
                set_interp(self.rig, pb.path_from_id("rotation_euler"), f, interp)
        for d, prop in ((scale, "scale"), (loc, "location")):
            if d:
                for bone, v in d.items():
                    pb = self._pb(bone)
                    if prop == "location" and self.mirror and bone.endswith("_R"):
                        v = (-v[0], v[1], v[2])
                    setattr(pb, prop, v)
                    pb.keyframe_insert(prop, frame=f)
                    if interp:
                        set_interp(self.rig, pb.path_from_id(prop), f, interp)

    def bone_scale(self, f, bone, s, interp=None):
        pb = self._pb(bone)
        pb.scale = s if hasattr(s, "__len__") else (s, s, s)
        pb.keyframe_insert("scale", frame=f)
        if interp:
            set_interp(self.rig, pb.path_from_id("scale"), f, interp)

    def bone_loc(self, f, bone, v, interp=None):
        pb = self._pb(bone)
        pb.location = v
        pb.keyframe_insert("location", frame=f)
        if interp:
            set_interp(self.rig, pb.path_from_id("location"), f, interp)

    def hold(self, f, bones=None):
        """Key evaluated pose at f for all (or given) animated bones."""
        ad = self.rig.animation_data
        if not ad or not ad.action:
            return
        seen = {}
        for fc in ad.action.fcurves:
            if fc.data_path.startswith("pose.bones"):
                bn = fc.data_path.split('"')[1]
                if bones and bn not in bones:
                    continue
                prop = fc.data_path.rsplit(".", 1)[1]
                seen.setdefault((bn, prop), {})[fc.array_index] = fc.evaluate(f)
        for (bn, prop), vals in seen.items():
            pb = self._pb(bn)
            cur = list(getattr(pb, prop))
            for i, v in vals.items():
                cur[i] = v
            setattr(pb, prop, cur)
            pb.keyframe_insert(prop, frame=f)

    def hold_all(self, f):
        self.hold(f)
        self.hold_place(f)

    # ----------------------------------------------------------------- locomotion
    def walk(self, f0, pts, speed=1.0, stride=0.55, cycle=None, bob=0.03, lean=4.0, arms=True,
             turn_frames=6, end_pose="stand", style="walk"):
        """Walk along polyline pts (list of (x,y,z)) starting at f0. Returns end frame.
        Uses self.walk_cycle(f, phase, style) to key limb poses."""
        pts = [Vector(p) for p in pts]
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        total = sum((b - a).length for a, b in segs)
        dur = max(2, int(round(total / speed * C.FPS)))
        f1 = f0 + dur
        # location keys at each polyline point with linear interp; yaw keys at corners
        acc = 0.0
        self.place(f0, pts[0], math.degrees(yaw_towards(pts[1] - pts[0])), interp="LINEAR")
        for i, (a, b) in enumerate(segs):
            acc += (b - a).length
            f = f0 + int(round(acc / total * dur))
            yaw = math.degrees(yaw_towards(b - a))
            if i > 0:
                fs = f0 + int(round((acc - (b - a).length) / total * dur))
                self.place(max(f0, fs - turn_frames // 2), None, math.degrees(yaw_towards(a - segs[i - 1][0])))
                self.place(fs + turn_frames // 2, None, yaw)
            self.place(f, b, yaw, interp="LINEAR")
        # limb cycle
        steps = max(1, int(round(total / stride)))
        fpstep = dur / steps
        for s in range(steps + 1):
            for half in (0, 0.5):
                fr = f0 + (s + half) * fpstep
                if fr > f1:
                    break
                self.walk_cycle(int(round(fr)), (s % 2) * 0.5 + half / 1.0 * 0.5, style)
                if half == 0:
                    event(int(round(fr)), "step", who=self.rig.name, style=style)
        if end_pose:
            self.pose(f1 + 3, end_pose)
        return f1

    def walk_cycle(self, f, phase, style):
        """Override per character. phase 0..1 over a full two-step cycle (0 = contact L)."""
        pass


def camera(name, coll, lens=35.0, sensor=36.0, clip_end=2000.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_end = clip_end
    cd.clip_start = 0.05
    ob = bpy.data.objects.new(name, cd)
    coll.objects.link(ob)
    return ob


def cam_key(cam, f, loc, target, lens=None, interp=None, roll=0.0):
    cam.location = loc
    e = C.look_at_rot(loc, target)
    if roll:
        e.rotate_axis("Z", math.radians(roll))
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
    if lens is not None:
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
    if interp:
        set_interp(cam, "location", f, interp)
        set_interp(cam, "rotation_euler", f, interp)


def shake(ob, f0, f1, amp=0.05, freq=2.0, path="location"):
    """Add a noise modifier restricted to [f0, f1] on each channel of path."""
    ad = ob.animation_data
    if not ad or not ad.action:
        ob.keyframe_insert(path, frame=f0)
    for i in range(3):
        fc = ob.animation_data.action.fcurves.find(path, index=i)
        if fc is None:
            ob.keyframe_insert(path, frame=f0, index=i)
            fc = ob.animation_data.action.fcurves.find(path, index=i)
        m = fc.modifiers.new("NOISE")
        m.scale = 1.0 / max(0.01, freq) * 2
        m.strength = amp
        m.phase = C.R.random() * 100
        m.use_restricted_range = True
        m.frame_start = f0
        m.frame_end = f1
        m.blend_in = min(3, (f1 - f0) / 3)
        m.blend_out = min(3, (f1 - f0) / 3)


# --------------------------------------------------------------------------- attachment helpers
def world_matrix_at(ob, f, bone=None):
    sc = bpy.context.scene
    sc.frame_set(int(f))
    if bone:
        return ob.matrix_world @ ob.pose.bones[bone].matrix
    return ob.matrix_world.copy()


def attach_to(ob, target, f, bone=None, name=None):
    """From frame f on, ob follows target (Child Of constraint, keeps current placement)."""
    con = ob.constraints.new("CHILD_OF")
    if name:
        con.name = name
    con.target = target
    if bone:
        con.subtarget = bone
    # inverse so that ob stays put at frame f
    tm = world_matrix_at(target, f, bone)
    con.inverse_matrix = tm.inverted()
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f)
    for fc in ob.animation_data.action.fcurves:
        if "influence" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    return con


def detach(ob, con, f):
    """At frame f stop following; ob stays where it is (keys its own transform)."""
    mw = world_matrix_at(ob, f)
    # hold own transform until f-1
    for p in ("location", "rotation_euler", "scale"):
        ob.keyframe_insert(p, frame=f - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f - 1)
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f)
    ob.matrix_world = mw  # with influence 0 the basis = world (no parent assumed)
    loc, rot, sc_ = mw.decompose()
    ob.location = loc
    ob.rotation_euler = rot.to_euler()
    ob.scale = sc_
    for p in ("location", "rotation_euler", "scale"):
        ob.keyframe_insert(p, frame=f)
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            if abs(kp.co.x - (f - 1)) < 0.01 or ("influence" in fc.data_path):
                kp.interpolation = "CONSTANT"


def arc(ob, f0, f1, p0, p1, height=0.5, spin=(0, 0, 0), steps=6):
    """Ballistic-looking arc of an object between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    r0 = Vector(ob.rotation_euler)
    for i in range(steps + 1):
        t = i / steps
        p = p0.lerp(p1, t)
        p.z += height * 4 * t * (1 - t)
        f = f0 + (f1 - f0) * t
        ob.location = p
        ob.rotation_euler = (r0.x + spin[0] * t, r0.y + spin[1] * t, r0.z + spin[2] * t)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        set_interp(ob, "location", f, "LINEAR")


def look(actor, f, target, pitch=None, bone="head", interp=None, limit=70, extra=None):
    """Turn actor's head toward a world point (yaw only + optional pitch)."""
    pos = actor.pos_at(f)
    yaw = math.radians(actor.yaw_at(f))
    d = Vector(target) - pos
    phi = yaw_towards(d)
    rel = math.degrees(wrap_angle_near(phi - yaw, 0))
    rel = max(-limit, min(limit, rel))
    if pitch is None:
        horiz = Vector((d.x, d.y)).length
        pitch = -math.degrees(math.atan2(d.z - 1.5, max(0.3, horiz))) * 0.6
    p = {bone: (pitch, rel, 0)}
    if extra:
        p.update(extra)
    actor.pose(f, p, interp)
    return rel
