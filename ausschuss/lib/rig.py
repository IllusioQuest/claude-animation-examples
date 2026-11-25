"""Puppet rigs: armatures with rigid, bone-parented mesh parts."""
import bpy
import math
from mathutils import Vector, Matrix
import core as C


def build_armature(name, bones, coll=None):
    """bones: list of (name, head, tail, parent or None, roll_deg)."""
    arm = bpy.data.armatures.new(name + "_arm")
    arm.display_type = "STICK"
    ob = bpy.data.objects.new(name, arm)
    C.link(ob, coll)
    vl = bpy.context.view_layer
    temp = False
    if ob.name not in bpy.context.scene.objects:
        bpy.context.scene.collection.objects.link(ob)
        temp = True
    vl.update()
    vl.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    for (bn, h, t, par, roll) in bones:
        b = eb.new(bn)
        b.head = h
        b.tail = t
        b.roll = math.radians(roll)
        if par:
            b.parent = eb[par]
            b.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    if temp:
        bpy.context.scene.collection.objects.unlink(ob)
    for pb in ob.pose.bones:
        pb.rotation_mode = "XYZ"
    return ob


def attach(ob, rig, bone):
    """Parent ob to a bone keeping its current (rest) world transform."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    pb = rig.pose.bones[bone]
    # bone-parent space = armature matrix * bone pose matrix * translation to tail
    bone_mat = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    ob.matrix_parent_inverse = bone_mat.inverted()
    ob.matrix_basis = mw
    return ob


class Parts:
    """Collects parts per bone and attaches them in one go."""

    def __init__(self, rig_name, coll):
        self.rig_name = rig_name
        self.coll = coll
        self.items = []

    def add(self, bone, ob):
        self.items.append((bone, ob))
        return ob

    def attach_all(self, rig):
        bpy.context.view_layer.update()
        for bone, ob in self.items:
            if ob.parent is None:
                attach(ob, rig, bone)
