# IMPLINGZ: Blockbench models (voxel style)

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User addition, 2026-10-22 | ART-DIRECTION, GODOT, 02 |

> Claude: read `docs/CLAUDE.md` before working from this file. Read this whole file before making, editing, exporting or reviewing any Blockbench model.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** how we make Blockbench models that look as good as the best Hypixel and Minecraft work, and how they get into Godot.

**Research behind it:** [BLOCKBENCH-STUDY.md](BLOCKBENCH-STUDY.md) studies the 26 reference listings the user chose (D-052): how they look, how they are built, and how to optimise models like them for Godot.

**Words used here.**
- **Blockbench:** a free 3D editor built for blocky, cube-based models with pixel-art textures.
- **Voxel style:** models built from boxes, painted with small pixel textures, as in Minecraft.
- **Texel density:** how many texture pixels cover one unit of model. If it's the same everywhere, every pixel in the game is the same size.
- **UV:** the map that says which part of the texture goes on which face of a box.
- **Bone / group:** a named part that moves (a head, a leg, a pickaxe head).

---

## 1. What is decided (D-044)

- **Tools, weapons, creatures and items** are made in **Blockbench**: pickaxes, swords, axes, the creatures, and other items.
- The style is **voxel, inspired by Hypixel and Minecraft** (D-044), with a **slight voxel feel**, chosen because it is easier to model (D-047).
- **The world stays stylised cartoon**, like the test project's assets (D-047). Items and enemies are made to sit in that world.
- Models go into **Godot** (D-037) as **glTF binary (`.glb`)**, exported by Blockbench itself (**D-116**, which replaces the FBX format in D-044). Blockbench stays the modelling tool.
- **Every tier of a tool has its own shape and detail**, not only its own colours, themed on its metal and gem, its animal or its wood (**D-114** for pickaxes, **D-115** for every tool). Example: the Dreadstone pickaxe has a small demon engraved at the top centre of its head.
- The aim is the **highest quality** Blockbench work we can do.
- **Implings are left out** (D-016). They are already made.
- We make our own models (D-018).

**Decided (D-047):** the **world** (ground, rocks, ore veins, trees, buildings) does **not** go voxel. It keeps the ART-DIRECTION rules, and ore veins keep the Stylized Ore look (D-019). See section 10 for how the two fit together.

## 2. What gets a Blockbench model (Proposed list)

Taken from the decided systems. **Decided (D-114, D-115): every tier of a tool is its own model with its own texture** (section 6).

| Group | Models | From | State |
|---|---|---|---|
| Pickaxes | 10 models, Stone to Stellarite | D-006, D-020, D-114 | Made and in the game (2026-10-22) |
| Axes | 10 models, Stone to Stellarite | D-106, D-115 | Made and in the game |
| Sickles | 10 models, Stone to Stellarite | D-024, D-063, D-115 | Made and in the game |
| Bows | 16 models, one per animal, Hare to Eclipse Dragon | D-030, D-032, D-115 | Made and in the game |
| Fishing rods | 10 models, one per wood | D-110, D-115 | Made and in the game |
| Swords | Tiers not decided | D-044 | Not made |
| Hunting animals | 16 creatures, Hare to Eclipse Dragon | D-032 | Not made |
| Items in the world | Dropped ore, ingots on the anvil, hides on the tanning rack, bundles on the drying rack | D-005, D-022, D-029 | Not made |
| Stations | Furnace, anvil, drying rack, tanning rack | **Open question**: world or item? (section 10) | Not made |

The inventory icons stay **2D pixel art at 48×48** (D-015). A Blockbench model does not replace its icon.

## 3. Project setup in Blockbench (Proposed)

- **Format: Generic Model.** It allows any rotation and exports glTF (and FBX). Don't use the Java Block/Item format: it limits rotations to 22.5° steps and is made for Minecraft resource packs, not for Godot.
- **Scale: 16 Blockbench units = 1 metre in Godot** (one Minecraft block). Every model is built against the same reference:
  - Keep a **scale dummy** in each project: a box the height of the player's Imp, hidden before export. **Open question:** the Imp's height in metres in Godot.
- **Pivot points first.** Before animating, put each group's pivot where it really bends: a shoulder, a knee, the base of a tail, the grip of a pickaxe.
- **Names.** Lower case with underscores: `body`, `head`, `leg_front_left`, `tail`, `handle`, `head_metal`. The same name for the same part across all creatures, so animations and code can be reused.
- **Keep the source.** Every model's `.bbmodel` file is committed. The `.glb` is a build output. The `.bbmodel`, or the script that writes it (section 6), is what gets edited.

## 4. What makes a pro Blockbench model (Proposed: the quality rules)

These are the habits that separate top Hypixel-style models from beginner ones.

### 4.1 One pixel size everywhere
- **Pick one texel density and never break it.** **Decided (D-053): 2 texture pixels per Blockbench unit** (32 pixels per metre, "resolution 32"). Every model in the game uses it.
- **Never stretch a box after texturing it.** A stretched box has stretched, rectangular pixels. It's the most obvious sign of amateur work.
- **Half-unit sizes.** Box sizes are in steps of 0.5 units (one texture pixel at D-053), so pixels land exactly on edges. The one exception is a small **Inflate** for an outer layer (fur, a hat, a glow shell), which may stretch pixels slightly on purpose.
- **No "mixels"** (mixed pixel sizes): a 4× detailed sword next to a 2× creature looks wrong. If something needs more detail, make it physically bigger, not denser.

### 4.2 Shape
- **Silhouette first.** Block out the big shapes with plain grey boxes. Fill the shape with black: can you still tell what it is? Only then add detail.
- **Chunky and exaggerated.** Heads big, tools fat, important parts oversized. This still matches the ART-DIRECTION "chunky shapes" pillar.
- **Odd widths for centred things.** A 3- or 5-pixel-wide handle has a centre pixel, so it looks symmetrical.
- **Few boxes, well placed.** A good creature is often 20 to 60 boxes. Every box should change the silhouette or carry a colour. Remove boxes nobody will see.
- **Rotated boxes sparingly.** A slight angle on an ear or a horn adds life. Too many angled boxes makes the pixel grid break up and look messy.

### 4.3 Texture painting
- **Small palette per material.** 3 to 5 shades of each colour: dark, mid, light, highlight. Hypixel-quality textures look clean because they use few colours.
- **Hue shifting.** Shadows move toward blue or purple, highlights move toward yellow or warm. Don't just add black or white. (This matches ART-DIRECTION's "warm light, coloured shadows".)
- **One light direction.** Light from the top, slightly front-left, on every model. Top faces are lightest, bottom faces darkest.
- **Edge highlights.** A one-pixel lighter line along top edges and corners makes a box read as solid.
- **Painted shadow (ambient occlusion).** Darken pixels where parts meet: under a head, where a blade meets a handle.
- **Clusters, not noise.** Group pixels into clear shapes (a patch of fur, a crack, a stripe). Random speckle looks dirty from the camera.
- **No pillow shading** (dark all round the edge, light in the middle). It makes things look flat and puffy.
- **The accent is brightest.** The pickaxe head, a creature's eyes, a glowing crystal carry the most saturated colour (ART-DIRECTION pillar 5).
- **Colours from the icon.** If the item has a 48×48 icon, its main colours come from that icon (ART-DIRECTION, section 2). Open the PNG and pick them up.
- **Aseprite is fine.** The repo already draws icons in Aseprite. Textures can be painted there with the same palettes, then reloaded in Blockbench.

### 4.4 UV layout
- **Box UV** for simple box creatures and parts: Blockbench lays out each box automatically, Minecraft-mob style.
- **Per-face UV** for detailed tools and items, where each face needs its own painting.
- **One texture per model**, power-of-two size (32×32, 64×64, 128×128). No unused space wasted on hidden faces.

### 4.5 Animation (creatures)
- **Animate in Blockbench's Animate tab.** Each creature needs at least: `idle`, `walk`, `attack`, `hit`. A run is needed if creatures flee.
- **Exaggerate.** Squash and stretch on landings, anticipation before an attack, overshoot and settle. Snappy timing reads better than smooth realism.
- **Loops loop.** The first and last keyframes of `idle` and `walk` match exactly.
- **The "poof" on defeat (D-028)** is a particle effect in Godot, not a Blockbench animation.
- **Same bone names on every creature**, so Godot code can say "play `hit`" on any of them.

## 5. Export to glTF and import into Godot (Decided format, D-116; steps tested on the tools)

**Why GLB, not FBX (D-116):** both were tested on the pickaxes on 2026-10-22. Blockbench's GLB carries its **Nearest** pixel filter into Godot and imports crisp. Its FBX imports blurry.

1. Blockbench: **File → Export → Export glTF Model**, binary (`.glb`), with the texture embedded. Hide the scale dummy first. Animations off for tools, on for creatures.
2. Copy the `.glb` into the game, in `godot-game/models/blockbench/<kind>s/` (section 8). Godot only loads files inside `godot-game/`.
3. In the `.glb`'s import settings, set **Embedded Image Handling: Embed as Uncompressed** (`gltf/embedded_image_handling=3` in the `.glb.import` file). This is required:
   - The default, **Extract Textures**, saves the texture as a separate PNG. Godot then imports that PNG as a 3D texture, **VRAM-compressed with mipmaps**, which smears the pixels.
   - Embed as Uncompressed keeps it as plain RGBA with no mipmaps and the Nearest filter. Nothing else needs setting by hand.
   - After changing an import setting, delete the model's files in `godot-game/.godot/imported/`, or Godot may skip the re-import.
4. Check the model in the real scene, under the game's lighting, next to the Imp.

**Tested on 2026-10-22:** all 56 tools, in the main scene, held by the Imp: right scale (16 units = 1 m), crisp pixels, no errors.

**Still to test (Proposed):** creatures with animations. glTF is Godot's most reliable route for animations, so the first creature is the check.

**Draw calls.** Blockbench's GLB keeps every box as its own mesh, so a held tool draws as 12 to 29 pieces. That's fine for one tool in hand. **Proposed:** if many players end up on screen in the web build, merge each model's meshes into one when it loads.

## 6. Tier variants (Decided, D-114 and D-115)

Each tier of a tool is **its own model and its own texture**, with its own shape and detail. This replaces the earlier plan of one model with one texture per tier.

- **Themed on what the tier is made of.** Metal tools (pickaxes, axes, sickles) on their metal and its gem (D-012 pairings). Bows on their animal, carrying its trophy. Rods on their wood, carrying its log's marks. Low tiers are plain and practical; high tiers are ornate and magical.
- **Colours only from the icons.** Metal and handle from the tool's icon, gems from `godot-game/assets/sprites/source/items/gemstone_*.png`, bow decorations from the trophy icons, rod marks from the log icons. Handles follow the hilt (D-058).
- **Built by scripts from data tables**, not by hand, so a tier is a row of data and every model follows the same rules. The scripts are in `godot-game/assets/models/source/blockbench/tools/`:
  - `build_pickaxe_bbmodel.py` (Stone) and `build_pickaxe_metal_bbmodel.py` (the metal tiers),
  - `bbsprite.py`, shared by the rest: it draws a head from a small pixel drawing, merges it into few boxes, and lights it automatically (light from the top left, edge highlights, painted shadow at joins),
  - `build_axe_sickle_bbmodel.py` and `build_bow_rod_bbmodel.py`.
- Each set also gets a **lineup** (`<kind>s_lineup.bbmodel`, every tier side by side) and a preview picture, to check the tiers together.
- In Godot, the tool's id picks its file (`gathering/tool_art.gd`, `ToolArt.model()`). There is no shared tool scene that swaps textures.

## 7. Budgets (Proposed)

Boxes are cheap: 12 triangles each.

| Model | Boxes | Texture |
|---|---|---|
| Held tool | 8–30 (the 56 tools use 12–29) | 64×64 or 128×128 |
| Small item (ore, ingot, hide) | 2–10 | 32×32 or 64×64 |
| Small creature (Hare, Fox) | 15–40 | 128×128 |
| Large creature (Behemoth, Dragon) | 40–150 | 256×256 |

Texture sizes are for 2 pixels per unit (D-053).

## 8. Files (Proposed)

```
godot-game/assets/models/source/blockbench/   sources (D-021, moved by D-117)
  tools/      build_*.py, bbsprite.py      the scripts that write the models
              pickaxe.bbmodel, pickaxe_stone.png       the Stone pickaxe
              <kind>_<tier>.bbmodel, .png              every other tool, e.g. axe_dreadstone
              <kind>s_lineup.bbmodel, *_preview.png    all tiers side by side
              export/                                   Blockbench's .glb exports (and the test .fbx)
  creatures/  <name>.bbmodel, .png, build_<name>_bbmodel.py

godot-game/models/blockbench/            what the game loads
  pickaxes/ axes/ sickles/ bows/ rods/   <kind>_<tier>.glb and its .glb.import
  creatures/                             <name>.glb

godot-game/assets/models/mobs/, trees/   J00BA's Blockbench sources (.bbmodel)
```

The `<tier>` part is the tool's material: `stone` to `stellarite` for metal tools, the animal for bows (`bow_eclipse_dragon`), the wood for rods. It is the tool's id in `GameData` without its kind. The `.fbx` files in `export/` were the D-116 test and aren't used.

## 9. Review checklist (Proposed)

Run this on every Blockbench model before its PR is marked ready. Note the result in the PR.

**Look**
- [ ] The silhouette reads when filled black.
- [ ] One pixel size: 2 texture pixels per unit (D-053). No stretched or mixed-size pixels.
- [ ] 3–5 shades per material, hue-shifted. No pure black shadows, no pillow shading, no noise.
- [ ] Lit from the top. Top faces lightest, bottoms darkest, edge highlights on top edges.
- [ ] The brightest colour is on the part that matters.
- [ ] If it has an icon, its main colours come from that icon.

**Fits the game**
- [ ] Right size next to the Imp in Godot.
- [ ] Looks crisp, not blurry: exported as `.glb` and imported with Embed as Uncompressed (section 5).
- [ ] For tier sets: each tier has its own shape and detail, themed on its material (D-114, D-115), and the lineup reads as one set.

**Tech**
- [ ] `.bbmodel` source (and its script, if any) committed with the export.
- [ ] Pivots at the joints. Bones named by the shared names.
- [ ] Creatures: `idle`, `walk`, `attack`, `hit`, and the loops loop.
- [ ] Within the budget in section 7, or the PR explains why not.
- [ ] Made by us (D-018).

## 10. Clashes with ART-DIRECTION (for your decision)

ART-DIRECTION was written for a smooth, painted, cartoon look in Three.js (D-014). Voxel models change some of its rules:

| ART-DIRECTION rule | For Blockbench models |
|---|---|
| "No pixel-art textures on 3D models" (section 2, Proposed) | Doesn't apply. Voxel models **are** pixel-textured. |
| "Big bevelled facets", "painted gradients" (section 3, Proposed) | Replaced by section 4 here: boxes, edge highlights, hue-shifted pixel shading. |
| Three.js materials (sections 7, 10, Proposed) | Replaced by Godot settings (GODOT.md section 7). |
| `.glb` files (section 10, Proposed) | **Still applies.** Blockbench models go into Godot as `.glb` (D-116). |
| Chunky shapes, warm light with coloured shadows, saturated accents (section 3, Proposed) | **Still apply**, and section 4 here follows them. |

**Decided (D-047): voxel items and enemies in a stylised cartoon world.** "Slight voxel feel" means the models are built from boxes, but they should look like they belong next to the test project's smooth, painted assets. **Proposed** ways to make that work:

1. **Use the world's colours.** Take each palette from ART-DIRECTION section 5 and from the item's icon. Keep shadows blue or purple and highlights warm, the same as the world's lighting.
2. **Light them with the world's lights.** Use the same materials and lights as the world, never unlit or flat-shaded materials, so they get the same shadows and sun.
3. **Higher pixel density than Minecraft (Decided, D-053).** **2 texture pixels per Blockbench unit**, 32 per metre, softens the blocky look. Keep it the same on every model (section 4.1).
4. **Slight bevels are allowed.** A little rounding or a small Inflate on the main boxes catches the light like the world's bevelled edges do.
5. **Test it early.** Put the first enemy (the Hare) and the first tool (the pickaxe) in the meadow next to the Imp and check they look like one game before making the rest.

## 11. Open questions

1. **Imp height** in Godot, so every model can be scaled against it.
2. **Stations** (furnace, anvil, racks): Blockbench, or world-style? They stand in the world, so world-style is **Proposed**.

Answered on 2026-10-20: the world stays stylised cartoon (D-047).

Answered on 2026-10-21: 2 texture pixels per unit (D-053).

Answered on 2026-10-22: glTF (`.glb`), not FBX (D-116). Every tier gets its own model (D-114, D-115).

## Pass history
| Pass | Change |
|---|---|
| User addition, 2026-10-20 | Doc created. Blockbench voxel models for tools, weapons, creatures and items, exported as FBX into Godot (D-044). Quality rules, pipeline, budgets and checklist are Proposed. Status Draft. |
| User addition, 2026-10-20 (later) | World stays stylised cartoon, items and enemies have a slight voxel feel (D-047). Section 10 rewritten with how they fit together. World-style question removed. |
| User addition, 2026-10-21 | Link to BLOCKBENCH-STUDY (D-052). Texel density decided: 2 pixels per unit (D-053). Sections 4.1, 7, 9 and 10 updated to match; open question 1 removed. |
| User addition, 2026-10-22 | All 56 tools made and put in the game. Each tier gets its own model (D-114, D-115): sections 2, 6, 8 and 9 rewritten. Models go into Godot as `.glb`, not FBX (D-116): sections 1, 3, 5 and 10 updated, open question 3 answered. Section 5 now holds the tested export and import steps. |
