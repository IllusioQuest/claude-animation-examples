import sys, bpy
sys.path.insert(0, "/home/user/claude-animation-examples/ausschuss/lib")
import core as C, rig as RG
C.reset()
r = RG.build_armature("T", [
 ("root",(0,0,0),(0,0.3,0),None,0),
 ("up",(0,0,1),(0,0,2),"root",0),
 ("down",(0.2,0,1.4),(0.2,0,1.0),"root",0),
 ("fwd",(0,0,0.1),(0,-0.3,0.1),"root",0),
 ("side",(0,0,1),(0.3,0,1),"root",0),
])
for b in r.data.bones:
    m=b.matrix_local
    print(b.name, "X",[round(v,2) for v in m.col[0][:3]], "Y",[round(v,2) for v in m.col[1][:3]], "Z",[round(v,2) for v in m.col[2][:3]])
