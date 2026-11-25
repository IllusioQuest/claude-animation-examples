import sys, bpy
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C
C.reset()
sc = bpy.context.scene
m = C.mat("rusty", (0.3,0.4,0.5), metal=0.8, rust=0.6, rough=0.4)
C.box("b", (1,1,1), m=m, loc=(0,0,0.5))
C.cyl("c", 0.4, 1, loc=(1.5,0,0.5), m=C.mat("paint",(0.8,0.2,0.1), rust=0.3))
C.sphere("s", 0.5, loc=(-1.5,0,0.5), m=C.mat("cloth",(0.3,0.5,0.2), dirt=0.5, rough=0.9))
C.torus("t", 0.4, 0.15, loc=(0,1.5,0.3), m=C.mat("rub",(0.05,0.05,0.05)))
C.text("tx","VERALTET", loc=(0,-1,1.5), m=C.emission("e",(1,0.1,0.05),3))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.location=(0,-6,3); cam.rotation_euler=C.look_at_rot((0,-6,3),(0,0,0.5)); sc.camera=cam
l = bpy.data.objects.new("sun", bpy.data.lights.new("sun","SUN")); sc.collection.objects.link(l); l.rotation_euler=(0.8,0.2,0.5); l.data.energy=3
w = bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.2,0.25,0.3,1)
sc.render.engine="BLENDER_EEVEE_NEXT"; sc.render.resolution_x=480; sc.render.resolution_y=270
sc.eevee.taa_render_samples=16
sc.render.filepath=sys.argv[-1]
bpy.ops.render.render(write_still=True)
