"""Build the whole film 'AUSSCHUSS' into one .blend.

Usage:
    blender -b -P build.py -- [--out ausschuss.blend] [--only 1,2] [--final]

Scenes S1..S6 share one global timeline (frame numbers are absolute). Scene FILM
strings them together in the sequencer (plus the soundtrack if present).
"""
import sys
import os
import json
import math
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.path.insert(0, os.path.join(HERE, "seq"))
sys.path.insert(0, HERE)

import bpy
from mathutils import Vector
import core as C
import anim as A
import characters as CH
import props as P
import sets as S
import sets2 as S2
import rig as RG


def argv():
    a = sys.argv
    return a[a.index("--") + 1:] if "--" in a else []


class Ctx:
    pass


def make_decal(name, text, size, loc, rot, rig, bone, coll, color=(0.75, 0.03, 0.02)):
    ob = C.text(name, text, size=size, loc=loc, rot=rot, m=C.mat("stamp_red", color, rough=0.8, dirt=0.3, bump=0),
                coll=coll)
    frame = C.box(name + "_frame", (size * len(text) * 0.62, 0.002, size * 1.5), loc=loc, rot=rot,
                  m=C.mat("stamp_red"), bevel=0, coll=coll)
    frame.modifiers.new("wire", "WIREFRAME").thickness = size * 0.12
    RG.attach(ob, rig, bone)
    RG.attach(frame, rig, bone)
    return [ob, frame]


def build_characters(ctx):
    ch = ctx.chars
    C.set_coll(ch)
    ctx.hedda = CH.build_human("Hedda", ch)
    ctx.funke = CH.build_funke(ch)
    ctx.erf = CH.build_erfasser(ch)
    ctx.bello = CH.build_bello(ch)
    # villagers
    vill_specs = [
        ("Vendor", 1.0, 1.25, "man", {"coat": (0.45, 0.3, 0.2), "hat": (0.2, 0.2, 0.25)}),
        ("OldMan", 0.95, 1.1, "oldman", {"coat": (0.3, 0.32, 0.4), "hat": (0.55, 0.15, 0.1)}),
        ("Woman1", 0.95, 1.0, "woman", {"coat": (0.55, 0.4, 0.25), "coat2": (0.3, 0.2, 0.35),
                                         "scarf": (0.7, 0.5, 0.1)}),
        ("Woman2", 0.98, 1.15, "woman", {"coat": (0.3, 0.45, 0.4), "coat2": (0.5, 0.15, 0.1),
                                          "scarf": (0.2, 0.3, 0.6)}),
        ("Man2", 1.05, 0.95, "man", {"coat": (0.25, 0.3, 0.2), "hat": (0.4, 0.3, 0.2)}),
        ("Man3", 1.0, 1.1, "man", {"coat": (0.5, 0.45, 0.35), "hat": (0.15, 0.15, 0.15)}),
        ("Kid1", 0.62, 1.0, "kid", {"coat": (0.6, 0.2, 0.15), "trousers": (0.2, 0.25, 0.4)}),
        ("Kid2", 0.58, 1.0, "kid", {"coat": (0.2, 0.45, 0.6), "trousers": (0.3, 0.25, 0.2),
                                     "hair": (0.1, 0.07, 0.05)}),
        ("Woman3", 0.92, 1.05, "woman", {"coat": (0.45, 0.25, 0.3), "coat2": (0.2, 0.3, 0.25),
                                          "scarf": (0.6, 0.6, 0.55)}),
    ]
    ctx.vill = {}
    for i, (nm, h, g, st, pal) in enumerate(vill_specs):
        ctx.vill[nm] = CH.build_human(nm, ch, h=h, girth=g, style=st, palette=pal, seed=40 + i)
    ctx.actors = [ctx.hedda, ctx.funke, ctx.erf, ctx.bello] + list(ctx.vill.values())
    # decals (hidden until used)
    ctx.decal_bello = make_decal("decal_bello", "OBSOLETE", 0.045, (0.0, 0.0, 0.545), (0, 0, 0), ctx.bello.rig,
                                 "body", ch)
    ctx.decal_funke = make_decal("decal_funke", "OBSOLETE", 0.022, (0.0, -0.103, 0.215), (90, 0, 0),
                                 ctx.funke.rig, "body", ch)
    ctx.decal_hedda = make_decal("decal_hedda", "OBSOLETE", 0.03, (0.0, -0.165, 1.68), (80, 0, 0),
                                 ctx.hedda.rig, "head", ch)
    ctx.decal_erf = make_decal("decal_erf", "OBSOLETE", 0.04, (0.0, -0.145, 2.04), (90, 0, 0), ctx.erf.rig,
                               "head", ch)
    for d in ctx.decal_bello + ctx.decal_funke + ctx.decal_hedda + ctx.decal_erf:
        A.hide(d, 0, True)
    # Erfasser's red scanner beam (spot light on the head)
    beam = P.point_light("erf_beam", (0, -0.2, 1.95), 0, (1.0, 0.05, 0.02), 0.02, coll=ch, kind="SPOT", spot=25,
                         rot=(80, 0, 0))
    RG.attach(beam, ctx.erf.rig, "head")
    ctx.erf_beam = beam
    # Funke's eye light (small warm point light that makes the eye glow onto surroundings)
    fl = P.point_light("funke_eyelight", (0, -0.16, 0.462), 0, (1.0, 0.55, 0.15), 0.02, coll=ch)
    RG.attach(fl, ctx.funke.rig, "head")
    ctx.funke_light = fl


def offstage_all(ctx, F, keep=()):
    for a in ctx.actors:
        if a not in keep:
            a.offstage(F)


def new_seq_scene(ctx, idx, name, f0, f1, world, colls):
    sc = bpy.data.scenes.new(name)
    sc.frame_start = f0
    sc.frame_end = f1
    S.setup_render(sc, preview=not ctx.final)
    sc.world = world
    for c in colls:
        sc.collection.children.link(c)
    lights = C.collection(name + "_lights")
    sc.collection.children.link(lights)
    cams = C.collection(name + "_cams")
    sc.collection.children.link(cams)
    ctx.seq[idx] = {"scene": sc, "lights": lights, "cams": cams, "f0": f0, "f1": f1}
    return sc, lights, cams


def set_end(ctx, idx, f1):
    ctx.seq[idx]["f1"] = f1
    ctx.seq[idx]["scene"].frame_end = f1


def shot(ctx, idx, name, f0, keys, lens=35, dof=None):
    """keys: list of (frame, loc, target[, lens]). Adds marker binding at f0."""
    s = ctx.seq[idx]
    cam = A.camera(name, s["cams"], lens=lens)
    for k in keys:
        fr, loc, tgt = k[0], k[1], k[2]
        A.cam_key(cam, fr, loc, tgt, k[3] if len(k) > 3 else lens)
    mk = s["scene"].timeline_markers.new(name, frame=f0)
    mk.camera = cam
    if s["scene"].camera is None:
        s["scene"].camera = cam
    if dof:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = dof[1]
        cam.data.dof.focus_distance = dof[0]
    return cam


def main():
    args = argv()
    out = os.path.join(HERE, "ausschuss.blend")
    only = None
    final = "--final" in args
    if "--out" in args:
        out = args[args.index("--out") + 1]
    if "--only" in args:
        only = [int(x) for x in args[args.index("--only") + 1].split(",")]
    t0 = time.time()
    C.reset()
    base = bpy.context.scene
    base.name = "_BUILD"
    ctx = Ctx()
    ctx.final = final
    ctx.seq = {}
    ctx.lib = C.collection("Lib")
    base.collection.children.link(ctx.lib)
    P.mats()
    P.scrap_library(ctx.lib)
    ctx.chars = C.collection("Characters")
    base.collection.children.link(ctx.chars)
    build_characters(ctx)
    print("characters", round(time.time() - t0, 1))
    ctx.c_scrap = C.collection("Scrapyard"); base.collection.children.link(ctx.c_scrap)
    ctx.scrap = S.build_scrapyard(ctx.c_scrap, ctx.lib)
    ctx.c_city = ctx.scrap["city"]
    base.collection.children.link(ctx.c_city)
    ctx.c_ws = C.collection("Workshop"); base.collection.children.link(ctx.c_ws)
    ctx.ws = S2.build_workshop(ctx.c_ws)
    ctx.c_vil = C.collection("Village"); base.collection.children.link(ctx.c_vil)
    ctx.vil = S2.build_village(ctx.c_vil)
    ctx.c_dep = C.collection("Depot"); base.collection.children.link(ctx.c_dep)
    ctx.dep = S2.build_depot(ctx.c_dep)
    ctx.c_props = C.collection("Props"); base.collection.children.link(ctx.c_props)
    C.set_coll(ctx.c_props)
    ctx.truck = P.reclamation_truck("truck", (0, 0, -300), 0, ctx.c_props)
    print("sets", round(time.time() - t0, 1))
    import importlib
    F = 1
    ctx.bounds = {}
    for i in range(1, 7):
        if not os.path.exists(os.path.join(HERE, "seq", f"seq{i}.py")):
            break
        mod = importlib.import_module(f"seq{i}")
        F_end = mod.build(ctx, F)
        ctx.bounds[i] = (F, F_end)
        print(f"seq{i}", F, F_end, round(time.time() - t0, 1))
        F = F_end + 1
    total_end = F - 1
    # FILM scene with sequencer
    film = bpy.data.scenes.new("FILM")
    film.frame_start = 1
    film.frame_end = total_end
    S.setup_render(film, preview=not final)
    film.use_nodes = False
    se = film.sequence_editor_create()
    for i in sorted(ctx.seq):
        s = ctx.seq[i]
        st = se.sequences.new_scene(f"S{i}", s["scene"], channel=1, frame_start=s["f0"])
        st.frame_final_start = s["f0"]
        st.frame_final_end = s["f1"] + 1
    snd = os.path.join(HERE, "sound", "soundtrack.wav")
    if os.path.exists(snd):
        se.sequences.new_sound("soundtrack", snd, channel=2, frame_start=1)
    film.render.image_settings.file_format = "FFMPEG"
    film.render.ffmpeg.format = "MPEG4"
    film.render.ffmpeg.codec = "H264"
    film.render.ffmpeg.audio_codec = "AAC"
    film.render.filepath = "//render/ausschuss_"
    for i in sorted(ctx.seq):
        sc = ctx.seq[i]["scene"]
        sc.render.filepath = f"//render/S{i}/f_"
    # events for the sound pipeline
    with open(os.path.join(HERE, "sound", "events.json"), "w") as fh:
        json.dump({"fps": C.FPS, "end": total_end, "bounds": ctx.bounds, "events": A.EVENTS}, fh, indent=0)
    if bpy.context.window:
        bpy.context.window.scene = film
    # remove build scene (constraints/inverses are baked into data)
    bpy.data.scenes.remove(base)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("saved", out, "frames", total_end, round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
