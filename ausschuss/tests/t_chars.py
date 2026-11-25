import sys, bpy, math
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, characters as CH, anim as A
C.reset()
sc = bpy.context.scene
coll = C.collection("chars"); sc.collection.children.link(coll)
h = CH.build_human("Hedda", coll)
f = CH.build_funke(coll); f.rig.location=(0.7,0,0)
e = CH.build_erfasser(coll); e.rig.location=(-1.0,0,0)
b = CH.build_bello(coll); b.rig.location=(1.4,0,0); b.rig.rotation_euler.z=math.radians(40)
v1 = CH.build_human("Vill1", coll, h=1.05, girth=1.2, style="man", seed=3, palette={"coat":(0.5,0.2,0.15)}); v1.rig.location=(-2.0,0.5,0)
v2 = CH.build_human("Vill2", coll, h=0.95, style="woman", seed=4, palette={"coat":(0.6,0.5,0.3),"scarf":(0.2,0.4,0.6)}); v2.rig.location=(-2.7,0.5,0)
v3 = CH.build_human("Kid", coll, h=0.6, style="kid", seed=5, palette={"coat":(0.2,0.5,0.3)}); v3.rig.location=(2.2,0,0)
ch = CH.build_chicken(coll, "chick", loc=(2.6,-0.3,0))
CH.build_pigeon_drone(coll, "pig", (0.3,-0.5,0))
CH.build_cat(coll, "cat", (-0.5,-0.6,0))
pose = sys.argv[-2]
if pose != "rest":
    h.pose(1, pose); f.pose(1, "hands_hips" if pose=="hands_hips" else "happy"); h.face(1,"happy")
sc.frame_set(1)
ground = C.box("g",(20,20,0.1),loc=(0,0,-0.05),m=C.mat("ground",(0.3,0.25,0.2)))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
import os
if os.environ.get("CLOSE"): cam.location=(0.35,-1.6,1.2); cam.rotation_euler=C.look_at_rot(cam.location,(0.3,0,0.9))
else: cam.location=(0.2,-5.5,1.6); cam.rotation_euler=C.look_at_rot(cam.location,(0,0,0.85))
sc.camera=cam
cam.data.lens=32
l = bpy.data.objects.new("sun", bpy.data.lights.new("sun","SUN")); sc.collection.objects.link(l); l.rotation_euler=(0.9,0.2,-0.6); l.data.energy=3.5
w = bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.35,0.4,0.5,1)
sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x=960; sc.render.resolution_y=540
sc.eevee.taa_render_samples=16
sc.render.filepath=sys.argv[-1]
bpy.ops.render.render(write_still=True)
