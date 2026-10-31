# Blockbench Detailed Prompts

> Status: draft v5 · Owner: J00BA · Last updated: 2026-10-31
>
> How Claude turns a short request like "make me a tall pine tree, dark green leaves, brown trunk" into a full, detailed build spec, and then builds a Hytale style Blockbench model from it. This doc covers every 3D asset type in the world. It must agree with `game_direction.md`, `game_worlds.md` and `resource_gathering.md`. Where they differ, those docs win.

---

## 0. How to use this doc

**For J00BA:** write a short request. Name the asset, plus anything you care about (size, colours, tier, biome, mood). Everything you leave out, Claude fills in from this doc.

```
Make me a tall pine tree, dark green leaves, brown trunk.
Make me a gold ore vein.
Make me a frost dragon, ice blue, cracked crystal armour.
Make me a blacksmith NPC, burly, leather apron.
Make me a voidstone sword.
```

**For Claude:** when you get a request like this, do these steps in order. Do not skip any.

1. **Find the category** in section 3 (trees, ore veins, rocks, foliage, tools, weapons, armour, NPCs, mobs, dragons, props, textures, effects). If it fits more than one, use the closest and borrow from the others.
2. **Read the global rules** (section 1) and the build method (section 2). They apply to every asset.
3. **Expand the request** into a full build spec using the category's **prompt template**. Every field gets a value. Values the user gave win. Everything else comes from the category's defaults, the tier and biome tables, and the reference analysis.
4. **Show the expanded spec** to the user at the top of your reply (short, in the template's layout), then build. Don't wait for approval unless the request is truly unclear.
5. **Build the model** as a `.bbmodel` file with an embedded, hand painted style texture (section 2).
6. **Run the quality checklist** (section 4) and fix anything that fails before you hand it over.
7. **Save it** in the right folder with a lowercase, underscore name (section 1.8).

> The golden rule: **a short request never means a simple model.** "A pine tree" gets the same care as a hero asset: layered silhouette, many cubes, every face textured with shaded, noisy, hand painted pixels.

---

## 1. Global rules (every asset)

### 1.1 The look we are going for

The art style is **Hytale** mixed with **RuneScape: Dragonwilds** (see `game_worlds.md` section 2).

- **Voxel built, not block based.** Models are made of many cubes of different sizes, stacked, offset and sometimes rotated. They are never just one big box.
- **Chunky, readable silhouettes.** Bold shapes that read from far away, with lots of small breakup on the edges up close.
- **Hand painted pixel textures.** Every face has real pixel detail: shading ramps, noise, highlights, cracks, grain. **No flat colour fills.**
- **Stylized, colourful, soft.** Saturated but not neon (except glowing parts). Warm lights, cool shadows.
- **Exaggerated proportions.** Big heads and eyes on characters, thick trunks and big canopies on trees, oversized ore chunks on rocks.

### 1.2 What the reference images teach

These are the reference images J00BA supplied, and what to copy from each.

| Reference | What to copy |
| --- | --- |
| **Round canopy tree** (dark trunk, layered leaves) | Canopy built from 10 to 20 overlapping slabs at different heights, each sticking out past the one below, so the outline is stepped, not a sphere. Leaf texture is dense small leaves with dark gaps, lighter on top faces. A side branch pokes out from the trunk. Trunk is made of vertical plank-like strips with grooves and a darker band near the top. Roots flare out at the base, with moss patches and tiny ground debris cubes. |
| **Hytale forest** (pines, spruces, autumn tree) | **The main reference for leaves.** Deep, soft, feathery canopies; tiers overlap so much that each tree reads as one solid spire; branches droop down and out; needle sprays painted on alpha cards; smooth dark to light gradient, teal blue shadows, no busy speckle; trunk hidden except near the ground; a pointed leader on top. |
| **Tall pine** | Narrow cone silhouette that tapers to a ragged tip. Foliage is many offset leaf clusters in overlapping tiers, not smooth cones. The outline is jagged everywhere. Trunk flares into a wide stepped root base. Two or three greens, darker inside, lighter on the outer tips. |
| **Big voxel tree** (cinematic) | Huge cube-built canopy with clusters that bulge out, trunk with a strong root flare, warm rim light on the edges. Shows the "big and chunky" end of the style. |
| **Willow-like tree** (yellow green) | Canopy that **droops**: hanging fringe strips on the edges, uneven top, a few holes that show the trunk. Twisted trunk with a branch arm. Good base for swamp and frost trees. |
| **Copper vein** (Blockbench screenshot) | Stone core made of many small grey cubes at different heights so the top is lumpy. Big chunky ore crystals (3 to 6 of them) sticking out at angles, mostly near the top and sides. The ore colour also runs through the stone texture as **cracks and veins**. Small ore and stone fragments lie loose on the ground around it. Moss on top. One 128×128 texture. |
| **Eagle** | Body built from layered feather slabs, wing that overlaps the body, white head with a hooked yellow beak, tiny yellow talons. Feathers painted as rows of light-edged pixel feathers. |
| **Pigeon** | Simple boxy body, but rich texture: gradient from blue grey to darker, feather rows, a big round orange eye with a dark pupil and a white highlight pixel, small head tuft. Proof that texture carries the detail. |
| **Fennec fox NPC** | Huge head and ears, big glossy eyes with highlight pixels, small body, clothes painted on with straps, buckles and stitching. Warm, friendly NPC look. |
| **Green imp** | The base imp: big cube head, giant dark eyes with highlights, pointy ears sticking out sideways, leafy tuft on top, short body and stubby limbs. This is the scale and charm reference for all characters. |
| **Frost dragon** | Dark body covered in pale blue ice crystal shards sticking out at angles. Green translucent looking wings. Open mouth with red inside. |
| **Void dragon** (being ridden) | Huge curved horns made from chained, rotated segments. Wing membranes with ragged holes. Glowing purple eyes and mouth. White bone spikes along the wing arms. Shows how big a dragon is next to a player. |
| **Basic sword** | Clean steel blade with a light centre line (fuller), soft gradient from dark at the base to light at the tip, simple cross guard, brown wrapped grip, round pommel. |
| **Void sword** | Same layout, but the blade glows purple with a darker core rune pattern, gem set in the guard, ornate dark guard with spikes, pale wrapped grip, glowing pommel. Shows how higher tiers get more ornate. |
| **16 Hytale plants** (flowers, bushes, grass, ferns, dead bushes, mushrooms, leaf litter) | **The main reference for foliage.** Plants are built from many flat alpha cards, one painted leaf or blade per card, fanning out from one base point and crossing each other. Full analysis in section 3.4.1. |
| **Pickaxe** | Curved two-sided head built from stepped segments that taper to points, a square metal socket with a gold emblem, a cap pin on top, a carved dark wood handle, a metal end cap. |

### 1.3 Units and scale

All models use the same scale so they look right next to each other.

| Thing | Size in Blockbench units |
| --- | --- |
| 1 Blockbench unit | 1 "pixel" of size. 16 units = 1 block ≈ 1 metre |
| Imp (player) height | **18 units** (the `scale_dummy_imp` in every mob file) |
| Door | 16 wide × 28 tall |
| Small bush | 8 to 14 tall |
| Ore vein | 16 to 32 wide, 12 to 28 tall |
| Normal tree (T1 to T3) | 64 to 112 tall |
| Tall tree (pine, titanwood) | 112 to 192 tall |
| Giant tree (worldbark) | 192 to 320 tall |
| Sheep / pig size mob | 10 to 18 tall |
| Cow / wolf size mob | 18 to 26 tall |
| Ogre size mob | 36 to 48 tall |
| Dragon (standing) | 26 to 64 tall, 40 to 120 long |

- The model stands on **y = 0**. Its centre of mass sits over **x = 0, z = 0**.
- Mobs and NPCs face **north (−z)**. This is how all existing mob files are set up.
- Every character and mob file includes a hidden **scale dummy**: a group `scale_dummy` with one cube `scale_dummy_imp` from `[-2, 0, -2]` to `[2, 18.5, 2]` (or placed beside the model), with `export: false` and `visibility: false`. Keep it in every file so size can be checked.

### 1.4 Texel density (how big a pixel is)

Every existing model uses **2 texture pixels per Blockbench unit** (32 pixels per block). This keeps pixels the same size on everything in the world, which is what makes the Hytale look feel consistent.

| Asset type | Pixels per unit | Why |
| --- | --- | --- |
| World assets: trees, ore veins, rocks, foliage, mobs, dragons, NPCs, props | **2** | Matches all existing mob models |
| Held items: tools, weapons | **4** | Seen up close in the player's hand and in previews, so they get finer detail |
| Worn armour | **2** | Must match the character it sits on |

- **Never stretch** a texture. A face that is 6 × 4 units gets exactly a 12 × 8 pixel UV area (at 2 px/unit).
- Half unit cubes (0.5) are fine and get 1 pixel. Don't go smaller than 0.5 units on world assets.

### 1.5 Texture rules

"Very detailed textures" means **every face is painted**, not filled. Follow all of these:

1. **One texture per model**, square and a power of two: 64, 128, 256 or 512. Pick the smallest that fits at the right texel density. Name it the same as the model (`pine_tree.png` for `pine_tree.bbmodel`) and embed it in the file.
2. **Colour ramps, not single colours.** Each material gets a ramp of **5 to 8 shades**, from deep shadow to highlight. **Hue shift** the ramp: shadows lean cooler (towards blue or purple), highlights lean warmer (towards yellow). Never just add black or white.
3. **Never use pure black (#000000) or pure white (#ffffff).** Darkest outline tone is a very dark version of the material colour.
4. **Face lighting baked in:** top faces are the lightest, side faces in the middle, bottom faces the darkest. North/south and east/west sides can differ slightly to fake a light direction (light comes from the top, slightly front left).
5. **Pixel noise on every face.** Scatter 2 to 3 nearby shades across each face so nothing is flat. Use clusters of 2 to 4 pixels, not single-pixel static.
6. **Edge highlights and contact shadows.** Lighten the top edge of each face by one shade. Darken pixels where a cube meets another cube or the ground (fake ambient occlusion).
7. **Material detail on top of noise:** bark grain, stone cracks, ore veins, leaf shapes, feather rows, fur strands, metal scratches, cloth stitching, wood grain. Each category below says what.
8. **Total colours per texture:** aim for **40 to 120** distinct colours. The existing mobs use 21 to 52, so new assets should go **beyond** them in detail, not below.
9. **Glowing parts** (voidstone, stellarite, magic, eyes on some mobs, effects) use bright, saturated, almost-white centres. Put them on cubes whose names end in `_glow`, so Godot can make them emissive. There is no separate emissive texture.
10. **Reuse UV space smartly.** Cubes that look the same (leaf clusters, stone chunks, ore crystals) can share the same UV area. This lets a huge tree keep a small texture. Faces that can never be seen (inside a canopy, pressed against another cube, under the model) get UV `[0, 0, 0, 0]` and texture `null`, like the hidden faces in `wolf.bbmodel`.
11. **Transparency** only for leaf edges, feathers, wing holes, cloth tatters and effects. Use hard alpha (fully on or off), not soft alpha.

### 1.6 Model build rules

1. **Blockbench format:** `format_version: "5.0"`, `model_format: "free"` (Generic Model), `box_uv: false` (per-face UV). Same as all existing files.
2. **Cubes only.** No meshes. Rotated cubes are allowed and encouraged for ore crystals, horns, branches, spikes and blades (rotate in steps of 22.5° or any angle in Blockbench's free format, but keep it readable).
3. **Many cubes, layered.** Break every big shape into a main block plus smaller blocks that step, overlap and stick out. Never leave a large flat face with nothing on it.
4. **Groups (bones) for every moving or logical part**, with a pivot (`origin`) at the joint. A root group named after the model holds everything.
5. **Name every group and cube** in lowercase with underscores. Main cube of a group is `<group>_box`. Sides use `_right` and `_left` (the model's right and left). Repeats are numbered: `leaf_cluster_1`, `leaf_cluster_2`.
6. **Symmetry:** characters and mobs are mirrored left and right, then broken slightly (a scar, a tilted ear, a missing scale) so they don't look copied. Trees and rocks are **never** symmetrical.
7. **Silhouette first.** The shape must read as the right thing as a solid black shape. Then add the details.

### 1.7 Cube budgets

These keep models detailed but still light enough for a browser game (see `game_worlds.md` section 2.2).

| Asset | Cubes | Texture |
| --- | --- | --- |
| Grass tuft, flower, mushroom, ground scatter | 6 to 30 (mostly alpha cards) | 64 |
| Bush, fern, large leaf plant | 30 to 90 (mostly alpha cards) | 128 |
| Ore vein, rock | 30 to 90 | 128 |
| Tree (T1 to T5) | 100 to 260 | 128 or 256 |
| Tree (T6 to T10, giant) | 150 to 400 | 256 or 512 |
| Tool, weapon | 10 to 40 | 64 or 128 |
| Armour piece | 10 to 40 | 64 or 128, one per piece |
| Small mob | 20 to 50 | 64 or 128 |
| Large mob, NPC | 40 to 130 | 128 or 256 |
| Dragon | 100 to 250 | 256 |
| Prop (crate, bench, sign) | 10 to 60 | 64 or 128 |
| Building | 100 to 500 | 256 or 512 |

### 1.8 File names and folders

Follow the repo naming rules: lowercase, `_` instead of spaces. Source files are `.bbmodel`. The texture is embedded and also saved as a `.png` in `godot-game/assets/textures/<group>/` with the same name (for example `textures/trees/pine_tree.png`, `textures/foliage/red_flame_bush.png`), like the existing tree textures.

| Asset | Folder |
| --- | --- |
| Trees | `godot-game/assets/models/trees/` |
| Ore veins | `godot-game/assets/models/ores/` |
| Rocks | `godot-game/assets/models/rocks/` |
| Foliage (grass, flowers, bushes, mushrooms, vines) | `godot-game/assets/models/foliage/` |
| Tools | `godot-game/assets/models/tools/` |
| Weapons | `godot-game/assets/models/weapons/` |
| Armour | `godot-game/assets/models/armour/` |
| NPCs | `godot-game/assets/models/npcs/` |
| Mobs | `godot-game/assets/models/mobs/` |
| Dragons | `godot-game/assets/models/mobs/` (they are mobs) |
| Props and buildings | `godot-game/assets/models/props/`, `godot-game/assets/models/buildings/` |
| Effects | `godot-game/assets/models/effects/` |
| Standalone textures (terrain, tiling) | `godot-game/assets/textures/<group>/` |

Names use the in-game id where one exists: `pine_tree.bbmodel`, `copper_vein.bbmodel`, `iron_pickaxe.bbmodel`, `obsidian_sword.bbmodel`. Variants get a number: `pine_tree_2.bbmodel`.

---

## 2. Build method (how Claude actually makes the file)

Claude can't click in Blockbench, so models are written as `.bbmodel` JSON by a script. Use this method every time.

1. **Write a Python build script** (in a scratch folder, not the repo) that:
   - Defines a palette (the ramps from section 5) as RGB values.
   - Lists every cube: name, `from`, `to`, optional `rotation` and `origin`, and which group it belongs to.
   - Lists every group with its pivot.
   - Packs UVs: for each visible face, reserves a rectangle in the texture at the right texel density (section 1.4), reusing shared rectangles for repeated parts.
   - **Paints each face rectangle** with Pillow: base ramp, face lighting (top/side/bottom), noise clusters, edge highlights, contact shadows, then the material detail pass (grain, cracks, veins, leaves, feathers).
   - Saves the PNG, base64 encodes it into the texture `source` field, and writes the `.bbmodel` JSON.
2. **Copy the JSON layout** from an existing file in `godot-game/assets/models/mobs/` (top level keys `meta`, `name`, `model_identifier`, `resolution`, `elements`, `groups`, `outliner`, `textures`, `animations`). Use fresh UUIDs for everything.
3. **Render a preview** (Pillow isometric or a quick three.js / Blender render if available) from the front three quarter view and look at it. Fix the silhouette and texture before calling it done.
4. **Animations** (mobs, NPCs, dragons, and the tree `hit` shake) go in the same file, using the names in section 3. Use `catmullrom` for smooth motion and `linear` for snappy hits, like the existing files.

> Painting tip: write small helper functions once (`ramp_fill`, `noise`, `edge_light`, `ao_edge`, `cracks`, `grain`, `leaf_pattern`, `feather_rows`, `veins`) and reuse them. Detail comes from layering several passes, not from one clever function.

---

## 3. Categories

Each category has:

- **Analysis:** what makes this asset look great in our style.
- **Anatomy:** the parts to build, in build order.
- **Texture recipe:** what to paint.
- **Prompt template:** the fields Claude must fill when expanding a short request.
- **Example:** a short request and the expanded spec.

### 3.1 Trees

**Analysis.** Trees are the biggest foliage in the world and the main lumbering node, so they must look rich from far away and up close. The references show the key moves: a **chunky trunk with a big root flare**, a **clean trunk with nothing stuck to it**, a **deep, overlapping canopy built only from alpha leaf cards** (no solid leaf blocks) with a soft, feathery outline (see **Leaves the Hytale way**), and **small ground details** (moss, roots, debris) that tie the tree to the ground. A tree with a smooth ball or perfect cone canopy is wrong.

**Anatomy (build order).**

1. `roots`: 4 to 8 root cubes flaring out from the trunk base, stepping down to the ground. Some overlap the ground plane slightly.
2. `trunk`: 2 to 6 stacked trunk sections that get a little thinner going up, offset by 0.5 to 1 unit so the trunk isn't perfectly straight. Each section starts exactly where the one below ends and sits **inside the footprint** of the one below. Add bark strip cubes (0.5 to 1 unit proud) flush on the sides. Nothing else touches the trunk: see **Clean trunks and branches** below.
3. `branches`: 2 to 6 branches. Rotated cubes coming out of the trunk at 20° to 50°, each ending inside a canopy cluster. Every branch piece starts inside the trunk or the branch it grows from, so nothing floats.
4. `canopy`: the leaves. Shape depends on the tree type (table below). Built the Hytale way from many **leaf cards** only (thin alpha cutout planes painted with needle or leaf sprays). **No solid leaf core cubes.** Follow **Leaves the Hytale way** below exactly.
5. `details`: moss patches on roots, mushrooms, fallen leaves, small stones, hanging vines, fruit, cones, tier specific extras (ice, runes, gems).

**Movement.**

- **Wind sway is done in Godot**, with a wind vertex shader on the leaf material, not with a Blockbench animation. It is cheaper, works with batched foliage (`MultiMeshInstance3D`) and keeps every tree moving without animation players. So don't make an `idle` sway animation.
- Keep the `canopy` and `branches` groups and keep leaves on their own cubes, so the shader can sway the leaves more than the trunk.
- **Every tree has a `hit` animation**: a short shake (about 0.4s, `linear`) played each time a player chops it. The `canopy` group rotates a few degrees back and forth (about 3° to 5°, settling to 0) and the `trunk` nudges about 1°. The pivot of `canopy` sits where the trunk meets the canopy, and the pivot of `trunk` at the ground.

**Leaves the Hytale way.**

The first pine built from this doc had the right trunk but the wrong leaves: **flat, thin, horizontal discs** stacked like plates, with big gaps showing the trunk, plus a busy speckle texture with neon yellow green dots. Hytale trees look completely different. Their foliage is a **deep, soft, feathery mass**: tiers overlap so much that the canopy reads as one solid shape, branches **droop down and out**, edges are made of **painted needle sprays with alpha**, and the colour is a **smooth gradient** from a dark inside to light tips. Copy these rules.

*What makes Hytale leaves look the way they do*

| Hytale does | Don't do |
| --- | --- |
| Volume: each tier is a thick, sloped skirt, as deep as it is wide at the tips | Thin flat discs or plates |
| Tiers overlap by **40 to 60%** of their height, so the canopy is one continuous mass | Even gaps between tiers |
| Branches **droop**: tier cards tilt **15° to 35° downward** from the trunk to the tip | Perfectly horizontal tiers |
| Trunk hidden inside the canopy; it shows only below the lowest tier and in **1 to 3 small glimpses** higher up | Trunk visible between every tier |
| Outline made of **alpha cutout needle sprays**, soft and feathery | Hard square cube edges |
| Painted **needle sprays and leaf clumps**, each with a light tip and a dark base | Random pixel noise or speckle |
| **Smooth gradient:** dark inside, mid body, light tips; top of the tree lighter than the bottom | Flat dark green with bright dots |
| Soft, low contrast highlights, slightly blue or teal for conifers, warm for broadleaf | Neon yellow green highlight pixels |
| Narrow spire with a single pointed **leader** at the top | Rounded or flat top |
| A few small accents: brown cones, orange dead needles, bare stub branches poking out low down | No accents, or lots of busy accents |

*How to build it with cubes*

1. **No leaf core.** Don't put solid cubes inside tiers or clusters. They end up wrapped round the trunk and branches as random blocks (J00BA removed every one by hand from `frostbark_tree`). Fill the inside with **inner cards** instead: 3 to 5 cards per tier (or cluster) starting at the trunk or branch, painted in the darkest shades of the leaf ramp, plus 2 **top cards** above them.
2. **Leaf cards.** Build each tier or cluster from **thin cubes (0 to 0.5 units thick)** that use alpha textured faces, like Hytale's foliage planes. Each card is 6 to 16 units long and 4 to 10 wide.
   - Conifer tier: **8 to 16 cards** radiating round the trunk like a skirt, each **rotated 15° to 35° downward** and twisted 5° to 15° so no two match. Add **crossed pairs** (two cards at 90° to each other) at the tips so the tier looks full from every angle.
   - Broadleaf cluster: 6 to 10 cards at mixed angles round the cluster centre, plus crossed pairs sticking out of the edges.
   - Top faces of a tier also get 2 to 4 flat or gently tilted cards so the top is not bare.
3. **Overlap.** Each tier starts **inside the tier below**: the next tier's cards begin at about half the height of the tier under it. Going up, tiers get narrower and slightly brighter.
4. **Leader and tip.** End conifers with a thin vertical leader (1 to 2 units wide) wrapped in 2 to 4 small crossed cards that come to a point.
5. **Broken edges.** Push 10 to 20% of the cards further out or lower than their neighbours, so the outline is irregular. Leave 1 to 3 small gaps where the trunk or a bare stub branch shows.
6. **Double sided.** Cards are seen from both sides: set the texture `render_sides` to `double`, and use alpha scissor with back face culling off in Godot.

*How to paint leaf cards*

- **Needle spray (conifers):** draw a central twig 1 pixel wide, then needles as 1 pixel diagonal strokes 2 to 5 pixels long fanning out on both sides, angled towards the tip. Stack 3 to 5 sprays per card, overlapping. Each needle is darker at the base and lighter at the end. The card's outline follows the needle tips, everything else is transparent.
- **Leaf clump (broadleaf):** groups of leaf shapes 3 to 6 pixels each (oval, pointed or five point for maple), each with a 1 pixel light edge on the top side and a darker shadow under it.
- **Gradient on every card:** dark near the trunk end, lighter at the tip. Upper tiers use the lighter half of the ramp, lower tiers the darker half.
- **Inner cards:** the two darkest ramp shades with soft needle or leaf shapes painted in, so gaps between the outer cards look deep, not black.
- **Ramp:** 6 to 8 shades with small steps between them (no big jumps). For conifers, shift shadows towards teal and blue and keep the lightest shade a soft green, never neon. Highlights only on the **top and outer** 2 to 3 pixels of each spray.
- **Accents:** at most 1 to 3% of pixels: brown cones, orange or rust dead needles, the odd lighter new growth tip.
- **Texture space:** paint **3 to 6 card variants** (one of them dark, for inner cards), and reuse them across every card by sharing UVs. A 256 texture is enough for a whole pine.

**Clean trunks and branches.**

Claude's first trees had random blocks stuck all over the trunk: the solid leaf cores of each tier, each one wider than the trunk and turned to a random angle, so with the cards hidden the trunk looked like a stack of green boxes. J00BA fixed `frostbark_tree.bbmodel` by hand, and it is the reference for every tree. Its trunk is only stacked `trunk_*` sections, flush `bark_strip_*` cubes, 2 low `stub_branch_*` cubes and a few small `ice_crystal_bark_*` details. Its canopy is only thin cards (`tier_<n>_card_*`, `_cross`, `inner_card_*`, `top_card_*`) plus snow and icicles.

*When building a tree:*

1. **Trunk.** Only `trunk_<n>` sections. Each one starts at the `to` height of the one below and fits inside its footprint (taper and offset inwards, never a lip sticking out).
2. **On the trunk,** only: `bark_strip_<n>` (thin, flush against a face, 0.5 to 1 unit proud), 1 to 3 small `stub_branch_<n>` low down that start inside the trunk, and the tree's small signature details (2 to 4 cubes, under 2 units thick, like ice crystals or runes). Nothing else.
3. **Branches** are chains of rotated cubes. Each piece starts inside the trunk or the piece before it.
4. **No solid cube in the canopy.** No `*_core*`, `centre_core`, `lobe_*_core` or filler blocks. Every leaf element is a card (one size is 0) or a thin card (0.5 or less). Solid cubes allowed above ground are only the trunk, branches, bark strips, stubs, the leader, and the small details listed above.

*When checking or fixing an existing tree:*

1. Run `python3 tools/clean_tree_trunks.py` (or pass the file). It lists, per model, the leaf cores (`core`), any other solid cube that the trunk or a branch runs through (`wraps`), branch pieces that don't touch the trunk or another branch (`floating`), and trunk sections with a gap or a lip (`step`).
2. Run `python3 tools/clean_tree_trunks.py --fix` to delete every leaf core cube, the groups they leave empty and their animation tracks. Fix `wraps`, `floating` and `step` by hand: delete the stray cube, or move it so it starts inside the trunk or branch.
3. Re-export with `python3 tools/bbmodel_to_gltf.py <file>` and look at the tree with the leaf cards hidden. The trunk must read as one clean, tapering column, like `frostbark_tree`.

**Canopy shapes.**

| Shape | Build | Used for |
| --- | --- | --- |
| Cone (conifer) | 8 to 16 drooping skirt tiers (8 to 16 cards + 3 to 5 inner cards each), overlapping 40 to 60%, each narrower going up, ending in a pointed leader | Pine, frostbark, titanwood |
| Round dome | 8 to 16 clusters (6 to 10 cards each) packed into a dome, wider in the middle, clusters bulge out unevenly | Oak, maple, hickory |
| Tall oval | Like the dome but narrow and tall, smaller clusters, a few more gaps | Birch |
| Drooping | Dome or oval, plus long hanging cards (4 to 12 units) along the edges, painted as trailing leaf strands | Swamp trees, runewood, willow types |
| Layered crown | Several thick, sloped canopy pads (layered cards) at different heights on thick branches | Gembark, worldbark |

**Texture recipe.**

- **Bark:** vertical grain lines 1 pixel wide, darker grooves every 3 to 5 pixels, a few knots (ring of 2 to 3 shades), lighter top faces on root steps. Base is darker and has moss (green clusters) creeping up 4 to 10 pixels. End grain (the top of cut faces) shows rings.
- **Leaves:** see **Leaves the Hytale way** above: needle sprays or leaf clumps on alpha cards, dark inner cards, a smooth dark to light gradient, soft highlights and very few accents.

**Tree tiers.** Use these defaults for each lumbering tree in `resource_gathering.md`. The user's words override them.

| Tree | Tier | Biome | Shape | Height | Bark ramp | Leaf ramp | Signature detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pine | T1 | Forest | Cone | 112 to 160 | Warm brown | Dark green, blue shadows | Pine cones, ragged tip, stepped root flare |
| Birch | T2 | Forest | Tall oval | 80 to 112 | White with black dashes | Bright yellow green | Black bark marks, thin trunk, airy canopy |
| Oak | T3 | Forest | Round dome | 80 to 112 | Dark brown, deep grooves | Rich mid green | Thick trunk, big side branch, acorns, moss |
| Maple | T4 | Mountain | Round dome | 80 to 112 | Grey brown | Red orange to gold | Five point leaf shapes, fallen leaves on ground |
| Hickory | T5 | Mountain, frost | Tall dome | 96 to 128 | Shaggy grey, peeling strips | Deep olive green | Peeling bark plates sticking out, nuts |
| Frostbark | T6 | Frost | Cone | 112 to 160 | Pale blue grey | Frosted blue green, white tips | Snow caps on every tier, icicles, ice crystals in bark |
| Titanwood | T7 | Plains, swamp | Very tall cone or column | 160 to 192 | Steel grey with silver bands | Deep teal | Huge root buttresses, metal-like sheen lines in bark |
| Runewood | T8 | Swamp | Drooping | 112 to 160 | Near black purple | Murky green with violet | Glowing runes carved in trunk (`_glow`), hanging vines |
| Gembark | T9 | Plains | Layered crown | 128 to 176 | Dark bark with gem crystals growing out | Jewel green, crystal sparkles | Rotated gem crystal cubes on trunk and branches (`_glow`) |
| Worldbark | T10 | Forest | Layered crown, giant | 192 to 320 | Ancient grey brown, huge grooves | Deep emerald with gold light | Enormous roots, glowing sap cracks, tiny floating leaf particles as cubes |

**Prompt template.**

```
TREE BUILD SPEC
name / id:        <tree>_tree            (e.g. pine_tree)
tier / biome:     <T1..T10> / <biome>
size:             <height> tall, canopy <width> wide, trunk <width> at base
silhouette:       <cone | round dome | tall oval | drooping | layered crown>, ragged stepped outline
trunk:            <sections>, lean <direction>, root flare with <n> roots, flush bark strips, nothing else on it
branches:         <n> rotated branches at <angles>, each ending in a cluster
canopy:           <n> tiers/clusters, each <n> alpha leaf cards + 3 to 5 dark inner cards, no solid cubes, cards droop 15 to 35°,
                  tiers overlap 40 to 60%, trunk hidden except <1 to 3> glimpses, pointed leader (conifers)
ground details:   <moss, mushrooms, stones, fallen leaves, cones>
bark texture:     <ramp>, vertical grain, grooves every 3 to 5 px, knots, moss at base
leaf texture:     <ramp, 6 to 8 small steps>, <needle sprays | leaf clumps> on alpha cards, dark base to light tip,
                  dark inner card variant, soft highlights on top and outer edges only, accents <= 3%
signature detail: <from tier table or user>
budget:           <cubes>, texture <size>, 2 px/unit, shared UV for repeated clusters
groups:           <tree> > roots, trunk, branches, canopy, details
animations:       hit (0.4s shake of canopy and trunk); wind sway is a Godot shader
```

**Example.** "Make me a tall pine tree, dark green leaves, brown trunk."

```
TREE BUILD SPEC
name / id:        pine_tree
tier / biome:     T1 / forest
size:             144 tall, canopy 56 wide at the bottom, trunk 10 wide at base
silhouette:       narrow cone, 12 tiers, jagged outline, 3 tiny clusters at a ragged tip
trunk:            5 sections tapering 10 → 4 wide, slight lean north east, 6 roots stepping out to 18 wide
branches:         no visible branches, tier clusters attach to trunk; 2 dead stub branches low down
canopy:           13 drooping skirt tiers, each 10 to 14 alpha cards tilted 20 to 30° down + 3 to 5 dark inner cards,
                  crossed card pairs at the tips, tiers overlap 50%, bottom tier 56 wide, trunk visible
                  below the lowest tier and in 2 small glimpses higher up, thin pointed leader on top
ground details:   2 pine cones, 4 needle litter flecks, moss on 3 roots, 1 small mushroom
bark texture:     warm brown ramp (7 shades), vertical grain, grooves, 2 knots, moss creeping 6 px up
leaf texture:     dark green ramp with teal blue shadows (7 small steps), 5 needle spray card variants
                  (1 dark, for inner cards), needles dark at the base and soft light green at the tips, lower tiers
                  darker than upper tiers, a few brown cones and rust dead needles, no neon highlights
signature detail: stepped root flare, ragged tip, cones
budget:           ~240 cubes, 256 texture, 2 px/unit, card UVs shared across all tiers
groups:           pine_tree > roots, trunk, canopy (tier_1..tier_12), details
animations:       hit (0.4s shake, canopy pivot at y 20, trunk pivot at y 0)
```

### 3.2 Ore veins

**Analysis.** Ore veins are the mining nodes, so the player must be able to tell at a glance **which ore** it is and **which tier**. The copper vein reference is the pattern: a **lumpy grey stone core**, **big ore chunks sticking out at angles**, the **ore colour running through the stone as veins**, and **loose fragments** on the ground. Higher tiers get bigger, more dramatic and eventually glow.

**Anatomy (build order).**

1. `base`: 1 to 3 wide low cubes that sit on the ground and sink into it slightly (y from −1).
2. `stone`: 15 to 40 stone cubes (2 to 8 units each) piled into a lumpy mound. Vary heights so the top is uneven, like the copper reference. Leave a few cubes sticking out on the sides.
3. `ore`: 3 to 8 ore chunks, 3 to 7 units each, **rotated** 10° to 40° on one or two axes, pushed half into the stone. Bigger chunks near the top, smaller ones on the sides. Some chunks are built from 2 cubes for a crystal or nugget shape.
4. `fragments`: 3 to 8 small loose cubes (1 to 2 units) of stone and ore scattered on the ground around the base.
5. `details`: moss on top, grass tufts at the base, biome extras (snow cap, ice, swamp slime, void crystals, star sparkles).

- **Ore veins have no animations.** They don't shake when mined. Mining feedback comes from the chip effects (section 3.13).

**Texture recipe.**

- **Stone:** grey ramp (6 to 8 shades, cool shadows) with clusters of noise, chiselled block lines, small cracks (1 pixel dark lines with a light pixel beside them), lighter top faces.
- **Veins in the stone:** ore coloured lines 1 to 2 pixels wide that wander across stone faces and continue over edges onto the next face. This is what makes the copper reference look rich.
- **Ore chunks:** the ore ramp with strong highlights on the top and top-left edges, a dark outline shade on the bottom edges. Metal ores get sharp specular pixels. Crystal ores get facet lines (diagonal light and dark halves). Glowing ores get a bright core.
- **Moss:** small green clusters on top faces only, spilling 1 to 2 pixels over the edge.

**Ore tiers.** Defaults for each ore in `resource_gathering.md`. Biome extras come from `game_worlds.md` section 4.4.

| Ore | Tier | Stone | Ore look | Ore ramp (dark → light) | Size | Glow | Signature detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coal | T1 | Mid grey | Black lumps, matte with faint blue sheen | #1a1a22 → #4a4e5c | 16 to 20 wide | No | Sooty dark streaks on the stone |
| Tin | T2 | Light grey | Dull silver nuggets | #5c6268 → #d6dbe0 | 16 to 20 | No | Pale speckles across the stone |
| Copper | T3 | Dark grey | Orange copper chunks, some green patina | #5a2410 → #f28c52 | 18 to 22 | No | Green patina pixels on chunk edges |
| Iron | T4 | Grey brown | Rusty red brown chunks with grey metal | #3e1c14 → #c47a5a | 18 to 24 | No | Rust stains running down the stone |
| Gold | T5 | Warm grey | Bright gold nuggets | #6b4100 → #ffe27a | 18 to 24 | Faint shine | Gold flecks glittering in the stone |
| Obsidian | T6 | Dark basalt | Glassy black purple shards | #0d0814 → #6a4c9c | 20 to 26 | No | Sharp glassy shards with bright edge highlights |
| Titanite | T7 | Pale stone | Steel blue crystals | #1e3248 → #a8d4f0 | 22 to 28 | Faint | Tall angular crystal columns |
| Dreadstone | T8 | Swamp stone, wet | Dark red black jagged spikes | #1c0608 → #b0242c | 22 to 28 | Red cracks (`_glow`) | Dripping slime, red glowing fissures |
| Voidstone | T9 | Black floating stone | Deep purple crystals | #120424 → #d06cff | 24 to 30 | Yes (`_glow`) | Small stone pieces float above the node |
| Stellarite | T10 | Star dusted stone | White gold crystals with starry flecks | #2a2050 → #fff6c8 | 26 to 32 | Yes (`_glow`) | Star sparkle pixels, tiny orbiting fragments |

**Gems** (dropped while mining, `resource_gathering.md` section 4.2) don't have their own nodes. They can appear as one small accent crystal on the ore vein: diamond on coal, topaz on tin, sapphire on copper, amethyst on iron, ruby on gold, emerald on obsidian, jade on titanite, painite on dreadstone, arcanium on voidstone, eclipsium on stellarite.

**Prompt template.**

```
ORE VEIN BUILD SPEC
name / id:        <ore>_vein            (e.g. copper_vein)
tier / biome:     <T1..T10> / <biome>
size:             <w> × <d> footprint, <h> tall
stone core:       <n> stone cubes, lumpy uneven top, <stone ramp>
ore chunks:       <n> chunks, <shape: nuggets | crystals | shards | spikes>, rotated 10 to 40°,
                  biggest at top, half buried
veins:            ore colour veins across stone faces, wrapping over edges
fragments:        <n> loose stone + ore pieces on the ground
details:          <moss, grass, snow, slime, floating rocks, sparkles>
gem accent:       <gem> crystal, 1 small rotated cube
glow:             <none | faint | _glow cubes on ...>
texture:          128, 2 px/unit, stone ramp + ore ramp from the ore table, cracks, highlights
groups:           <ore>_vein > base, stone, ore, fragments, details
```

**Example.** "Make me a gold ore vein."

```
ORE VEIN BUILD SPEC
name / id:        gold_vein
tier / biome:     T5 / frost (also swamp and stellar)
size:             22 × 20 footprint, 18 tall
stone core:       28 warm grey stone cubes, lumpy top, one tall cube at the back left
ore chunks:       6 gold nugget chunks (two 2-cube nuggets), rotated 15 to 35°, biggest on top
veins:            thin gold veins wandering over 70% of stone faces
fragments:        4 stone pieces, 2 gold nuggets on the ground
details:          snow cap on top stones and snow drift on the north side (frost variant)
gem accent:       1 ruby crystal on the east side
glow:             faint, gold chunks get bright highlight pixels but no emissive
texture:          128, warm grey ramp + gold ramp, cracks, specular pixels on gold
groups:           gold_vein > base, stone, ore, fragments, details
```

### 3.3 Rocks and boulders

**Analysis.** Rocks fill the world and frame paths and cliffs. They are ore veins without the ore: lumpy, layered, mossy, never a single box.

- **Anatomy:** `base`, `stone` (10 to 40 cubes, stepped like a small cliff), `details` (moss, lichen, grass at the base, pebbles).
- **Texture:** stone ramp per biome (forest grey green, mountain blue grey, frost pale with snow tops, plains sandy, swamp dark and wet, void black purple, stellar dark blue with sparkles), cracks, lichen spots, moss on tops.
- **Variants:** make 3 sizes (`_small`, `_medium`, `_large`) from the same texture.

```
ROCK BUILD SPEC
name / id:        <biome>_rock_<size>
size:             <w> × <d> × <h>
shape:            <rounded boulder | flat slab | jagged spire | rock pile>, <n> cubes, stepped
details:          <moss, lichen, snow, pebbles, grass>
texture:          <biome stone ramp>, cracks, lichen, light tops, 2 px/unit, 64 or 128
```

### 3.4 Foliage and plants

**Analysis.** Foliage is what makes the world look lush (`game_worlds.md` sections 2 and 4.10). It is drawn in big batches, so each piece must be **cheap but beautiful**. J00BA supplied 16 Hytale plant references (section 3.4.1). Every plant Claude makes must match them in **design and quality**. Study the rules below before building any plant.

**The big lesson from the references:** Hytale plants are almost never built from solid cubes. They are built from **many flat alpha cutout cards** (cubes 0 units thick), each card painted as **one leaf, one blade, one petal or one twig** with its own gradient and midrib. The cards **fan out from one base point** at many angles and **cross through each other**, so the plant looks full and round from every side. The detail is in the **shape of each painted leaf** and in the **number of cards**, not in solid geometry.

#### 3.4.1 What the plant references teach

| Reference | Type | Size (units) | Colours | What to copy |
| --- | --- | --- | --- | --- |
| Yellow pansy flower | Flower | 10 tall, 10 wide | Petals gold `#eacc5b` to orange `#bd7134`, violet `#6a5aa8` face marks, leaves `#2e5707` to `#5b871e` | 3 flower heads on short curved stems, each head 2 to 3 square petal cards turned outward like a face, a dark violet blotch and a bright yellow eye in the centre. Broad rounded leaf cards in a rosette at the base, spilling onto the ground |
| Big leafy green bush (in world) | Bush | 24 tall, 18 wide | `#285a17` `#316716` `#447819` `#5e8d1f` `#72962b` | An upright, rounded cone of 40+ pointed leaf cards, each leaf a separate painted shape with a light edge and darker vein. No visible core: the leaves overlap so densely that the bush reads as solid. Bottom leaves droop onto the ground |
| Grass tufts on the ground | Grass | 4 to 8 tall | Same greens as the ground texture `#4d6f0d` to `#7aad1d` | Short crossed blade cards that **use the exact ground colours**, so tufts melt into the terrain and only add texture and height. Blades lean outward at different angles |
| Dark fern / small palm | Fern | 20 tall, 18 wide | Dark teal greens `#1d2c20` `#244a2c` `#3c5e3a` `#516331`, stems `#3a3020` | Two or three short dark stems with arching fronds at the top, plus a skirt of lower fronds that droop to the ground. Each frond is a long card with serrated leaflet edges cut by alpha |
| Dead bush | Dead bush | 16 tall, 14 wide | Grey browns `#272019` `#312c24` `#4a3e34` `#5e4e44` | No leaves. 10 to 20 thin twig cards branching from one stump, each twig a stepped zigzag line 1 to 2 pixels wide with forked tips. A few long straight sticks poke up above the rest |
| Thorn bush | Dead bush (thorny) | 14 tall, 18 wide | Purple browns `#211918` `#2c241f` `#403530` `#5a4844` | Three clumps of branches that **curl over at the tips** like hooks, with small thorn pixels sticking out of every branch. Dense at the base, open at the top |
| Dry grass tuft | Grass (tall) | 10 tall, 20 wide | Olive gold `#6a760f` `#859519` `#a8a030` `#c8b448` | A dense fan of blades, plus 4 to 8 **very long, 1 pixel thin blades** that shoot out almost sideways and bend down, giving a wild, wind blown outline. Tips have jagged pixel steps |
| Red flame bush | Bush (spiky) | 16 tall, 18 wide | Leaves deep red `#8a1e18` → `#b73620` → orange `#e86a2c` → yellow tips `#f4b048`, stems dark grey `#3a3a36` | Lance shaped leaves with **serrated pixel edges** pointing up and out like flames, on thin dark grey stems that branch from the base. Each leaf goes from dark red at the base to yellow at the tip |
| Copper autumn bush | Bush (round) | 16 tall, 20 wide | Rust `#5e2622` `#6f3828` `#a85a3c` `#d08a5c`, stems `#4a2a20` | A round bush of short **oblong leaves in clumps** at the ends of thick brown branches. Visible branches at the base. Leaves light peach on the top edge, rust in the middle, dark brown underneath |
| Big leaf plant | Large leaf plant | 16 tall, 22 wide | `#2e4a20` `#36641f` `#457623` `#4d8428` `#6aa040`, midrib `#5a3a22` | 10 to 14 long, pointed leaves that **arch out from the centre** like a hosta or canna. Each leaf has a **dark brown red midrib line** down the middle and a smooth gradient from darker base to lighter middle |
| Frost grass tuft | Grass (frost) | 10 tall, 20 wide | Icy `#83a772` `#a6cbc0` `#cee5ca` `#e4f4ec` | Same build as the dry grass tuft, recoloured pale icy green white. Shows how one shape gets reused across biomes by changing only the colours |
| Frost bush | Bush (frost) | 16 tall, 20 wide | `#779982` `#a6cbc0` `#b9dacc` `#d2ecd5`, stems `#5e7a70` | Puffy, rounded leaf clumps (like snow loaded leaves) on pale stems, and long frosty leaves sweeping out sideways. Almost white tops, blue green shadows underneath |
| Leafy green shrub | Bush (twiggy) | 18 tall, 18 wide | Leaves `#3b6815` `#507f18` `#5e941d` `#7ab03a`, stems `#7a5a2a` | Many thin brown stems growing up and out, each ending in **clusters of small rounded leaves** (3 to 5 pixels each). Leaves get brighter towards the top and outside |
| Red mushrooms | Mushroom | 3 to 6 tall, caps 4 to 8 wide | Cap `#7a1c24` `#9c2830` `#c03a40`, spots `#f0c8c8`, stem `#d8d0c0`, base `#c8c8b8` | The exception: **solid flat slab caps** (thin cubes) with a darker rim and pale pink spots, on short pale stems. A frilly **white alpha card ring** sits on the ground round each base. A group of 3 at different heights |
| Orange leaf litter | Ground scatter | 0.1 tall, cluster 24 wide | `#c86a18` `#e08a28` `#f0a840` | Small flat leaf cards (2 to 3 units each) **lying flat on the ground**, slightly tilted, in a loose cluster. Bright against the grass |
| Yellow leaf litter | Ground scatter | 0.1 tall, cluster 24 wide | `#e0a020` `#f0b830` `#f8d050` | Same as above in gold. Use under birch, maple and autumn trees |

#### 3.4.2 Build rules for every plant

1. **Cards, not blocks.** Use cubes that are **0 units thick** on one axis (a flat plane) for every leaf, blade, petal, frond and twig. Only mushroom caps, thick stems and crystals use solid cubes.
2. **One card = one painted shape.** Each card shows one leaf (or blade, petal, twig) cut out with alpha. Never paint a whole bush on one card.
3. **Radiate from a base point.** All cards start at or near one point at the bottom centre (or 2 to 3 points for clumpy plants), then **fan up and out**. Rotate each card on **two axes**: tilt outward 10° to 80° from vertical and turn round the base in uneven steps (for example 0°, 37°, 71°, 118°, 160° ...), never in a perfect circle.
4. **Cross the cards.** At least half the cards should cross another card at 60° to 90°, so the plant looks full from every view. Cards may pass right through each other.
5. **Layers by height.** Low outer cards droop (tilted 60° to 85°, tips touching the ground). Middle cards stand at 30° to 60°. Top cards are almost upright (10° to 30°). This gives the rounded dome or fan shape in the references.
6. **Card count makes the quality.** Use the counts in 3.4.4. A bush with 8 cards looks cheap; the references use 30 to 80.
7. **Vary every card.** Change length by ±30%, width by ±20% and colour by one ramp step between cards. Use 3 to 6 different painted card variants per plant and reuse them.
8. **Sink the base.** Start cards 0.5 to 1 unit below y = 0 so no gap shows where the plant meets the terrain.
9. **Stems and branches** (shrubs, flame bush, autumn bush, dead bush) are thin cards or 0.5 to 1 unit cubes coming out of the base, and the leaf cards attach at their tips.
10. **Double sided, hard alpha.** Texture `render_sides` set to `double`. Alpha is fully on or off, no soft edges. In Godot: alpha scissor, back face culling off.
11. **No outlines, no black.** The references never outline leaves. Shape comes from the light edge on top and the shadow underneath.
12. **Footprint.** Most plants fit in **one block (16 × 16 units)**, like the references. Grass and flowers are smaller. Only big bushes and large leaf plants spill slightly past one block.

#### 3.4.3 How to paint plant cards

Plants use the same texel density as everything else, **2 px per unit**. Every card is a little painting:

- **Leaf shape first.** Draw the outline on a transparent background with **stepped pixel edges**: pointed lance (flame bush, big leaf plant), oval (shrub, autumn bush), rounded (pansy leaves, frost bush), serrated (fern leaflets, flame bush edges), blade (grass), twig (dead bush).
- **Gradient along the leaf:** darker at the base where it joins the stem, lighter towards the tip. 4 to 6 shades per leaf.
- **Midrib:** one darker (or for the big leaf plant, red brown) line down the middle of broad leaves, with the half facing up one shade lighter than the half facing down.
- **Light edge:** the top or outer edge of each leaf gets a 1 pixel highlight one shade lighter.
- **Shadow base:** the bottom 20 to 30% of each card is 1 to 2 shades darker, so the inside of the plant reads as shade.
- **Smooth, not noisy.** Use clean bands of colour like the references, with only a little pixel variation. No speckle, no neon pixels.
- **Accents:** flower eyes, berries, spots and thorns are 1 to 3 pixel details in a contrast colour.
- **Twigs:** 1 to 2 pixel wide lines in a dark ramp, lighter on one side, with forks and small knots.
- **Texture size:** 64 for grass, flowers, mushrooms and litter, 128 for bushes, ferns and big leaf plants.

#### 3.4.4 Plant types

| Type | Size (units) | Cards / cubes | Build | Texture | Wind |
| --- | --- | --- | --- | --- | --- |
| Grass tuft | 4 to 8 tall, 6 to 10 wide | 6 to 14 blade cards | Crossed blade cards in a fan, uses the ground colours | 64 | Strong |
| Tall or dry grass tuft | 8 to 14 tall, 14 to 22 wide | 14 to 30 cards, 4 to 8 of them long and thin | Dense fan plus long blades shooting out sideways and bending down | 64 | Strong |
| Flower | 6 to 12 tall | 3 to 6 stems, 2 to 4 petal cards per head, 4 to 8 leaf cards | 1 to 4 heads on curved stems, leaf rosette at the base | 64 | Medium |
| Bush (leafy) | 14 to 24 tall, 14 to 20 wide | 30 to 80 leaf cards, 3 to 8 stem cards | Dense dome or upright cone, no visible core, drooping lower leaves | 128 | Medium |
| Bush (twiggy shrub) | 14 to 18 tall | 8 to 16 stems, 30 to 60 small leaf cards in clusters | Stems visible, leaf clusters at the stem tips | 128 | Medium |
| Bush (spiky, flame) | 14 to 18 tall | 6 to 10 stems, 25 to 50 lance leaf cards | Leaves point up and out, serrated edges | 128 | Medium |
| Dead or thorn bush | 12 to 18 tall | 10 to 24 twig cards | Branches from one stump, forked or hooked tips, thorns | 64 or 128 | Light |
| Fern | 12 to 22 tall | 1 to 3 stems, 8 to 16 frond cards | Arching fronds from the top of short stems, lower fronds droop to the ground | 128 | Medium |
| Large leaf plant | 12 to 18 tall, 18 to 24 wide | 10 to 14 big leaf cards | Long pointed leaves arching out from the centre, midribs | 128 | Light |
| Mushroom group | 3 to 8 tall | 2 to 4 mushrooms, each 2 to 4 cubes + 1 to 2 ring cards | Flat slab caps with a darker rim and spots, pale stems, frilly ring at the base | 64 | None |
| Ground scatter (leaf litter, petals, twigs) | under 0.5 tall, cluster 16 to 32 wide | 8 to 20 flat cards | Cards lie almost flat (tilted 0° to 15°) in a loose cluster | 64 | Light |
| Reeds, cattails | 16 to 32 tall | 6 to 14 cards, 1 to 3 cattail heads (small cubes) | Tall upright blades, a few bent over | 64 | Strong |
| Vines, hanging moss | 8 to 40 long | 4 to 16 cards in a chain | Hanging strips with leaf shapes | 64 | Light |
| Crystal cluster (void, stellar) | 6 to 20 tall | 4 to 12 solid rotated cubes | Pointed crystal columns from one base, `_glow` cores | 64 | None |

- **Foraging plants** (from `resource_gathering.md` section 6, once J00BA adds the table) use these types, plus one clear **"pick me" accent**: bright flowers, berries or a soft glow, so players can spot them among normal foliage.
- **Make variants.** Every plant gets 2 to 4 variants (`_2`, `_3`) with a different card layout, so batched foliage doesn't look copied.
- **Recolour, don't rebuild.** One shape can serve several biomes by swapping the ramp (the dry grass and frost grass references are the same model). Name the recolours by biome: `dry_grass_tuft`, `frost_grass_tuft`.

#### 3.4.5 Wind

Foliage sways with the same Godot wind shader as trees and has **no Blockbench animations**. The "Wind" column in 3.4.4 says how strongly each type should move. Keep the base of every card still and let the tips move most: put card bases near y = 0 so the shader can scale sway by height.

#### 3.4.6 Prompt template

```
PLANT BUILD SPEC
name / id:        <plant>               (e.g. red_flame_bush, forest_fern, dry_grass_tuft)
type / biome:     <type from 3.4.4>, <biome>
closest reference: <reference from 3.4.1>
size:             <h> tall, <w> wide, footprint <one block or less>
silhouette:       <dome | upright cone | fan | rosette | clump | flat scatter>
build:            <n> alpha cards (+ <n> stems / solid cubes), radiating from <1 to 3> base points,
                  tilt layers: low droop 60 to 85°, middle 30 to 60°, top 10 to 30°, crossed pairs
card shapes:      <lance | oval | rounded | serrated | blade | twig | petal>, <3 to 6> variants
colours:          <leaf ramp, 5 to 6 shades>, <stem ramp>, <accent>
texture:          <64 | 128>, 2 px/unit, base to tip gradient, midrib, 1 px light edge, shadow base,
                  smooth bands, no outlines, hard alpha, double sided
wind:             <none | light | medium | strong>
variants:         <2 to 4>
groups:           <plant> > stems, leaves (or blades / petals / fronds / twigs), accents
```

#### 3.4.7 Examples

**"Make me a red bush."**

```
PLANT BUILD SPEC
name / id:        red_flame_bush
type / biome:     bush (spiky), mountain
closest reference: red flame bush
size:             16 tall, 18 wide, fits one block
silhouette:       rounded fan, leaves pointing up and out like flames
build:            8 thin dark grey stems branching from the base, 40 lance leaf cards on the stems,
                  lower leaves tilted 60 to 75°, middle 35 to 55°, top 10 to 25°, crossed pairs
card shapes:      lance with serrated pixel edges, 5 variants (long, short, wide, narrow, curved)
colours:          leaves #8a1e18 #b73620 #d4502a #e86a2c #f4b048, stems #2e2e2a #3a3a36 #4e4e48
texture:          128, 2 px/unit, dark red base to yellow tip, midrib, 1 px light edge
wind:             medium
variants:         3
groups:           red_flame_bush > stems, leaves
```

**"Make me some grass for the forest."**

```
PLANT BUILD SPEC
name / id:        forest_grass_tuft (+ _2, _3, _4)
type / biome:     grass tuft, forest
closest reference: grass tufts on the ground
size:             6 tall, 8 wide
silhouette:       low fan
build:            10 blade cards from one base point, 5 crossed pairs, tilted 10 to 50°, base sunk 0.5
card shapes:      blades 1 to 2 px wide at the tip, 3 to 4 px at the base, 4 variants
colours:          the forest_grass ground colours #4d6f0d #587e0e #608a10 #679411 #7aad1d
texture:          64, 2 px/unit, darker base, lighter tips, stepped tip edges
wind:             strong
variants:         4
groups:           forest_grass_tuft > blades
```

**"Make me red mushrooms."**

```
PLANT BUILD SPEC
name / id:        red_mushroom_group
type / biome:     mushroom group, forest
closest reference: red mushrooms
size:             6 tall, 14 wide
silhouette:       clump of 3 at different heights
build:            3 mushrooms: caps are flat slab cubes 8 × 1.5 × 8, 6 × 1.5 × 6 and 5 × 1.5 × 5 with a
                  thinner rim slab underneath, pale stems 1.5 to 2 wide, 2 frilly ring cards at each base
card shapes:      ring frill (white, ragged alpha edge)
colours:          cap #7a1c24 #9c2830 #c03a40, spots #f0c8c8 #f8e0e0, stem #c8c0b0 #d8d0c0, ring #c8c8b8
texture:          64, 2 px/unit, light cap top with 4 to 8 spots, dark red rim and underside with gill lines
wind:             none
variants:         2
groups:           red_mushroom_group > mushroom_1, mushroom_2, mushroom_3
```

### 3.5 Tools

**Analysis.** Tools are the gathering progression (`resource_gathering.md` section 2.1): stone → bronze → iron → gold → obsidian → titanite → dreadstone → voidstone → stellarite. Every tier must look **clearly better** than the last. The pickaxe reference shows the level of detail: a stepped curved head, a socket with an emblem, a cap pin, a carved handle, an end cap.

**Anatomy.**

| Tool | Parts |
| --- | --- |
| Pickaxe | `handle` (long, 1.5 × 1.5 thick, carved), `end_cap`, `socket` (square collar where head meets handle), `head` (2 arms built from 3 to 5 stepped, rotated cubes each, tapering to points), `cap_pin`, `emblem` |
| Axe | `handle` (slight curve with 2 to 3 offset cubes), `end_cap`, `socket`, `blade` (wide head with a stepped curved edge, 4 to 8 cubes), `back_spike` (higher tiers), `binding` (wrap or rivets) |
| Rod, foraging tool, bow | Same tier rules once their tables are in `resource_gathering.md` |

- **Size:** a pickaxe is about 16 to 20 units long, an axe 14 to 18. Held in the right hand, the grip is centred on the pivot.
- **Texel density 4 px/unit** (section 1.4).
- **Pivot:** at the grip point (where the hand holds it), so Godot can attach it to the hand bone.

**Tier look.**

| Tier | Head material | Handle | Extras |
| --- | --- | --- | --- |
| Stone | Chipped grey flint, chunky, rough edges, lashed with rope | Plain branch with bark | Rope binding |
| Bronze | Warm bronze with darker patina | Light wood, leather wrap | Rivets |
| Iron | Dark grey steel with scratches | Mid wood, leather wrap | Metal socket and end cap |
| Gold | Shiny gold with bright highlights | Dark wood, red wrap | Engraved lines |
| Obsidian | Glassy black purple with sharp shine | Black wood, silver bands | Faceted edge highlights |
| Titanite | Steel blue crystal metal | Pale metal handle | Crystal inlays |
| Dreadstone | Dark red black, jagged | Bone or dark iron | Red glowing cracks (`_glow`) |
| Voidstone | Purple crystal, glowing edges | Dark metal with violet wrap | Glow core, small floating shard |
| Stellarite | White gold with star flecks | Gold and white handle | Glow edges, star gem emblem |

```
TOOL BUILD SPEC
name / id:        <tier>_<tool>          (e.g. iron_pickaxe)
tier:             <stone..stellarite>
size:             <length> long, head <width> wide
head:             <n> cubes, stepped and rotated, tapering points / curved edge, <material ramp>
socket + emblem:  <socket look>, emblem <symbol>
handle:           <material>, carved pattern / wrap, end cap <material>
extras:           <rivets, bindings, inlays, glow parts>
texture:          64 or 128, 4 px/unit, metal scratches, edge highlights, grain on wood
pivot:            at the grip point
groups:           <id> > handle, head, details
```

**Example.** "Make me an iron pickaxe."

```
TOOL BUILD SPEC
name / id:        iron_pickaxe
tier:             iron (T5 gather tier)
size:             18 long, head 16 wide
head:             2 arms × 4 stepped cubes rotated 10° per step, sharp points, dark steel ramp (7 shades)
socket + emblem:  square iron collar, small embossed anvil emblem
handle:           mid brown wood, diagonal leather wrap on the lower third, iron end cap
extras:           4 rivets on the socket, cap pin on top
texture:          128, 4 px/unit, scratches and dents on steel, bright edge line on top of each arm
pivot:            [0, 3, 0] grip point
groups:           iron_pickaxe > handle, head, details
```

### 3.6 Weapons

**Analysis.** Weapons are crafted (`game_worlds.md` section 3.2, `crafting.md`) and follow the same tier ladder as tools. The two sword references show the range: the basic sword is clean and simple, the void sword is glowing and ornate. Detail grows with tier.

**Anatomy.**

| Weapon | Parts |
| --- | --- |
| Sword | `blade` (3 to 6 tapering cubes, fuller line, tip), `guard` (cross piece, curled ends at higher tiers), `gem` (higher tiers), `grip` (wrapped), `pommel` |
| Dagger | Short sword layout, curved or straight |
| Axe (battle) | Bigger, double headed axe layout |
| Mace, hammer | Head with flanges or studs, long handle |
| Spear | Long shaft, leaf blade, binding |
| Bow | Curved limbs from 6 to 10 rotated cubes, grip, string (thin cube) |
| Staff | Shaft, carved top holding a gem or orb (`_glow`) |
| Shield | Front plate built from layered cubes, rim, boss, emblem |

- **Size:** sword 20 to 28 long, dagger 10 to 14, spear 36 to 44, bow 24 to 30 tall, shield 14 to 18 wide.
- **Texel density 4 px/unit.** Pivot at the grip.

**Texture recipe.** Blades get a vertical gradient (darker at the guard, lighter at the tip), a 1 to 2 pixel light fuller line, a bright edge highlight and a darker spine. Grips get a diagonal wrap pattern. Gems get facets and a highlight pixel. Glowing blades (voidstone, stellarite) get a bright edge, a darker core with rune shapes, and colour bleeding onto the guard.

```
WEAPON BUILD SPEC
name / id:        <tier>_<weapon>        (e.g. voidstone_sword)
tier:             <stone..stellarite>
size:             <length>
silhouette:       <straight | curved | broad | spiked>, ornate level <1..5 by tier>
blade / head:     <n> cubes, tapering, fuller, <material ramp>
guard:            <shape>, gem <gem or none>
grip + pommel:    <wrap colour>, <pommel shape>
glow:             <none | _glow parts>
texture:          64 or 128, 4 px/unit, gradient blade, edge highlights, wrap pattern
pivot:            at the grip
groups:           <id> > blade, guard, grip, pommel, details
```

**Example.** "Make me a voidstone sword."

```
WEAPON BUILD SPEC
name / id:        voidstone_sword
tier:             voidstone (T9)
size:             26 long
silhouette:       broad straight blade, slight flare near the tip, ornate level 4
blade:            5 tapering cubes, violet ramp with a near black core and white violet edge,
                  rune shapes in the core (_glow)
guard:            dark metal, 2 curled spikes each side, arcanium gem in the centre (_glow)
grip + pommel:    pale lilac cloth wrap, dark metal pommel with a small glowing gem
glow:             blade_edge_glow, gem_glow, pommel_glow
texture:          128, 4 px/unit
pivot:            at the centre of the grip
groups:           voidstone_sword > blade, guard, grip, pommel
```

### 3.7 Armour

**Analysis.** Armour is worn by the imp, so it must **fit the imp's body** and use the **same texel density (2 px/unit)**. It is built as separate pieces that sit 0.25 to 0.5 units outside the body cubes and follow the imp's bones. Tiers follow the tool ladder materials.

- **Pieces:** `helmet`, `chestplate`, `shoulders` (left and right), `gauntlets`, `belt`, `leggings`, `boots`.
- **One file per piece**, named `<tier>_<piece>.bbmodel` (for example `gold_helmet.bbmodel`, `iron_boots.bbmodel`), with its own texture. Inside the file, groups are named after the imp bone the piece follows (`head`, `body`, `arm_right`, ...), so Godot can attach each group to that bone.
- Every armour file includes the hidden `scale_dummy` so the fit can be checked.
- **Build:** plates are layered cubes that overlap like real armour (shoulder pads stacked 2 to 3 high, chest plate with a raised centre ridge, helmet with a visor and crest). Low tiers are leather and simple; high tiers have trims, gems, horns, crests and glow.
- **Texture:** metal plates with rivets, scratches and bright top edges; leather with stitching and buckles; cloth with folds and patterns. Trims in a contrast colour.
- **Fit rule:** leave the imp's big eyes and ears free. Helmets must have ear holes or ear guards, because the imp's ears stick out sideways.

```
ARMOUR BUILD SPEC
name / id:        <tier>_<piece>        (e.g. gold_helmet), one file per piece
tier:             <stone..stellarite>
fits:             base imp, 0.25 to 0.5 units outside the body cubes, follows bone <bone>
pieces:           <list>, each layered from <n> cubes
style:            <leather | plate | scale | crystal | bone>, trims <colour>, ornaments <list>
glow:             <none | _glow parts>
texture:          2 px/unit, rivets, scratches, stitching, edge highlights
groups:           match imp bone names
```

### 3.8 NPC characters

**Analysis.** NPCs live in the hub world: shop keepers, challenge givers, crafting station keepers (`game_worlds.md` section 3.2). The fennec NPC and the green imp show the look: **big head, big shiny eyes, small body, expressive face, clothes that say their job**. NPCs should look friendly and readable from across the village square, with a clear job prop (apron and hammer, satchel and scroll, fishing hat and rod).

**Anatomy.**

1. `body` (pivot at the hips): torso, belly, clothing layers, belt, satchel or apron.
2. `head` (pivot at the neck): head is **as big or bigger than the torso**. Eyes 3 to 4 units wide with highlights. Ears, hair, hat, beard as separate cubes.
3. `arm_right`, `arm_left` (pivot at the shoulder), with `hand_right` holding the job prop if they carry one.
4. `leg_right`, `leg_left` (pivot at the hip).
5. `prop`: the job item, its own group under the hand or body.

- **Height:** 18 to 26 units (about the imp's size, taller for adults like a blacksmith).
- **Animations:** `idle` (breathing, blink by moving eyelid cubes), `talk` (head bob and hand gesture), `wave`, `work` (job action, for example hammering), `walk`.

**Texture recipe.** Skin or fur ramp with soft shading; eyes with a dark pupil, a coloured iris, **one or two white-ish highlight pixels** and a darker top lid line; clothes with folds (darker vertical lines), stitching, buttons, buckles, straps, patterns; a job colour that's easy to spot (blacksmith dark orange, merchant purple, guard blue).

```
NPC BUILD SPEC
name / id:        <role>_npc            (e.g. blacksmith_npc)
role / location:  <shop | challenge giver | crafter | quest giver>, <hub landmark>
species / look:   <imp | fox | other>, <build>, <height>
head:             big head, eyes <colour> with highlights, ears <shape>, hair/hat <...>, expression <...>
outfit:           <layers>, job colour <...>, straps/buckles/stitching
prop:             <job item>, held in <hand>
animations:       idle, talk, wave, work, walk
texture:          128 or 256, 2 px/unit
groups:           <id> > body > head, arm_right, arm_left, ... ; leg_right, leg_left ; scale_dummy
```

**Example.** "Make me a blacksmith NPC, burly, leather apron."

```
NPC BUILD SPEC
name / id:        blacksmith_npc
role / location:  crafter (smelter and anvil keeper), hub crafting area
species / look:   imp, burly with broad shoulders and thick forearms, 24 tall
head:             big imp head, amber eyes with 2 highlight pixels, soot smudges on cheeks,
                  thick bushy brows, short beard, ears sticking out sideways, bandana
outfit:           rolled sleeves, thick brown leather apron with stitched edges, pocket with tongs,
                  belt with iron buckle, heavy boots, burn marks on the apron
prop:             iron hammer in the right hand
animations:       idle (breathe, blink), talk, wave, work (hammer swing), walk
texture:          256, 2 px/unit, orange forge glow tint on the front faces
groups:           blacksmith_npc > body > head (jaw, ear_right, ear_left), arm_right (hammer),
                  arm_left ; leg_right, leg_left ; scale_dummy
```

### 3.9 Mobs and creatures

**Analysis.** Mobs are hunted in the resource world. The existing files (`cow`, `pig`, `highland_cow`, `wolf`, `ogre`) set the structure, and the eagle and pigeon references set the texture bar. Keep the existing rig layout and make textures **richer** than the existing ones.

**Rig layout (copy from the existing mobs).**

| Mob type | Groups |
| --- | --- |
| Four legged | `<mob>` > `body` > `head` (`jaw`, `ear_right`, `ear_left`), `tail` (`tail_mid`, `tail_tip`) ; `leg_front_right`, `leg_front_left`, `leg_back_right`, `leg_back_left` ; `scale_dummy` |
| Two legged | `<mob>` > `body` > `head` (`jaw`, `ear_right`, `ear_left`), `arm_right` > `forearm_right`, `arm_left` > `forearm_left` ; `leg_right`, `leg_left` ; `scale_dummy` |
| Bird | `<mob>` > `body` > `head` (`beak`), `wing_right` > `wing_tip_right`, `wing_left` > `wing_tip_left`, `tail` ; `leg_right`, `leg_left` ; `scale_dummy` |

- **Animations:** every mob has `idle`, `walk`, `run`, `attack`, `hit`. Add `roar`, `fly`, `glide`, `swim` or others when the mob needs them. Use the timings of the existing files as a guide (wolf walk 0.9s, run 0.5s; cow walk 1.4s).
- **Anatomy detail:** add fur tufts, manes, horns in segments, hooves, claws, teeth, belly and back plates as separate small cubes (the highland cow uses 60+ fringe cubes for its shaggy coat).

**Texture recipe.** Fur: strands drawn as short 1 pixel lines in 3 shades, flowing in one direction, lighter on the back and darker on the belly. Feathers: rows of feather shapes with a light edge and a dark base, overlapping like the eagle. Skin: soft gradient with spots, scars or wrinkles. Eyes: always a highlight pixel. Hooves, claws and horns: their own ramp with growth rings.

```
MOB BUILD SPEC
name / id:        <mob>
biome / tier:     <biome> / <T1..T10 or to be decided>
type:             <four legged | two legged | bird | other>
size:             <h> tall, <l> long (compared with the 18 unit imp)
silhouette:       <key shape notes>
anatomy:          <head, horns, mane, tail, fur tufts, spikes ...>, <n> cubes
coat / skin:      <ramp>, <pattern: fur strands | feathers | scales | skin spots>
eyes:             <colour>, highlight pixel
animations:       idle, walk, run, attack, hit (+ <extras>)
texture:          <size>, 2 px/unit
groups:           <rig from the table above> + scale_dummy
```

### 3.10 Dragons

**Analysis.** Dragons are the showpiece mobs. The existing `dragon.bbmodel` and `pale_dragon.bbmodel` set the rig (neck in 3 segments, head with upper and lower jaw, 3 part wings, 3 part tail, arms and legs with hands and feet) and a large animation set. The frost dragon and void dragon references show where to push further: **armour of crystal shards, wing membranes with holes, huge curved horns made of chained rotated segments, glowing eyes and mouths, spikes along the spine and wings**.

**Rig (copy from `dragon.bbmodel`).** `<dragon>` > `body` > `neck_base` > `neck_mid` > `neck_upper` > `head` (`jaw_upper`, `jaw`, `horn_right`, `horn_left`) ; `wing_right` > `wing_mid_right` > `wing_tip_right` ; same for left ; `tail` > `tail_mid` > `tail_end` ; `arm_right` > `forearm_right` > `hand_right` ; same for left ; `thigh_right` > `leg_right` > `foot_right` ; same for left ; `scale_dummy`.

**Animations.** `idle`, `look`, `walk`, `run`, `turn_left`, `turn_right`, `roar`, `attack`, `claw`, `hit`, `takeoff`, `fly`, `glide`, `hover`, `land`.

**Build notes.**

- **Size:** 2 to 4 times longer than the existing dragon for big world bosses (the void dragon reference is big enough to ride).
- **Horns:** 3 to 6 rotated segments per horn, each smaller and turned a bit more, to make a smooth curve.
- **Wings:** arm bones as thin cubes, membranes as thin (0.5) panels between them, with alpha holes and tears on older or evil dragons. Bone spikes at the wing joints.
- **Spine:** a row of spikes or plates from head to tail tip, getting smaller towards the tail.
- **Element armour:** crystals, scales, plates or flames that stick out at angles across the back, shoulders and tail.

**Element themes.**

| Element | Body | Wings | Armour | Glow |
| --- | --- | --- | --- | --- |
| Frost | Dark slate blue | Pale teal green membranes | Ice blue crystal shards, frost on scales | Pale blue eyes, icy breath mouth |
| Fire | Deep red to black | Orange membranes with darker veins | Black horn plates, ember cracks | Orange eyes and cracks (`_glow`) |
| Void | Near black purple | Crimson membranes with holes | Purple crystal spines | Purple eyes and mouth (`_glow`) |
| Swamp | Murky green brown | Torn olive membranes | Moss, hanging vines, mud | Toxic green eyes |
| Stellar | Deep navy with star flecks | Starry translucent-look membranes | White gold plates | Gold star glow |
| Pale | Bone white, grey shadows | Pale grey membranes | Bone ridges | Pale blue eyes (like `pale_dragon`) |

```
DRAGON BUILD SPEC
name / id:        <element>_dragon
biome / role:     <biome>, <mob | boss | rideable later>
size:             <h> tall standing, <l> long, <wingspan> wingspan
silhouette:       <lean | bulky | serpentine>, horn shape <...>
head:             skull + snout + brow, jaw open/closed, teeth, <n> horn segments each side
wings:            3 part, membranes <colour>, holes <yes/no>, joint spikes
body + tail:      spine spikes, belly plates, element armour <...>
texture:          256, 2 px/unit, scales pattern, element ramp, glow parts
animations:       full dragon set (see above)
groups:           dragon rig from dragon.bbmodel + scale_dummy
```

**Example.** "Make me a frost dragon, ice blue, cracked crystal armour."

```
DRAGON BUILD SPEC
name / id:        frost_dragon
biome / role:     frost, boss mob
size:             40 tall standing, 90 long, 110 wingspan
silhouette:       bulky shoulders, lean tail, swept back horns
head:             wide skull, open jaw with red inner mouth, 2 rows of pale teeth,
                  5 horn segments each side curving back, ice crystal spikes on the brow
wings:            3 part, pale teal membranes with frost veins, no holes, ice spikes at joints
body + tail:      dark slate scales, ice blue crystal shards (rotated 15 to 45°) bursting from
                  shoulders, spine and tail, cracks of light blue in the crystals
texture:          256, 2 px/unit, scale rows on body, frosted edges, white highlight pixels on ice
animations:       full dragon set
groups:           dragon rig + scale_dummy
```

### 3.11 Props and buildings

**Analysis.** The hub world is a village around a castle with market stalls, crafting stations, benches, doors and notice boards (`game_worlds.md` section 3.3). Props use the same rules as everything else: layered cubes, no flat faces, rich texture.

- **Wood:** planks as separate cubes with gaps, grain, nail pixels, worn lighter edges.
- **Stone:** blocks as separate cubes with mortar lines, chipped corners, moss in the cracks.
- **Metal:** bands, rivets, rust in the corners.
- **Cloth:** awnings and banners with folds and patterns, hard alpha tattered edges.
- **Interactable props** (benches, doors, notice boards, stations) get a group for the moving part (`door`, `lid`) with a pivot at the hinge.

```
PROP BUILD SPEC
name / id:        <prop>                (e.g. market_stall, smelter, notice_board)
location:         <hub landmark | resource world biome>
size:             <w> × <d> × <h>
materials:        <wood | stone | metal | cloth>, ramps
build:            <n> cubes, separate planks/blocks, wear and damage
interaction:      <none | door / lid / sit point>, pivot at <...>
texture:          <size>, 2 px/unit
```

### 3.12 Textures (standalone)

**Analysis.** Terrain is smooth heightmap ground painted with **stylized voxel / pixel textures** (`game_worlds.md` section 2). These textures are not on a `.bbmodel`; they are tiling PNGs in `godot-game/assets/textures/`.

- **Tiling:** must tile seamlessly in both directions. Check by placing 3 × 3 copies.
- **Size:** 64 or 128 pixels per tile, matching **32 px per metre** (same texel density as the models).
- **Detail:** 3 layers: base ramp noise, mid size shapes (stones, grass clumps, cracks, snow drifts), and small accents (pebbles, flowers, sparkles). Avoid obvious repeating marks.
- **Set per biome:** grass, dirt, path, rock, plus biome specials (snow and ice for frost, mud and slime for swamp, void rock for void, star dust for stellar).

```
TEXTURE BUILD SPEC
name / id:        <biome>_<surface>      (e.g. frost_snow, forest_grass)
size:             <64 | 128>, tiling both ways
base ramp:        <colours>
mid layer:        <shapes>
accents:          <small details>
check:            3 × 3 tile preview, no visible seams or repeats
```

### 3.13 Effects

**Analysis.** Effects are small cube models used for particles and feedback: ore chips flying when mining, wood chips when chopping, leaves falling, magic sparkles, level up bursts, portal swirl, mint token sparkle. They must be **tiny, bright and readable**.

- **Build:** 1 to 12 small cubes per effect piece (0.5 to 3 units). Godot will spawn many copies, so keep each one simple.
- **Texture:** strong colour, bright centre, darker edges, hard alpha. Glow pieces use `_glow`.
- **Animation:** an optional `play` animation (scale up, spin, fade by scaling to 0) if the effect is a model, not a Godot particle.
- **Match the source:** mining chips use the ore ramp, chopping chips use the bark ramp, so the effect matches what's being gathered.

```
EFFECT BUILD SPEC
name / id:        <effect>              (e.g. copper_chip, leaf_fall, level_up_burst, portal_swirl)
used for:         <action>
pieces:           <n> cubes, <size>, <shapes>
colours:          <ramp>, glow <yes/no>
animation:        <play: scale / spin / rise / fade>, <length>
texture:          32 or 64, 2 px/unit
```

---

## 4. Quality checklist

Check every item before handing a model over. If one fails, fix it.

**Shape**

- [ ] The silhouette reads as the right thing from far away.
- [ ] No large flat faces without detail cubes or texture detail.
- [ ] Stepped, ragged edges on natural things (trees, rocks, foliage). Never a perfect sphere, cone or box.
- [ ] Correct size compared with the 18 unit imp (section 1.3).
- [ ] Stands on y = 0, centred on x = 0, z = 0. Characters face north (−z).
- [ ] Within the cube budget (section 1.7).
- [ ] Trees: `python3 tools/clean_tree_trunks.py` reports 0 for `core`, `wraps`, `floating` and `step`. With the cards hidden, the trunk is one clean tapering column with only bark strips, stubs and small details on it (section 3.1, **Clean trunks and branches**).
- [ ] Plants: built from alpha cards fanning from a base point (section 3.4.2), with the card count from section 3.4.4, and compared side by side with the closest reference in section 3.4.1.

**Texture**

- [ ] Every visible face is painted. No flat fills.
- [ ] Correct texel density (2 px/unit, or 4 for tools and weapons). No stretched pixels.
- [ ] Each material uses a 5 to 8 shade, hue shifted ramp. No pure black or white.
- [ ] Top faces light, sides mid, bottoms dark. Contact shadows where parts meet.
- [ ] Material detail added (grain, cracks, veins, leaves, fur, feathers, stitching).
- [ ] Eyes have highlight pixels.
- [ ] Tier and biome are recognisable from the colours alone.
- [ ] Hidden faces have no UV and no texture. Repeated parts share UV space.

**File**

- [ ] Format 5.0, free model, per-face UV.
- [ ] All groups and cubes named in lowercase with underscores; pivots at the joints.
- [ ] `scale_dummy` included (characters and mobs), with export and visibility off.
- [ ] Texture embedded and saved as a matching `.png`.
- [ ] Animations present and named as in section 3 (mobs, NPCs, dragons, and `hit` on trees). No animations on ore veins.
- [ ] File saved in the right folder with a lowercase underscore name (section 1.8).

---

## 5. Colour ramps

Starting ramps for common materials, dark → light. Hue shift them further if the asset needs it.

| Material | Ramp |
| --- | --- |
| Pine leaves | #0f2a24 #173d2c #1f5233 #2a6b3a #3d8544 #5ea04e #8cbf5e |
| Broadleaf leaves | #1a2e14 #24461a #31611f #437d26 #5c9a30 #7fb840 #a8d45a |
| Birch leaves | #2c4a14 #3f6a1a #568c22 #73ab2c #93c63c #b9dd58 |
| Autumn leaves (maple) | #4a1410 #78201a #a8361e #d2582a #ec8436 #f8b450 |
| Warm brown bark | #24140e #3a2216 #52321e #6c4428 #885834 #a67244 |
| Dark bark | #120c0e #1e1416 #2c1e1e #3c2a26 #503830 |
| Grey stone | #1c1e26 #2c2f38 #3e424c #545862 #6c707a #8a8e96 #aeb2b8 |
| Warm stone | #2a2220 #3e332e #554740 #6e5e54 #8a786a #a89484 |
| Moss | #1e3014 #2e481a #42621f #5c7e28 #7a9a34 |
| Steel | #1a1e24 #2c323a #444c56 #606a76 #848e9a #b0b8c2 #dfe4ea |
| Bronze | #3a1e0c #5c3414 #82501e #a86e2c #c88e40 #e2b060 |
| Gold | #4a2c00 #7a4c00 #a87400 #d29e10 #f2c636 #ffe27a #fff4c0 |
| Leather | #2a160e #422416 #5c3420 #78462a #965c36 |
| Imp green skin | #1e3a2a #2c523a #3e6c4a #548a5c #6ea672 #90c08c |
| Fur (fox / tan) | #4a2a10 #6e401a #965a24 #ba7a34 #d89c4c #f0c070 |
| Ice | #1e3448 #2e5070 #4874a0 #6c9cc8 #9cc8e8 #d0ecf8 |
| Void glow | #120424 #2a0c4a #4a1878 #7428b0 #a448e0 #d06cff #f0c8ff |
| Stellar glow | #2a2050 #4a3c80 #8070b0 #c8b080 #f0d890 #fff6c8 |

---

## 6. Turning a short request into a spec

When the request is short, fill the gaps in this order:

1. **User's words** win (colours, size, mood, extra parts).
2. **Tier table** for the asset (sections 3.1, 3.2, 3.5) for the look of that tier.
3. **Biome** from `game_worlds.md` sections 4.4 to 4.6 for extras like snow, slime or glow.
4. **Category defaults** (anatomy, budget, texture recipe).
5. **Reference analysis** (section 1.2) for the feel.

Word hints:

| User says | Means |
| --- | --- |
| tall, towering | Top of the size range or above, narrower |
| huge, giant, ancient | 1.5 to 2 times the range, thicker, more roots, more detail |
| small, young | Bottom of the range, fewer cubes, brighter colours |
| dark, dead, evil | Lower saturation, cooler, holes and tatters, maybe glow |
| magic, rare, legendary | Glow parts, gems, ornate extras |
| snowy, frozen | Snow caps on top faces, icicles, pale blue tint |
| mossy, old | Moss on top faces, cracks, worn edges |
| variant, another | Same spec, change the cube layout and seed so it's not a copy |

If something truly can't be guessed (for example a new mob with no description), make a sensible choice, say what you chose, and list it as a question after the build.

---

## 7. Decisions

J00BA's answers to the first draft's open questions.

| Question | Decision |
| --- | --- |
| Held item detail | Tools and weapons use 4 px/unit (section 1.4) |
| Glow parts | Cubes named with a `_glow` suffix, made emissive in Godot (section 1.5) |
| Tree and foliage wind | Godot wind shader, no Blockbench sway animation (section 3.1) |
| Gathering feedback | Trees shake with a `hit` animation. Ore veins don't animate (sections 3.1 and 3.2) |
| Armour files | One file per piece (section 3.7) |
| Leaf cores on trees | None. Trees use inner cards, not solid core cubes, and nothing but bark strips, stubs and small details touches the trunk. `frostbark_tree` is the reference (section 3.1) |
