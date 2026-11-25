"""Build the soundtrack for AUSSCHUSS from sound/events.json.

  python3 sound/make_sound.py            -> sound/soundtrack.wav (+ stems)

Score: MIDI (General MIDI orchestra in the spirit of 1930s–50s cartoon scores, with
mickey-mousing on events) rendered by fluidsynth. Foley: synthesised (sfx.py).
"""
import json
import os
import subprocess
import sys
import numpy as np
import mido
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as X

SR = X.SR
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

D = json.load(open(os.path.join(HERE, "events.json")))
FPS = D["fps"]
EVENTS = D["events"]
BOUNDS = {int(k): v for k, v in D["bounds"].items()}
TOTAL = D["end"] / FPS + 1.0


def s(fr):
    return (fr - 1) / FPS


def seq_t(i):
    return s(BOUNDS[i][0]), s(BOUNDS[i][1] + 1)


def ev(kind, seq=None, who=None):
    out = []
    for e in EVENTS:
        if e["kind"] != kind:
            continue
        if seq is not None and e.get("seq") != seq:
            continue
        if who is not None and e.get("who") != who:
            continue
        lo, hi = BOUNDS[e.get("seq", 1)]
        if not (lo <= e["frame"] <= hi):
            continue
        out.append(e)
    return out


def ts(kind, seq=None, **kw):
    return [s(e["frame"]) for e in ev(kind, seq, **kw)]


def first(kind, seq, default=None):
    t = ts(kind, seq)
    return t[0] if t else default


# =========================================================================== score
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def N(name):
    if isinstance(name, int):
        return name
    acc = 0
    base = name[0]
    rest = name[1:]
    while rest and rest[0] in "#b":
        acc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + NOTE[base] + acc


GM = {"strings": (48, 0), "pizz": (45, 1), "clarinet": (71, 2), "bassoon": (70, 3), "oboe": (68, 4),
      "flute": (73, 5), "mute_tp": (59, 6), "trombone": (57, 7), "tuba": (58, 8), "drums": (0, 9),
      "celesta": (8, 10), "glock": (9, 11), "xylo": (13, 12), "harp": (46, 13), "timpani": (47, 14),
      "horn": (60, 15)}
GM2 = {"strings_b": (49, 0), "musicbox": (10, 1), "harmonica": (22, 2), "piccolo": (72, 3), "brass": (61, 4),
       "trumpet": (56, 5), "vibes": (11, 6), "tremolo": (44, 7), "drums": (0, 9)}
BAND = {"piano": (0, 0), "clarinet": (71, 1), "trumpet": (56, 2), "bass": (32, 3), "drums": (0, 9),
        "banjo": (105, 4)}


class Score:
    def __init__(self, inst):
        self.inst = inst
        self.notes = {k: [] for k in inst}

    def n(self, tr, t, dur, pitch, vel=80):
        if t < 0 or t > TOTAL:
            return
        self.notes[tr].append((t, max(0.03, dur), N(pitch), int(max(1, min(127, vel)))))

    def chord(self, tr, t, dur, pitches, vel=70):
        for p in pitches:
            self.n(tr, t, dur, p, vel)

    def mel(self, tr, t0, spec, beat=0.5, vel=80, tr_=0, legato=0.95):
        t = t0
        for tok in spec.split():
            if tok == "|":
                continue
            p, d = tok.split("/")
            d = float(d) * beat
            if p != "r":
                self.n(tr, t, d * legato, N(p) + tr_, vel)
            t += d
        return t

    def gliss(self, tr, t0, p0, p1, dur, vel=70, step=2):
        a, b = N(p0), N(p1)
        rng = list(range(a, b + 1, step)) if b > a else list(range(a, b - 1, -step))
        if not rng:
            return
        dt = dur / len(rng)
        for i, p in enumerate(rng):
            self.n(tr, t0 + i * dt, dt * 1.5, p, vel)

    def roll(self, tr, t0, dur, pitch, vel=70, rate=0.06):
        t = t0
        while t < t0 + dur:
            self.n(tr, t, rate, pitch, int(vel * (0.7 + 0.3 * (t - t0) / max(dur, 1e-3))))
            t += rate

    def write(self, path):
        mid = mido.MidiFile(ticks_per_beat=480)
        meta = mido.MidiTrack()
        meta.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        mid.tracks.append(meta)
        for tr, (prog, ch) in self.inst.items():
            track = mido.MidiTrack()
            msgs = []
            if ch != 9:
                msgs.append((0, mido.Message("program_change", program=prog, channel=ch)))
            msgs.append((0, mido.Message("control_change", control=91, value=60, channel=ch)))  # reverb
            for (t, d, p, v) in self.notes[tr]:
                msgs.append((int(t * 960), mido.Message("note_on", note=p, velocity=v, channel=ch)))
                msgs.append((int((t + d) * 960), mido.Message("note_off", note=p, velocity=0, channel=ch)))
            msgs.sort(key=lambda x: (x[0], 0 if x[1].type == "note_off" else 1))
            last = 0
            for tick, m in msgs:
                m.time = tick - last
                last = tick
                track.append(m)
            mid.tracks.append(track)
        mid.save(path)


def render_midi(mid, wav, gain=0.5):
    subprocess.run(["fluidsynth", "-ni", "-g", str(gain), "-r", str(SR), "-F", wav, SF2, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32) / 32768.0
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    return x


# --------------------------------------------------------------------------- themes
FUNKE = "G4/.5 C5/.5 E5/.5 G5/1.5 F5/.5 E5/.5 D5/.5 C5/1.5 A4/.5 D5/.5 F5/.5 A5/1 G5/.5 E5/.5 G5/.5 F5/.5 D5/.5 C5/2"
SPARK = "E5/.25 G5/.25 C6/1"
HEDDA = "A4/1 C5/.5 D5/.5 F5/1.5 E5/.5 D5/1 C5/.5 A4/.5 C5/2 Bb4/1 D5/.5 C5/.5 A4/1 G4/1 F4/3"
BELLO = "A4/1.5 G4/.5 F4/1 E4/1 D4/1 F4/1 E4/2"
ERF_TB = "Bb2/1 Db3/.5 F3/.5 Eb3/1 Db3/.5 C3/.5 Bb2/2 F2/2"
SWING = ("C5/.5 D5/.5 F5/1 A5/1 F5/1 G5/.75 F5/.25 D5/1 F5/2 C5/.5 D5/.5 F5/1 A5/1 C6/1 Bb5/.75 A5/.25 G5/1 F5/2 "
         "D5/.5 F5/.5 A5/1 G5/.5 F5/.5 D5/1 C5/.5 D5/.5 F5/1 A5/2 G5/.5 A5/.5 Bb5/1 A5/.5 G5/.5 E5/1 F5/2 r/2")
SWING_CH = [("F3", ["A3", "C4", "D4", "F4"]), ("D3", ["F#3", "A3", "C4"]), ("G2", ["F3", "Bb3", "D4"]),
            ("C3", ["E3", "Bb3", "D4"]), ("F3", ["A3", "C4", "F4"]), ("D3", ["F#3", "A3", "C4"]),
            ("G2", ["F3", "Bb3", "D4"]), ("F3", ["A3", "C4", "F4"])]
GALOP = ("D5/.5 D5/.5 G5/.5 D5/.5 Bb5/.5 A5/.5 G5/.5 F#5/.5 G5/.5 D5/.5 Bb4/.5 D5/.5 G4/1 r/1 "
         "Eb5/.5 Eb5/.5 G5/.5 Eb5/.5 C6/.5 Bb5/.5 A5/.5 G5/.5 F#5/.5 A5/.5 D6/.5 C6/.5 Bb5/.5 A5/.5 G5/.5 F#5/.5")


def swing_band(sc, t0, t1, beat=0.5, vel=80, lead="clarinet", tr_=0):
    """The radio tune: 8 bars of 4 beats, looping between t0 and t1."""
    bar = 4 * beat
    t = t0
    while t < t1 - 0.01:
        sc.mel(lead, t, SWING, beat, vel, tr_)
        if "trumpet" in sc.inst:
            sc.mel("trumpet", t + bar * 4, SWING, beat, vel - 15, tr_ - 12)
        for b_, (root, ch) in enumerate(SWING_CH):
            tb = t + b_ * bar
            if tb >= t1:
                break
            r = N(root) + tr_
            for k in range(4):
                tk = tb + k * beat
                if tk >= t1:
                    break
                bassn = r + [0, 7, 12, 7][k] - 12
                sc.n("bass", tk, beat * 0.9, bassn, vel)
                if k % 2 == 0:
                    sc.n("piano", tk, beat * 0.5, r - 12, vel - 10)
                else:
                    sc.chord("piano", tk, beat * 0.45, [N(c) + tr_ for c in ch], vel - 15)
                sc.n("drums", tk, 0.1, 42 if k % 2 == 0 else 38, vel - 30 if k % 2 == 0 else vel - 20)
                sc.n("drums", tk + beat * 0.66, 0.08, 42, vel - 40)
                if "banjo" in sc.inst and k % 2 == 1:
                    sc.chord("banjo", tk, beat * 0.3, [N(c) + tr_ + 12 for c in ch], vel - 30)
        t += 8 * bar
    return t


def oompah(sc, tr, t0, t1, root, fifth, beat, vel=70, chord_tr=None, chord=None):
    t = t0
    k = 0
    while t < t1:
        sc.n(tr, t, beat * 0.5, root if k % 2 == 0 else fifth, vel)
        if chord_tr and chord:
            sc.chord(chord_tr, t + beat * 0.5, beat * 0.3, chord, vel - 20)
        t += beat
        k += 1


def compose():
    O = Score(GM)
    O2 = Score(GM2)
    R = Score(BAND)  # diegetic radio / jukebox
    # ------------------------------------------------------------------ SEQ 1
    a, b = seq_t(1)
    # the title stamp and the first seconds of dawn belong to wind and wires; the music comes in after
    O.chord("strings", a + 3.0, 6.5, ["D3", "A3", "F4"], 40)
    O.mel("flute", a + 4.8, HEDDA, 0.55, 45, -12)
    # the Erfasser's scanner: a ticking woodblock metronome and a cold tremolo under every POV shot
    for e in ev("pov_in"):
        t0 = s(e["frame"])
        d = dur_of(e, 2.0)
        tt = t0
        k = 0
        while tt < t0 + d:
            O.n("drums", tt, 0.05, 76 if k % 4 == 0 else 77, 70 if k % 4 == 0 else 50)
            tt += 0.25
            k += 1
        O2.n("tremolo", t0, d, "E2", 45)
        O2.n("tremolo", t0, d, "F2", 38)
    for t in ts("truck", 1):
        O.roll("timpani", t + 3.0, 2.0, "D2", 35)
    t = first("junk_dump", 1)
    if t:
        O.gliss("xylo", t, "C6", "C4", 0.6, 70, 1)
    steps = ts("step", 1, who="Hedda")
    pz = ["D4", "F4", "A4", "F4", "E4", "G4", "Bb4", "G4"]
    for i, t in enumerate(steps):
        if t < first("startle", 1, 1e9):
            O.n("pizz", t, 0.2, pz[i % len(pz)], 70)
            if i % 2 == 0:
                O.n("bassoon", t, 0.18, N(pz[i % len(pz)]) - 24, 55)
    t = first("radio_crackle", 1)
    if t:
        O.mel("clarinet", t, "A5/.25 G5/.25 A5/.25 G5/.25 A5/.25 C6/1", 0.4, 65)
    for e in ev("step", 1, who="Bello")[:1]:
        O.mel("oboe", s(e["frame"]), BELLO, 0.55, 60)
    t = first("wag", 1)
    if t:
        O.gliss("harp", t, "D4", "D6", 0.8, 60, 2)
        O.mel("celesta", t + 0.8, "A5/.5 F5/.5 D5/1", 0.4, 50)
    t_sq = first("squeak", 1)
    t_buzz = first("verdict_buzz", 1)
    if t_sq:
        t1 = t_buzz or t_sq + 5
        oompah(O, "tuba", t_sq, t1, N("Bb1"), N("F2"), 0.6, 75)
        O.mel("trombone", t_sq + 1.2, ERF_TB, 0.6, 70)
        tt = t_sq
        while tt < t1:
            O.n("drums", tt, 0.1, 38, 50)
            tt += 1.2
    if t_buzz:
        O.chord("trombone", t_buzz, 0.8, ["Bb2", "E3", "A3"], 95)
        O.chord("horn", t_buzz, 0.8, ["B3", "F4"], 90)
    for t in ts("stamp", 1):
        O.n("timpani", t, 0.5, "F2", 110)
        O.n("trombone", t + 0.05, 0.6, "F2", 90)
    for t in ts("net_catch", 1):
        O.roll("strings", t - 0.6, 0.6, "A4", 60, 0.05)
        O.chord("horn", t, 0.5, ["D4", "Ab4"], 100)
    t = first("crunch", 1)
    if t:
        O.chord("trombone", t, 1.2, ["D2", "Ab2", "D3"], 120)
        O.chord("tuba", t, 1.2, ["D1", "Ab1"], 120)
        O.n("timpani", t, 1.5, "D2", 127)
        O.n("drums", t, 1.5, 49, 120)
    t = first("lens_land", 1)
    if t:
        O.n("celesta", t, 1.0, "E6", 70)
        O.gliss("harp", t + 0.3, "A5", "A3", 1.2, 40, 2)
        O.chord("strings", t + 1.0, 5.0, ["D3", "F3", "A3", "D4"], 35)
        O.mel("oboe", t + 2.0, BELLO, 0.7, 45)
    t = first("tiny_flicker", 1)
    if t:
        O.mel("celesta", t, SPARK, 0.4, 45)
    # ------------------------------------------------------------------ SEQ 2
    a, b = seq_t(2)
    O.chord("harp", a, 4.0, ["F3", "C4", "A4"], 40)
    O.mel("clarinet", a + 0.5, "C5/1 A4/1 F4/2", 0.6, 45)
    m0 = a + 4.0
    m1 = first("click", 2, a + 15.0)
    beat = 60 / 132
    tt = m0
    pat = ["C5", "E5", "G5", "E5", "D5", "F5", "A5", "F5"]
    k = 0
    while tt < m1 - 0.3:
        O.n("xylo", tt, beat * 0.4, pat[k % 8], 60)
        if k % 2 == 0:
            O.n("pizz", tt, beat * 0.5, ["C3", "G2", "D3", "G2"][(k // 2) % 4], 65)
        tt += beat / 2
        k += 1
    O.mel("clarinet", m0 + 1.0, HEDDA, beat, 60, -5)
    O.mel("clarinet", m0 + 1.0 + 15 * beat, HEDDA, beat, 60, -5)
    taps = ts("knock", 2)
    O.chord("strings", m1, 6.0, ["C3", "G3", "E4"], 30)
    t = first("clunk_dead", 2)
    if t:
        O.mel("mute_tp", t + 0.3, "Bb4/1 A4/1 Ab4/1 G4/3", 0.45, 70)
    t_fl = first("flicker_on", 2)
    if t_fl:
        O.roll("celesta", t_fl, 0.6, "C6", 40, 0.05)
    t = first("lid_open", 2)
    if t:
        O.gliss("harp", t, "C4", "C6", 0.7, 60, 2)
    t_p = first("ping", 2)
    if t_p:
        O.mel("glock", t_p, SPARK, 0.4, 80)
        O.mel("celesta", t_p + 1.2, FUNKE, 0.42, 60)
        O.mel("flute", t_p + 1.2, FUNKE, 0.42, 40, 12)
        O.chord("strings", t_p + 1.2, 7.0, ["C3", "G3", "E4"], 35)
    for t in ts("step_tiny", 2):
        O.mel("bassoon", t, "C3/.5 E3/.5 C3/.5", 0.25, 70)
    t = first("plop", 2)
    if t:
        O.n("timpani", t, 0.5, "C2", 110)
    t = first("imitate", 2)
    if t:
        O.mel("mute_tp", t, "G4/1 E4/2", 0.3, 80)
    t = first("glass_break", 2)
    if t:
        O.gliss("xylo", t - 1.2, "C5", "C6", 1.0, 70, 2)
        O.n("drums", t, 1.2, 49, 115)
        O.chord("trombone", t + 0.05, 0.4, ["C3", "F#3"], 100)
        O.mel("bassoon", t + 1.0, "C3/1 B2/1 Bb2/2", 0.35, 70)
    t = first("creak", 2)
    if t:
        O.roll("strings", t - 0.4, 1.0, "E4", 50, 0.05)
    t = first("crash", 2)
    if t:
        O.n("drums", t, 1.0, 49, 120)
        O.n("timpani", t, 0.8, "C2", 120)
    t = first("pot_bong", 2)
    if t:
        O.n("glock", t + 0.05, 0.8, "C5", 70)
    t = first("gen_die", 2)
    if t:
        O.gliss("tuba", t - 0.6, "C3", "C1", 1.2, 80, 1)
        O.mel("celesta", t + 1.5, SPARK, 0.6, 35)
    t_roar = first("gen_roar", 2)
    if t_roar:
        O.mel("horn", t_roar, FUNKE, 0.4, 85, -12)
        O.mel("flute", t_roar, FUNKE, 0.4, 70, 12)
        O.mel("strings", t_roar, FUNKE, 0.4, 70)
        oompah(O, "tuba", t_roar, t_roar + 9.6, N("C2"), N("G1"), 0.4, 70)
        O.n("drums", t_roar, 1.0, 49, 100)
    for t in ts("laugh", 2):
        O.mel("clarinet", t, "G5/.25 A5/.25 G5/.25 A5/.25 G5/.25 A5/.25 C6/.5", 0.3, 60)
    t = first("ping_happy", 2)
    if t:
        O.mel("glock", t, SPARK, 0.35, 80)
    t_sl = first("snore", 2)
    if t_sl:
        tl = t_sl - 1.0
        O2.mel("musicbox", tl, FUNKE, 0.7, 55)
        O2.chord("strings_b", tl, b - tl, ["C3", "G3", "E4"], 30)
    # ------------------------------------------------------------------ SEQ 3
    a, b = seq_t(3)
    O2.mel("harmonica", a + 0.5, "D4/2 F4/1 A4/1 G4/2 F4/1 D4/1 E4/3 r/1 D4/2 F4/1 G4/1 A4/3", 0.65, 50)
    t_on = first("music_radio_start", 3)
    t_off = first("music_radio_stop", 3)
    if t_on and t_off:
        swing_band(R, t_on, t_off, 0.5, 85)
        # the cartoon orchestra joins in after 8 beats
        join = t_on + 4.0
        O.mel("clarinet", join, SWING, 0.5, 60)
        oompah(O, "tuba", join, t_off, N("F1"), N("C2"), 0.5, 55)
        tt = join
        while tt < t_off:
            O.n("xylo", tt, 0.1, "F5", 35)
            tt += 1.0
        O.n("drums", t_off, 0.3, 57, 90)
        O.chord("tuba", t_off + 0.6, 2.5, ["Bb1"], 80)
        O.mel("trombone", t_off + 0.8, ERF_TB, 0.7, 60)
        O.roll("timpani", t_off + 0.6, 2.5, "Bb1", 50)
    for t in ts("land_spring", 3):
        O.gliss("pizz", t - 0.5, "C4", "C5", 0.4, 60, 2)
    # ------------------------------------------------------------------ SEQ 4
    a, b = seq_t(4)
    t_ch = first("chase_start", 4, a + 1)
    t_bar = first("barrel_thunk", 4, a + 15)
    beat = 60 / 168

    def galop(t0, t1):
        tt = t0
        while tt < t1 - 0.2:
            end = O.mel("xylo", tt, GALOP, beat, 75)
            O.mel("clarinet", tt, GALOP, beat, 60)
            oompah(O, "tuba", tt, min(end, t1), N("G1"), N("D2"), beat, 70, "pizz", ["G3", "Bb3", "D4"])
            k = tt
            while k < min(end, t1):
                O.n("drums", k, 0.1, 38, 60)
                O.chord("horn", k, beat * 0.3, ["G3", "D4"], 55)
                k += 4 * beat
            tt = end
        # cut off hard

    galop(a, t_bar)
    for t in ts("cloth_flap", 4):
        O.gliss("trombone", t, "F3", "Bb2", 0.6, 80, 1)
    for t in ts("bolts_spill", 4):
        O.gliss("xylo", t, "C6", "C4", 0.6, 80, 1)
    for t in ts("spin_out", 4):
        for k in range(6):
            O.gliss("flute", t + k * 0.2, "C5", "C6", 0.18, 50, 3)
    t_ping = first("ping", 4)
    if t_bar:
        tt = t_bar + 0.3
        while tt < (t_ping or t_bar + 4):
            O.n("pizz", tt, 0.15, "D3", 55)
            tt += 0.6
    if t_ping:
        O.mel("glock", t_ping, "C6/1", 0.3, 80)
        O.chord("horn", t_ping + 0.4, 0.8, ["D4", "Ab4"], 100)
    t_scrap = (t_ping or t_bar) + 1.2
    t_net = first("net_catch", 4)
    galop(t_scrap, t_net or t_scrap + 5)
    if t_net:
        O.chord("trombone", t_net, 0.8, ["G2", "Db3", "G3"], 110)
        O.n("drums", t_net, 0.8, 49, 100)
    for t in ts("stamp", 4):
        O.n("timpani", t, 0.6, "G2", 115)
    t_rev = first("engine_rev", 4)
    if t_rev:
        O.mel("oboe", t_rev, FUNKE, 0.65, 55, -3)
        O.chord("strings", t_rev, b - t_rev, ["C3", "Eb3", "G3"], 35)
    # ------------------------------------------------------------------ SEQ 5
    a, b = seq_t(5)
    O.chord("strings", a, 5.0, ["F2", "C3", "Gb3"], 35)
    for t in ts("press_slam", 5):
        O.n("timpani", t, 0.4, "F2", 100)
        O.n("tuba", t, 0.3, "F1", 80)
        O.n("strings", t + 0.6, 0.2, "C3", 50)
    for i, t in enumerate(ts("step", 5, who="Hedda")):
        if t < first("net_catch", 5, 1e9):
            O.n("pizz", t, 0.2, ["F3", "Ab3", "C4", "Ab3"][i % 4], 60)
    for t in ts("net_catch", 5):
        O.chord("horn", t, 0.6, ["F4", "B4"], 100)
    for t in ts("stamp", 5):
        O.n("timpani", t, 0.5, "F2", 115)
        O.mel("trombone", t + 0.1, "F3/1 E3/1 Eb3/1 D3/3", 0.25, 85)
    for t in ts("squeeze", 5):
        O.mel("bassoon", t, "F2/.5 G2/.5 A2/.5 Bb2/.5 C3/1", 0.15, 70)
    t_jam = first("press_jam", 5)
    if t_jam:
        O.chord("trombone", t_jam, 1.2, ["F2", "B2", "E3"], 115)
        O.chord("strings", t_jam, 1.2, ["F3", "Gb3", "B3", "C4"], 90)
        O.n("drums", t_jam, 1.0, 49, 110)
    for t in ts("cage_pop", 5):
        O.n("glock", t, 0.3, "C6", 70)
    t_jb = first("jukebox_start", 5)
    if t_jb:
        swing_band(R, t_jb, b, 0.5, 70, tr_=0)
        join = t_jb + 4.0
        O.mel("clarinet", join, SWING, 0.5, 60)
        O.mel("horn", join + 8.0, SWING, 0.5, 60, -12)
        oompah(O, "tuba", join, b, N("F1"), N("C2"), 0.5, 60)
    for t in ts("bonk", 5):
        O.n("drums", t, 0.3, 77, 110)
    stamps5 = ts("stamp", 5)
    if len(stamps5) >= 2:
        t = stamps5[-1]
        O.mel("mute_tp", t + 0.3, "Bb4/1 A4/1 Ab4/1 G4/3", 0.3, 85)
    # ------------------------------------------------------------------ SEQ 6
    a, b = seq_t(6)
    O.mel("clarinet", a + 1.0, HEDDA, 0.7, 45)
    O.chord("strings", a, 8.0, ["F2", "C3", "A3"], 30)
    t_w = first("warm_chord", 6)
    if t_w:
        O.chord("strings", t_w, 6.0, ["F3", "A3", "C4", "F4"], 55)
        O.chord("horn", t_w + 0.3, 5.0, ["A3", "C4"], 50)
    t_js = first("jukebox_soft", 6)
    if t_js:
        swing_band(R, t_js, t_js + 16.0, 0.6, 45)
        O.mel("strings", t_js + 4.0, FUNKE, 0.55, 55, 5)
        O.mel("flute", t_js + 4.0, FUNKE, 0.55, 45, 17)
        O.mel("horn", t_js + 4.0 + 8.8, FUNKE, 0.55, 55, -7)
    t = first("wink", 6)
    if t:
        O.mel("glock", t, "C6/.25 E6/.25 G6/1", 0.3, 80)
    t = first("glint", 6)
    if t:
        O.roll("celesta", t, 0.5, "C7", 50, 0.04)
    t_i = first("iris_out", 6)
    if t_i:
        O.gliss("harp", t_i, "F3", "F6", 1.2, 70, 2)
        O.mel("strings", t_i + 0.2, "C5/.5 D5/.5 E5/.5 F5/2", 0.35, 80)
        O.roll("timpani", t_i + 1.0, 1.2, "F2", 70)
    t = first("final_chord", 6)
    if t:
        for tr, ch in (("strings", ["F3", "A3", "C4", "F4"]), ("horn", ["F3", "C4"]), ("trombone", ["F2", "C3"]),
                       ("tuba", ["F1"]), ("flute", ["A5", "C6"])):
            O.chord(tr, t, 2.0, ch, 95)
        O.n("timpani", t, 0.6, "F2", 120)
        O.n("drums", t, 2.0, 49, 100)
    return O, O2, R


# =========================================================================== sfx mixing
class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.L = np.zeros(self.n, np.float32)
        self.R = np.zeros(self.n, np.float32)

    def add(self, t, x, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= self.n or x is None:
            return
        j = min(self.n, i + len(x))
        x = x[: j - i] * gain
        self.L[i:j] += x * (1 - max(0, pan)) * 0.9
        self.R[i:j] += x * (1 + min(0, pan)) * 0.9

    def add_st(self, t, st, gain=1.0):
        i = int(t * SR)
        j = min(self.n, i + len(st))
        self.L[i:j] += st[: j - i, 0] * gain
        self.R[i:j] += st[: j - i, 1] * gain

    def arr(self):
        return np.stack([self.L, self.R], 1)


def dur_of(e, default=1.0):
    return e.get("dur", default * FPS) / FPS


def sfx_for(e):
    k = e["kind"]
    seq = e.get("seq", 1)
    if k == "step":
        who = e.get("who", "")
        style = e.get("style", "walk")
        if who == "Funke":
            return X.step("tiny"), 0.5
        if who == "Bello":
            return X.step("metal"), 0.25
        surf = "wood" if seq == 2 else ("metal" if seq == 5 and 12 < s(e["frame"]) - seq_t(5)[0] < 21 else "dirt")
        soft = {"sneak": 0.4, "run": 1.0, "shuffle": 0.5}.get(style, 0.7)
        return X.step(surf, soft), 0.8
    table = {
        "knock": (lambda: X.knock(1.0), 0.9), "knock_small": (lambda: X.knock(1.5), 0.8),
        "knock_soft": (lambda: X.knock(1.2), 0.5), "knock_wood": (lambda: X.knock(0.8), 0.6),
        "knock_metal": (X.knock_metal, 0.9), "stamp": (X.stamp, 1.0), "whoosh": (X.whoosh, 0.8),
        "whoosh_small": (lambda: X.whoosh(0.3), 0.5), "net_catch": (lambda: X.cloth(0.4), 0.8),
        "crunch": (X.crunch, 1.0), "press_slam": (X.press_slam, 0.9), "press_start": (lambda: X.hiss(0.8), 0.6),
        "hydraulic": (lambda: X.hiss(0.9), 0.6), "clank": (X.knock_metal, 0.6), "pop": (X.pop, 0.8),
        "lens_land": (lambda: X.tink(3600), 0.8), "bolt_land": (lambda: X.tink(4200), 0.6),
        "tiny_flicker": (lambda: X.sparkle(0.3), 0.4), "flicker_on": (lambda: X.sparkle(0.6), 0.5),
        "ping": (lambda: X.tink(2093), 0.6), "ping_happy": (lambda: X.tink(2637), 0.6),
        "verdict_buzz": (X.buzz, 0.8), "drop_in": (lambda: X.thud(90, 0.3), 0.8), "rummage": (X.clatter, 0.6),
        "pocket": (lambda: X.cloth(0.25), 0.5), "startle": (lambda: X.whoosh(0.2, 1500, 4000), 0.3),
        "sniff": (lambda: X.cloth(0.15), 0.3), "radio_crackle": (lambda: X.static(0.8), 0.6),
        "junk_dump": (lambda: X.crash(1.6), 0.7), "click": (lambda: X.tink(5000), 0.5),
        "clunk_dead": (lambda: X.thud(120, 0.2), 0.6), "sigh": (lambda: X.cloth(0.6), 0.25),
        "lid_open": (lambda: X.slide_whistle(400, 900, 0.25), 0.3), "step_tiny": (lambda: X.step("tiny"), 0.6),
        "land_spring": (X.boing, 0.6), "plop": (lambda: X.thud(80, 0.3), 0.9), "boing": (lambda: X.boing(180, 0.8), 0.7),
        "glass_break": (X.glass_break, 0.9), "creak": (X.creak, 0.7), "crash": (X.crash, 1.0),
        "pot_bong": (lambda: X.bong(420), 0.8), "pot_bong_small": (lambda: X.bong(520), 0.5),
        "steam_hiss": (lambda: X.hiss(0.7), 0.25), "scribble": (lambda: X.whoosh(0.3, 2500, 7000), 0.35), "hud_tick": (lambda: X.beep(2600), 0.18),
        "scan_lock": (lambda: X.beep(1200), 0.35), "pov_in": (lambda: X.static(0.25), 0.25), "drip": (lambda: X.tink(1800), 0.12),
        "pop_up": (lambda: X.slide_whistle(400, 1400, 0.5), 0.6), "gen_sputter": (X.sputter, 0.8),
        "gen_die": (lambda: X.gen_engine(1.5, die=True), 0.9), "hammer_tiny": (lambda: X.tink(2500), 0.6),
        "screw": (X.ratchet, 0.6), "snore": (lambda: X.snore(1.4), 0.6), "snore_old": (lambda: X.snore(1.6, True), 0.5),
        "imitate": (None, 0), "laugh": (None, 0), "drone_beep": (lambda: X.beep(1700), 0.6),
        "record_scratch": (X.record_scratch, 1.0), "cloth_flap": (lambda: X.cloth(0.5), 0.8),
        "bolts_spill": (lambda: X.clatter(0.8, 20), 0.9), "barrel_thunk": (lambda: X.thud(150, 0.4), 0.9),
        "neck_extend": (lambda: X.slide_whistle(300, 1500, 0.35), 0.5), "thud": (lambda: X.thud(70, 0.4), 1.0),
        "heavy_land": (lambda: X.thud(55, 0.5), 1.0), "bonk": (lambda: X.knock(0.7), 1.0),
        "cage_pop": (lambda: X.knock_metal(), 0.5), "cage_slam": (lambda: X.crash(0.8), 0.8),
        "clunk_land": (lambda: X.thud(110, 0.25), 0.5), "squeeze": (lambda: X.spring_squeeze(0.4), 0.6),
        "press_jam": (lambda: X.crash(1.2), 0.9), "metal_scrape": (lambda: X.scrape(0.6), 0.6),
        "wink": (lambda: X.tink(3136), 0.4), "glint": (lambda: X.sparkle(0.5), 0.5),
        "cat_meow": (X.meow, 0.6), "fiddle": (lambda: X.ratchet(1.0), 0.4), "wag": (None, 0),
        "engine_rev": (lambda: X.engine(2.0, 40, rev=True), 0.9), "determined": (None, 0),
    }
    if k in table:
        fn, g = table[k]
        return (fn() if fn else None), g
    # duration-based
    if k == "unicycle":
        return X.unicycle(dur_of(e)), 0.6
    if k == "truck":
        return X.engine(dur_of(e) + 1.0, 36), 0.9
    if k == "scan":
        return X.scan(dur_of(e)), 0.6
    if k == "roll":
        return X.roll(dur_of(e, 0.6)), 0.8
    if k == "solder":
        return X.crackle(dur_of(e), 120), 0.6
    if k == "weld_outside":
        return lp_quiet(X.crackle(dur_of(e), 80)), 0.4
    if k == "spin_out":
        d = dur_of(e)
        return X.slide_whistle(600, 1200, d, vib=8) * 0.5 + X.squeak(d, 2000) * 0.5, 0.7
    if k == "vacuum_zoom":
        return X.motor_whine(dur_of(e), 1100), 0.5
    if k == "alarm":
        return X.siren(dur_of(e)), 0.45
    if k == "drag_metal":
        return X.scrape(dur_of(e)), 0.5
    if k == "gen_roar":
        return X.gen_engine(1.5, start=True), 0.9
    if k == "squeak":
        return X.squeak(0.2), 0.6
    if k == "clock_tick":
        d = dur_of(e)
        out = np.zeros(int(d * SR), np.float32)
        for i in range(int(d)):
            c = X.tink(4000) * 0.4
            out[int(i * SR):int(i * SR) + len(c)] += c[: len(out[int(i * SR):int(i * SR) + len(c)])]
        return out, 0.5
    return None, 0


def lp_quiet(x):
    return X.lp(x, 1500) * 0.7


def ambience(mix):
    # SEQ1 dawn wind + distant city hum
    a, b = seq_t(1)
    mix.add(a, X.wind(b - a, 1.0, 1), 0.8)
    rng1 = np.random.default_rng(1)
    t = a + 3.0
    while t < b:
        mix.add(t, X.drone_chirp(), 0.4, pan=rng1.uniform(-0.6, 0.6))
        t += rng1.uniform(4, 9)
    mix.add(a, X.hum(b - a, 55, 0.03), 1.0)
    # SEQ2: outside wind first 4 s, then interior generator hum until it dies, again after roar
    a, b = seq_t(2)
    mix.add(a, X.wind(4.5, 0.8, 2), 0.7)
    mix.add(a, X.crickets(4.5), 0.8)
    t_sl = first("snore", 2)
    if t_sl:
        mix.add(t_sl - 1.0, X.crickets(b - t_sl + 1.0), 0.4)
    t_die = first("gen_die", 2, b)
    t_roar = first("gen_roar", 2, b)
    mix.add(a + 4.0, X.gen_engine(max(0.1, t_die - a - 4.0)), 0.25)
    mix.add(t_roar + 1.4, X.gen_engine(max(0.1, b - t_roar - 1.4)), 0.25)
    mix.add(a + 4.0, X.crackle(b - a - 4.0, 8) * 0.5, 0.4)
    # SEQ3 village: light wind, tin chickens, drone chirps
    a, b = seq_t(3)
    mix.add(a, X.wind(b - a, 0.6, 3), 0.7)
    rng = np.random.default_rng(3)
    t = a + 1.0
    t_stop = first("music_radio_stop", 3, b)
    while t < t_stop:
        mix.add(t, X.cluck(), 0.7, pan=rng.uniform(-0.7, 0.7))
        t += rng.uniform(1.5, 4.0)
    t = a + 2.0
    while t < b:
        mix.add(t, X.drone_chirp(), 0.6, pan=rng.uniform(-0.5, 0.5))
        t += rng.uniform(3, 7)
    # SEQ4 wind
    a, b = seq_t(4)
    mix.add(a, X.wind(b - a, 0.8, 4), 0.7)
    # SEQ5 industrial hum + conveyor rumble until the jam
    a, b = seq_t(5)
    mix.add(a, X.wind(5.0, 0.8, 5), 0.7)
    t_jam = first("press_jam", 5, b)
    mix.add(a + 5.0, X.hum(max(0.1, t_jam - a - 5.0), 48, 0.08), 1.0)
    mix.add(a + 5.0, X.engine(max(0.5, t_jam - a - 5.0), 22) * 0.5, 0.5)
    mix.add(t_jam, X.hum(max(0.1, b - t_jam), 48, 0.05), 1.0)
    # SEQ6 dawn wind – and, for the first time in the film, real birds (sparse, then more and more)
    a, b = seq_t(6)
    mix.add(a, X.wind(b - a, 0.7, 6), 0.7)
    rng6 = np.random.default_rng(6)
    t = a + 2.5
    k = 0
    while t < b - 2.0:
        prog = (t - a) / (b - a)
        mix.add(t, X.birdsong(60 + k), 0.25 + 0.35 * prog, pan=rng6.uniform(-0.8, 0.8))
        t += rng6.uniform(5.0, 9.0) * (1.0 - 0.7 * prog)
        k += 1


def radio_filter(st, strength=1.0):
    mono = st.mean(1)
    f = X.bp(mono, 350, 3200, 3)
    f = np.tanh(f * 3.0) / 1.5
    f += 0.04 * X.crackle(len(f) / SR, 30)[: len(f)] * strength
    return np.stack([f, f], 1)


def master(x):
    # gentle 'old print' colour: band-limit, a whisper of crackle, soft limiting
    y = np.stack([X.hp(x[:, 0], 45), X.hp(x[:, 1], 45)], 1)
    y = np.stack([X.lp(y[:, 0], 11000), X.lp(y[:, 1], 11000)], 1)
    cr = X.crackle(len(y) / SR, 4)[: len(y)] * 0.015
    y[:, 0] += cr
    y[:, 1] += cr
    # broadband compressor (RMS envelope, ~80 ms) then limiter
    mono = np.abs(y).max(1)
    win = int(0.08 * SR)
    envl = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode="same")) + 1e-6
    rms = np.sqrt(np.mean(mono ** 2))
    thr = rms * 2.0
    ratio = 3.0
    g = np.where(envl > thr, (thr / envl) ** (1 - 1 / ratio), 1.0)
    g = np.convolve(g, np.ones(win) / win, mode="same")
    y = y * g[:, None]
    # loudness target ~ -20 dBFS RMS
    rms = np.sqrt(np.mean(y ** 2)) + 1e-9
    y = y * (10 ** (-20 / 20) / rms)
    y = np.tanh(y * 1.2) / np.tanh(1.2)
    peak = np.max(np.abs(y))
    if peak > 0.97:
        y = y / peak * 0.97
    return y


def main():
    out_dir = HERE
    O, O2, R = compose()
    stems = {}
    for name, sc, gain in (("orch", O, 0.55), ("orch2", O2, 0.55), ("band", R, 0.55)):
        mid = os.path.join(out_dir, f"{name}.mid")
        wav = os.path.join(out_dir, f"stem_{name}.wav")
        sc.write(mid)
        stems[name] = render_midi(mid, wav, gain)
    mix = Mix(TOTAL)
    # music
    mix.add_st(0, stems["orch"], 1.0)
    mix.add_st(0, stems["orch2"], 4.0)
    band = stems["band"]
    # radio colouring for the diegetic band (seq3 radio fully filtered, seq5/6 jukebox lightly)
    t3a, t3b = seq_t(3)
    i0, i1 = int(t3a * SR), int(t3b * SR)
    band_f = band.copy()
    band_f[i0:i1] = radio_filter(band[i0:i1])
    t5a = seq_t(5)[0]
    j0 = int(t5a * SR)
    band_f[j0:] = 0.6 * radio_filter(band[j0:], 0.3) + 0.4 * band[j0:]
    mix.add_st(0, band_f, 1.1)
    # foley
    for e in EVENTS:
        lo, hi = BOUNDS[e.get("seq", 1)]
        if not (lo <= e["frame"] <= hi):
            continue
        x, g = sfx_for(e)
        if x is not None and g > 0:
            mix.add(s(e["frame"]), np.asarray(x, np.float32), g, pan=np.random.uniform(-0.25, 0.25))
    ambience(mix)
    y = master(mix.arr())
    wavfile.write(os.path.join(out_dir, "soundtrack.wav"), SR, (y * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out_dir, "soundtrack.wav"), "-c:a",
                    "libvorbis", "-q:a", "6", os.path.join(out_dir, "soundtrack.ogg")], check=True)
    print("soundtrack", round(len(y) / SR, 1), "s")


if __name__ == "__main__":
    main()
