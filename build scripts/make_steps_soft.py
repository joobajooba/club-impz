"""Soft footsteps (replaces the step_* sounds of make_sounds.py, which J00BA found harsh).

A footstep is mostly a low, muffled thump with a little brush of the ground on top:
  heel   a soft low thud: a sine that drops 110 -> 65 Hz, plus low band noise (the body of the step)
  roll   ~35 ms later a quieter, muffled scuff as the foot rolls (low-passed noise, no crackle)
Everything goes through a gentle low-pass, starts with a 7 ms fade (no click) and dies away smoothly.
  grass  muffled, a touch of leafy brush (low-pass ~1.6 kHz)
  snow   a soft compressed crunch (band 700-1500 Hz, gently grained), still low-passed
  stone  a soft muted tap (a little higher thud, short), no clicks
Writes step_<ground>_<n>.wav (22050 Hz, 16 bit mono) to godot-game/assets/sounds/.
"""
import math, os, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
_spec = importlib.util.spec_from_file_location('ms_filters', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_sounds.py'))
SR = 22050


def biquad(*a, **k):
    return _filters().biquad(*a, **k)


_mod = None


def _filters():
    global _mod
    if _mod is None:
        src = open(_spec.origin, encoding='utf8').read().split('# ---- footsteps')[0]   # the filters only, no writing
        _mod = type(sys)('ms_filters'); exec(src, _mod.__dict__)
    return _mod

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "godot-game", "assets", "sounds")


def t_(sec): return np.arange(int(SR * sec)) / SR


def smooth_env(n, attack=0.007, decay=12.0):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    a = 0.5 - 0.5 * np.cos(np.pi * a)                    # click-free start
    tail = np.ones(n)
    k = int(0.04 * SR)
    tail[-k:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, k))   # and a clean end
    return a * np.exp(-t * decay) * tail


def step(ground, seed):
    r = np.random.default_rng(seed)
    dur = 0.30
    n = int(SR * dur)
    t = t_(dur)
    # heel: a soft low thud
    f0 = {"grass": 105, "snow": 95, "stone": 150}[ground] * r.uniform(0.92, 1.08)
    f = f0 * (0.62 + 0.38 * np.exp(-t * 30))
    thud = np.sin(2 * math.pi * np.cumsum(f) / SR) * smooth_env(n, 0.006, {"grass": 26, "snow": 24, "stone": 40}[ground])
    body = biquad(r.standard_normal(n), "lp", 380) * smooth_env(n, 0.008, 30) * 0.6
    # roll: a quieter scuff a moment later
    lag = int(r.uniform(0.03, 0.045) * SR)
    sc = np.zeros(n)
    src = r.standard_normal(n - lag)
    if ground == "grass":
        brush = biquad(biquad(src, "lp", 1600), "hp", 180) * 1.1
    elif ground == "snow":
        grain = 1 + 0.6 * np.sign(r.standard_normal(n - lag)) * (r.random(n - lag) < 0.08)   # gentle packing grains
        brush = biquad(biquad(src * grain, "bp", 1100, 0.7), "lp", 2200) * 1.6
    else:
        brush = biquad(biquad(src, "bp", 700, 0.9), "lp", 1800) * 0.8
    sc[lag:] = brush * smooth_env(n - lag, 0.012, {"grass": 18, "snow": 13, "stone": 30}[ground])
    x = thud * 0.9 + body + sc
    x = biquad(x, "lp", {"grass": 2400, "snow": 2800, "stone": 2600}[ground])   # nothing harsh
    x -= x.mean()
    return x / (np.max(np.abs(x)) or 1) * 0.6


def write(name, x):
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    spec = np.abs(np.fft.rfft(x)) ** 2
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    centroid = (spec * fr).sum() / spec.sum()
    low = spec[fr < 500].sum() / spec.sum()
    hi = spec[fr > 3000].sum() / spec.sum()
    onset = np.max(np.abs(np.diff(x[:int(0.01 * SR)])))
    print(f"{name:14s} centroid {centroid:6.0f} Hz   energy <500 Hz {low * 100:4.0f}%   >3 kHz {hi * 100:5.2f}%   start slope {onset:.3f}")


if __name__ == "__main__":
    for i in range(4): write(f"step_grass_{i + 1}", step("grass", 200 + i))
    for i in range(3): write(f"step_snow_{i + 1}", step("snow", 300 + i))
    for i in range(3): write(f"step_stone_{i + 1}", step("stone", 400 + i))
