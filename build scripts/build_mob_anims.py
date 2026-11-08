"""Walk and run cycles for the mobs, written into their .bbmodel files (replacing the old 3-key walk / run).

Measured in Blockbench: a positive X keyframe swings a hanging leg forward (the mobs face north, -z).

  quad  (cow, highland_cow, pig, wolf)  walk: 4-beat lateral walk (back left, front left, back right, front right),
        each foot lifts on its swing; body bobs twice a cycle and rolls toward the leg it stands on, head nods,
        ears and tail follow through late, the cow's bell swings.
        run: a trot (cow, highland cow, pig: diagonal pairs) or a bounding gallop (wolf: back legs together,
        then front legs, the spine pitching).
  biped (ogre, stone_golem)  walk: legs in opposite phase, arms swing against the legs, the torso twists with the
        arms and rolls onto the standing leg, bobs at each heel strike, head steadies against the twist; the club
        or chain drags a beat behind its arm, the loincloth swings. The golem is slow and heavy: more roll, more bob.
        run: longer strides, a forward lean, bigger arm pumps.
  dragon (ember_dragon)  walk / run: 4-beat walk / trot on arm-forearm-hand and thigh-leg-foot (elbows and knees
        fold on the swing), an S wave down the neck and the tail, folded wings rock.
  dragon and pale_dragon keep their own walks (839 hand-tuned keyframes already).

Every cycle is sampled at 16 keys with catmull-rom easing and loops. The ground speed each gait covers (feet
don't slide) is printed and written to mob_speeds.json for the game.
"""
import copy, json, math, os, random, sys, uuid

REPO = r"C:\Users\lucas\club-impz\godot-game\assets\models\mobs"
BB = r"C:\Users\lucas\blockbench_models\mobs"
MOBS = {
    "cow": (REPO, "quad", dict(walk=(1.4, 20), run=(0.62, 30), gait="trot")),
    "highland_cow": (REPO, "quad", dict(walk=(1.6, 18), run=(0.7, 28), gait="trot")),
    "pig": (REPO, "quad", dict(walk=(0.8, 24), run=(0.4, 34), gait="trot")),
    "wolf": (REPO, "quad", dict(walk=(0.95, 22), run=(0.48, 40), gait="gallop")),
    "ogre": (REPO, "biped", dict(walk=(1.5, 24), run=(0.85, 36), heavy=1.0)),
    "stone_golem": (BB, "biped", dict(walk=(2.0, 18), run=(1.15, 26), heavy=1.8)),
    "ember_dragon": (BB, "dragon", dict(walk=(1.6, 22), run=(0.8, 32))),
}
N = 16
rng = random.Random(77)


def nu(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def wave(p, phase=0.0): return math.sin(2 * math.pi * (p - phase))


def leg_cycle(p, A, stance=0.62, lift=1.0):
    """Leg angle (+ = forward) and foot lift for cycle position p (0..1, 0 = foot plants, forward).
    Stance: the foot sweeps from +A to -A at an even pace. Swing: it eases back to +A, lifted."""
    p %= 1.0
    if p < stance:
        return A - 2 * A * (p / stance), 0.0, 0.0
    s = (p - stance) / (1 - stance)
    e = 0.5 - 0.5 * math.cos(math.pi * s)                 # ease in-out
    return -A + 2 * A * e, lift * math.sin(math.pi * s), math.sin(math.pi * s)


class Anim:
    def __init__(self, name, length):
        self.name, self.length, self.tracks = name, length, {}

    def key(self, bone, ch, t, xyz):
        self.tracks.setdefault(bone, {}).setdefault(ch, []).append((t, xyz))

    def sample(self, bone, ch, fn):
        """fn(p) -> (x, y, z) for p in 0..1; N keys plus the closing key (== the first, for the loop)."""
        for i in range(N + 1):
            p = i / N
            self.key(bone, ch, round(p * self.length, 4), fn(p % 1.0))


def quad(m, A, T, run, gait):
    L = m["leg"]                                          # leg length (units): pivot height of the legs
    lift = 0.16 * L if not run else 0.26 * L
    a = Anim("run" if run else "walk", T)
    if not run:     # 4-beat lateral sequence walk
        ph = {"leg_back_left": 0.0, "leg_front_left": 0.25, "leg_back_right": 0.5, "leg_front_right": 0.75}
        stance = 0.66
    elif gait == "gallop":
        ph = {"leg_back_left": 0.0, "leg_back_right": 0.08, "leg_front_left": 0.45, "leg_front_right": 0.53}
        stance = 0.42
    else:           # trot: diagonal pairs
        ph = {"leg_back_left": 0.0, "leg_front_right": 0.0, "leg_back_right": 0.5, "leg_front_left": 0.5}
        stance = 0.48
    for leg, f in ph.items():
        if leg not in m["bones"]: continue
        def fn(p, f=f):
            ang, up, _ = leg_cycle(p - f, A, stance, lift)
            return (ang, 0, 0)
        def fp(p, f=f):
            _, up, _ = leg_cycle(p - f, A, stance, lift)
            return (0, up, 0)
        a.sample(leg, "rotation", fn); a.sample(leg, "position", fp)
    bob = (0.05 if not run else 0.1) * L
    if gait == "gallop" and run:   # the spine pitches: nose down as the front legs land, up as the back legs push
        a.sample("body", "rotation", lambda p: (6 * wave(p, 0.2), 0, 1.5 * wave(p, 0.1)))
        a.sample("body", "position", lambda p: (0, bob * (1.4 * wave(p, 0.0) - 0.4), 0))
        a.sample("head", "rotation", lambda p: (-5 * wave(p, 0.25) + 4, 0, 0))
        tail_amp, ear = 10, -18
    else:
        roll = 2.0 if not run else 3.0
        a.sample("body", "rotation", lambda p: (0.8 * wave(2 * p, 0.1), 1.2 * wave(p, 0.3), roll * wave(p, 0.15)))
        a.sample("body", "position", lambda p: (0, -bob * (0.5 + 0.5 * math.cos(4 * math.pi * p)), 0))
        nod = 4 if not run else 6
        a.sample("head", "rotation", lambda p: (nod * wave(2 * p, 0.3) - (2 if not run else -3), 2.5 * wave(p, 0.45), -roll * 0.6 * wave(p, 0.2)))
        tail_amp, ear = (9 if not run else 14), (0 if not run else -14)
    if "jaw" in m["bones"]:
        a.sample("jaw", "rotation", lambda p: (1.5 + 1.5 * wave(2 * p, 0.5), 0, 0))
    for side, sg in (("ear_right", 1), ("ear_left", -1)):
        if side in m["bones"]:
            a.sample(side, "rotation", lambda p, sg=sg: (ear + 4 * wave(2 * p, 0.45), 0, sg * 6 * wave(2 * p, 0.4)))
        if side + "_tip" in m["bones"]:
            a.sample(side + "_tip", "rotation", lambda p, sg=sg: (6 * wave(2 * p, 0.6), 0, sg * 5 * wave(2 * p, 0.55)))
    tails = [b for b in ("tail", "tail_mid", "tail_lower", "tail_tip") if b in m["bones"]]
    for i, b in enumerate(tails):   # each segment later and wider: follow through
        lag = 0.12 * (i + 1)
        lift_t = (10 if run else 0) if i == 0 else 0
        a.sample(b, "rotation", lambda p, lag=lag, i=i, lift_t=lift_t: (lift_t + 3 * wave(2 * p, lag), tail_amp * (1 + 0.5 * i) * wave(p, lag), 0))
    if "bell" in m["bones"]:
        a.sample("bell", "rotation", lambda p: (8 * wave(2 * p, 0.35), 0, 6 * wave(p, 0.3)))
    speed = 2 * L * math.sin(math.radians(A)) / (stance * T)   # units / s the planted foot sweeps back
    return a, speed


def biped(m, A, T, run, heavy):
    L = m["leg"]
    lift = (0.14 if not run else 0.24) * L
    a = Anim("run" if run else "walk", T)
    stance = 0.6 if not run else 0.44
    for leg, f in (("leg_right", 0.0), ("leg_left", 0.5)):
        if leg not in m["bones"]: continue
        a.sample(leg, "rotation", lambda p, f=f: (leg_cycle(p - f, A, stance, lift)[0], 0, 0))
        a.sample(leg, "position", lambda p, f=f: (0, leg_cycle(p - f, A, stance, lift)[1], 0))
    arm_a = A * (0.55 if not run else 0.85)
    for arm, f in (("arm_right", 0.5), ("arm_left", 0.0)):   # each arm swings with the opposite leg
        if arm not in m["bones"]: continue
        sg = 1 if arm.endswith("right") else -1
        a.sample(arm, "rotation", lambda p, f=f, sg=sg: (arm_a * math.cos(2 * math.pi * (p - f)), 0, sg * (3 + 2 * heavy) * (0.5 + 0.5 * wave(p, f))))
    for fa, f in (("forearm_right", 0.5), ("forearm_left", 0.0)):
        if fa not in m["bones"]: continue
        bend = 8 if not run else 30
        a.sample(fa, "rotation", lambda p, f=f, bend=bend: (bend + (5 if not run else 9) * math.cos(2 * math.pi * (p - f - 0.08)), 0, 0))
    for prop, f in (("club", 0.5), ("chain", 0.0)):          # drags a beat behind its arm
        if prop in m["bones"]:
            a.sample(prop, "rotation", lambda p, f=f: (5 * math.cos(2 * math.pi * (p - f - 0.18)), 0, 3 * wave(p, f + 0.2)))
    bob = (0.05 if not run else 0.09) * L * heavy
    roll = (2.0 if not run else 2.5) * heavy
    twist = 5 if not run else 8
    lean = 0 if not run else -9                               # negative x leans the top forward
    a.sample("body", "position", lambda p: (roll * 0.12 * wave(p, 0.25), -bob * (0.5 + 0.5 * math.cos(4 * math.pi * p)), 0))
    a.sample("body", "rotation", lambda p: (lean + 1.5 * heavy * wave(2 * p, 0.1), twist * math.cos(2 * math.pi * p), roll * wave(p, 0.25)))
    if "head" in m["bones"]:
        a.sample("head", "rotation", lambda p: (-lean * 0.6 + 2 * wave(2 * p, 0.3), -twist * 0.7 * math.cos(2 * math.pi * p), -roll * 0.7 * wave(p, 0.25)))
    if "jaw" in m["bones"]:
        a.sample("jaw", "rotation", lambda p: (2 + 2 * wave(2 * p, 0.4), 0, 0))
    for side, sg in (("ear_right", 1), ("ear_left", -1)):
        if side in m["bones"]:
            a.sample(side, "rotation", lambda p, sg=sg: (3 * wave(2 * p, 0.45), sg * 5 * wave(2 * p, 0.5), sg * 6 * wave(2 * p, 0.4)))
    if "loincloth" in m["bones"]:
        a.sample("loincloth", "rotation", lambda p: (8 * wave(2 * p, 0.3) - (6 if run else 0), 0, 5 * wave(p, 0.35)))
    speed = 2 * L * math.sin(math.radians(A)) / (stance * T)
    return a, speed


def dragon(m, A, T, run):
    L = m["leg"]
    a = Anim("run" if run else "walk", T)
    stance = 0.64 if not run else 0.46
    if not run:
        ph = {"right_hind": 0.0, "right_front": 0.25, "left_hind": 0.5, "left_front": 0.75}
    else:
        ph = {"right_hind": 0.0, "left_front": 0.0, "left_hind": 0.5, "right_front": 0.5}
    lift = (0.15 if not run else 0.25) * L
    for side in ("right", "left"):
        fh, ff = ph[side + "_hind"], ph[side + "_front"]
        def thigh(p, f=fh):
            ang, up, sw = leg_cycle(p - f, A, stance, lift)
            return (ang, 0, 0)
        a.sample("thigh_" + side, "rotation", thigh)
        a.sample("thigh_" + side, "position", lambda p, f=fh: (0, leg_cycle(p - f, A, stance, lift)[1], 0))
        a.sample("leg_" + side, "rotation", lambda p, f=fh: (-(10 + 45 * leg_cycle(p - f, A, stance)[2]), 0, 0))   # knee folds on the swing
        a.sample("foot_" + side, "rotation", lambda p, f=fh: (8 + 30 * leg_cycle(p - f, A, stance)[2] - 0.3 * leg_cycle(p - f, A, stance)[0], 0, 0))
        a.sample("arm_" + side, "rotation", lambda p, f=ff: (leg_cycle(p - f, A * 0.9, stance)[0], 0, 0))
        a.sample("arm_" + side, "position", lambda p, f=ff: (0, leg_cycle(p - f, A, stance, lift * 0.8)[1], 0))
        a.sample("forearm_" + side, "rotation", lambda p, f=ff: (12 + 40 * leg_cycle(p - f, A, stance)[2], 0, 0))    # elbow folds on the swing
        a.sample("hand_" + side, "rotation", lambda p, f=ff: (-6 - 30 * leg_cycle(p - f, A, stance)[2], 0, 0))
    bob = (0.05 if not run else 0.09) * L
    roll = 2.0 if not run else 3.0
    a.sample("body", "position", lambda p: (0, -bob * (0.5 + 0.5 * math.cos(4 * math.pi * p)), 0))
    a.sample("body", "rotation", lambda p: (1.2 * wave(2 * p, 0.1) + (-4 if run else 0), 2.5 * wave(p, 0.2), roll * wave(p, 0.15)))
    neck = ["neck_base", "neck_mid", "neck_upper", "head"]
    for i, b in enumerate(neck):     # S wave travelling up the neck; the head steadies at the end
        amp = 3.5 if b != "head" else -4.0
        a.sample(b, "rotation", lambda p, i=i, amp=amp: (2.0 * wave(2 * p, 0.15 * i + 0.2), amp * wave(p, 0.12 * i + 0.35), 0))
    if "jaw" in m["bones"]:
        a.sample("jaw", "rotation", lambda p: (3 + 3 * wave(2 * p, 0.5), 0, 0))
    for i, b in enumerate(["tail", "tail_mid", "tail_end"]):
        a.sample(b, "rotation", lambda p, i=i: (2 * wave(2 * p, 0.2 * i), (6 + 4 * i) * (1.3 if run else 1.0) * wave(p, 0.15 * (i + 1) + 0.5), 0))
    for side, sg in (("right", 1), ("left", -1)):   # folded wings rock with the body, tips lag
        for i, b in enumerate(["wing_", "wing_mid_", "wing_tip_"]):
            bone = b + side
            if bone in m["bones"]:
                a.sample(bone, "rotation", lambda p, i=i, sg=sg: (1.5 * wave(2 * p, 0.2 + 0.1 * i), 0, sg * (2.5 + 1.5 * i) * wave(2 * p, 0.25 + 0.12 * i)))
    speed = 2 * L * math.sin(math.radians(A)) / (stance * T)
    return a, speed


def to_json(a, by_name, m):
    animators = {}
    for bone, chans in a.tracks.items():
        g = by_name.get(bone)
        if g is None: continue
        kfs = []
        for ch, keys in chans.items():
            for t, (x, y, z) in keys:
                kfs.append({"channel": ch, "data_points": [{"x": f"{x:.3f}", "y": f"{y:.3f}", "z": f"{z:.3f}"}],
                            "uuid": nu(), "time": t, "color": -1, "interpolation": "catmullrom",
                            "bezier_linked": True, "bezier_left_time": [-0.1, -0.1, -0.1], "bezier_left_value": [0, 0, 0],
                            "bezier_right_time": [0.1, 0.1, 0.1], "bezier_right_value": [0, 0, 0]})
        animators[g["uuid"]] = {"name": bone, "type": "bone", "rotation_global": False, "quaternion_interpolation": False, "keyframes": kfs}
    return animators


def build(name):
    folder, kind, cfg = MOBS[name]
    path = os.path.join(folder, f"{name}.bbmodel")
    d = json.load(open(path, encoding="utf8"))
    by_name = {g["name"]: g for g in d["groups"]}
    legs = [g for g in d["groups"] if g["name"] in ("leg_front_right", "leg_back_right", "leg_right", "thigh_right")]
    leg = max(g["origin"][1] for g in legs)
    m = {"bones": set(by_name), "leg": leg}
    speeds = {}
    for which in ("walk", "run"):
        T, A = cfg[which]
        if kind == "quad": a, sp = quad(m, A, T, which == "run", cfg["gait"])
        elif kind == "biped": a, sp = biped(m, A, T, which == "run", cfg["heavy"])
        else: a, sp = dragon(m, A, T, which == "run")
        speeds[which] = round(sp / 16.0, 3)                   # metres per second
        old = next((x for x in d["animations"] if x["name"] == which), None)
        new = {"uuid": old["uuid"] if old else nu(), "name": which, "loop": "loop", "override": False, "length": T,
               "snapping": 24, "selected": False, "group_name": "", "scope": 0, "anim_time_update": "", "blend_weight": "",
               "start_delay": "", "loop_delay": "", "animators": to_json(a, by_name, m)}
        if old: d["animations"][d["animations"].index(old)] = new
        else: d["animations"].append(new)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(d, fh, indent="\t")
    keys = sum(len(an["keyframes"]) for x in d["animations"] if x["name"] in ("walk", "run") for an in x["animators"].values())
    print(f"{name:13s} {kind:6s} leg={leg:5.1f}u  walk {speeds['walk']} m/s  run {speeds['run']} m/s  ({keys} keys)")
    return speeds


if __name__ == "__main__":
    out = {}
    for n in (sys.argv[1:] or list(MOBS)):
        out[n] = build(n)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mob_speeds.json"), "w"), indent=1)
