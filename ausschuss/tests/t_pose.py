import sys, bpy, math, json
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, characters as CH, anim as A
C.reset()
sc = bpy.context.scene
coll = C.collection("chars"); sc.collection.children.link(coll)
variants = json.loads(sys.argv[-2])
acts=[]
for i,(pose,face) in enumerate(variants):
    h = CH.build_human("H%d"%i, coll); h.rig.location=(i*0.9,0,0)
    h.pose(1,"stand"); 
    if isinstance(pose,str): h.pose(1,pose)
    else: h.pose(1,pose)
    h.face(1,face)
sc.frame_set(1)
n=len(variants)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cx=(n-1)*0.45
cam.location=(cx+0.6,-1.2-n*0.75,1.35); cam.rotation_euler=C.look_at_rot(cam.location,(cx,0,1.05)); sc.camera=cam; cam.data.lens=40
l = bpy.data.objects.new("sun", bpy.data.lights.new("sun","SUN")); sc.collection.objects.link(l); l.rotation_euler=(0.9,0.2,-0.6); l.data.energy=3.5
w = bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.35,0.4,0.5,1)
sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x=960; sc.render.resolution_y=540
sc.eevee.taa_render_samples=8
sc.render.filepath=sys.argv[-1]
bpy.ops.render.render(write_still=True)
