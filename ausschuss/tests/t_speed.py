import bpy, sys, time
sc=bpy.context.scene
sc.eevee.taa_render_samples=int(sys.argv[-2])
sc.frame_start=1; sc.frame_end=4
sc.render.filepath=sys.argv[-1]
t=time.time()
class T: pass
def pre(s, *a): T.t=time.time()
def post(s, *a): print("FRAME", s.frame_current, round(time.time()-T.t,2))
bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
bpy.ops.render.render(animation=True)
print("total", time.time()-t)
