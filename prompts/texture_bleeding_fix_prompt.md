# Fix texture bleeding on every Blockbench model and Imp trait

Repo: `joobajooba/club-impz`. Follow the GitHub workflow in the root `CLAUDE.md` (work on a `staging/` branch and open a draft PR). Read `docs/CLAUDE.md` and `docs/MODELS-BLOCKBENCH.md` (sections 4.1, 4.4 and 5) before you start.

Remove the thin white or dark lines that show along cube edges, on every Blockbench model and every Imp trait, without changing how any model looks otherwise.

## Reference

- `godot-game/assets/models/impz/head/head_afro.bbmodel` with `godot-game/assets/textures/impz/head/head_afro.png`: the afro hair trait, where J00BA first saw the lines. Use it as the test case before touching anything else.
- `docs/MODELS-BLOCKBENCH.md`: one texel density everywhere (D-053: 2 px per unit, trees 8 px per unit, D-120), half-unit box sizes so pixels land on edges, GLB export with the Nearest filter and **Embed as Uncompressed** (D-116).
- `build scripts/render_bb.py` (orthographic renderer for `.bbmodel` files) for before and after pictures.

## What is wrong

Every face's UV rectangle sits **flush against the edge of its island** in the texture. When a face is drawn, the pixels right on its edge can sample the texel just **outside** the island. What is out there is not the face's colour:

- **Imp traits and bodies** (`godot-game/assets/models/impz/`, 72 files, Hytale character format, per-face UV, 64 to 256 px textures). The atlas packers in `build scripts/head_lib.py`, `cloth_lib.py` and `eye_lib.py` start from a blank atlas (RGB 0, alpha 0) and leave a **1 px gap** between faces (`x += w + 1`, `y + shelf + 1`). So the texel next to every face edge is fully transparent. That shows as a see-through or white line, and black where the background is dark. In `head_afro.png` the column at x = 54, between the `mass_wide` north face (u 0 to 54) and its south face (u 55 to 109), is all alpha 0. About 83% of that texture is transparent gutter.
- **Everything else** (`godot-game/assets/models/` armour, buildings, foliage, items, mobs, npcs, props, tools, trees, weapons, and `source/`, about 500 files, Generic Model format). The faces are packed **touching** (0 px gap). A face edge can sample the next face's paint, which only shows as a line when that next face is a different colour or has transparent texels.

The Godot side is already right for the exported `.glb` files (318 imports use `gltf/embedded_image_handling=3`, so no mipmaps and Nearest filtering). Mipmaps or linear filtering would make bleeding much worse, so they must stay off.

## What to change

### 1. Measure first

Write `build scripts/check_texture_bleed.py`. For every `.bbmodel` with one texture, and each face that has a texture:

- convert its `uv` to texture pixels (scale by `width / uv_width` and `height / uv_height`),
- look at the 1 px ring just outside the face rectangle,
- flag the face if any ring texel is transparent (alpha < 255), or belongs to another face that is **not** the face joined to it on the cube (a different colour island).

Print a table per folder: models checked, models with flagged faces, flagged faces. Run it before any change and keep the output for the PR. Models that use several textures (the `*_lineup.bbmodel` files and other view-only sheets) are only listed, not fixed. Rebuild them from the fixed models if their script allows it.

### 2. Pad and dilate every UV island (the main fix)

Every face island must have **at least a 1 px border of its own edge colour** around it, so that a sample that lands just outside the face still gets the right colour.

- Islands need **at least 2 px between them** so each one gets its own 1 px border. A 1 px gap is not enough: the shared gutter texel can only take one neighbour's colour, and the other face still shows a line.
- **Dilation:** copy each edge texel of the island one pixel outward (the four sides, plus the corner texel diagonally), with **alpha 255** where the edge texel is opaque. Fill only texels that lie **outside every face rectangle**. Never write inside a face.
- **Keep intended holes.** Some trait texels are alpha 0 on purpose (texels hidden under another cube, cut-out shapes in the eyes, clothing and hair). Do not fill or change any texel inside a face. If a face's edge texel is transparent on purpose, its padding texel stays transparent too.
- Where a model's islands are 0 or 1 px apart, **repack** them with 2 px gaps: move each face's pixels and its `uv` together, by whole pixels, so the model shows exactly the same paint. If the atlas no longer fits, go to the next power-of-two size and set `width`, `height`, `uv_width` and `uv_height` to match, so texel density is unchanged (D-053).
- Leave geometry alone: cube sizes, positions, rotations, pivots, bone names, groups, attachment points and animations stay exactly as they are.

### 3. Fix the generators too

The scripts that write these models must produce padded textures from now on, or the next rebuild brings the lines back:

- `build scripts/head_lib.py`, `cloth_lib.py`, `eye_lib.py` and `build_imp_bodies.py` (Imp traits and bodies),
- `godot-game/assets/models/source/blockbench/tools/bbsprite.py` and the other `build_*.py` scripts under `godot-game/assets/models/source/blockbench/` (tools, weapons, armour, items, props, npcs, buildings, creatures, world).

Put the padding and dilation in **one shared helper** (for example `build scripts/uv_padding.py`), used by both the packers and the fix pass, so the rule lives in one place. Do not change what the scripts paint.

Several scripts read from or write to J00BA's PC (`C:/Users/lucas/blockbench_models/...`). Don't rerun those builds from the cloud. Fix the files in the repo with a pass over the committed `.bbmodel` and `.png` files, and patch the scripts so J00BA's next local run matches.

### 4. Keep the embedded and PNG textures identical

Each Imp trait `.bbmodel` embeds its texture as base64 **and** points to a PNG through `relative_path` (see `build scripts/export_trait_models.py`). Write the fixed texture to both, and check that the decoded embedded image equals the PNG pixel for pixel, as that script does. Do the same for any other model that has both.

### 5. UV inset (only where padding can't be done)

A slight UV inset (pulling each face's UV in by a small fraction of a texel, about 0.01 to 0.05 px) also stops edge sampling, but it breaks "pixels land exactly on edges" (section 4.1) and the Hytale character format may only keep whole-pixel UVs. **Don't use it by default.** Use it only for a model where padding is not possible, list each such model in the PR, and check that Blockbench and the exported `.glb` keep the fractional values.

### 6. Godot import settings

- Every Blockbench `.glb.import` under `godot-game/models/blockbench/` must keep `gltf/embedded_image_handling=3`: no mipmaps, no VRAM compression, Nearest filter. List any file that differs.
- Re-export the `.glb` of every model whose texture changed, from Blockbench (File → Export → Export glTF Model, binary, texture embedded), into its existing place. Delete that model's files in `godot-game/.godot/imported/` so Godot re-imports it.
- When the Imp traits get `.glb` files, they follow the same settings.
- Don't change the non-Blockbench world assets (`godot-game/FBX/`, `godot-game/FBX (Unity)/`, `godot-game/glTF/`, `godot-game/models/mining/`, the terrain textures). They are the stylised cartoon world (D-047) and use their own import settings.

## Order of work

1. `head_afro` alone: run the check, apply the fix, render before and after. Stop and show J00BA the close-ups before going on.
2. The rest of the Imp traits and bodies (`impz/back`, `bodies`, `clothing`, `eyes`, `head`, `green_imp.bbmodel`, `imp_green.bbmodel`).
3. Everything else, one folder at a time, only the models the check flagged.

## Checks before the PR

- `check_texture_bleed.py` reports **0 flagged faces** for every fixed model.
- For each model, the paint inside every face is unchanged. Compare each face's pixels before and after the fix (after any repack, through the new UVs). Any difference fails the check.
- Geometry, groups and animations are byte-for-byte the same as before, apart from `uv` values and texture size fields.
- The game opens in Godot 4.7 with no import errors, and the tools in the Imp's hand still look crisp.

## Output

- The fixed `.bbmodel` files and PNGs, saved in place.
- `build scripts/check_texture_bleed.py`, the shared padding helper, and the patched build scripts.
- In the PR: the check table before and after, the list of repacked models (with any atlas size change), any model that needed a UV inset, and any `.glb.import` that differed.
- Close-up renders of `head_afro` before and after, front and side, at a zoom where the old lines are clear. Add the same pair for one trait from each of back, clothing and eyes, one tool and one armour piece, so J00BA can check the lines are gone and nothing else moved.
