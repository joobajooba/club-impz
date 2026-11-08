"""Writes build_foliage_rocks.py from build_rocks.py: plain natural rocks for the game's five biomes, to scatter
like foliage. Same painting and texture sharing, new shapes (a few big overlapping lumps, not stepped rings) and
only each biome's own natural details (no veins, glints, stars, slime or ice crystals)."""
import re

s = open("build_rocks.py", encoding="utf8").read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)


def T(block):
    return "\n".join("\t" * 0 + l for l in block.split("\n"))


# doc string
a = s.index('"""'); b = s.index('"""', a + 3) + 3
s = s[:a] + '''"""Foliage rocks: plain natural rocks for the game's five biomes (blockbench_detailed_prompts.md 3.3), to scatter
through the world like the plants: <biome>_rock_<size> for small, medium and large, the three sizes of a biome
sharing one texture (the doc's rule). Not ore-like: a few big rounded lumps of plain stone, with only the biome's
own natural details.

  forest    rounded mossy boulder, grey green stone, moss cushions, pale lichen, grass tufts
  mountain  angular crag, blue grey stone with faint layers, orange lichen, pebbles
  frost     rounded boulder, pale grey stone, snow caps spilling over
  plains    low flat sandstone shelf, sandy stone in soft bands, sand drifts, dry grass
  swamp     low half-sunk stone, dark wet stone, moss, reeds, small mushrooms

Painted in world space like the ore veins (moss, snow, layers and cracks run over the edges); faces nobody can
see get no UV. 2 px/unit, one 256 texture per biome (J00BA chose 256 over the doc's 64/128), no animations.
Usage: py -3 build_foliage_rocks.py [forest mountain ...]   (no args = all five)
"""''' + s[b:]

rep('''CFG = {
    "forest":   dict(seed=101, style="rounded", top="moss", lichen="lichen_g", base="grass", extras=["moss_cushion", "pebbles"]),
    "mountain": dict(seed=202, style="jagged", top="none", lichen="lichen_o", base="none", extras=["pebbles", "strata_faint"]),
    "frost":    dict(seed=303, style="rounded", top="snow", lichen=None, base="none", extras=["snow_cap", "ice", "pebbles"]),
    "plains":   dict(seed=404, style="slab", top="none", lichen="lichen_o", base="dry", extras=["strata", "pebbles"]),
    "swamp":    dict(seed=505, style="sunken", top="moss", lichen=None, base="reed", extras=["moss_cushion", "drips", "mushrooms", "wet"]),
    "void":     dict(seed=606, style="spire", top="none", lichen=None, base="none", extras=["glints", "float"]),
    "stellar":  dict(seed=707, style="pile", top="none", lichen=None, base="none", extras=["stars", "sparkles"]),
}''', '''CFG = {
    "forest":   dict(seed=1101, style="boulder", top="moss", lichen="lichen_g", base="grass", extras=["moss_cushion", "pebbles"]),
    "mountain": dict(seed=1202, style="crag", top="none", lichen="lichen_o", base="none", extras=["pebbles", "strata_faint"]),
    "frost":    dict(seed=1303, style="boulder", top="snow", lichen=None, base="none", extras=["snow_cap", "pebbles"]),
    "plains":   dict(seed=1404, style="flat", top="none", lichen="lichen_o", base="dry", extras=["strata_soft", "sand", "pebbles"]),
    "swamp":    dict(seed=1505, style="sunk", top="moss", lichen=None, base="reed", extras=["moss_cushion", "mushrooms", "wet"]),
}''')
rep('''    "frost":    R("#3a4552 #46525f''', '''    "frost":    R("#2e3640 #3a434e #47515c #545f6a #626d78 #707b86 #7f8994 #8e98a2 #9da6af #acb4bc #bbc2c9 #cad0d6"),
    "frost_old":    R("#3a4552 #46525f''')
rep('''    "star":     R(''', '''    "sand":     R("#7c603f #8d6f4a #9e7e56 #ae8e63 #bd9e72 #cbad82 #d8bd93"),
    "star":     R(''')
rep('''SIZES = {"small": (7.0, 4.5), "medium": (15.0, 9.0), "large": (28.0, 17.0)}''',
    '''SIZES = {"small": (6.0, 3.5), "medium": (13.0, 7.5), "large": (24.0, 13.0)}''')
rep('''        "swamp": (-0.2, 0.5, -0.3), "void": (0.4, -0.3, 0.6), "stellar": (-0.3, 0.0, 0.6)}''',
    '''        "swamp": (-0.2, 0.5, -0.3)}''')

# shapes: replace everything from the style dispatch up to the base slab with the lump builder
a = s.index('        if style == "rounded":')
b = s.index('        if size != "small":                          # a low base slab')
e = s.index('\n', s.index('cube(size, f"base_1"', b)) + 1
s = s[:a] + '''        def lumps(cw, cd, ch, n, y0=0.0, tall=1.0, skirt=True, crown=True):
            """A natural rock: a core block, a wide low skirt at the foot, an inset crown that rounds the top,
            and lumps pushed half into the sides so the outline bulges and never reads as a box."""
            add(0, 0, h2(y0), cw, cd, ch * tall)
            top = y0 + ch * tall
            if skirt:
                add(rng.uniform(-0.05, 0.05) * W, 0, 0.0, cw * 1.22, cd * 1.2, max(1.0, ch * 0.3))
            if crown:
                add(rng.uniform(-0.08, 0.08) * W, rng.uniform(-0.06, 0.06) * W, h2(top - ch * 0.12), cw * 0.66, cd * 0.62, max(1.0, ch * 0.28))
            a0 = rng.uniform(0, math.tau)
            for i in range(n):
                a = a0 + i * math.tau / n + rng.uniform(-0.35, 0.35)
                rx, rz = cw * 0.5 * math.cos(a), cd * 0.5 * math.sin(a)
                lw, ld = cw * rng.uniform(0.32, 0.48), cd * rng.uniform(0.34, 0.5)
                lh = ch * tall * rng.uniform(0.4, 0.75)
                ly = y0 + ch * tall * rng.uniform(0.0, 0.35)
                add(rx * 0.85, rz * 0.85, h2(max(0.0, ly)), lw, ld, lh)
            if n >= 4:                                 # a small knob on the crown
                add(rng.uniform(-0.12, 0.12) * W, rng.uniform(-0.1, 0.1) * W, h2(top + ch * 0.1), cw * 0.3, cd * 0.3, max(0.5, ch * 0.18))

        n = {"small": 2, "medium": 4, "large": 6}[size]
        if style == "boulder":
            lumps(W * 0.6, W * 0.52, H * 0.72, n)
        elif style == "crag":                          # angular: taller, narrower, with a split slab leaning on it
            lumps(W * 0.5, W * 0.42, H * 0.75, n, tall=1.25, crown=False)
            add(W * 0.3, -W * 0.08, 0.0, W * 0.22, W * 0.3, H * rng.uniform(0.75, 0.95))
            if size != "small":
                add(-W * 0.22, W * 0.12, 0.0, W * 0.18, W * 0.22, H * rng.uniform(0.55, 0.7))
        elif style == "flat":                          # a low sandstone shelf with a second shelf on top
            lumps(W * 0.7, W * 0.5, H * 0.45, n, skirt=True, crown=False)
            add(W * 0.1, -W * 0.05, h2(H * 0.4), W * 0.5, W * 0.36, H * 0.3)
            if size == "large":
                add(-W * 0.12, W * 0.08, h2(H * 0.65), W * 0.3, W * 0.24, H * 0.22)
        elif style == "sunk":                          # half sunk into the mud: the core starts below the ground
            lumps(W * 0.66, W * 0.56, H * 0.8, n, y0=-H * 0.3, skirt=False)
''' + s[e:]

# extras: sand drifts round the foot (plains), and soft layers
rep('''        if "drips" in ex:''', '''        if "sand" in ex:                             # sand drifted against the foot of the rock
            for i in range({"small": 1, "medium": 2, "large": 3}[size]):
                a = rng.uniform(0, math.tau); r = W * 0.42
                x, z = ox + r * math.cos(a), r * 0.8 * math.sin(a)
                f, t = box(x, z, 0.0, W * rng.uniform(0.25, 0.35), W * 0.18, 1.0 if size != "small" else 0.5)
                cube(size, f"sand_drift_{i + 1}", g_det, f, t, rotation=(0, math.degrees(-a), 0), origin=[h2(x), 0, h2(z)], kind="sand")
        if "drips" in ex:''')
rep('''            elif kind in ("moss", "snow", "slime", "stem", "cap"):''', '''            elif kind in ("moss", "snow", "slime", "stem", "cap", "sand"):''')
rep('''        if "strata_faint" in ex and face != "up":''', '''        if "strata_soft" in ex and face != "up":     # soft sandstone bands
            v += np.sin(Y * 1.3 + fbm(X * 0.2, 0, Z * 0.2) * 3.5) * 0.6
        if "strata_faint" in ex and face != "up":''')
s = s.replace('"rocks_showcase"', '"rocks_showcase"')
open("build_foliage_rocks.py", "w", encoding="utf8", newline="\n").write(s)
print("written")
