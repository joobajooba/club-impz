"""Club Impz sound effects, synthesised (no sound files existed): footsteps per ground and the mobs' calls.
Writes 16-bit mono 22050 Hz .wav files to godot-game/assets/sounds/. numpy only.

  step_grass_1..4   soft crunch of grass and earth      step_snow_1..3   crisp squeak and crunch of snow
  step_stone_1..3   gritty tap on rock and gravel
  cow_moo_1..2      a low rising-falling "mmmooo"        highland_cow_moo_1  deeper, longer
  pig_oink_1..2     two or three short nasal grunts      wolf_howl_1      a long howl that rises and falls
  wolf_bark_1       two short barks                      ogre_grunt_1..2  low growling grunts
  golem_rumble_1    grinding stone rumble                dragon_roar_1    a big ragged roar (the dark dragon)
  ember_roar_1      deeper roar with fire crackle        pale_screech_1   a high icy screech (pale dragon)
"""
import math, os, wave
import numpy as np

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "godot-game", "assets", "sounds")
rng = np.random.default_rng(42)


def t_(sec): return np.arange(int(SR * sec)) / SR


def biquad(x, kind, f, q=0.707, gain_db=0.0):
    """RBJ cookbook biquad (lowpass, highpass, bandpass, peak). f may be an array (a sweeping filter)."""
    n = len(x)
    f = np.broadcast_to(np.asarray(f, float), (n,))
    y = np.zeros(n)
    x1 = x2 = y1 = y2 = 0.0
    A = 10 ** (gain_db / 40)
    step = 32                                            # recompute coefficients every 32 samples
    for i0 in range(0, n, step):
        w0 = 2 * math.pi * min(f[i0], SR * 0.45) / SR
        cs, sn = math.cos(w0), math.sin(w0)
        al = sn / (2 * q)
        if kind == "lp": b0, b1, b2, a0, a1, a2 = (1 - cs) / 2, 1 - cs, (1 - cs) / 2, 1 + al, -2 * cs, 1 - al
        elif kind == "hp": b0, b1, b2, a0, a1, a2 = (1 + cs) / 2, -(1 + cs), (1 + cs) / 2, 1 + al, -2 * cs, 1 - al
        elif kind == "bp": b0, b1, b2, a0, a1, a2 = al, 0, -al, 1 + al, -2 * cs, 1 - al
        else: b0, b1, b2, a0, a1, a2 = 1 + al * A, -2 * cs, 1 - al * A, 1 + al / A, -2 * cs, 1 - al / A
        b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
        for i in range(i0, min(n, i0 + step)):
            xi = x[i]
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, xi, y1, yi
            y[i] = yi
    return y


def env(n, attack, release, hold=0.0, curve=2.0):
    """Attack-hold-release envelope over n samples (seconds)."""
    t = np.arange(n) / SR
    e = np.ones(n)
    a = int(attack * SR); r = int(release * SR)
    if a: e[:a] = (np.arange(a) / a) ** 0.7
    if r: e[-r:] *= (1 - np.arange(r) / r) ** curve
    return e


def saw(freq, n):
    ph = np.cumsum(np.broadcast_to(freq, (n,)) / SR)
    return 2 * (ph % 1.0) - 1


def pulse(freq, n, width=0.3):
    ph = np.cumsum(np.broadcast_to(freq, (n,)) / SR)
    return np.where((ph % 1.0) < width, 1.0, -1.0)


def noise(n): return rng.standard_normal(n)


def norm(x, peak=0.9):
    x = x - np.mean(x)
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def fade(x, ms=8):
    k = int(SR * ms / 1000)
    x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
    return x


def write(name, x, peak=0.9):
    x = fade(norm(x, peak))
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print(f"{name:20s} {len(x) / SR:.2f}s")


# ---- footsteps ---------------------------------------------------------------------------------------
def step_grass(seed):
    r = np.random.default_rng(seed)
    n = int(SR * 0.22)
    x = r.standard_normal(n)
    x = biquad(x, "bp", 700 + r.uniform(-150, 150), 0.9) * 1.0 + biquad(x, "lp", 2600, 0.7) * 0.35
    thud = np.sin(2 * math.pi * (80 + r.uniform(-10, 10)) * t_(0.22)) * np.exp(-t_(0.22) * 38)
    crunch = np.zeros(n)
    for _ in range(9):                                    # little crackles of grass
        i = int(r.uniform(0.0, 0.12) * SR)
        crunch[i:i + 60] += r.standard_normal(60) * np.exp(-np.arange(60) / 14)
    crunch = biquad(crunch, "hp", 1800)
    e = np.exp(-t_(0.22) * 22) * env(n, 0.004, 0.06)
    return (x * 0.8 + crunch * 0.6) * e + thud * 0.7


def step_snow(seed):
    r = np.random.default_rng(seed)
    n = int(SR * 0.26)
    x = np.zeros(n)
    for _ in range(40):                                   # many tiny squeaky crunches
        i = int(r.uniform(0.0, 0.17) * SR)
        L = int(r.uniform(20, 70))
        x[i:i + L] += r.standard_normal(L) * np.exp(-np.arange(L) / (L / 3))
    x = biquad(x, "bp", 2400 + r.uniform(-300, 300), 0.8) + biquad(x, "lp", 900) * 0.5
    thud = np.sin(2 * math.pi * 70 * t_(0.26)) * np.exp(-t_(0.26) * 30) * 0.5
    return x * np.exp(-t_(0.26) * 12) * env(n, 0.01, 0.08) + thud


def step_stone(seed):
    r = np.random.default_rng(seed)
    n = int(SR * 0.18)
    tap = np.sin(2 * math.pi * (190 + r.uniform(-30, 30)) * t_(0.18)) * np.exp(-t_(0.18) * 60)
    grit = biquad(r.standard_normal(n), "bp", 3000 + r.uniform(-500, 500), 1.2) * np.exp(-t_(0.18) * 35)
    click = biquad(r.standard_normal(n), "hp", 1200) * np.exp(-t_(0.18) * 140)
    return tap * 0.9 + grit * 0.7 + click * 0.6


# ---- animals -----------------------------------------------------------------------------------------
def voice(f0, dur, formants, vib=(5.0, 0.02), breath=0.08, open_curve=None, src="saw"):
    """A voiced call: a pitch curve f0(t) through formant band-passes, with vibrato and a little breath."""
    n = int(SR * dur)
    t = t_(dur)
    f = np.asarray(f0(t / dur), float) * (1 + vib[1] * np.sin(2 * math.pi * vib[0] * t))
    s = saw(f, n) if src == "saw" else pulse(f, n, 0.35)
    s = s + breath * noise(n)
    out = np.zeros(n)
    for fc, q, g in formants:
        fcs = fc(t / dur) if callable(fc) else fc
        out += biquad(s, "bp", fcs, q) * g
    if open_curve is not None:
        out = biquad(out, "lp", open_curve(t / dur))
    return out


def cow(seed, low=1.0, dur=1.5):
    r = np.random.default_rng(seed)
    d = dur * r.uniform(0.9, 1.1)
    base = 118 * low * r.uniform(0.95, 1.05)
    f0 = lambda u: base * (0.85 + 0.25 * np.sin(np.pi * np.clip(u * 1.15, 0, 1)) - 0.12 * u)
    x = voice(f0, d, [(lambda u: 320 + 380 * np.sin(np.pi * np.clip(u * 1.2, 0, 1)), 4, 1.0), (1100, 6, 0.35), (2400, 8, 0.12)],
              vib=(4.5, 0.015), breath=0.05, open_curve=lambda u: 500 + 2200 * np.sin(np.pi * np.clip(u * 1.1, 0, 1)) ** 1.5)
    return x * env(len(x), 0.18, 0.5, curve=1.5)


def pig(seed):
    r = np.random.default_rng(seed)
    parts = []
    for k in range(r.integers(2, 4)):
        d = r.uniform(0.11, 0.18)
        base = r.uniform(170, 230)
        f0 = lambda u, b=base: b * (1.1 - 0.3 * u)
        g = voice(f0, d, [(900, 5, 1.0), (2200, 7, 0.5), (400, 4, 0.5)], vib=(30, 0.06), breath=0.35, src="pulse")
        g = g * env(len(g), 0.01, 0.05)
        parts.append(g); parts.append(np.zeros(int(SR * r.uniform(0.05, 0.12))))
    return np.concatenate(parts)


def wolf_howl(seed):
    d = 2.6
    f0 = lambda u: 380 + 260 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) ** 0.6 - 120 * np.clip(u - 0.7, 0, 1) * 3
    n = int(SR * d)
    t = t_(d)
    f = f0(t / d) * (1 + 0.012 * np.sin(2 * math.pi * 5.5 * t))
    tone = np.sin(2 * math.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * math.pi * np.cumsum(f) / SR)
    x = tone + 0.12 * biquad(noise(n), "bp", f.mean(), 3)
    x = biquad(x, "lp", 2200)
    return x * env(n, 0.25, 0.9, curve=1.2)


def wolf_bark(seed):
    r = np.random.default_rng(seed)
    parts = []
    for k in range(2):
        d = 0.16
        g = voice(lambda u: 420 * (1.15 - 0.4 * u), d, [(900, 3, 1.0), (1800, 5, 0.6)], vib=(0, 0), breath=0.5)
        parts.append(g * env(len(g), 0.005, 0.1)); parts.append(np.zeros(int(SR * 0.14)))
    return np.concatenate(parts)


def ogre_grunt(seed):
    r = np.random.default_rng(seed)
    d = r.uniform(0.7, 1.0)
    base = r.uniform(78, 95)
    x = voice(lambda u: base * (1.05 - 0.2 * u), d, [(450, 3, 1.0), (900, 5, 0.5), (220, 3, 0.6)], vib=(22, 0.08), breath=0.25)
    rough = 1 + 0.5 * np.sign(np.sin(2 * math.pi * 31 * t_(len(x) / SR)))      # a gravelly flutter
    return x * rough * env(len(x), 0.04, 0.3)


def golem_rumble(seed):
    d = 2.2
    n = int(SR * d)
    t = t_(d)
    low = np.sin(2 * math.pi * np.cumsum(42 + 8 * np.sin(2 * math.pi * 0.7 * t)) / SR)
    grind = biquad(noise(n), "bp", 260 + 120 * np.sin(2 * math.pi * 1.3 * t), 1.5) * (0.5 + 0.5 * np.abs(np.sin(2 * math.pi * 6 * t)))
    cracks = np.zeros(n)
    for _ in range(14):
        i = int(rng.uniform(0, d - 0.05) * SR)
        cracks[i:i + 220] += biquad(noise(220), "bp", 1500, 2) * np.exp(-np.arange(220) / 40)
    x = low * 1.0 + grind * 0.8 + cracks * 0.5
    return x * env(n, 0.3, 0.8)


def roar(seed, base=70, dur=1.9, bright=1.0, crackle=0.0):
    n = int(SR * dur)
    t = t_(dur)
    u = t / dur
    f = base * (0.9 + 0.5 * np.sin(np.pi * np.clip(u * 1.2, 0, 1)) - 0.2 * u)
    s = saw(f * (1 + 0.03 * noise(n).cumsum() / np.sqrt(np.arange(1, n + 1))), n)
    s = np.tanh(3 * (s + 0.6 * noise(n)))                                      # ragged and throaty
    x = biquad(s, "bp", (500 + 900 * np.sin(np.pi * np.clip(u * 1.1, 0, 1))) * bright, 1.2)
    x += biquad(s, "lp", 300) * 0.8
    if crackle:
        c = np.zeros(n)
        for _ in range(int(60 * crackle)):
            i = int(rng.uniform(0, dur - 0.02) * SR)
            c[i:i + 90] += noise(90) * np.exp(-np.arange(90) / 12)
        x += biquad(c, "hp", 2500) * 0.6
    return x * env(n, 0.12, 0.7, curve=1.4)


def screech(seed):
    d = 1.4
    n = int(SR * d)
    t = t_(d)
    u = t / d
    f = 900 + 700 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) - 300 * u
    s = saw(f * (1 + 0.02 * np.sin(2 * math.pi * 9 * t)), n) + 0.5 * noise(n)
    x = biquad(s, "bp", 2400 + 800 * np.sin(np.pi * u), 2.5) + biquad(s, "bp", 4200, 4) * 0.5
    shimmer = biquad(noise(n), "hp", 6000) * 0.15                              # icy hiss
    return (x + shimmer) * env(n, 0.06, 0.6)


for i in range(4): write(f"step_grass_{i + 1}", step_grass(10 + i), 0.8)
for i in range(3): write(f"step_snow_{i + 1}", step_snow(20 + i), 0.8)
for i in range(3): write(f"step_stone_{i + 1}", step_stone(30 + i), 0.8)
for i in range(2): write(f"cow_moo_{i + 1}", cow(40 + i))
write("highland_cow_moo_1", cow(50, low=0.82, dur=1.9))
for i in range(2): write(f"pig_oink_{i + 1}", pig(60 + i))
write("wolf_howl_1", wolf_howl(70), 0.8)
write("wolf_bark_1", wolf_bark(71))
for i in range(2): write(f"ogre_grunt_{i + 1}", ogre_grunt(80 + i))
write("golem_rumble_1", golem_rumble(90))
write("dragon_roar_1", roar(100, base=75, dur=1.9))
write("ember_roar_1", roar(101, base=55, dur=2.3, bright=0.8, crackle=1.0))
write("pale_screech_1", screech(102), 0.8)


# ---- tools and items ---------------------------------------------------------------------------------
def pick_hit(seed):
    """Pickaxe on stone: a bright metallic ring over a short crack of stone."""
    r = np.random.default_rng(seed)
    d = 0.45
    n = int(SR * d)
    t = t_(d)
    ring = sum(np.sin(2 * math.pi * f * r.uniform(0.97, 1.03) * t) * a * np.exp(-t * k)
               for f, a, k in ((1850, 1.0, 11), (2930, 0.6, 15), (4410, 0.35, 22), (6200, 0.2, 30)))
    crack = biquad(r.standard_normal(n), "bp", 1600, 0.9) * np.exp(-t * 45)
    thud = np.sin(2 * math.pi * 140 * t) * np.exp(-t * 40)
    return ring * 0.55 + crack * 1.0 + thud * 0.6


def pop(seed, up=True):
    d = 0.16
    t = t_(d)
    f = (520 + 900 * t / d) if up else (900 - 500 * t / d)
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 26) + 0.2 * biquad(noise(len(t)), "hp", 3000) * np.exp(-t * 60)


for i in range(3): write(f"pick_hit_{i + 1}", pick_hit(110 + i), 0.75)
write("item_pickup", pop(120, True), 0.6)
write("item_drop", pop(121, False), 0.6)
