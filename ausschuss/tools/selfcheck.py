"""Second-level checks the plain collision test cannot see.

    blender -b ausschuss.blend -S S2_Workshop_Night -P tools/selfcheck.py -- [out.json]

1. limbs inside their own body (forearm/hand in torso, coat, head)
2. carried things inside their carrier (Funke in Hedda's coat, props in a hand) –
   grouping does NOT follow Child Of constraints here
3. foot skating: a sole on the ground that moves sideways faster than a slide
4. pops: a rig or camera that jumps within one camera shot
"""
import sys
import json
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else None
sc = bpy.context.scene
VL = sc.view_layers[0]
dg = VL.depsgraph
f0, f1 = sc.frame_start, sc.frame_end
HUMANS = ["Hedda", "Vendor", "OldMan", "Woman1", "Woman2", "Man2", "Man3", "Kid1", "Kid2", "Woman3"]
RIGS = HUMANS + ["Funke", "Erfasser", "Bello"]
LIMB = ("farm", "hand", "thumb", "cuff")
BODY = ("torso", "skirt", "head", "belt")
cams = [o for o in sc.objects if o.type == "CAMERA"]
markers = sorted((m.frame, m.camera.name if m.camera else "") for m in sc.timeline_markers)


def shot_at(f):
    cur = None
    for fr, name in markers:
        if fr <= f:
            cur = (fr, name)
    return cur


def goto(f):
    sc.frame_set(f)
    VL.update()


def W(o):
    return o.evaluated_get(dg).matrix_world


cache = {}


def local(o):
    if o.name not in cache:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        cache[o.name] = (np.array([v.co[:] for v in me.vertices]), [tuple(p.vertices) for p in me.polygons])
        oe.to_mesh_clear()
    return cache[o.name]


def world(o):
    v, p = local(o)
    m = np.array(W(o))
    return v @ m[:3, :3].T + m[:3, 3], p


def depth(pts, tree):
    best = 0.0
    if len(pts) > 120:
        pts = pts[np.linspace(0, len(pts) - 1, 120).astype(int)]
    for v in pts:
        r = tree.find_nearest(Vector(v), 0.4)
        if r[0] is not None and (Vector(v) - r[0]).dot(r[1]) < -1e-4:
            best = max(best, r[3])
    return best


rigs = [bpy.data.objects[n] for n in RIGS if n in bpy.data.objects]
issues = []
# ---------------------------------------------------------------- pops & skating (every frame)
prev = {}
prev_sole = {}
for f in range(f0, f1 + 1):
    goto(f)
    sh = shot_at(f)
    for r in rigs + cams:
        if r.type == "ARMATURE" and r.evaluated_get(dg).matrix_world.translation.z < -100:
            prev.pop(r.name, None)
            continue
        p = W(r).translation.copy()
        if r.name in prev:
            pf, pp, psh = prev[r.name]
            jump = (p - pp).length
            if psh == sh and jump > (0.45 if r.type == "ARMATURE" else 0.6):
                if r.type == "ARMATURE" or (sh and sh[1] == r.name):
                    issues.append({"kind": "pop", "f": f, "who": r.name, "d": round(jump, 2), "shot": sh[1] if sh else ""})
        prev[r.name] = (f, p, sh)
    for n in HUMANS:
        r = bpy.data.objects.get(n)
        if not r or W(r).translation.z < -100:
            continue
        soles = [(s, bpy.data.objects.get(f"{n}_{s}")) for s in ("soleL", "soleR")]
        soles = [(s, W(o).translation.copy()) for s, o in soles if o]
        if len(soles) == 2:
            s, p = min(soles, key=lambda x: x[1].z)  # the stance foot is the lower one
            k = f"{n}_{s}"
            if k in prev_sole and p.z < W(r).translation.z + 0.06:
                pp = prev_sole[k]
                v = Vector((p.x - pp.x, p.y - pp.y)).length * 24
                if v > 0.8:
                    issues.append({"kind": "skate", "f": f, "who": n, "part": s, "v": round(v, 2),
                                   "shot": sh[1] if sh else ""})
            prev_sole.clear() if False else None
            for s2, p2 in soles:
                prev_sole[f"{n}_{s2}"] = p2
# ---------------------------------------------------------------- self & carried intersection (every 3rd)
for f in range(f0, f1 + 1, 3):
    goto(f)
    sh = shot_at(f)
    for n in HUMANS:
        r = bpy.data.objects.get(n)
        if not r or W(r).translation.z < -100:
            continue
        kids = [c for c in r.children if c.type == "MESH" and not c.hide_render]
        body = [c for c in kids if any(c.name.endswith("_" + b) or c.name == f"{n}_{b}" for b in BODY)]
        limbs = [c for c in kids if any(k in c.name for k in LIMB)]
        trees = {}
        for b in body:
            w, p = world(b)
            trees[b.name] = BVHTree.FromPolygons([tuple(x) for x in w], p)
        for l in limbs:
            wl, _ = world(l)
            for bn, t in trees.items():
                if bn.endswith("head"):
                    continue
                d = depth(wl, t)
                if d > 0.05:
                    issues.append({"kind": "self", "f": f, "who": n, "a": l.name, "b": bn, "d": round(d, 3),
                                   "shot": sh[1] if sh else ""})
        # attached things (Child Of on this rig, active)
        for o in sc.objects:
            for c in o.constraints:
                if c.type == "CHILD_OF" and c.target == r and c.influence > 0.5 and not o.hide_render:
                    parts = [o] if o.type == "MESH" else [x for x in o.children_recursive if x.type == "MESH"]
                    for pt in parts:
                        if pt.hide_render:
                            continue
                        try:
                            wp, _ = world(pt)
                        except Exception:
                            continue
                        for bn, t in trees.items():
                            d = depth(wp, t)
                            if d > 0.04:
                                issues.append({"kind": "carried", "f": f, "who": n, "a": pt.name, "b": bn,
                                               "d": round(d, 3), "shot": sh[1] if sh else ""})
# ---------------------------------------------------------------- summary
from collections import defaultdict
agg = defaultdict(list)
for i in issues:
    key = (i["kind"], i["who"], i.get("a", i.get("part", "")), i.get("b", ""), i["shot"])
    agg[key].append(i)
rows = []
for k, v in agg.items():
    fs = [x["f"] for x in v]
    mx = max(x.get("d", x.get("v", 0)) for x in v)
    rows.append((k, min(fs), max(fs), len(v), mx))
rows.sort(key=lambda r: (r[0][0], -r[4]))
for (kind, who, a, b, shot), a0, a1, n, mx in rows:
    a = a.split("_", 1)[-1] if a.startswith(who) else a
    b = b.split("_", 1)[-1] if b.startswith(who) else b
    print(f"{kind:8s} {who:9s} {a:14s} {b:10s} {shot:22s} {a0}-{a1} n={n} max={mx}")
if OUT:
    json.dump(issues, open(OUT, "w"))
