import bpy, sys, time
sc=bpy.context.scene
mode=sys.argv[-1]
sc.frame_start=1; sc.frame_end=2
sc.eevee.taa_render_samples=4
if "nofog" in mode:
    bpy.data.objects["fog"].hide_render=True
if "noshadow" in mode:
    sc.eevee.use_shadows=False
if "nocomp" in mode:
    sc.use_nodes=False
if "sres" in mode:
    sc.eevee.shadow_resolution_scale=0.25
    sc.eevee.shadow_pool_size="16"
if "s1" in mode:
    sc.eevee.taa_render_samples=1
if "small" in mode:
    sc.render.resolution_percentage=15
sc.render.filepath="/tmp/claude-0/-home-user-claude-animation-examples/33a5c91d-89d0-59a9-a8d6-06f837470fdf/scratchpad/spd_"
class T: pass
def pre(s, *a): T.t=time.time()
def post(s, *a): print("FRAME", mode, s.frame_current, round(time.time()-T.t,2))
bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
bpy.ops.render.render(animation=True)
