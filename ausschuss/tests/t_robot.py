import sys, bpy, math, json
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, characters as CH, anim as A
C.reset()
sc = bpy.context.scene
coll = C.collection("chars"); sc.collection.children.link(coll)
variants = json.loads(sys.argv[-2])
for i,pose in enumerate(variants):
    f = CH.build_funke(coll, "F%d"%i); f.rig.location=(i*0.35,0,0)
    f.pose(1,"stand"); f.pose(1,pose)
e = CH.build_erfasser(coll); e.rig.location=(-0.7,0.6,0); e.pose(1,"stamp_up")
b = CH.build_bello(coll); b.rig.location=(len(variants)*0.35+0.3,0.3,0); b.rig.rotation_euler.z=math.radians(30); b.pose(1,"sniff")
sc.frame_set(1)
n=len(variants)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cx=(n-1)*0.175
cam.location=(cx,-2.3,0.75); cam.rotation_euler=C.look_at_rot(cam.location,(cx,0,0.45)); sc.camera=cam; cam.data.lens=40
l = bpy.data.objects.new("sun", bpy.data.lights.new("sun","SUN")); sc.collection.objects.link(l); l.rotation_euler=(0.9,0.2,-0.6); l.data.energy=3.5
w = bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.35,0.4,0.5,1)
sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x=960; sc.render.resolution_y=540
sc.eevee.taa_render_samples=8
sc.render.filepath=sys.argv[-1]
bpy.ops.render.render(write_still=True)
