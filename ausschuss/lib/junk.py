"""Detailed junk templates for the scrap library: each item is one mesh (multi-material) built with bmesh,
so that hundreds of instances stay cheap. Replaces the plain primitive templates of props.scrap_library."""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix, Euler
import core as C

V = Vector


class Kit:
    def __init__(self, name, mats):
        self.name = name
        self.bm = bmesh.new()
        self.mats = mats

    def _place(self, geom_verts, loc, rot, mi, smooth=False):
        m = Matrix.Translation(V(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=m, verts=geom_verts)
        faces = {f for v in geom_verts for f in v.link_faces}
        for f in faces:
            f.material_index = mi
            f.smooth = smooth

    def box(self, size, loc=(0, 0, 0), rot=(0, 0, 0), mi=0, bevel=0.0):
        tb = bmesh.new()
        bmesh.ops.create_cube(tb, size=1.0)
        bmesh.ops.scale(tb, vec=V(size), verts=tb.verts)
        if bevel > 0:
            bmesh.ops.bevel(tb, geom=list(tb.edges), offset=bevel, segments=2, affect="EDGES")
        me = bpy.data.meshes.new("_tmp")
        tb.to_mesh(me)
        tb.free()
        n0 = len(self.bm.verts)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        self.bm.verts.ensure_lookup_table()
        vs = [self.bm.verts[i] for i in range(n0, len(self.bm.verts))]
        self._place(vs, loc, rot, mi, smooth=bevel > 0)

    def cyl(self, r, h, loc=(0, 0, 0), rot=(0, 0, 0), mi=0, segs=20, r2=None, smooth=True):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                                    radius2=r if r2 is None else r2, depth=h)
        self._place(res["verts"], loc, rot, mi, smooth)

    def torus(self, R, r, loc=(0, 0, 0), rot=(0, 0, 0), mi=0, seg=24, segr=8):
        vs = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            for j in range(segr):
                b = 2 * math.pi * j / segr
                vs.append(self.bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a),
                                             r * math.sin(b))))
        for i in range(seg):
            for j in range(segr):
                a0 = vs[i * segr + j]
                a1 = vs[((i + 1) % seg) * segr + j]
                a2 = vs[((i + 1) % seg) * segr + (j + 1) % segr]
                a3 = vs[i * segr + (j + 1) % segr]
                self.bm.faces.new((a0, a1, a2, a3))
        self._place(vs, loc, rot, mi, True)

    def sphere(self, r, loc=(0, 0, 0), scale=(1, 1, 1), mi=0, segs=12, rings=8):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r)
        bmesh.ops.scale(self.bm, vec=V(scale), verts=res["verts"])
        self._place(res["verts"], loc, (0, 0, 0), mi, True)

    def wave_sheet(self, w, h, waves=10, depth=0.03, loc=(0, 0, 0), rot=(0, 0, 0), mi=0):
        nx = waves * 4
        vs = []
        for i in range(nx + 1):
            x = -w / 2 + w * i / nx
            y = math.sin(i / nx * waves * 2 * math.pi) * depth
            vs.append((self.bm.verts.new((x, y, -h / 2)), self.bm.verts.new((x, y, h / 2))))
        for i in range(nx):
            self.bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
        flat = [v for p in vs for v in p]
        self._place(flat, loc, rot, mi, True)

    def done(self, coll):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        C.link(ob, coll)
        return ob


def build_library(coll, m):
    M = C.mat
    lib = {}
    chrome = m["chrome"]
    dark = m["dark"]
    rubber = m["rubber"]

    def barrel(name, body):
        k = Kit(name, [body, dark])
        k.cyl(0.3, 0.88, segs=28)
        for z in (-0.22, 0.22):
            k.torus(0.302, 0.014, loc=(0, 0, z), seg=28, segr=6)
        for z in (-0.44, 0.44):
            k.torus(0.29, 0.016, loc=(0, 0, z), seg=28, segr=6)
        k.cyl(0.04, 0.03, loc=(0.16, 0, 0.445), mi=1, segs=10)
        k.cyl(0.03, 0.02, loc=(-0.15, 0.06, 0.445), mi=1, segs=10)
        return k.done(coll)
    lib["barrel_r"] = barrel("lib_barrel_r", m["paint_red"])
    lib["barrel_b"] = barrel("lib_barrel_b", m["paint_blue"])
    lib["barrel_rust"] = barrel("lib_barrel_rust", m["rust"])
    # tyre with tread blocks and a rusty rim
    k = Kit("lib_tire", [rubber, m["rust"]])
    k.torus(0.32, 0.12, seg=36, segr=12)
    for i in range(36):
        a = 2 * math.pi * i / 36
        k.box((0.05, 0.16, 0.03), loc=(math.cos(a) * 0.44, math.sin(a) * 0.44, 0),
              rot=(0, 90, math.degrees(a)), mi=0)
    k.cyl(0.22, 0.12, mi=1, segs=24)
    lib["tire"] = k.done(coll)
    # fridge: rounded body, door seam, freezer door, chrome handles, little feet
    k = Kit("lib_fridge", [m["paint_white"], chrome, M("seam_dark", (0.03, 0.025, 0.02), rough=0.9, dirt=0, bump=0)])
    k.box((0.7, 0.65, 1.6), bevel=0.05)
    k.box((0.66, 0.012, 0.012), loc=(0, -0.326, 0.28), mi=2)
    k.box((0.05, 0.04, 0.4), loc=(0.27, -0.35, 0.0), mi=1, bevel=0.012)
    k.box((0.05, 0.04, 0.2), loc=(0.27, -0.35, 0.52), mi=1, bevel=0.012)
    for sx in (-0.28, 0.28):
        for sy in (-0.25, 0.25):
            k.cyl(0.025, 0.05, loc=(sx, sy, -0.82), mi=1, segs=8)
    lib["fridge"] = k.done(coll)
    # crate: slatted boards on a frame
    k = Kit("lib_crate", [m["wood"], M("wood_dark", (0.2, 0.12, 0.06), rough=0.85, dirt=0.5, bump=0.3, scale=6)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box((0.05, 0.05, 0.5), loc=(0.275 * sx, 0.275 * sy, 0), mi=1)
    for face in range(4):
        rz = face * 90
        for j in range(3):
            z = -0.17 + j * 0.17
            ax = Euler((0, 0, math.radians(rz))).to_matrix()
            p = ax @ V((0, -0.29, z))
            k.box((0.56, 0.02, 0.13), loc=p, rot=(0, 0, rz), mi=0)
    k.box((0.58, 0.58, 0.02), loc=(0, 0, 0.24), mi=0)
    lib["crate"] = k.done(coll)
    # corrugated sheets
    k = Kit("lib_panel", [m["corr1"]])
    k.wave_sheet(1.6, 1.0, waves=9, depth=0.025)
    lib["panel"] = k.done(coll)
    k = Kit("lib_panel2", [m["paint_green"]])
    k.wave_sheet(1.2, 0.8, waves=7, depth=0.02)
    lib["panel2"] = k.done(coll)
    # pipe with flanges
    k = Kit("lib_pipe", [m["rust"], m["pipe"]])
    k.cyl(0.08, 2.4, segs=14)
    for z in (-1.18, 1.18):
        k.cyl(0.13, 0.04, loc=(0, 0, z), mi=1, segs=14)
    lib["pipe"] = k.done(coll)
    # I-beam
    k = Kit("lib_beam", [m["rust"]])
    k.box((0.14, 0.02, 3.0))
    for sx in (-0.075, 0.075):
        k.box((0.02, 0.16, 3.0), loc=(sx, 0, 0))
    lib["beam"] = k.done(coll)
    # cable spool lying around (replaces the plain drum)
    k = Kit("lib_drum", [m["wood"], m["steel"]])
    for z in (-0.13, 0.13):
        k.cyl(0.45, 0.04, loc=(0, 0, z), segs=28)
    k.cyl(0.2, 0.24, mi=1, segs=20)
    k.cyl(0.06, 0.32, mi=1, segs=10)
    lib["drum"] = k.done(coll)
    # car door with window frame, handle and a mirror
    k = Kit("lib_cardoor", [m["paint_blue"], chrome, M("glass_dark", (0.02, 0.03, 0.03), rough=0.1)])
    k.box((1.1, 0.1, 0.55), loc=(0, 0, -0.12), bevel=0.04)
    for x in (-0.53, 0.53):
        k.box((0.04, 0.05, 0.38), loc=(x * 0.9, 0, 0.33), rot=(0, -12 if x < 0 else 0, 0), mi=1)
    k.box((1.0, 0.05, 0.035), loc=(0, 0, 0.5), mi=1)
    k.box((0.9, 0.012, 0.32), loc=(0.02, 0, 0.33), mi=2)
    k.box((0.14, 0.04, 0.03), loc=(0.35, -0.065, 0.04), mi=1, bevel=0.01)
    lib["car_door"] = k.done(coll)
    # old TV: cabinet, inset screen frame, knobs, rabbit-ear antenna, legs
    k = Kit("lib_tv", [m["plastic"], dark, chrome, M("tv_wood", (0.3, 0.17, 0.08), rough=0.6, dirt=0.4, bump=0.2,
                                                       scale=6)])
    k.box((0.6, 0.5, 0.48), mi=3, bevel=0.04)
    k.box((0.5, 0.02, 0.38), loc=(-0.03, -0.25, 0.01), mi=1, bevel=0.02)
    for i in range(2):
        k.cyl(0.02, 0.03, loc=(0.26, -0.255, 0.1 - i * 0.1), rot=(90, 0, 0), mi=2, segs=10)
    for sx in (-1, 1):
        k.cyl(0.004, 0.45, loc=(0.1 * sx, 0.05, 0.42), rot=(0, 25 * sx, 0), mi=2, segs=5)
        k.cyl(0.012, 0.15, loc=(0.24 * sx, 0, -0.31), rot=(0, 8 * sx, 0), mi=1, segs=6)
    lib["tv"] = k.done(coll)
    lib["tv_screen"] = C.box("lib_tv_screen", (0.42, 0.02, 0.3), m=m["screen"], bevel=0.04)
    # washing machine with porthole
    k = Kit("lib_washer", [m["paint_white"], chrome, M("glass_dark", (0.02, 0.03, 0.03), rough=0.1), dark])
    k.box((0.6, 0.6, 0.85), bevel=0.03)
    k.torus(0.17, 0.025, loc=(0, -0.3, -0.05), rot=(90, 0, 0), mi=1, seg=28, segr=6)
    k.cyl(0.16, 0.02, loc=(0, -0.3, -0.05), rot=(90, 0, 0), mi=2, segs=24)
    k.box((0.56, 0.02, 0.12), loc=(0, -0.3, 0.33), mi=3)
    for i in range(3):
        k.cyl(0.02, 0.02, loc=(-0.15 + i * 0.12, -0.315, 0.33), rot=(90, 0, 0), mi=1, segs=10)
    lib["washer"] = k.done(coll)
    # robot arm: segments, joints, a claw
    k = Kit("lib_rarm", [m["paint_yel"], dark, chrome])
    k.cyl(0.06, 0.55, loc=(0, 0, -0.32), segs=14)
    k.sphere(0.08, loc=(0, 0, 0), mi=1)
    k.cyl(0.05, 0.5, loc=(0, 0, 0.28), segs=14)
    k.sphere(0.06, loc=(0, 0, 0.55), mi=1)
    for sx in (-1, 1):
        k.box((0.02, 0.04, 0.14), loc=(0.04 * sx, 0, 0.66), rot=(0, -15 * sx, 0), mi=2)
    lib["robot_arm"] = k.done(coll)
    # gear with real teeth and spokes
    k = Kit("lib_gear", [m["rust"]])
    k.cyl(0.3, 0.08, segs=32)
    for i in range(18):
        a = 2 * math.pi * i / 18
        k.box((0.07, 0.08, 0.08), loc=(math.cos(a) * 0.33, math.sin(a) * 0.33, 0), rot=(0, 0, math.degrees(a)))
    lib["gear"] = k.done(coll)
    # enamel sign with a stripe and a post stub
    k = Kit("lib_sign", [m["paint_red"], m["paint_white"], m["steel"]])
    k.box((1.4, 0.04, 0.6), bevel=0.01)
    k.box((1.2, 0.045, 0.12), loc=(0, 0, 0), mi=1)
    k.cyl(0.03, 0.7, loc=(0, 0.04, -0.6), mi=2, segs=8)
    lib["sign"] = k.done(coll)
    return lib
