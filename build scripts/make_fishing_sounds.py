"""Club Impz fishing sounds, synthesised (scripts/player/fisher.gd plays them). Standard library only.
Writes 16-bit mono 22050 Hz .wav files to godot-game/assets/sounds/, like make_sounds.py.

  fish_plop     the float lands on the water: a soft rising "plip" over a little splash
  fish_nibble   a fish nibbles the bait: two tiny bloops
  fish_splash   the fish bites or comes out of the water: a short splash of water
"""
import math, os, random, struct, wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "godot-game", "assets", "sounds")
rnd = random.Random(7)


def lowpass(xs, cutoff):
    a = 1.0 - math.exp(-2.0 * math.pi * cutoff / SR)
    y, out = 0.0, []
    for x in xs:
        y += a * (x - y)
        out.append(y)
    return out


def bloop(dur, f0, f1, decay, at=0.0, total=None):
    """A water drop: a sine whose pitch rises quickly from f0 to f1, dying away."""
    n = int(SR * (total or dur))
    out = [0.0] * n
    phase = 0.0
    start = int(SR * at)
    for i in range(int(SR * dur)):
        t = i / SR
        f = f1 + (f0 - f1) * math.exp(-t * 40.0)
        phase += 2.0 * math.pi * f / SR
        if start + i < n:
            out[start + i] = math.sin(phase) * math.exp(-t * decay) * min(1.0, t / 0.003)
    return out


def splash(dur, cutoff, attack, decay):
    xs = [rnd.uniform(-1.0, 1.0) for _ in range(int(SR * dur))]
    xs = lowpass(lowpass(xs, cutoff), cutoff * 1.5)
    return [x * min(1.0, (i / SR) / attack) * math.exp(-(i / SR) * decay) for i, x in enumerate(xs)]


def mix(*tracks):
    n = max(len(t) for t, _ in tracks)
    out = [0.0] * n
    for t, g in tracks:
        for i, x in enumerate(t):
            out[i] += x * g
    return out


def write(name, xs, peak=0.8):
    m = max(abs(x) for x in xs) or 1.0
    fade = int(SR * 0.01)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i, x in enumerate(xs):
            g = min(1.0, (len(xs) - i) / fade)
            frames += struct.pack("<h", int(max(-1.0, min(1.0, x / m * peak * g)) * 32767))
        w.writeframes(bytes(frames))


write("fish_plop", mix((bloop(0.22, 260, 820, 24), 1.0), (splash(0.22, 2200, 0.004, 26), 0.45)), 0.55)
write("fish_nibble", mix((bloop(0.07, 520, 1050, 60, 0.0, 0.2), 1.0), (bloop(0.07, 560, 1150, 60, 0.09, 0.2), 0.8)), 0.4)
write("fish_splash", mix((splash(0.6, 1700, 0.006, 7.5), 1.0), (bloop(0.2, 300, 900, 20), 0.5),
                         (bloop(0.15, 380, 1100, 26, 0.12, 0.6), 0.35)), 0.7)
print("fishing sounds written to", os.path.normpath(OUT))
