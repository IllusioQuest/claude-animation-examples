"""Synthesised cartoon foley (numpy). Every function returns a mono float32 array at SR."""
import numpy as np
from scipy import signal

SR = 48000
_rng = np.random.default_rng(1)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.002, d=0.1, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4) * (curve / 4))
    return e


def noise(dur):
    return _rng.standard_normal(int(dur * SR)).astype(np.float32)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo / (SR / 2), min(0.99, hi / (SR / 2))], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    sos = signal.butter(order, min(0.99, f / (SR / 2)), btype="low", output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    sos = signal.butter(order, f / (SR / 2), btype="high", output="sos")
    return signal.sosfilt(sos, x)


def sine_glide(f0, f1, dur, shape="exp"):
    t = t_(dur)
    if shape == "exp":
        f = f0 * (f1 / f0) ** (t / dur)
    else:
        f = f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def modal(freqs, decays, amps, dur):
    t = t_(dur)
    out = np.zeros_like(t)
    for f, d, a in zip(freqs, decays, amps):
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    return out


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return (x / m * peak).astype(np.float32)


# --------------------------------------------------------------------------- library
def knock(pitch=1.0):
    x = modal([850 * pitch, 2150 * pitch, 3400 * pitch], [0.05, 0.025, 0.012], [1, 0.5, 0.25], 0.18)
    x += 0.3 * bp(noise(0.18), 1500, 6000) * env(int(0.18 * SR), 0.0005, 0.006)
    return norm(x, 0.8)


def knock_metal():
    return norm(modal([1250, 2730, 4100, 5900], [0.25, 0.15, 0.1, 0.06], [1, 0.6, 0.4, 0.2], 0.5), 0.6)


def tink(f=3200):
    return norm(modal([f, f * 2.76, f * 5.4], [0.08, 0.04, 0.02], [1, 0.5, 0.2], 0.25), 0.5)


def step(kind="dirt", soft=1.0):
    d = 0.09
    x = noise(d)
    if kind == "dirt":
        x = bp(x, 300, 2500) * env(len(x), 0.003, 0.025)
        x += 0.4 * lp(noise(d), 200) * env(len(x), 0.002, 0.02)
    elif kind == "wood":
        x = modal([180, 420], [0.04, 0.02], [1, 0.4], d) + 0.2 * bp(x, 800, 3000) * env(len(x), 0.001, 0.01)
    elif kind == "metal":
        x = modal([520, 1400, 2900], [0.08, 0.05, 0.03], [1, 0.5, 0.3], 0.2) * 0.6
    elif kind == "tiny":
        x = modal([1800, 3900], [0.03, 0.015], [1, 0.4], 0.08)
    return norm(x, 0.35 * soft)


def thud(f=70, dur=0.35):
    t = t_(dur)
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-t / 0.03))) / SR) * np.exp(-t / 0.09)
    x += 0.3 * lp(noise(dur), 400) * env(len(t), 0.001, 0.03)
    return norm(x, 0.9)


def whoosh(dur=0.45, lo=300, hi=3000):
    n = int(dur * SR)
    x = noise(dur)
    out = np.zeros(n)
    seg = 512
    for i in range(0, n, seg):
        tt = i / n
        c = lo + (hi - lo) * np.sin(np.pi * tt)
        out[i:i + seg] = bp(x[i:i + seg], c * 0.7, c * 1.4)[:len(out[i:i + seg])]
    e = np.sin(np.pi * np.arange(n) / n) ** 2
    return norm(out * e, 0.6)


def stamp():
    x = thud(110, 0.3) * 0.8
    k = knock(0.6)
    out = np.zeros(int(0.4 * SR))
    out[:len(x)] += x
    out[:len(k)] += 0.6 * k
    return norm(out, 0.95)


def crunch(dur=1.2):
    n = int(dur * SR)
    out = 0.6 * lp(noise(dur), 300) * env(n, 0.005, 0.4)
    for i in range(70):
        pos = int(_rng.uniform(0, 0.8) * n)
        c = modal([_rng.uniform(300, 3000), _rng.uniform(2000, 7000)], [0.02, 0.01], [1, 0.5], 0.06)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])] * _rng.uniform(0.2, 0.8) * (1 - pos / n)
    b = thud(45, 0.8)
    out[:len(b)] += b
    return norm(out, 0.95)


def press_slam():
    out = np.zeros(int(1.0 * SR))
    b = thud(38, 0.9)
    out[:len(b)] += b
    m = modal([180, 410, 690, 1130], [0.4, 0.3, 0.2, 0.1], [1, 0.7, 0.5, 0.3], 0.9) * 0.5
    out[:len(m)] += m
    out += 0.2 * lp(noise(1.0), 900) * env(len(out), 0.001, 0.15)
    return norm(out, 0.95)


def hiss(dur=1.0):
    n = int(dur * SR)
    x = bp(noise(dur), 2000, 9000) * np.sin(np.pi * np.arange(n) / n) ** 0.5
    x += 0.4 * np.sin(2 * np.pi * 95 * t_(dur)) * np.sin(np.pi * np.arange(n) / n)
    return norm(x, 0.35)


def engine(dur, f=38, rev=False):
    t = t_(dur)
    ff = f * (1 + (1.2 * t / dur if rev else 0)) * (1 + 0.03 * np.sin(2 * np.pi * 3 * t))
    ph = np.cumsum(ff) / SR
    x = signal.sawtooth(2 * np.pi * ph) * 0.5 + 0.5 * np.sin(2 * np.pi * ph * 2)
    x = lp(x, 400) * (0.7 + 0.3 * np.sin(2 * np.pi * ph * 0.5))
    x += 0.15 * lp(noise(dur), 600)
    e = np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.8)
    return norm(x * e, 0.45)


def squeak(dur=0.25, f=2600):
    t = t_(dur)
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.15 * np.sin(2 * np.pi * 9 * t))) / SR)
    return norm(x * np.sin(np.pi * t / dur) ** 2, 0.18)


def unicycle(dur):
    """Rhythmic squeak of a dry wheel bearing."""
    n = int(dur * SR)
    out = np.zeros(n)
    i = 0
    while i < n:
        s = squeak(0.12, _rng.uniform(2300, 2900))
        out[i:i + len(s)] += s[:len(out[i:i + len(s)])]
        i += int(SR * 0.33)
    return out


def scan(dur):
    t = t_(dur)
    x = np.sin(2 * np.pi * np.cumsum(1400 + 500 * np.sin(2 * np.pi * 6 * t)) / SR)
    x *= 0.5 + 0.5 * signal.square(2 * np.pi * 12 * t)
    return norm(x * np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.05), 0.2)


def buzz(dur=0.5, f=110):
    t = t_(dur)
    return norm(lp(signal.square(2 * np.pi * f * t), 1500) * env(len(t), 0.005, dur), 0.4)


def beep(f=1600, dur=0.12):
    t = t_(dur)
    return norm(signal.square(2 * np.pi * f * t) * np.minimum(1, (dur - t) / 0.01), 0.15)


def pop():
    x = 0.8 * sine_glide(900, 250, 0.08) * env(int(0.08 * SR), 0.001, 0.03)
    return norm(np.concatenate([x, np.zeros(1000)]) + 0.2 * np.pad(noise(0.01), (0, len(x) + 1000 - 480)), 0.7)


def roll(dur):
    n = int(dur * SR)
    x = bp(noise(dur), 1500, 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(np.linspace(14, 3, n)) / SR))
    return norm(x * np.linspace(1, 0.2, n), 0.2)


def sparkle(dur=0.5):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(18):
        pos = int(_rng.uniform(0, 0.8) * n)
        c = tink(_rng.uniform(2500, 7000)) * 0.4
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    return norm(out, 0.35)


def crackle(dur, density=60):
    n = int(dur * SR)
    out = 0.05 * bp(noise(dur), 2000, 8000)
    for i in range(int(density * dur)):
        pos = int(_rng.uniform(0, 1) * n)
        c = noise(0.003) * _rng.uniform(0.2, 1.0)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    return norm(bp(out, 800, 9000), 0.3)


def boing(f=220, dur=0.6):
    t = t_(dur)
    ff = f * (1 + 0.6 * np.exp(-t / 0.08)) * (1 + 0.08 * np.sin(2 * np.pi * 18 * t) * np.exp(-t / 0.3))
    ph = np.cumsum(ff) / SR
    x = signal.sawtooth(2 * np.pi * ph)
    # jaw-harp-like formant sweep
    out = np.zeros_like(x)
    seg = 480
    for i in range(0, len(x), seg):
        c = 600 + 1800 * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * i / SR))
        out[i:i + seg] = bp(x[i:i + seg], c * 0.6, c * 1.6)[:len(out[i:i + seg])]
    return norm(out * np.exp(-t / 0.25), 0.5)


def slide_whistle(f0, f1, dur, vib=6):
    t = t_(dur)
    f = f0 * (f1 / f0) ** (t / dur) * (1 + 0.012 * np.sin(2 * np.pi * vib * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.08 * bp(noise(dur), 1000, 5000)
    e = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.05)
    return norm(x * e, 0.35)


def glass_break():
    n = int(0.9 * SR)
    out = 0.7 * hp(noise(0.9), 3000) * env(n, 0.001, 0.08)
    for i in range(40):
        pos = int(_rng.uniform(0, 0.7) * n)
        c = tink(_rng.uniform(3000, 9000)) * _rng.uniform(0.2, 0.7)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    return norm(out, 0.8)


def creak(dur=0.6):
    t = t_(dur)
    pulses = (np.sin(2 * np.pi * np.cumsum(30 + 40 * t / dur) / SR) > 0.97).astype(float)
    x = np.convolve(pulses, modal([320, 780, 1500], [0.01, 0.006, 0.003], [1, 0.6, 0.3], 0.02))[:len(t)]
    return norm(x, 0.5)


def crash(dur=1.5):
    n = int(dur * SR)
    out = np.zeros(n)
    b = thud(60, 0.6)
    out[:len(b)] += b
    for i in range(50):
        pos = int(_rng.exponential(0.15) * SR)
        if pos >= n:
            continue
        c = modal([_rng.uniform(150, 900), _rng.uniform(900, 3000)], [0.08, 0.04], [1, 0.5], 0.2) * _rng.uniform(0.2, 0.9)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    out += 0.3 * bp(noise(dur), 500, 6000) * env(n, 0.002, 0.25)
    return norm(out, 0.95)


def bong(f=400):
    return norm(modal([f, f * 2.7, f * 5.2, f * 8.1], [0.9, 0.5, 0.3, 0.15], [1, 0.5, 0.35, 0.2], 1.4), 0.7)


def gen_engine(dur, start=False, die=False):
    t = t_(dur)
    if die:
        f = 28 * np.maximum(0.1, 1 - t / dur)
    elif start:
        f = 28 * np.minimum(1, 0.3 + t / 0.8)
    else:
        f = np.full_like(t, 28.0)
    ph = np.cumsum(f) / SR
    pulses = signal.square(2 * np.pi * ph, duty=0.15) * 0.5 + 0.5
    x = lp(pulses, 300) + 0.2 * lp(noise(dur), 500)
    e = np.ones_like(t)
    if die:
        e = np.maximum(0, 1 - t / dur)
    return norm(x * e, 0.35)


def sputter(dur=1.0):
    n = int(dur * SR)
    out = np.zeros(n)
    for k in range(9):
        pos = int((k * 0.1 + _rng.uniform(0, 0.05)) * SR)
        c = thud(_rng.uniform(40, 70), 0.12) * _rng.uniform(0.3, 0.8)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    return norm(out, 0.6)


def snore(dur=1.4, old=False):
    t = t_(dur)
    f = 55 if old else 75
    x = lp(noise(dur), 900) * (0.4 + 0.6 * (signal.square(2 * np.pi * f * t) * 0.5 + 0.5))
    x = lp(x, 1200)
    e = np.sin(np.pi * t / dur) ** 2
    return norm(x * e, 0.25)


def static(dur):
    return norm(bp(noise(dur), 500, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t_(dur))), 0.25)


def record_scratch():
    t = t_(0.6)
    rate = np.sin(2 * np.pi * 4 * t) * np.exp(-t / 0.3)
    x = bp(noise(0.6), 400, 4000) * np.abs(rate)
    x += 0.5 * np.sin(2 * np.pi * np.cumsum(300 + 900 * rate) / SR) * np.exp(-t / 0.2)
    return norm(x, 0.7)


def cloth(dur=0.3):
    n = int(dur * SR)
    return norm(bp(noise(dur), 400, 3000) * np.sin(np.pi * np.arange(n) / n) ** 2, 0.35)


def spring_squeeze(dur=0.5):
    return slide_whistle(300, 1200, dur, vib=14)


def siren(dur):
    t = t_(dur)
    f = 650 + 250 * np.sin(2 * np.pi * 0.7 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return norm(lp(x, 2500) * np.minimum(1, t / 0.5), 0.3)


def motor_whine(dur, f=900):
    t = t_(dur)
    ff = f * (1 + 0.15 * np.sin(2 * np.pi * 0.8 * t))
    x = signal.sawtooth(2 * np.pi * np.cumsum(ff) / SR)
    return norm(bp(x, 500, 4000) * np.minimum(1, t / 0.2) * np.minimum(1, (dur - t) / 0.5), 0.2)


def scrape(dur=1.0):
    t = t_(dur)
    x = bp(noise(dur), 1500, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * t))
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(700 + 150 * np.sin(2 * np.pi * 3 * t)) / SR)
    return norm(x * np.minimum(1, t / 0.1) * np.minimum(1, (dur - t) / 0.2), 0.25)


def wind(dur, strength=1.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = lp(x, 700) + 0.3 * bp(rng.standard_normal(n), 800, 2500)
    mod = lp(rng.standard_normal(n), 0.4, order=1)
    mod = 0.5 + 0.5 * mod / (np.max(np.abs(mod)) + 1e-9)
    return norm(x * mod, 0.22 * strength)


def hum(dur, f=50, level=0.08):
    t = t_(dur)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.25 * np.sin(2 * np.pi * 3 * f * t)
    return (x / 1.75 * level).astype(np.float32)


def clatter(dur=0.5, n_hits=8):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(n_hits):
        pos = int(_rng.uniform(0, 0.8) * n)
        c = modal([_rng.uniform(400, 2500)], [0.03], [1], 0.08) * _rng.uniform(0.3, 1.0)
        out[pos:pos + len(c)] += c[:len(out[pos:pos + len(c)])]
    return norm(out, 0.4)


def ratchet(dur=0.6):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(0, n, int(SR * 0.04)):
        c = modal([2500], [0.006], [1], 0.02)
        out[i:i + len(c)] += c[:len(out[i:i + len(c)])]
    return norm(out, 0.3)


def meow():
    t = t_(0.7)
    f = 500 + 300 * np.sin(np.pi * t / 0.7)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    out = bp(x, 700, 2500) * np.sin(np.pi * t / 0.7)
    return norm(out, 0.25)


def cluck():
    """Tin-chicken cluck: short metallic formant blips."""
    out = []
    for k in range(_rng.integers(2, 5)):
        t = t_(0.07)
        f = _rng.uniform(500, 700)
        x = signal.sawtooth(2 * np.pi * f * t) * np.exp(-t / 0.03)
        x = bp(x, 900, 3000) + 0.3 * modal([2400], [0.02], [1], 0.07)
        out.append(x)
        out.append(np.zeros(int(_rng.uniform(0.04, 0.1) * SR)))
    return norm(np.concatenate(out), 0.25)


def crickets(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    carrier = np.sin(2 * np.pi * 4700 * t)
    gate = (np.sin(2 * np.pi * 30 * t) > 0.3) * (np.sin(2 * np.pi * 1.1 * t) > 0.2)
    return norm(carrier * gate, 0.05)


def drone_chirp():
    return norm(sine_glide(2200, 3200, 0.06) * env(int(0.06 * SR), 0.002, 0.03), 0.12)
