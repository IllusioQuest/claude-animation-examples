import sys, bpy, math, time, os
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, sets as S, sets2 as S2, props as P, characters as CH
C.reset()
sc = bpy.context.scene
lib = C.collection("Lib"); sc.collection.children.link(lib)
P.scrap_library(lib)
CH.build_bello(C.collection("tmp"))  # creates Bello materials
which = os.environ["SET"]
coll = C.collection(which); sc.collection.children.link(coll)
S.setup_render(sc)
sc.render.resolution_percentage=40
sc.eevee.taa_render_samples=4
lc = C.collection("L"); sc.collection.children.link(lc)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
from mathutils import Vector
if which=="ws":
    d=S2.build_workshop(coll); O=S2.WORKSHOP
    sc.world=S.world("w", (0.02,0.03,0.06),(0.01,0.01,0.03), strength=0.5)
    cam.location=O+Vector((0.5,-2.3,1.6)); tgt=O+Vector((0,1.5,1.1)); cam.data.lens=18
elif which=="vil":
    d=S2.build_village(coll); O=S2.VILLAGE
    sc.world=S.world("w", (0.9,0.75,0.55),(0.35,0.5,0.75), strength=1.0)
    S.sun("sun",(50,0,30),4.0,(1,0.9,0.75),lc)
    cam.location=O+Vector((-2,-16,3.5)); tgt=O+Vector((0,2,1.5)); cam.data.lens=24
elif which=="dep":
    d=S2.build_depot(coll); O=S2.DEPOT
    sc.world=S.world("w", (0.05,0.06,0.1),(0.01,0.01,0.03), strength=0.5)
    cam.location=O+Vector((-6,-14,2)); tgt=O+Vector((0,4,4)); cam.data.lens=24
elif which=="hall":
    d=S2.build_depot(coll); O=S2.HALL
    sc.world=S.world("w", (0.05,0.06,0.1),(0.01,0.01,0.03), strength=0.3)
    cam.location=O+Vector((-16,-9,4)); tgt=O+Vector((6,0,3)); cam.data.lens=20
cam.rotation_euler=C.look_at_rot(cam.location,tgt)
sc.render.filepath=sys.argv[-1]
bpy.ops.render.render(write_still=True)
