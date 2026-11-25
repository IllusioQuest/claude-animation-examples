"""Uneven ground. The outdoor terrains get real relief – hummocks, dips, ridges – everywhere nobody walks.

The action is measured from the finished animation: every keyed object (characters, props, vehicles,
cameras) is sampled over the sequences that use a terrain; around those paths the ground only gets a few
centimetres of trodden unevenness, further out the full relief fades in. Roads stay level. Static set
pieces standing on the ground are settled onto the new surface.
"""
import math
import bpy
from mathutils import Vector, noise
from mathutils.kdtree import KDTree

V = Vector


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Ground:
    def __init__(self, centre, kd, n, amp=1.1, near=3.5, far=10.0, roads=(), micro=0.018, far_amp=5.0,
                 far_r=70.0, seed=0.0):
        self.c = V(centre)
        self.kd, self.n = kd, n
        self.amp, self.near, self.far = amp, near, far
        self.roads = roads
        self.micro = micro
        self.far_amp, self.far_r = far_amp, far_r
        self.off = V((seed * 17.3, seed * 5.1, 0))

    def mask(self, x, y):
        if self.n == 0:
            return 1.0
        _, _, d = self.kd.find(V((x, y, 0)))
        m = smooth(self.near, self.far, d)
        for (x0, x1, y0, y1) in self.roads:
            dx = max(x0 - x, 0, x - x1)
            dy = max(y0 - y, 0, y - y1)
            m *= smooth(0.5, 3.0, math.hypot(dx, dy))
        return m

    def road(self, x, y):
        for (x0, x1, y0, y1) in self.roads:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return True
        return False

    def h(self, x, y):
        p = V((x, y, 0)) + self.off
        mid = noise.fractal(p / 13.0, 0.6, 2.1, 3) * self.amp + noise.noise(p / 4.5) * self.amp * 0.25
        r = (V((x, y)) - self.c.xy).length
        m = self.mask(x, y)
        big = noise.fractal(p / 60.0, 0.5, 2.0, 3) * self.far_amp * smooth(self.far_r * 0.6, self.far_r * 1.6, r) * m
        micro = 0.0 if self.road(x, y) else noise.noise(p / 0.9) * self.micro + noise.noise(p / 2.7) * self.micro * 0.8
        return micro + m * (mid + 0.35 * self.amp) + big


def action_points(scenes, bounds, coll_names):
    """xy of every root-level keyed object (and camera) over the given scenes, inside bounds."""
    pts = []
    (x0, x1, y0, y1) = bounds
    for sc in scenes:
        f0, f1 = sc.frame_start, sc.frame_end
        objs = set()
        for o in sc.objects:
            if o.parent is not None or not o.animation_data or not o.animation_data.action:
                continue
            objs.add(o)
        for o in objs:
            act = o.animation_data.action
            fx = act.fcurves.find("location", index=0)
            fy = act.fcurves.find("location", index=1)
            fz = act.fcurves.find("location", index=2)
            if fx is None or fy is None:
                continue
            step = 3
            cam = o.type == "CAMERA"
            for f in range(f0, f1 + 1, step):
                x, y = fx.evaluate(f), fy.evaluate(f)
                z = fz.evaluate(f) if fz else 0.0
                if z < -50 or not (x0 <= x <= x1 and y0 <= y <= y1):
                    continue
                pts.append((x, y))
                if cam:  # keep the ground low in a wider circle around cameras
                    for a in range(0, 360, 60):
                        pts.append((x + math.cos(math.radians(a)) * 1.5, y + math.sin(math.radians(a)) * 1.5))
    return pts


def build_kd(pts):
    kd = KDTree(max(1, len(pts)))
    for i, (x, y) in enumerate(pts):
        kd.insert((x, y, 0), i)
    kd.balance()
    return kd, len(pts)


def regrid(terrain, g, size, res=360, a=0.22):
    """Re-mesh the terrain with dense spacing in the middle and bake g.h into the vertices."""
    import bmesh
    for md in list(terrain.modifiers):
        terrain.modifiers.remove(md)
    loc = terrain.matrix_world.translation.copy()
    coords = []
    for i in range(res + 1):
        u = -1 + 2 * i / res
        coords.append(size / 2 * (a * u + (1 - a) * u ** 3))
    bm = bmesh.new()
    vs = []
    for j, yv in enumerate(coords):
        row = []
        for i, xv in enumerate(coords):
            wx, wy = loc.x + xv, loc.y + yv
            row.append(bm.verts.new((xv, yv, g.h(wx, wy))))
        vs.append(row)
    for j in range(res):
        for i in range(res):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            f.smooth = True
    me = terrain.data
    bm.to_mesh(me)
    bm.free()


def settle(coll, g, terrain, skip=()):
    """Put static, unparented ground pieces of a set onto the new surface."""
    n = 0
    for o in coll.all_objects:
        if o is terrain or o.parent is not None or o.name.startswith(skip):
            continue
        if o.animation_data and o.animation_data.action and o.animation_data.action.fcurves.find("location"):
            continue
        if o.type not in ("MESH", "EMPTY", "CURVE", "FONT"):
            continue
        z = o.location.z
        if z > 1.6 or z < -2.0:
            continue
        o.location.z = z + g.h(o.location.x, o.location.y)
        n += 1
    return n


def apply(ctx):
    S = ctx.seq
    sc_of = lambda i: S[i]["scene"] if i in S else None
    out = []
    # ---- scrapyard (S1, S4 second half, S6)
    terr = bpy.data.objects.get("scrap_terrain")
    if terr:
        scenes = [s for s in (sc_of(1), sc_of(4), sc_of(6)) if s]
        pts = action_points(scenes, (-60, 60, -60, 70), None)
        pts += [(x, 24.0) for x in range(-100, 101, 2)]  # pylons and cables stay where they are
        kd, n = build_kd(pts)
        g = Ground((0, 0, 0), kd, n, amp=1.0, near=3.0, far=9.0,
                   roads=[(3.5, 8.5, -300, 320), (-32, 9, 5.5, 10.5)], seed=1.0, far_r=60)
        regrid(terr, g, 600, res=400)
        out.append(("scrap", n, settle(ctx.c_scrap, g, terr, skip=("road", "pline", "citywall", "s_crow", "hut"))))
        # the hut stands on its own levelled patch (it is the set of S2's exterior and S6)
        ctx.ground_scrap = g
    # ---- village (S3, S4 first half)
    terr = bpy.data.objects.get("village_terrain")
    if terr:
        scenes = [s for s in (sc_of(3), sc_of(4)) if s]
        c = terr.matrix_world.translation
        pts = action_points(scenes, (c.x - 60, c.x + 60, c.y - 60, c.y + 60), None)
        kd, n = build_kd(pts)
        g = Ground(c, kd, n, amp=0.55, near=2.5, far=7.0, seed=2.0, far_r=55, micro=0.014)
        regrid(terr, g, 400, res=360)
        out.append(("village", n, settle(ctx.c_vil, g, terr, skip=("v_pigeonwire", "v_line", "v_lights", "v_wire"))))
        ctx.ground_vil = g
    # ---- depot outside the fence: paved lot near the wall, rough ground beyond
    terr = bpy.data.objects.get("depot_terrain")
    if terr:
        scenes = [s for s in (sc_of(5),) if s]
        c = terr.matrix_world.translation
        pts = action_points(scenes, (c.x - 60, c.x + 60, c.y - 60, c.y + 30), None)
        pts += [(c.x + x, c.y + y) for x in range(-40, 41, 2) for y in range(-2, 8, 2)]  # fence line and wall
        kd, n = build_kd(pts)
        g = Ground(c, kd, n, amp=0.6, near=4.0, far=12.0, seed=3.0, far_r=70, micro=0.01)
        regrid(terr, g, 400, res=300)
        out.append(("depot", n, 0))
    print("relief", out)
