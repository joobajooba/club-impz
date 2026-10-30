"""What the Blockbench dragons share: the scale-painting patterns, and the
movement (the leg IK wiring, neck poses, tail secondary motion and every
animation), written once for any dragon built on the same skeleton.

Used by build_dragon_bbmodel.py and build_pale_dragon_bbmodel.py. A dragon
calls moves() with its bones and a few measurements and gets its animation
functions back; the skeleton contract is the bone names and joint layout of
build_dragon_bbmodel.py: legs hang from joints at the underside (arm >
forearm > hand bends back at the elbow, thigh > leg > foot forward at the
knee), the neck is three segments bent into an S by the 3-4-5 angle with
the head turned back level, wings fold along the flanks and open with x then
z, and the tail is three segments whose rest rotations are its droop.

Keys are in Blockbench's convention (bbrig.py): a positive x pitches a part
down at its front (the head) or up at its back (the tail), a positive y
turns it to its right, a positive z rolls the right side up.
"""

import math

import numpy as np

from bbcreature import fi, rot, track
from bbrig import const, ease, frames, lin, pair, sampled, solve_legs, two_bone, world
from bbrig import stride as rig_stride

# ---------------------------------------------------------------- scale painting

def scales(a, b, v, w=4):
    """Scale rows: scales w px wide and 3 rows tall, every other row offset
    by half a scale. Each scale has one dark seam pixel at its lower corner
    and one lit pixel at its top, so the rows read as overlapping scales
    without turning into a checkerboard. a runs along a row, b counts rows
    upward."""
    r = b // 3
    c = (a + (r % 2) * (w // 2)) % w
    if b % 3 == 0 and c == 0:
        return v - 1
    if b % 3 == 2 and c == w // 2:
        return v + 1
    return v


def plates(b, v):
    """Banded belly plates: 2 px tall, a dark seam under each."""
    return v - 1 if b % 2 == 0 else v


def side_coords(t):
    """(along, up) on a side face, so rows run along the body."""
    x, y, z = t.p
    if t.f in ("east", "west"):
        return fi(-z), fi(y)
    if t.f in ("north", "south"):
        return fi(x), fi(y)
    return fi(x), fi(-z)


# ---------------------------------------------------------------- movement

ANIMATION_NAMES = ("idle", "look", "walk", "run", "turn_left", "turn_right", "roar", "attack",
                   "claw", "hit", "takeoff", "fly", "glide", "hover", "land")


def moves(BONES, TILT, HAND=(3, -12), FOOT=(3, 6), WING_UP=75, FLY_HEIGHT=30, LEGS_TUCKED=None,
          ROAR_TAIL_LIFT=6):
    """The animation functions for a dragon. HAND and FOOT are the hand's and
    foot's pivots at rest (y, z px); WING_UP the wing x key that raises a
    folded wing straight up (90 + its rest x); FLY_HEIGHT the px the flight
    set holds it above the ground; LEGS_TUCKED the legs' world pitch in
    flight; ROAR_TAIL_LIFT how far the tail lifts as it rears to roar (a long
    tail needs more to clear the ground). Returns {name: function}; walk
    takes turn (-1, 0, 1)."""
    LEGS_TUCKED = LEGS_TUCKED or {"front": (15, -75, -40), "hind": (-10, -80, -60)}


    ZERO = const((0, 0, 0))


    def legs(length, body_rot=ZERO, body_pos=ZERO, root_pos=ZERO, **spec):
        """Keys for all four legs. spec: front_right, front_left, hind_right,
        hind_left -> spec(t) (bbrig.solve_legs); default planted at rest."""
        plant_hand = const(("plant", HAND, 0))
        plant_foot = const(("plant", FOOT, 0))
        chains = [
            ("arm_right", "forearm_right", "hand_right", 1, spec.get("front_right", plant_hand)),
            ("arm_left", "forearm_left", "hand_left", 1, spec.get("front_left", plant_hand)),
            ("thigh_right", "leg_right", "foot_right", -1, spec.get("hind_right", plant_foot)),
            ("thigh_left", "leg_left", "foot_left", -1, spec.get("hind_left", plant_foot)),
        ]
        return solve_legs(BONES, length, chains, rot={"body": body_rot},
                          pos={"body": body_pos, "dragon": root_pos})


    def lifted(kind, side, keys, body_rot, body_pos=ZERO, root_pos=ZERO):
        """A leg leaving and rejoining the ground. keys: [(t, pose)], pose a
        (upper, lower, foot) world pitch, or None for planted at that moment.
        Between two planted keys the leg stays planted; otherwise it eases from
        pose to pose, starting and ending on the exact planted solve, so it never
        pops."""
        upper = ("arm_" if kind == "front" else "thigh_") + side
        lower = ("forearm_" if kind == "front" else "leg_") + side
        rest = HAND if kind == "front" else FOOT
        bend = 1 if kind == "front" else -1
        l1 = abs(BONES[upper][1][1] - BONES[lower][1][1])
        l2 = abs(BONES[lower][1][1] - rest[0])

        def planted_pose(t):
            M = world(BONES, "body", {"body": body_rot(t)}, {"body": body_pos(t), "dragon": root_pos(t)})
            hip = (M @ np.array([*BONES[upper][1], 1.0]))[:3]
            return (*two_bone((hip[1], hip[2]), rest, l1, l2, bend), 0.0)

        poses = [(t, planted_pose(t) if p is None else p) for t, p in keys]
        f = ease(poses)

        def spec(t):
            for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
                if t0 <= t <= t1:
                    if p0 is None and p1 is None:
                        return ("plant", rest, 0)
                    return ("free", f(t))
            p = keys[0][1] if t < keys[0][0] else keys[-1][1]
            return ("plant", rest, 0) if p is None else ("free", p)
        return spec


    def gait(period, phases, reach, lift, duty):
        """Four legs stepping in place. phases: front_right, front_left,
        hind_right, hind_left as fractions of the cycle."""
        fr, fl, hr, hl = phases
        return {"front_right": rig_stride(period, fr, HAND, reach, lift, duty, 20),
                "front_left": rig_stride(period, fl, HAND, reach, lift, duty, 20),
                "hind_right": rig_stride(period, hr, FOOT, reach, lift, duty, 20),
                "hind_left": rig_stride(period, hl, FOOT, reach, lift, duty, 20)}


    def wings(**k):
        """Wing segments from right-side keys: wing=[...], mid=[...], tip=[...]."""
        interp = k.get("interp", "linear")
        out = {}
        for part, bone in (("wing", "wing_*"), ("mid", "wing_mid_*"), ("tip", "wing_tip_*")):
            if part in k:
                out.update(pair(bone, k[part], interp))
        return out


    # Neck poses are the pitch of each segment and the head in the body's frame
    # (0 = upright for the neck, level for the head; negative leans forward or
    # looks down). neck_pose turns them into keys; yaw and roll spread along the
    # neck, the head taking the most.
    REST_NECK = (-TILT, 0.0, TILT, 0.0)
    NECK_CHAIN = ("neck_base", "neck_mid", "neck_upper", "head")
    YAW_SHARE = (0.2, 0.25, 0.25, 0.3)


    def neck_keys(pose, yaw=0.0, roll=0.0):
        base, mid, upper, head = pose
        rel = (base, mid - base, upper - mid, head - upper)
        rest = (-TILT, TILT, TILT, -TILT)
        return {b: (rest[i] - rel[i], yaw * YAW_SHARE[i], roll * YAW_SHARE[i])
                for i, b in enumerate(NECK_CHAIN)}


    def neck_track(keys, interp="catmullrom"):
        """keys: [(t, pose)] or [(t, pose, yaw)] or [(t, pose, yaw, roll)]."""
        out = {b: [] for b in NECK_CHAIN}
        for k in keys:
            t, pose, *yr = k
            for b, v in neck_keys(pose, *yr).items():
                out[b].append((t, tuple(round(c, 3) for c in v)))
        return {b: track("rotation", ks, interp) for b, ks in out.items()}


    def neck_sampled(length, fn):
        """fn(t) -> (pose, yaw, roll), keyed every frame."""
        out = {b: [] for b in NECK_CHAIN}
        for t in frames(length):
            for b, v in neck_keys(*fn(t)).items():
                out[b].append((t, tuple(round(c, 3) for c in v)))
        return {b: track("rotation", ks, "linear") for b, ks in out.items()}


    def offset(pose, d):
        return tuple(a + b for a, b in zip(pose, d))


    def tail_wave(length, amp_y, amp_x=0.0, cycles=1, lag=0.12, bias=(0, 0, 0)):
        """Secondary motion down the tail: each segment follows the one before
        a little later and a little wider. bias[0] > 0 lifts the tail."""
        out = {}
        for i, b in enumerate(("tail", "tail_mid", "tail_end")):
            g = 1 + 0.35 * i
            out[b] = sampled("rotation", length, lambda t, i=i, g=g: (
                bias[0] + amp_x * g * math.sin(2 * math.pi * (cycles * t / length - lag * i) + 1.2),
                bias[1] + amp_y * g * math.sin(2 * math.pi * (cycles * t / length - lag * i)),
                bias[2]))
        return out


    TAIL_STRAIGHT = {b: (BONES[b][2][0], 0, 0) for b in ("tail", "tail_mid", "tail_end")}

    # Fly's first frame: takeoff ends on it, land starts on it.
    FLY_NECK = (-55, -55, -55, 0)
    FLY_START = {"wing": (WING_UP, 0, -40), "mid": (0, 0, 0), "tip": (0, 0, 0)}


    def free_legs(pose):
        return {"front_right": const(("free", pose["front"])), "front_left": const(("free", pose["front"])),
                "hind_right": const(("free", pose["hind"])), "hind_left": const(("free", pose["hind"]))}


    def idle():
        L = 4.0
        return {"loop": "loop", "length": L, "bones": {
            "body": track("scale", [(0, (1, 1, 1)), (1.0, (1.025, 1, 1.01)), (2.0, (1, 1, 1)),
                                    (3.0, (1.025, 1, 1.01)), (4.0, (1, 1, 1))]),
            **neck_track([(0, REST_NECK), (1.0, offset(REST_NECK, (2, 0, -3, 2)), 14, 2),
                          (2.0, offset(REST_NECK, (0, 2, 0, -4)), 24, 0),
                          (3.0, offset(REST_NECK, (-2, 0, 2, 0)), -20, -2), (4.0, REST_NECK)]),
            "jaw": lin((0, (0, 0, 0)), (1.6, (0, 0, 0)), (1.9, (5, 0, 0)), (2.3, (0, 0, 0)),
                       (4.0, (0, 0, 0))),
            **tail_wave(L, 6, 2),
            **wings(wing=[(0, (0, 0, 0)), (2.6, (0, 0, 0)), (2.9, (12, 0, 4)), (3.3, (0, 0, 0)),
                          (4.0, (0, 0, 0))], interp="catmullrom"),
        }}


    def look():
        """Looking around: a slow scan to one side, a hold, a scan to the other,
        the head leading and the neck following."""
        L = 4.0
        return {"loop": "loop", "length": L, "bones": {
            **neck_track([(0, REST_NECK), (0.7, offset(REST_NECK, (0, 0, 0, 4)), 50, 6),
                          (1.5, offset(REST_NECK, (0, 0, 0, 4)), 46, 6),
                          (2.4, offset(REST_NECK, (4, 0, 0, -6)), -50, -6),
                          (3.2, offset(REST_NECK, (4, 0, 0, -6)), -46, -6), (4.0, REST_NECK)]),
            **tail_wave(L, 5, 1),
        }}


    def walk(turn=0):
        """A four-beat walk (hind right, front right, hind left, front left).
        turn=+1/-1 bends it into a right/left turn: the neck leads, the tail
        trails, the body leans in."""
        L = 1.6
        w = 2 * math.pi / L
        body_rot = lambda t: (1.0 * math.sin(2 * w * t), 2 * math.cos(w * t) + 4 * turn,   # noqa: E731
                              -2 * math.sin(w * t) - 3 * turn)
        body_pos = lambda t: (0, -0.5 + 0.25 * (1 - math.cos(2 * w * t)), 0)           # noqa: E731
        return {"loop": "loop", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
            **legs(L, body_rot, body_pos, **gait(L, (0.25, 0.75, 0.0, 0.5), 1.8, 2.0, 0.65)),
            **neck_sampled(L, lambda t: (offset(REST_NECK, (2 * math.sin(2 * w * t), 0, 0,
                                                            -2 * math.sin(2 * w * t))),
                                         -6 * math.cos(w * t) + 36 * turn, 4 * math.sin(w * t) + 8 * turn)),
            **tail_wave(L, 7, 1.5, bias=(0, -10 * turn, 0)),
            **wings(wing=[(t, (6, 0, 2 + math.sin(2 * w * t))) for t in frames(L)[::4]]),
        }}


    def run():
        """A bounding gallop: the hind pair drives, the front pair reaches; the
        neck stretches forward, the tail streams out straight, the wings lift in
        their own plane for balance."""
        L = 0.8
        w = 2 * math.pi / L
        body_rot = lambda t: (4 * math.sin(w * t + 0.6), 0, 1.5 * math.sin(w * t))     # noqa: E731
        body_pos = lambda t: (0, -0.6 + 0.6 * max(0.0, math.sin(w * t)), 0)            # noqa: E731
        return {"loop": "loop", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
            **legs(L, body_rot, body_pos, **gait(L, (0.5, 0.6, 0.0, 0.1), 1.8, 2.5, 0.45)),
            **neck_sampled(L, lambda t: ((-55, -40, -25, -2 - 3 * math.sin(w * t + 1.4)), 0, 0)),
            "jaw": rot((0, (6, 0, 0)), (L, (6, 0, 0))),
            **tail_wave(L, 5, 4, bias=(14, 0, 0)),
            **wings(wing=[(t, (35 + 8 * math.sin(w * t), 0, 0)) for t in frames(L)[::2]]),
        }}


    def roar():
        """Rear up on the hind legs with the forelegs raised and the wings thrown
        up and open, draw the neck back, then thrust it forward with the jaws
        wide, shaking with the roar; settle back down."""
        L = 2.6
        body_rot = ease([(0, (0, 0, 0)), (0.45, (4, 0, 0)), (0.95, (-24, 0, 0)), (1.9, (-22, 0, 0)),
                         (2.35, (0, 0, 0)), (L, (0, 0, 0))])
        raised = (55, 15, 45)
        front = {s: lifted("front", s, [(0, None), (0.5, None), (0.95, raised), (1.9, offset(raised, (-5, 0, 0))),
                                         (2.3, None), (L, None)], body_rot) for s in ("right", "left")}
        shake = lambda t: 2.5 * math.sin(2 * math.pi * 11 * t) if 1.15 < t < 1.9 else 0.0   # noqa: E731
        pose = ease([(0, REST_NECK), (0.45, (-40, -10, 25, -12)), (0.95, (-15, 15, 50, 25)),
                     (1.15, (-50, -25, 0, 12)), (1.9, (-48, -22, 2, 10)), (2.35, REST_NECK), (L, REST_NECK)])
        return {"loop": "once", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot, front_right=front["right"], front_left=front["left"]),
            **neck_sampled(L, lambda t: (offset(pose(t), (0, 0, 0, shake(t))), shake(t), 0)),
            "jaw": lin((0, (0, 0, 0)), (0.45, (0, 0, 0)), (0.95, (12, 0, 0)), (1.15, (42, 0, 0)),
                       (1.9, (40, 0, 0)), (2.25, (0, 0, 0)), (L, (0, 0, 0))),
            **tail_wave(L, 10, 3, cycles=2, bias=(ROAR_TAIL_LIFT, 0, 0)),
            # x raises the wings straight up before z opens them, and z closes
            # them again before x folds them.
            **wings(wing=[(0, (0, 0, 0)), (0.6, (WING_UP, 0, 0)), (0.95, (WING_UP, 0, -55)),
                          (1.9, (WING_UP, 0, -50)), (2.15, (WING_UP, 0, 0)), (L, (0, 0, 0))],
                    mid=[(0, (0, 0, 0)), (0.95, (0, 0, 0)), (1.15, (0, 14, 0)), (1.9, (0, 10, 0)),
                         (2.15, (0, 0, 0)), (L, (0, 0, 0))]),
        }}


    def attack():
        """A bite: coil the neck back, lunge with the jaws wide, snap shut."""
        L = 1.3
        body_rot = ease([(0, (0, 0, 0)), (0.35, (-3, 0, 0)), (0.55, (3, 0, 0)), (0.8, (2, 0, 0)),
                         (1.15, (0, 0, 0)), (L, (0, 0, 0))])
        body_pos = ease([(0, (0, 0, 0)), (0.35, (0, -0.3, 1.0)), (0.55, (0, -0.4, -1.0)), (0.8, (0, -0.4, -0.8)),
                         (1.15, (0, 0, 0)), (L, (0, 0, 0))])
        return {"loop": "once", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
            **legs(L, body_rot, body_pos),
            **neck_track([(0, REST_NECK), (0.35, (-30, -5, 20, -6)), (0.55, (-68, -62, -52, -6)),
                          (0.8, (-60, -52, -44, -6)), (1.15, REST_NECK), (L, REST_NECK)]),
            "jaw": lin((0, (0, 0, 0)), (0.35, (14, 0, 0)), (0.5, (40, 0, 0)), (0.6, (0, 0, 0)),
                       (0.8, (6, 0, 0)), (1.0, (0, 0, 0)), (L, (0, 0, 0))),
            **tail_wave(L, 8, 3),
            **wings(wing=[(0, (0, 0, 0)), (0.35, (20, 0, 0)), (0.55, (8, 0, 0)), (1.15, (0, 0, 0)),
                          (L, (0, 0, 0))], interp="catmullrom"),
        }}


    def claw():
        """A swipe with the right foreleg: rock back onto the hind legs, raise
        the arm high, rake it down and forward at chest height, plant it again.
        The head follows the strike."""
        L = 1.3
        body_rot = ease([(0, (0, 0, 0)), (0.35, (-14, 6, 4)), (0.6, (-6, -8, -3)), (0.85, (-4, -4, 0)),
                         (1.15, (0, 0, 0)), (L, (0, 0, 0))])
        right = lifted("front", "right", [(0, None), (0.1, None), (0.35, (60, 100, 80)),
                                          (0.6, (45, 20, 20)), (0.85, (25, 8, 10)), (1.1, None), (L, None)],
                       body_rot)
        return {"loop": "once", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot, front_right=right),
            **neck_track([(0, REST_NECK), (0.35, offset(REST_NECK, (-4, 4, 6, 6)), 18, 6),
                          (0.6, offset(REST_NECK, (-14, -12, -8, -8)), -20, -4),
                          (1.1, REST_NECK), (L, REST_NECK)]),
            "jaw": lin((0, (0, 0, 0)), (0.35, (16, 0, 0)), (0.6, (24, 0, 0)), (0.9, (0, 0, 0)),
                       (L, (0, 0, 0))),
            **tail_wave(L, 9, 3, bias=(0, -6, 0)),
            **wings(wing=[(0, (0, 0, 0)), (0.35, (18, 0, 0)), (0.6, (6, 0, 0)), (1.1, (0, 0, 0)),
                          (L, (0, 0, 0))], interp="catmullrom"),
        }}


    def hit():
        L = 0.6
        body_rot = ease([(0, (0, 0, 0)), (0.08, (-6, 0, 3)), (0.25, (2, 0, -1)), (L, (0, 0, 0))])
        return {"loop": "once", "length": L, "bones": {
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot),
            **neck_track([(0, REST_NECK), (0.08, offset(REST_NECK, (12, 8, 6, 14)), 16, 10),
                          (0.25, offset(REST_NECK, (-3, -2, -2, -3)), -5, -2), (L, REST_NECK)]),
            "jaw": lin((0, (0, 0, 0)), (0.08, (26, 0, 0)), (0.35, (0, 0, 0)), (L, (0, 0, 0))),
            **tail_wave(0.6, 10, 4),
            **wings(wing=[(0, (0, 0, 0)), (0.08, (16, 0, 10)), (0.25, (4, 0, 2)), (L, (0, 0, 0))],
                    interp="catmullrom"),
        }}


    def fly():
        L = 1.0
        w = 2 * math.pi / L
        root = lambda t: (0, FLY_HEIGHT + 1.2 * math.sin(w * t), 0)                    # noqa: E731
        body_rot = lambda t: (2 * math.sin(w * t + 0.8), 0, 0)                          # noqa: E731
        return {"loop": "loop", "length": L, "bones": {
            "dragon": sampled("position", L, root),
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot, root_pos=root, **free_legs(LEGS_TUCKED)),
            **neck_sampled(L, lambda t: (offset(FLY_NECK, (0, 0, 0, -2 * math.sin(w * t + 0.8))), 0, 0)),
            **{b: sampled("rotation", L, lambda t, b=b, i=i: (
                TAIL_STRAIGHT[b][0] + 3 * math.sin(w * t + 1.5 + i), 4 * math.sin(w * t + i), 0))
               for i, b in enumerate(("tail", "tail_mid", "tail_end"))},
            # Downstroke to the bottom at 0.5, upstroke back. The outer segments
            # lag: bent up on the way down, bent down and swept back on the way up.
            **wings(wing=[(0, (WING_UP, 0, -40)), (0.5, (WING_UP, 0, -130)), (L, (WING_UP, 0, -40))],
                    mid=[(0, (0, 0, 0)), (0.25, (0, 14, 0)), (0.5, (0, 4, 0)), (0.75, (0, -10, 0)),
                         (L, (0, 0, 0))],
                    tip=[(0, (0, 0, 0)), (0.25, (0, 16, 0)), (0.5, (0, 6, 0)), (0.75, (0, -14, 0)),
                         (L, (0, 0, 0))], interp="catmullrom"),
        }}


    def hover():
        """Hovering: the body upright, deep beats, the legs hanging ready, the
        tail swinging under it as a counterweight; the head stays level."""
        L = 0.9
        w = 2 * math.pi / L
        root = lambda t: (0, FLY_HEIGHT + 2 * math.sin(w * t + 1.6), 0)                # noqa: E731
        body_rot = lambda t: (-40 + 2 * math.sin(w * t), 0, 0)                          # noqa: E731
        hang = {"front": (20, -20, 10), "hind": (30, -10, 20)}
        return {"loop": "loop", "length": L, "bones": {
            "dragon": sampled("position", L, root),
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot, root_pos=root, **free_legs(hang)),
            **neck_sampled(L, lambda t: ((-55, -45, -40, -40 - 2 * math.sin(w * t)), 0, 0)),
            **tail_wave(L, 6, 4, bias=(-10, 0, 0)),
            **wings(wing=[(0, (WING_UP, 0, -30)), (0.45, (WING_UP, 0, -140)), (L, (WING_UP, 0, -30))],
                    mid=[(0, (0, 0, 0)), (0.22, (0, 16, 0)), (0.45, (0, 4, 0)), (0.68, (0, -12, 0)),
                         (L, (0, 0, 0))],
                    tip=[(0, (0, 0, 0)), (0.22, (0, 18, 0)), (0.45, (0, 6, 0)), (0.68, (0, -16, 0)),
                         (L, (0, 0, 0))], interp="catmullrom"),
        }}


    def takeoff():
        """Crouch with the wings raised, leap, three strokes, into fly."""
        L = 1.8
        root = ease([(0, (0, 0, 0)), (0.4, (0, 0, 0)), (0.6, (0, 6, 0)), (0.95, (0, 13, 0)),
                     (1.35, (0, 22, 0)), (L, (0, FLY_HEIGHT, 0))])
        body_pos = ease([(0, (0, 0, 0)), (0.4, (0, -1.5, 0)), (0.6, (0, 0, 0)), (L, (0, 0, 0))])
        body_rot = ease([(0, (0, 0, 0)), (0.4, (6, 0, 0)), (0.6, (-14, 0, 0)), (1.0, (-6, 0, 0)),
                         (L, (0, 0, 0))])
        off = 0.62
        leg = {(k, s): lifted(k, s, [(0, None), (off, None), (off + 0.6, LEGS_TUCKED[k]), (L, LEGS_TUCKED[k])],
                              body_rot, body_pos, root)
               for k in ("front", "hind") for s in ("right", "left")}
        tail = {b: rot((0, (0, 0, 0)), (0.4, (6, 0, 0)), (0.9, TAIL_STRAIGHT[b]), (L, TAIL_STRAIGHT[b]))
                for b in TAIL_STRAIGHT}
        return {"loop": "once", "length": L, "bones": {
            "dragon": sampled("position", L, root),
            "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
            **legs(L, body_rot, body_pos, root, front_right=leg[("front", "right")],
                   front_left=leg[("front", "left")], hind_right=leg[("hind", "right")],
                   hind_left=leg[("hind", "left")]),
            **neck_track([(0, REST_NECK), (0.4, (-50, -30, -10, -5)), (0.8, (-55, -48, -40, -2)),
                          (L, FLY_NECK)]),
            **tail,
            **wings(wing=[(0, (0, 0, 0)), (0.4, (WING_UP, 0, 0)), (0.65, (WING_UP, 0, -130)),
                          (0.95, (WING_UP, 0, -40)), (1.2, (WING_UP, 0, -130)),
                          (1.5, (WING_UP, 0, -40)), (L, FLY_START["wing"])],
                    mid=[(0, (0, 0, 0)), (0.4, (0, 0, 0)), (0.52, (0, 16, 0)), (0.65, (0, 4, 0)),
                         (0.8, (0, -10, 0)), (0.95, (0, 0, 0)), (1.08, (0, 14, 0)), (1.2, (0, 4, 0)),
                         (1.35, (0, -10, 0)), (1.5, (0, 0, 0)), (L, FLY_START["mid"])],
                    tip=[(0, (0, 0, 0)), (0.4, (0, 0, 0)), (0.52, (0, 18, 0)), (0.65, (0, 6, 0)),
                         (0.8, (0, -14, 0)), (0.95, (0, 0, 0)), (1.08, (0, 16, 0)), (1.2, (0, 6, 0)),
                         (1.35, (0, -14, 0)), (1.5, (0, 0, 0)), (L, FLY_START["tip"])]),
        }}


    def land():
        """Glide in, flare upright with the legs reaching down, braking beats,
        touch down hind feet first, drop onto the forelegs, close the wings up,
        then fold them."""
        L = 2.2
        root = ease([(0, (0, FLY_HEIGHT, 0)), (0.35, (0, 24, 0)), (0.75, (0, 9, 0)),
                     (1.0, (0, 0, 0)), (L, (0, 0, 0))])
        body_rot = ease([(0, (0, 0, 0)), (0.35, (-10, 0, 0)), (0.75, (-30, 0, 0)), (1.0, (-26, 0, 0)),
                         (1.3, (2, 0, 0)), (1.6, (0, 0, 0)), (L, (0, 0, 0))])
        body_pos = ease([(0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.35, (0, -1.0, 0)), (1.7, (0, -0.2, 0)),
                         (L, (0, 0, 0))])
        touch = {"hind": 0.95, "front": 1.25}
        leg = {(k, s): lifted(k, s, [(0, LEGS_TUCKED[k]), (0.35, (0.5 * LEGS_TUCKED[k][0], 0, 0)),
                                     (touch[k], None), (L, None)], body_rot, body_pos, root)
               for k in ("front", "hind") for s in ("right", "left")}
        tail = {b: rot((0, TAIL_STRAIGHT[b]), (0.75, offset(TAIL_STRAIGHT[b], (14, 0, 0))),
                       (1.3, (4, 0, 0)), (1.7, (0, 0, 0)), (L, (0, 0, 0))) for b in TAIL_STRAIGHT}
        return {"loop": "once", "length": L, "bones": {
            "dragon": sampled("position", L, root),
            "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
            **legs(L, body_rot, body_pos, root, front_right=leg[("front", "right")],
                   front_left=leg[("front", "left")], hind_right=leg[("hind", "right")],
                   hind_left=leg[("hind", "left")]),
            **neck_track([(0, FLY_NECK), (0.35, (-50, -40, -25, -8)), (0.75, (-62, -50, -40, -28)),
                          (1.3, (-30, 4, 40, -2)), (1.7, REST_NECK), (L, REST_NECK)]),
            **tail,
            # z closes the wings straight up before x folds them down.
            **wings(wing=[(0, FLY_START["wing"]), (0.35, (WING_UP, 0, -90)), (0.6, (WING_UP, 0, -45)),
                          (0.85, (WING_UP, 0, -120)), (1.3, (WING_UP, 0, 0)), (1.75, (0, 0, 0)),
                          (L, (0, 0, 0))],
                    mid=[(0, FLY_START["mid"]), (0.35, (0, 6, 0)), (0.6, (0, -12, 0)), (0.85, (0, 14, 0)),
                         (1.3, (0, 0, 0)), (L, (0, 0, 0))],
                    tip=[(0, FLY_START["tip"]), (0.35, (0, 8, 0)), (0.6, (0, -14, 0)), (0.85, (0, 16, 0)),
                         (1.3, (0, 0, 0)), (L, (0, 0, 0))]),
        }}

    def glide():
        """Gliding: wings level and still but for a slow flex, banking side to
        side, the tail steering against the bank, the head looking down and
        around."""
        L = 3.0
        w = 2 * math.pi / L
        root = lambda t: (0, FLY_HEIGHT + 0.8 * math.sin(w * t), 0)                    # noqa: E731
        body_rot = lambda t: (1.5 * math.sin(w * t + 0.8), 0, 8 * math.sin(w * t))     # noqa: E731
        return {"loop": "loop", "length": L, "bones": {
            "dragon": sampled("position", L, root),
            "body": sampled("rotation", L, body_rot),
            **legs(L, body_rot, root_pos=root, **free_legs(LEGS_TUCKED)),
            **neck_sampled(L, lambda t: (offset(FLY_NECK, (0, 0, 0, -4)), 18 * math.sin(w * t + 0.9),
                                         -6 * math.sin(w * t))),
            **{b: sampled("rotation", L, lambda t, b=b, i=i: (
                TAIL_STRAIGHT[b][0] + 2 * math.sin(w * t + i), -6 * math.sin(w * t - 0.4 * i), 0))
               for i, b in enumerate(("tail", "tail_mid", "tail_end"))},
            **pair("wing_*", [(t, (WING_UP, 0, -88 + 3 * math.sin(w * t))) for t in frames(L)[::6]]),
            **wings(mid=[(0, (0, 6, 0)), (L, (0, 6, 0))], tip=[(0, (0, 10, 0)), (L, (0, 10, 0))]),
        }}


    return {"idle": idle, "look": look, "walk": walk, "run": run,
            "turn_left": lambda: walk(-1), "turn_right": lambda: walk(1), "roar": roar,
            "attack": attack, "claw": claw, "hit": hit, "takeoff": takeoff, "fly": fly,
            "glide": glide, "hover": hover, "land": land}


def build(fns, names):
    """Call the named animation functions: {name: animation}."""
    return {n: fns[n]() for n in names}
