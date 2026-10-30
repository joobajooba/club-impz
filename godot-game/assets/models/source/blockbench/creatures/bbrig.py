"""Rig helpers for the creatures whose animations are solved, not only keyed.

Used by build_eagle_bbmodel.py and build_dragon_bbmodel.py, on top of
bbcreature.py:
- RigCreature: a Creature whose boxes can keep faces that are covered at
  rest, because an animation opens them up (under a wing, inside a mouth).
- Blockbench's key convention and forward kinematics over the bone tree, so
  a script can ask where a bone is in the world on any frame.
- Two-bone leg IK, turned into keys every frame, so feet stay planted while
  the body above them moves.

Blockbench 5.2.2 applies a rotation key as (-x, -y, +z) on top of the bone's
rest rotation (checked against Blockbench's own animator on the eagle), and
a position key as an offset (-x, +y, +z). Angles are degrees; positions are
texture pixels (px).
"""

import math

import numpy as np

from bbcreature import Creature, face_frame, rot_matrix, track, turn_about

FPS = 24
PX = 0.5


class RigCreature(Creature):
    """Elements may list faces to keep (e["keep"]) although they are covered
    at rest."""

    def visible_faces(self):
        vis = super().visible_faces()
        for ei, e in enumerate(self.elements):
            for f in e.get("keep", ()):
                _, _, _, w, h = face_frame(e, f)
                vis[(ei, f)] = (int(w), int(h))
        return vis


# ---------------------------------------------------------------- keys

def ease(keys):
    """A function of time through (t, value) keys, eased in and out."""
    def f(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                u = u * u * (3 - 2 * u)
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * u for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * u
        return keys[-1][1]
    return f


def const(v):
    return lambda t: v


def frames(length):
    return [round(k / FPS, 4) for k in range(round(length * FPS) + 1)]


def sampled(channel, length, fn):
    """A key every frame, linear between them."""
    return track(channel, [(t, tuple(round(c, 3) for c in fn(t))) for t in frames(length)],
                 interp="linear")


def lin(*keys):
    return track("rotation", keys, interp="linear")


def pair(bone, keys, interp="linear"):
    """Rotation tracks for a right/left pair ("wing_*") from right-side keys;
    the left mirrors y and z."""
    return {bone.replace("*", "right"): track("rotation", keys, interp),
            bone.replace("*", "left"): track("rotation", [(t, (x, -y, -z)) for t, (x, y, z) in keys],
                                             interp)}


def euler(R):
    """Blockbench (ZYX) Euler angles of a rotation matrix."""
    b = math.asin(max(-1.0, min(1.0, -R[2][0])))
    a = math.atan2(R[2][1], R[2][2])
    c = math.atan2(R[1][0], R[0][0])
    return tuple(math.degrees(v) for v in (a, b, c))


def key_to_math(rest, key):
    return (rest[0] - key[0], rest[1] - key[1], rest[2] + key[2])


def math_to_key(rest, m):
    return (rest[0] - m[0], rest[1] - m[1], m[2] - rest[2])


# ---------------------------------------------------------------- kinematics

def world(bones, bone, rot, pos):
    """A bone's world matrix (4x4, px) for rotation and position keys given
    as {bone: (x, y, z)}; bones without keys sit at rest."""
    chain = []
    b = bone
    while b:
        chain.append(b)
        b = bones[b][0]
    M = np.eye(4)
    for b in reversed(chain):
        _, piv, rest = bones[b]
        kx, ky, kz = pos.get(b, (0, 0, 0))
        T = np.eye(4)
        T[:3, 3] = (-kx, ky, kz)
        M = M @ T @ turn_about(key_to_math(rest, rot.get(b, (0, 0, 0))), piv)
    return M


def two_bone(h, a, l1, l2, bend=1):
    """World pitch (degrees, 0 = straight down) of the upper and lower bone
    putting the end on a, from the joint at h, both (y, z) px. bend=1 puts
    the middle joint behind the line (a bird's heel, a dog's elbow), -1 in
    front of it (a knee). Out of reach, the limb points straight at a."""
    v = np.array(a, float) - np.array(h, float)
    u = v / max(float(np.linalg.norm(v)), 1e-6)
    d = min(max(float(np.linalg.norm(v)), abs(l1 - l2) + 1e-6), l1 + l2 - 1e-6)
    n = np.array([-u[1], u[0]])
    if n[1] * bend < 0:
        n = -n
    x = (d * d + l1 * l1 - l2 * l2) / (2 * d)
    k = np.array(h, float) + u * x + n * math.sqrt(max(0.0, l1 * l1 - x * x))
    e = np.array(h, float) + u * d
    u1, u2 = (k - h) / l1, (e - k) / l2
    return math.degrees(math.atan2(-u1[1], -u1[0])), math.degrees(math.atan2(-u2[1], -u2[0]))


def pitch(at):
    return rot_matrix(at, 0, 0)


def solve_legs(bones, length, legs, rot=None, pos=None):
    """Keys every frame for three-bone legs (upper > lower > foot) whose rest
    pose stands straight down. legs: [(upper, lower, foot, bend, spec)];
    spec(t) gives ("plant", (y, z) world target for the foot's pivot, foot
    pitch) or ("free", (upper, lower, foot) world pitch). rot/pos: {bone:
    fn(t) -> key} for the bones above the legs."""
    rot, pos = rot or {}, pos or {}
    out = {}
    for upper, lower, foot, bend, spec in legs:
        p_u, p_l, p_f = (np.array(bones[b][1], float) for b in (upper, lower, foot))
        l1 = float(np.linalg.norm((p_l - p_u)[1:]))
        l2 = float(np.linalg.norm((p_f - p_l)[1:]))
        rest_u = bones[upper][2]
        keys = {upper: [], lower: [], foot: []}
        for t in frames(length):
            rk = {b: f(t) for b, f in rot.items()}
            pk = {b: f(t) for b, f in pos.items()}
            Mp = world(bones, bones[upper][0], rk, pk)
            hip = (Mp @ np.array([*p_u, 1.0]))[:3]
            mode, *args = spec(t)
            if mode == "plant":
                target, phi = args
                at, al = two_bone((hip[1], hip[2]), target, l1, l2, bend)
            else:
                at, al, phi = args[0]
            local = euler(Mp[:3, :3].T @ pitch(at))
            keys[upper].append((t, math_to_key(rest_u, local)))
            keys[lower].append((t, (at - al, 0, 0)))
            keys[foot].append((t, (al - phi, 0, 0)))
        for b, ks in keys.items():
            out[b] = track("rotation", [(t, tuple(round(c, 3) for c in v)) for t, v in ks], "linear")
    return out


def stride(period, phase, rest, reach, lift, duty=0.55, toe=8):
    """An in-place step for a foot whose rest pivot is at rest=(y, z): it
    slides back along the ground through the stance, then lifts and swings
    forward. Returns spec(t) for solve_legs."""
    y0, z0 = rest

    def spec(t):
        u = ((t / period) + phase) % 1.0
        if u < duty:
            s = u / duty
            return ("plant", (y0, z0 - reach + 2 * reach * s), 0)
        s = (u - duty) / (1 - duty)
        z = z0 + reach - 2 * reach * (s * s * (3 - 2 * s))
        return ("plant", (y0 + lift * math.sin(math.pi * s), z), toe * math.sin(math.pi * s))
    return spec
