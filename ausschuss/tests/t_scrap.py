import sys, bpy, math, time, os
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, sets as S, props as P, characters as CH
t0=time.time()
C.reset()
sc = bpy.context.scene
lib = C.collection("Lib"); sc.collection.children.link(lib)
coll = C.collection("Scrapyard"); sc.collection.children.link(coll)
d = S.build_scrapyard(coll, lib)
sc.collection.children.link(d["city"])
ch = C.collection("Chars"); sc.collection.children.link(ch)
h = CH.build_human("Hedda", ch); h.rig.location=(-4,-1,0); h.rig.rotation_euler.z=math.radians(-30)
tr = P.reclamation_truck("truck", (4, 10, 0), math.radians(90), coll)
print("build", time.time()-t0)
S.setup_render(sc)
sc.world = S.world("w1", horizon=(1.0,0.45,0.25), zenith=(0.08,0.12,0.3), ground=(0.05,0.04,0.04), strength=1.0,
   fog_density=float(os.environ.get("FOG","0.0")), fog_color=(0.75,0.7,0.8), sun_dir=(0,1,0.05), sun_glow=3.0)
lc = C.collection("L"); sc.collection.children.link(lc)
if float(os.environ.get("BOX","0"))>0: S.fog_box("fog", lc, (0,100,0), (500,600,80), float(os.environ["BOX"]), (0.8,0.65,0.6))
S.sun("sun", (88,0,180+10), 3.0, (1.0,0.6,0.35), lc)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
import os
v = os.environ.get("V","a")
if v=="a": cam.location=(-10,-22,3.0); tgt=(2,10,3.0); cam.data.lens=28
elif v=="b": cam.location=(-7,-12,1.6); tgt=(-15,-3,1.5); cam.data.lens=35
cam.rotation_euler=C.look_at_rot(cam.location,tgt); sc.camera=cam
sc.render.filepath=sys.argv[-1]
t1=time.time()
bpy.ops.render.render(write_still=True)
print("render", time.time()-t1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/-home-user-claude-animation-examples/33a5c91d-89d0-59a9-a8d6-06f837470fdf/scratchpad/scrap.blend")
