# Build the merchant's stall for the hub market

Build the merchant's stall as a Hytale style Blockbench model for Club Impz. It stands at the east end of Market Street, against the town wall, where the street ends at a blossom tree today. This is where players will sell what they gather and buy from the merchant, so it is the market's focal piece: a bit bigger and grander than the four stalls beside it, in the same family of style.

Repo: `joobajooba/club-impz`. Follow the GitHub workflow in the root `CLAUDE.md`: branch `staging/market_stall_merchant` from the default branch and open a **draft** PR. Read these first and follow them exactly. Where this prompt and the docs disagree, the docs win:

- `docs/blockbench_detailed_prompts.md`: sections 1 and 2 (global rules, **house texture style 1.5.1**, build method), 3.11 Props and buildings, 4 Quality checklist, 5 Colour ramps.
- `docs/MODELS-BLOCKBENCH.md` and `docs/ART-DIRECTION.md` (its 3D asset checklist goes in the PR).
- `docs/02-resources.md`, "The merchant (Decided, D-073 to D-077)": what the merchant buys and sells. The goods on the stall show exactly that, nothing else.
- `build scripts/build_stalls.py` and `build scripts/stall_lib.py`: the four existing stalls. **Build this one the same way**, as a new `market_stall_merchant()` function in `build_stalls.py`, reusing `Stall`, `stall_mats`, the ramps in `R`, and the painters (`boards`, `stripes`, `valance`, `sign`, `crate`, `sack`, `barrel`, `cloth`, `glass`, `book`, `lantern`, `window`, `roof`).
- `build scripts/build_hub_town.py`, function `square()`: where the stall goes (section 9 below).

If you don't have the repo, follow the rules in this prompt. They are taken from those docs.

## Reference

- `docs/images/merchant_stall/market_spot.png`: J00BA's screenshot. The red box is the spot: against the stone wall, past the end of the cobbled street, where the small pink blossom tree in a stone planter stands now, between two urn planters. The purple and teal booth on the left is `market_stall_potion`, the cart with the honey yellow canopy on the right is `market_stall_bakery`.
- `docs/images/merchant_stall/neighbour_stalls.png`: the four existing stalls rendered from their `.bbmodel` files, left to right: potion, bakery, fruit, cloth. Match their level of detail, their chunky walnut posts, gold carved trims, painted shop signs and goods piled on the counters.

## 1. Workflow (in this order, skip nothing)

1. Restate the build spec (section 3) briefly at the top of your reply, then build. Don't wait for approval.
2. Add `market_stall_merchant()` to `build scripts/build_stalls.py` and register it in `BUILDERS`. Add any new ramps or icon painters to `stall_lib.py` next to the existing ones. Don't change the other four stalls.
3. Render a preview from the front three quarter view with `build scripts/render_bb.py`, next to `market_stall_potion` and `market_stall_bakery` at the same scale, with the hidden imp shown. Compare it with both reference images. Fix the silhouette and the texture before calling it done.
4. Run `build scripts/check_texture_bleed.py` on the new model and fix anything it reports.
5. Run the quality checklist (section 10) and fix anything that fails.
6. Save the files (section 8), place the stall in the hub (section 9), open the draft PR.

The golden rule: **a stall never means a few big boxes.** Every post, board, tile and awning stripe is its own cube or its own painted detail, and every visible face is painted in the house style: lighter in the centre, darker at the edges, soft contact shadows, no outlines, no speckle noise.

## 2. Style

- Hytale mixed with RuneScape: Dragonwilds. Stylized, colourful, soft lighting, bold chunky shapes.
- Same family as the four stalls: walnut timber, gold carved trims, a cobble plinth like the potion booth, a painted hanging sign, lanterns, goods crammed on every surface.
- Its own colours so it stands out at the end of the street: a **deep red clay tile roof**, an **indigo and cream striped awning** with a scalloped gold-edged valance, walnut posts and beams, cream plaster panels between the timbers, gold trim. None of the neighbours use red tiles or indigo, so it reads as different from the potion booth (plum and teal) and the bakery cart (honey and sage) on either side.
- Cheerful and prosperous, not grim: a successful trader who buys everything.

## 3. Build spec

```
PROP BUILD SPEC
name / id:     market_stall_merchant
location:      hub, east end of Market Street, back against the town wall (the market's focal piece)
size:          about 80 wide (x) × 44 deep (z, awning included) × 78 tall to the top of the crest
materials:     wood (walnut posts and beams, oak counter boards), plaster panels, stone (cobble plinth),
               clay tiles (roof), cloth (awning, valance, rugs, hides), metal (iron brackets, scale, gold trim),
               goods (ore, ingots, gems, hides, logs, bundles, bags, hilts, flasks, hats)
build:         about 260 cubes (hard cap 320), separate planks, tiles and goods, wear and small damage
interaction:   none in the model. No moving parts, no door group
texture:       512 × 512, 2 px/unit, shared swatches (the stall_lib atlas)
groups:        market_stall_merchant > booth, roofs, awning, counter, bay_buy, bay_coin, bay_sell, sign, details, scale_dummy
animations:    none (cloth sways with the Godot wind shader if one is used)
```

## 4. Scale, units and orientation

- 1 Blockbench unit = 1 pixel. 16 units = 1 m. The imp is **18 units** tall.
- Hidden scale dummy: group `scale_dummy`, cube `scale_dummy_imp` from `[-2, 0, -60]` to `[2, 18.5, -56]`, export and visibility off (what `House.finish()` already adds).
- The model stands on y = 0, centred on x = 0. Front (the customers' side) faces **north (−z)**, like every stall. The back faces south (+z) and sits against the town wall in the game.
- From the front, the customer's **left is +x** and their **right is −x**. All x values below use this.
- Format 5.0, free model, per-face UV, cubes only. Rotated cubes are fine (awning slats, leaning goods).
- For size: the potion booth is 54 × 29 × 70.5 and the bakery cart 47 × 41 × 46.5. This stall is wider than both and about as tall as the potion booth's roof, plus a crest.

## 5. Layout (units, ground at y = 0)

| Part | Group | From → to (x, y, z) | Notes |
| --- | --- | --- | --- |
| Cobble plinth | booth | −39, 0, −14 → 39, 2, 16 | Like the potion booth's plinth. A front step −20 → 20, 0 → 1, −16 → −14 |
| Back wall | booth | −37, 2, 12 → 37, 46, 16 | Walnut timber frame (3 posts, a mid rail at y 24, a top beam) with cream plaster panels set 0.5 back between the timbers |
| Side walls | booth | x −37 → −35 and 35 → 37, y 2 → 46, z −4 → 12 | Same timber and plaster. One arched leaded window in each (house_lib `window`, cream frame, indigo shutters) |
| Front posts | booth | 4 posts at x −36, −13, 13, 36 (3 × 3), y 2 → 44, z −12 → −9 | Stone bases and gold carved capitals like the potion booth. They split the front into three bays |
| Front beam | booth | −38, 42, −12.5 → 38, 46, −8.5 | Gold carved band along the front face |
| Main roof | roofs | eave y 46 → ridge y 64, ridge along x | Red clay tiles, 6 to 8 stepped slabs per side, 3 unit eave overhang on all sides, walnut gable boards at the ends, gold ridge cap with small finials at both ends |
| Front cross gable | roofs | over the centre bay, x −14 → 14, eave y 46 → peak y 70 | Smaller gable facing north, same tiles, ridge meeting the main roof. Its plaster gable face holds the coin sign (section 6) |
| Crest | roofs | top of the cross gable, to y 78 | A gold crest strip and one gold finial with a small coin disc |
| Awning | awning | x −38 → 38, from the front beam at y 42, sloping down and out to y 34 at z −26 | Indigo and cream stripes, gold piping, scalloped valance hanging 4 units below the edge. Two iron rods angle down from the posts to hold it up. Split into three panels, one per bay, with a small gap at each post so it reads as three awnings under one roof |
| Counter | counter | −35, 2, −11 → 35, 13, −6 | Oak boards in three sections (one per bay) with gold carved bands, a walnut top 1 unit thick from y 13 to 14 that overhangs by 1 |
| Back shelves | bay_buy / bay_sell | two rows on the back wall at y 22 and y 32, z 9 → 12 | Walnut shelves on iron brackets, goods on them |
| Merchant's space | — | x −10 → 10, z −5 → 11, open floor | Leave room behind the centre counter for the merchant NPC to stand. No goods here |

Keep the overall shape **asymmetric in the details** (goods, hides, sacks, rugs) but balanced in the frame (posts, roof, awning), like the neighbours.

## 6. The three bays and the goods

The goods show what the merchant does (`docs/02-resources.md`, D-073 to D-077). Take the colours of every gathered item from its icon in `godot-game/assets/sprites/source/items/` (open the PNG, don't guess from the name). Goods are small, chunky, and stacked or piled, never neat rows of the same cube.

**Customer's left, `bay_buy` (+x): what the merchant buys.**
- On the counter: an open crate of ore nuggets (copper, tin, iron from their `nugget_` icons), a stack of 6 to 9 ingots in a criss-cross pile (copper, iron, gold from their `ingot_` icons), a small open box of 3 to 4 cut gems (ruby, sapphire, emerald from their `gemstone_` icons).
- Hanging over the counter front and the left side wall: 2 or 3 hides on pegs (`hide_wolf`, `hide_fox`, `hide_boar`), cloth cards with hard alpha ragged edges.
- On the floor beside the bay: a stack of 3 logs (`log_oak`, `log_ash`) with painted end rings, a burlap sack spilling ore, and 2 dried herb bundles hanging from the beam (`bundle_` icons).
- On the back shelves: rolled leather, a jar of seeds, a trophy or two (a fang, an antler, from the `trophy_` icons).

**Centre, `bay_coin`: the merchant's desk.**
- A brass balance scale (iron post, gold pans, chains) on the counter, the left pan lower with an ingot on it.
- Stacks of gold coins in 4 to 6 short columns of different heights, a small open coin chest with a heap of coins. Coins are gold with a light top edge and a darker rim.
- An open ledger book with a quill in an ink pot.
- Under the counter front: a carved panel with a coin icon, like the potion booth's counter panel.
- Above, on the cross gable: a round painted **coin sign** (about 14 across), gold rim, a raised coin with a simple star or crown stamped in the middle, on the plaster gable face.

**Customer's right, `bay_sell` (−x): what the merchant sells.**
- Bags for extra inventory space: 3 leather backpacks and satchels of different sizes, one on the counter and two hanging from hooks on the post.
- Energy refills: a small rack of 4 to 6 stoppered flasks with a glowing warm gold liquid, on cubes named `*_glow` so Godot makes them emissive.
- Wood hilts: a small wall rack on the side wall with an Ash Wood Hilt and an Oak Wood Hilt (from `hilt_ash_hilt` and `hilt_oak_hilt`).
- Cosmetics: a hat stand with 2 hats, a folded cloak on the counter, a little mirror on the back wall.
- A price board leaning against the counter end: a small chalkboard with painted coin marks, like the bakery's A-frame.

**Details (group `details`):**
- Two lanterns hanging from the front beam at the outer posts (stall_lib `lantern_hang`, glass on `*_glow` cubes).
- A rolled rug and a barrel at the right end, a stack of crates at the left end, so the stall's ends are not bare.
- A strip of moss and a few loose cobbles at the plinth corners, a little ivy on one side wall.
- Do **not** model the town wall, the urn planters, the cobbled street or the grass. They are separate assets.

**Back side.** In the game the back is 3 to 4 units from the town wall, so nobody sees its south face. Give the south faces of the back wall and the roof's back slope the plain swatch so they still render, but spend no detail there. The sides and the roof must be fully finished: the stall is seen from the street at an angle.

## 7. Texture

- One texture, 512 × 512, named `market_stall_merchant.png`, embedded in the file. The stall_lib atlas packs it.
- 2 texture pixels per unit on every face. Never stretch.
- **House style (section 1.5.1)**: every face lighter in the centre and darker at its edges, soft contact shadows under the roof, the awning, the counter top and where goods sit on surfaces, gradients one ramp step at a time, low noise only where the material needs it. No 1 px dark rims, no outlines, no speckle.
- Top faces lightest, sides middle, bottoms darkest. Light from the top, slightly front left.
- No pure black or white. Aim for 60 to 120 colours.
- Hidden faces get UV `[0, 0, 0, 0]` and texture `null`. Repeated parts share swatches.

**Materials:**
- **Walnut posts and beams:** vertical grain, worn lighter edges, darker at the base.
- **Plaster panels:** soft cream with a few warm patches and one or two hairline cracks, darker where they meet the timber.
- **Oak counter boards:** horizontal planks with gaps, grain, nail pixels, the gold carved band in front.
- **Cobble plinth:** the potion booth's cobble swatch.
- **Red tile roof:** curved clay tiles in staggered rows, each tile lighter in its middle and on its lower edge, a dark gap under each row, a few lighter weathered tiles and a moss patch near one eave. Darker under the eaves.
- **Awning:** indigo and cream stripes with soft vertical folds, lighter on top, gold piping, the scalloped valance cut with hard alpha.
- **Gold trim and the coin sign:** carved motif (stall_lib `carved` trim) with crisp light edges.
- **Goods:** each with its icon's colours and the same soft rounded shading. Ingots get a light top bevel, gems a pale lit centre, hides soft fur strokes, logs end rings.

**Ramps (dark → light).** Use the stall_lib ramps where they exist: `walnut`, `oak`, `plaster`, `cobble`, `gold`, `iron`, `indigo`, `canvas`, `tile_red`, `burlap`, `paper`, `glass`, `glow`. If `indigo` reads too purple next to the potion booth, add `awn_indigo`: `#0e1636 #172456 #213678 #2e4a98 #4462b2 #6482c8 #8ca4dc`. Energy flasks use `glow`.

## 8. Naming, groups and files

- Every group and cube in lowercase with underscores. The main cube of a group is `<group>_box`. Sides use `_left` and `_right`. Repeats are numbered: `tile_row_1`, `ingot_1`, `coin_stack_1`.
- Root group `market_stall_merchant` containing: `booth`, `roofs`, `awning`, `counter`, `bay_buy`, `bay_coin`, `bay_sell`, `sign`, `details`, `scale_dummy`.
- Pivots at the base centre of each group.
- Save the model as `godot-game/assets/models/buildings/stalls/market_stall_merchant.bbmodel` and the texture as `godot-game/assets/textures/buildings/stalls/market_stall_merchant.png`, beside the other stalls.
- Export the `.glb` with `build scripts/bb_export.py`. That runs Blockbench on J00BA's PC only: if you can't run it, say so in the PR and leave the `.glb` for J00BA.

## 9. Placing it in the hub

In `build scripts/build_hub_town.py`:

1. Add `"merchant"` to the stall names in the `MODELS` loop, so the alias `stall_merchant` points at `market_stall_merchant`.
2. In `square()`, replace `place("blossom_tree_planter", sx * 69.5, -16.0, 0, s=1.6)` with the stall, back to the wall, facing west down Market Street: `place("stall_merchant", 73.1, -16.0, "W")`. The town wall's inner face is at x = 74.375, so the stall's back (local z +16, 1.0 m) ends about 0.3 m short of it. `square()` is only called for the market (east), so the crafters' yard's blossom tree at x = −69.5 stays.
3. Keep the two `urn_planter`s at x 66.5, z −22 and −10. They frame the stall.
4. Add a vendor NPC spot behind the centre counter, facing the street: `npc("vendor_merchant", *local_to_world(73.1, -16.0, 90.0, 0.0, -0.1), "W", "market vendor (merchant)")`. Check the numbers against the model's real extent.
5. Rerun the script to rewrite `godot-game/data/hub_town.json`, then run the game and stand where the screenshot was taken. Check: the stall sits flush to the wall with nothing floating or clipping into it, the counter can be reached on foot, the urns don't overlap it, and the street lamps don't block the view of the sign.

Hooking the stall up to the merchant menu (`ui/merchant_menu.gd`) is **not** part of this job. Note it in the PR as a possible next step.

## 10. Quality checklist (fix anything that fails)

**Shape**
- [ ] As a solid black silhouette it reads as a market stall with a red roof, a front gable with a round sign, and a three-part striped awning, and it reads as different from the potion booth and the bakery cart.
- [ ] The counter top is about 14 units high, under the shoulders of the hidden 18 unit imp.
- [ ] No large flat faces: posts, panels, tiles, trims and goods break every surface.
- [ ] Stands on y = 0, centred on x = 0, front facing north (−z).
- [ ] 320 cubes or fewer.

**Texture**
- [ ] Compared side by side with `docs/images/imp_style_reference.png` and the neighbour stalls render: same softness and detail.
- [ ] Every visible face painted, lighter centre and darker edges, no outlines, no speckle.
- [ ] 2 px/unit everywhere, no stretched pixels, `check_texture_bleed.py` clean.
- [ ] 6 to 8 shade hue shifted ramps, no pure black or white.
- [ ] Goods match their item icons.
- [ ] Hidden faces have no UV and no texture. Repeated parts share UV space.

**File**
- [ ] Format 5.0, free model, per-face UV.
- [ ] Every group and cube in lowercase with underscores.
- [ ] `scale_dummy` included with export and visibility off.
- [ ] No animations.
- [ ] Texture embedded and saved as a matching `.png`.
- [ ] The `ART-DIRECTION.md` 3D asset checklist result is in the PR.

When you're done, show J00BA the preview render next to the neighbour stalls and an in-game screenshot from the same spot as `market_spot.png`, give the cube count and the colour count, and list any choices you made that this prompt didn't specify.
