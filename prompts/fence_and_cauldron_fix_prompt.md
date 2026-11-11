# Fix the crafters' yard fences and the cauldron's striped brew

Repo: `joobajooba/club-impz`. Follow the GitHub workflow in the root `CLAUDE.md`. The fences and the cauldron only exist on `staging/hub-redesign` (draft PR #64), so branch from it as `staging/fence-cauldron-fix` and open a **stacked** draft PR with `staging/hub-redesign` as its base. Read `docs/CLAUDE.md` and `docs/MODELS-BLOCKBENCH.md` before you start.

Two fixes, nothing else:

1. **Fences.** Every fence run must either connect to another fence or end in a post. No rail may stop in mid-air, and no two posts may sit on top of each other.
2. **Cauldron.** Remove the flickering grey and green stripes on top of the cauldron.

## Reference

- `docs/images/fence_and_cauldron_fix/fences_open_ends.png`: J00BA's screenshot of the yard. Front rails end in mid-air, and the side fences stop short of the front fences.
- `docs/images/fence_and_cauldron_fix/cauldron_brew_stripes.png`: J00BA's screenshot of the brewer's cauldron. The brew shows as broken green and grey stripes.
- `build scripts/build_hub_town.py`, function `yard()` and `YARD_PLOTS` (about lines 257 to 320): places every fence. It writes `godot-game/data/hub_town.json`, read by `scripts/world/hub_town.gd`.
- `build scripts/build_workshop_props.py`, functions `fence_rail()` and `fence_post()`: the two fence models (`godot-game/assets/models/props/workshop/fence_rail.bbmodel` / `.glb`, `fence_post.bbmodel` / `.glb`).
- `build scripts/build_stations.py`, function `cauldron()` (about line 542): the cauldron model (`godot-game/assets/models/props/stations/cauldron.bbmodel` / `.glb`). Crossed-box octagons come from `octo()` in `build scripts/house_lib.py`.
- `build scripts/check_texture_bleed.py`, `build scripts/render_bb.py` and `build scripts/bb_export.py` (Blockbench export, runs on J00BA's PC only).

## 1. Fences

### The fence models

16 Blockbench units = 1 m. Every model faces north (-z) and `yaw` is Godot `rotation.y` (N = 0, W = 90, S = 180, E = -90).

- `fence_rail`: one 2 m length. Its only post is on the **west** end, centred 15/16 m west of the model origin. The rails run from there to **+1.0 m** (the east end), which has **no post**. A rail is only closed at its east end if the next rail's post, or a `fence_post`, stands there.
- `fence_post`: a lone post, centred on the origin.
- At yaw 90 the rail's post end points **south** (+z) and its open end **north** (-z).

### What is wrong now

These come from the placements in `hub_town.json` (`git show origin/staging/hub-redesign:godot-game/data/hub_town.json`). Fence x positions are the plot edges -63.5, -55.75, -48.0, -40.25, -32.5.

1. **Corners don't meet.** The side fences between plots run from the back of the plot to 8.0 m deep, but the front fences sit at 9.2 m (`PLOT_D - 0.3`). Each front corner has a **1.2 m gap**: north row side fences end at z = -21.5, front fences at z = -20.3. South row side fences end at z = -10.5, front fences at z = -11.7.
2. **Front rails have one open end.** Each side of a gateway is a single `fence_rail` with its post on the west end. On the west side of every gateway, the gate end has no post (for example x = -61.5). On the east side, the plot-edge end has no post. The next plot's rail post covers that end, except at the **east end of the yard (x = -32.5, both rows)** and, in the south row, **beside the open passage plot (x = -48.0)**.
3. **North row side fences are reversed.** The rails' posts land on the street ends, so the **back end (z = -29.5) is an open rail end**. The extra `fence_post` at z = -21.5 sits on the last rail's own post (z = -21.5625), so there are **two posts in one spot** and they flicker.
4. In the south row the end posts sit at -10.5 rather than -10.5625, where the next post would be. They are 1/16 m off the post spacing.

### What to change

- Add one helper in `build_hub_town.py`, for example `fence_run(points)`, that builds a straight run from a list of corner points. It places the rails so the posts are evenly spaced, puts a post at **every** joint and at **both ends**, and turns the rails so their post ends line up. Place every fence in the yard through it. Don't place a rail or a post by hand.
- **Corners share one post.** Where a side fence meets the front fences of the two plots either side of it, there is exactly one post at that point.
- **Make the corners meet.** The side fences must reach the front fence line. A side fence is built from whole rails, so pick one of these:
  - **Recommended:** move the front fence line to `d = 9.0` (0.5 m from the street edge) and add a 1 m rail, `fence_rail_half`, to `build_workshop_props.py`. Build it exactly like `fence_rail` (same post, cap, rails, materials and texture density), just 16 units long. Each side fence is then four 2 m rails plus one 1 m rail.
  - If the gate sign (`d = PLOT_D - 0.6`) or the brewer's `stall_potion` (`d = 7.0`) would clash with the new line, keep the front line where it is and make the short rail 1.2 m long instead. Say which option you used in the PR.
- The front fence on each side of a gateway stays 2 m long (from the plot edge to the gate), with a post at the gate end and the shared corner post at the plot edge.
- The **passage plot** (south row, between x = -48.0 and -40.25) has no front fence. The side fences on either side of it end in a post at the front line.
- The **back ends** of the side fences (z = -29.5 north, -2.5 south) end in a post too.
- Fences keep `collide="extent"` for rails. Posts stay `collide=False` unless a gap opens that lets players walk between two plots. Check the colliders still close every plot apart from its gateway and the passage.
- Search the rest of `hub_town.json`, and every scene and script, for any other `fence` placement (for example the older `assets/models/props/fence.bbmodel`). Apply the same rule to it. If there is none, say so in the PR.

### Check script

Write `build scripts/check_fences.py`. It reads `hub_town.json` and, using the post and rail end positions from the fence `.bbmodel` files (not hard-coded numbers), reports:

- every rail end that has no post within 0.05 m (its own post, another rail's post or a `fence_post`),
- every pair of posts closer than 0.1 m (doubled posts),
- every side fence end that is not on the front fence line or the back of its plot.

It must report **0** of each before the PR. Run it on the current file first and keep that output for the PR.

## 2. Cauldron

### What is wrong

This is **not** UV bleeding. `check_texture_bleed.py` already reports 0 flagged faces for every model in `props/stations`, including the cauldron. The stripes are **z-fighting**: two faces drawn in the same plane, with different paint, and the GPU switches between them pixel by pixel.

At **y = 14**, three faces lie on top of each other:

- `pot_rim_a` up and `pot_rim_b` up: the rim is two crossed **solid** slabs, so its top is a solid grey lid over the whole pot, not a ring. Their two tops overlap in the middle with different shading.
- `brew_glow` up: the green brew (y 13.5 to 14), its top in the same plane as the grey lid.
- `bubble_1_glow` down also sits in that plane.

So the brew and the lid fight, which shows as the green and grey stripes in the screenshot.

The same crossed-box octagons put other faces on top of each other in the cauldron: `pot_body_a/b` up (y 13), `pot_belly_a/b` up (11.5) and down (6.5), `pot_base_a/b` up (5) and down (4), the leg tops against `pot_base` down (4), `pot_rim_a` east/west against the bail lugs, the table leg tops against `table_top` down (9), `chain` against `tripod_lashing` and `chain_hook`, `bottle_1_body_glow` east against `bottle_2_body_glow` west, `crate_bundle_1/2` and `3/4`, and `wood_stack_1/2` up against `wood_stack_3` down. Most of these are hidden or the same paint, but any that can be seen will flicker too.

### What to change

In `build_stations.py` `cauldron()`:

- **Make the rim a ring**, not a lid: an octagonal band round the top edge (about 1 to 1.5 units wide), open in the middle.
- **Sink the brew below the rim top**, for example its top at y = 13.5, so the rim's inner walls show above the liquid and no brew face shares a plane with any rim face. Keep the brew the same size and paint, filling the opening.
- Sit the bubbles on the brew's new surface.
- **No two faces may overlap in the same plane** anywhere in the cauldron. Where a face is fully covered by another cube (leg tops under the base, body top under the rim, table leg tops under the table top), hide it, the way the builders already hide `down` faces. Where both are visible (the belly ledges, crossed boxes touching), trim or split the boxes so they meet edge to edge instead of overlapping, or hide one of the pair if the other covers the same area with the same paint.
- Don't change the cauldron's look otherwise: the same size, tripod, chain, fire, table, bottles, crates and wood, and the same paint per part.
- If you change `octo()` in `house_lib.py`, add an option instead of changing its default. Many other models use it, and they are out of scope.

Add a coplanar-overlap test to `check_texture_bleed.py`, or write it as `build scripts/check_coplanar.py`: for every pair of visible faces on unrotated cubes that lie in the same plane, face the same way and overlap by more than 0.01 units, flag the pair. The cauldron must report **0**. Run it over `godot-game/assets/models/props/` and **list** the other models it flags in the PR, without fixing them.

## Building and exporting

`build_workshop_props.py`, `build_stations.py` and `bb_export.py` write to and run on J00BA's PC (`C:/Users/lucas/...` and a local Blockbench). Run them there, as for the hub redesign:

1. Run `py build_stations.py cauldron` and `py build_workshop_props.py fence_rail_half` (and `fence_rail` / `fence_post` only if you changed them), and copy the `.bbmodel` files and textures into their places in the repo.
2. Pad the new textures (the builders pad on save since the texture-bleed fix). `check_texture_bleed.py` must still report 0 for these models.
3. Export each changed model to `.glb` with `bb_export.py` (binary, texture embedded) into its existing place, next to the `.bbmodel`. A new `.glb` gets an `.import` with `gltf/embedded_image_handling=3`, like the others.
4. Add `fence_rail_half` to the `MODELS` list in `build_hub_town.py`, rerun it to rewrite `hub_town.json`, and rerun the terrain bake if the yard's ground rects changed.

If you are working from the cloud and can't reach J00BA's PC, make the script and `.bbmodel` changes, commit them, and say in the PR that the `.glb` export still needs to run on J00BA's PC. Don't hand-edit a `.glb`.

## Checks before the PR

- `check_fences.py`: 0 open rail ends, 0 doubled posts, 0 side fences short of the front line.
- The coplanar check: 0 for the cauldron.
- `check_texture_bleed.py`: 0 for the cauldron and the fence models.
- The game opens in Godot 4.7 with no import errors, the hub loads, and every yard plot is closed except at its gateway and the passage.

## Output

- The patched `build_hub_town.py`, `build_workshop_props.py`, `build_stations.py`, the rewritten `hub_town.json`, the changed and new `.bbmodel`, `.png` and `.glb` files, and the check scripts.
- In the PR: `check_fences.py` output before and after, the option used for the front line, any other fence placements found, and the coplanar check output for the cauldron and the list of other flagged models.
- In-game screenshots from the same spots as J00BA's two screenshots, before and after: the yard fences from the street, a front corner close up, the yard's east end, the passage, and the cauldron from above at a distance where the stripes showed. Add a `render_bb.py` render of the cauldron top, before and after.
