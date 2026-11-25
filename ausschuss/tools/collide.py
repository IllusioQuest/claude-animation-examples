"""Interpenetration checker.

    blender -b ausschuss.blend -S S1_Scrapyard_Dawn -P tools/collide.py -- [step] [out.json]

For every sampled frame: every visible mesh object that moves (or belongs to a moving group,
e.g. a character rig) is tested against everything else in the scene. Parts of the same group
(same top-level parent, or attached via an active Child Of constraint) are not tested against
each other. Reports penetration depth (how far vertices sit behind the nearest surface).
"""
import sys
import json
import bpy
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(args[0]) if args else 3
OUT = args[1] if len(args) > 1 else None
MIN_DEPTH = 0.03
SKIP = ("fog", "smoke", "iris", "glow", "beam", "cone", "dust", "spark", "rain", "star", "sky", "decal",
        "shadowcatch", "volume", "halo", "flare", "puff", "steam", "light_", "ray")

sc = bpy.context.scene
VL = sc.view_layers[0]
dg = VL.depsgraph


def goto(f):
    sc.frame_set(f)
    VL.update()
f0, f1 = sc.frame_start, sc.frame_end
frames = list(range(f0, f1 + 1, STEP))


def top(ob):
    while ob.parent:
        ob = ob.parent
    return ob


def group_of(ob):
    """Group name at the current frame (follows active Child Of constraints)."""
    seen = 0
    o = ob
    while seen < 10:
        seen += 1
        tgt = None
        for c in o.constraints:
            if c.type == "CHILD_OF" and c.target and c.influence > 0.5:
                tgt = c.target
        if tgt is not None:
            o = tgt
            continue
        if o.parent:
            o = o.parent
            continue
        break
    return o.name


meshes = [o for o in sc.objects if o.type in ("MESH", "CURVE", "FONT")
          and not any(s in o.name.lower() for s in SKIP)]
local = {}  # name -> (verts np (n,3), polys list)


def local_mesh(o):
    if o.name in local:
        return local[o.name]
    oe = o.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except RuntimeError:
        local[o.name] = None
        return None
    if me is None or len(me.polygons) == 0:
        local[o.name] = None
        if me is not None:
            oe.to_mesh_clear()
        return None
    v = np.array([vv.co[:] for vv in me.vertices])
    p = [tuple(pp.vertices) for pp in me.polygons]
    oe.to_mesh_clear()
    local[o.name] = (v, p)
    return local[o.name]


# pass 1: which objects move
mats = {}
vis = {}
for f in frames:
    goto(f)
    for o in meshes:
        mats.setdefault(o.name, []).append(np.array(o.evaluated_get(dg).matrix_world))
        vis.setdefault(o.name, []).append(o.visible_get() and not o.hide_render)
moving = set()
for n, ms in mats.items():
    a = ms[0]
    if any(np.abs(m - a).max() > 1e-4 for m in ms[1:]):
        moving.add(n)
print("objects", len(meshes), "moving", len(moving), flush=True)


def world(o, idx):
    lm = local_mesh(o)
    if lm is None:
        return None
    v, p = lm
    m = mats[o.name][idx]
    w = v @ m[:3, :3].T + m[:3, 3]
    return w, p


def aabb(w):
    return w.min(0), w.max(0)


static_cache = {}


def static_entry(o):
    if o.name not in static_cache:
        r = world(o, 0)
        if r is None:
            static_cache[o.name] = None
        else:
            w, p = r
            static_cache[o.name] = (w, BVHTree.FromPolygons([tuple(x) for x in w], p, epsilon=0.0), aabb(w))
    return static_cache[o.name]


def depth(wa, tb, bb):
    """max distance of wa's vertices behind tb's surface (within tb's aabb)."""
    lo, hi = bb
    m = np.all((wa >= lo - 0.01) & (wa <= hi + 0.01), axis=1)
    pts = wa[m]
    if len(pts) > 150:
        pts = pts[np.linspace(0, len(pts) - 1, 150).astype(int)]
    best = 0.0
    for v in pts:
        r = tb.find_nearest(Vector(v), 0.6)
        if r[0] is None:
            continue
        co, nrm, _, d = r
        if (Vector(v) - co).dot(nrm) < -1e-4 and d > best:
            best = d
    return best


hits = []
by_name = {o.name: o for o in meshes}
for idx, f in enumerate(frames):
    goto(f)
    groups = {o.name: group_of(o) for o in meshes if vis[o.name][idx]}
    moving_groups = {groups[n] for n in moving if n in groups}
    dyn = {}
    for n, g in groups.items():
        if g in moving_groups or n in moving:
            o = by_name[n]
            if mats[n][idx][2, 3] < -100:
                continue
            r = world(o, idx)
            if r is None:
                continue
            w, p = r
            dyn[n] = (w, BVHTree.FromPolygons([tuple(x) for x in w], p, epsilon=0.0), aabb(w), g)
    stat = [n for n in groups if n not in dyn and mats[n][idx][2, 3] > -100]
    sb = [(n, static_entry(by_name[n])) for n in stat]
    sb = [(n, e) for n, e in sb if e is not None]
    if sb:
        SLO = np.array([e[2][0] for _, e in sb])
        SHI = np.array([e[2][1] for _, e in sb])
    dn = list(dyn)
    for i, a in enumerate(dn):
        wa, ta, (la, ha), ga = dyn[a]
        # vs static (vectorized aabb prefilter)
        cand = np.nonzero(np.all(ha >= SLO, axis=1) & np.all(SHI >= la, axis=1))[0] if sb else []
        for j in cand:
            b, (wb, tb, (lb, hb)) = sb[j]
            inside = np.all(la >= lb) and np.all(ha <= hb)
            if not inside and not ta.overlap(tb):
                continue
            d = max(depth(wa, tb, (lb, hb)), depth(wb, ta, (la, ha)) if len(wb) < 4000 else 0)
            if d > MIN_DEPTH:
                hits.append((f, ga, a, groups[b], b, round(d, 3)))
        # vs other dynamic groups
        for b in dn[i + 1:]:
            wb, tb, (lb, hb), gb = dyn[b]
            if gb == ga:
                continue
            if np.any(ha < lb) or np.any(hb < la):
                continue
            if not ta.overlap(tb):
                continue
            d = max(depth(wa, tb, (lb, hb)), depth(wb, ta, (la, ha)))
            if d > MIN_DEPTH:
                hits.append((f, ga, a, gb, b, round(d, 3)))
    if idx % 5 == 0:
        print("frame", f, "hits so far", len(hits), flush=True)

# aggregate: (groupA, groupB-or-object) -> frame ranges, max depth, worst parts
agg = {}
for f, ga, a, gb, b, d in hits:
    k = (ga, gb if gb != b else b)
    e = agg.setdefault(k, {"frames": set(), "max": 0, "worst": ""})
    e["frames"].add(f)
    if d > e["max"]:
        e["max"], e["worst"] = d, f"{a} <-> {b} @ {f}"


def ranges(fs):
    fs = sorted(fs)
    out = []
    s = p = fs[0]
    for x in fs[1:]:
        if x - p > STEP:
            out.append((s, p))
            s = x
        p = x
    out.append((s, p))
    return out


res = []
for (ga, gb), e in sorted(agg.items(), key=lambda kv: -kv[1]["max"]):
    rr = ranges(e["frames"])
    res.append({"a": ga, "b": gb, "max": e["max"], "worst": e["worst"], "ranges": rr})
    print(f"{ga:22s} {gb:28s} max {e['max']:.3f}  {e['worst']:60s} {rr}")
if OUT:
    json.dump(res, open(OUT, "w"), indent=1)
