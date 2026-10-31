# World Build Notes

> Status: v1 · Built from `docs/godot_world_build_prompt.md` · Last updated: 2026-10-30
>
> How the first playable slice of the Club Impz worlds is put together in Godot: the terrain, biome data, scatter and environment systems, where to tune them, the controls, every placeholder that is waiting for a real model or texture, and every choice that the docs didn't cover.

---

## 1. Running it

| What | How |
| --- | --- |
| Editor | Open `godot-game/` in Godot 4.7 (Compatibility renderer). Press F5. |
| Start in a world | `godot --path godot-game -- --world=resource --biome=frost` (`--world=hub|resource|test|lineup`) |
| Re-bake the world data | `godot --headless --path godot-game --script res://scripts/tools/bake_world_data.gd` |
| Re-convert the models | `python3 tools/bbmodel_to_gltf.py` (all) or `python3 tools/bbmodel_to_gltf.py path/to/model.bbmodel` |
| Web build | Project > Export > Web (preset "Web", threads off) to `godot-game/export/web/` (git ignored), then serve the folder, for example `python3 -m http.server`. The web build takes the start flags from the URL: `index.html?world=resource&biome=frost` |

### 1.1 Controls

| Key | Action |
| --- | --- |
| W A S D or arrow keys | Move (relative to the camera) |
| Shift | Sprint (6.5 m/s, walk is 4 m/s) |
| Space | Jump |
| Right mouse drag | Orbit the camera |
| Mouse wheel | Zoom (3 to 14 m) |
| 3 | Toggle the debug overlay (FPS, draw calls, position, biome) |
| 4 | Teleport to the next biome centre (resource world) |
| 5 | Flip between day and night (2 s fade, restarts the 30 minute timer) |
| 6 | Toggle fast sprint (sprint at 5x speed, for testing) |

---

## 2. Project layout

```
godot-game/
  project.godot, export_presets.cfg
  scenes/   main.tscn, hub/hub_world.tscn, resource/resource_world.tscn, player/imp_player.tscn, shared/portal.tscn,
            hub/*_placeholder.tscn, hub/hub_castle.tscn, resource/*_placeholder.tscn, resource/ores/*_vein_placeholder.tscn,
            test/flat_test_world.tscn, test/model_lineup.tscn
  scripts/  main.gd, debug_overlay.gd
            player/   imp_player.gd (controller + camera), imp_visual.gd (placeholder imp)
            terrain/  world_data.gd (loads the baked data), terrain_world.gd (chunks, colliders, far mesh, material)
            world/    game_world.gd, scatter.gd, hub_props.gd, hub_castle.gd, resource_landmarks.gd, portal.gd,
                      prop_placeholder.gd, ore_vein_placeholder.gd
            environment/ biome_environment.gd
            tools/    bake_world_data.gd, model_lineup.gd
  shaders/  terrain.gdshader, foliage_wind.gdshader, water.gdshader
  data/     biomes.json, scatter.json, *_terrain.png, *_mask.png, *_layout.json
tools/      bbmodel_to_gltf.py, generate_terrain_textures.py
```

`main.tscn` keeps the player, the fade layer and the debug overlay alive and swaps the world scenes in and out. Every player starts in the hub.

---

## 3. Terrain

### 3.1 Baked data

`scripts/tools/bake_world_data.gd` builds both worlds from `FastNoiseLite` with fixed seeds, so every load is the same, and writes them to `godot-game/data/`. The PNGs are imported with **Keep** (`importer="keep"`), so they ship unchanged and load in the web build.

| File | Size | Contents |
| --- | --- | --- |
| `resource_terrain.png` | 641 × 257 (2 m per pixel) | **RG** = height, 16 bit: `height = (R × 256 + G) / 200 − 20` m. **BA** = warped depth `s`, 16 bit: `s = (B × 256 + A) / 50` m |
| `resource_mask.png` | 1280 × 512 (1 m per pixel) | **R** path, **G** wet / low ground (riverbanks, frozen lake, dry riverbeds), **B** special patch (plains green grass at the watering hole, swamp slime at the dreadstone pit), **A** forest leaf litter / tree clusters |
| `resource_layout.json` | | Main path and branch polylines, landmark positions, water planes, waterfall, spawn point |
| `hub_terrain.png`, `hub_mask.png`, `hub_layout.json` | 101 × 101 / 200 × 200 | Same for the 200 × 200 m hub. Mask **R** dirt paths, **B** cobblestone |

**Repainting:** the masks can be painted by hand (keep the channel meanings). The height map is 16 bit split over two channels, so edit it through the bake script rather than by hand. If you hand paint a mask, stop re-baking or the bake will overwrite it.

**Resource world layout** (x is depth, z is width):

- 1280 × 512 m, x from 0 to 1280, z from −256 to 256. Five 256 m bands in depth order: forest, mountain, frost, plains, swamp. The borders are warped by noise (±26 m) and blend over 45 m (`blend_half_width` 22.5 m each side).
- The portal clearing is at x 36, z 0. The main path runs from it to x 1240, with a branch to every landmark.
- A ring of tall mountains closes the edges. Void and stellar will be separate floating island meshes past x 1280.

### 3.2 Runtime terrain (`terrain_world.gd`)

- **Chunks:** 64 × 64 m chunks with 2 m vertex spacing and smooth normals, built two per frame, nearest first, out to `view_chunks` chunks (4 in the resource world, 3 in the hub).
- **Colliders:** a `HeightMapShape3D` for the 3 × 3 chunks round the player.
- **Far mesh:** an 8 m spacing mesh of the whole world. It is hidden within 150 m of the camera (shader discard) and sits 1.2 m lower, so the detailed chunks always win. This is how the highest peak is visible from the forest.
- **No stepped ground:** the ground is smooth. The pixel look comes from the textures.

### 3.3 Terrain shader (`shaders/terrain.gdshader`)

- **Texture array:** all 28 textures in one `Texture2DArray`, in the layer order from `terrain_textures.md` section 2 (the list is `layer_files` in `data/biomes.json`). It is built at load with `create_from_images()` after generating mipmaps, and sampled with `filter_nearest_mipmap` and repeat.
- **UVs:** `world.xz / 4` (one 128 px tile = 4 m = 32 px per metre). Steep rock uses the dominant-axis projection (triplanar without blending, so pixels stay crisp).
- **Biome:** comes from the warped depth `s` in the vertex UV. Inside a border only the two strongest biomes are evaluated, and a hash dither on the 32 px per metre grid picks one per pixel. So the borders blend in pixel steps, not a soft fade.
- **Layer rules** (`terrain_textures.md` section 4.2), per biome in `data/biomes.json` under `terrain`:

| Field | Meaning |
| --- | --- |
| `base` | Base layer |
| `patch`, `patch_threshold` | Noise patches (forest dry grass, frost tundra, plains green, swamp moss) |
| `litter` | Layer where the mask's A channel is high (forest leaf litter) |
| `wet` | Mask G (riverbanks, frozen lake ice, dry riverbeds) |
| `high`, `high_y` | Above a height (mountain snow, plains mesa tops, swamp islands) |
| `mid`, `mid_slope` | Moderate slopes (mountain scree below cliffs) |
| `special` | Mask B (plains green grass, swamp slime, hub cobblestone) |
| `steep`, `steep_slope` | Cliffs (triplanar) |
| `path` | Mask R |
| `border_patch` | Frost only: tundra gets more likely near the biome borders |

### 3.4 Water (`shaders/water.gdshader`)

- **Planes:** flat water planes from `water` in the layout JSON: the forest river below and above the waterfall, the frost open pool, the plains watering hole, and the swamp water over the whole swamp. The colour is the biome's `water` value in `biomes.json`.
- **Look:** stepped pixel ripples snapped to 32 px per metre, soft transparency, no refraction.
- **Waterfall:** the same shader on a vertical quad with `flow` > 0.

---

## 4. Scatter (`scripts/world/scatter.gd`, `data/scatter.json`)

- **Rules:** every rule lists the biomes, a density word (or `spacing` in metres), the meshes with weights, a scale range, and filters:
  - `avoid`: path, wet, water, special, steep.
  - `require`: litter, wet, special, near_path.
  - `height` range, noise `patch`, `near` a landmark, and `clear` (keep trees away from landmark clearings).
- **Density words** (`density_spacing` in `biomes.json`): carpet 1.5 m, dense 2.4 m, scattered 6 m, rare 22 m. One plant per jittered cell of that size.
- **Foliage:** one `MultiMeshInstance3D` per plant per **48 m cell**, built one cell per frame round the player, out to `foliage_view_distance` (52 m). Plants shrink out over the last 8 m. No shadows.
- **Trees:** one `MultiMeshInstance3D` per tree per **128 m cell**, out to `tree_view_distance` (240 m, or a rule's `view`). Cylinder trunk colliders in the 3 × 3 tree cells round the player.
- **Deterministic:** the seed is `hash(cell, rule index, rule seed)`, so the same plants grow in the same places every load.
- **Wind** (`shaders/foliage_wind.gdshader`): sway grows with height above the model's base, so bases stay still. Leaf cards use the biome's `wind` from `biomes.json` (strongest in plains and mountain, weakest in swamp); trunks don't move.
- **Recolouring:** `recolor` maps the leaf cards' brightness onto a dark-to-light ramp, so one grass shape serves every biome (`game_worlds.md` section 4.10). `petal` recolours only red petals (the placeholder wildflowers from the rose). `tint` and `trunk_tint` multiply.

---

## 5. Environment (`scripts/environment/biome_environment.gd`)

- **Presets:** one per biome in `biomes.json` under `env`: sky top and horizon colours, ground colour, sun colour, energy and angle, ambient light, fog colour, density and sky affect. The values come from the Sky and light and Fog rows in `game_worlds.md` section 4.8.
- **Switching:** an `Area3D` per biome band (resource world). Entering one fades the environment and the sun to that biome over 3 seconds. Depth fog only.
- **Particles:** one `CPUParticles3D` per biome that follows the player: pollen (forest and hub), falling leaves (mountain), snow (frost), dust and seeds (plains), fireflies (swamp).
- **Sound hooks:** an empty `AudioStreamPlayer` per biome named `ambient_<biome>`, waiting for sound files.
- **Draw distance:** the fog hides the chunk edge. The swamp has the densest fog.

---

## 6. Placeholders waiting for real assets

| Placeholder | Where | Replace with |
| --- | --- | --- |
| `imp_visual.gd` (box imp) | Player | The real imp model, under the `visual` node |
| `market_stall_placeholder`, `smelter_placeholder`, `workbench_placeholder`, `anvil_placeholder` | Hub | Blockbench props |
| `portal.tscn` (glowing ring) | Hub, resource world | Portal model and effect |
| `*_vein_placeholder` (coal, tin, copper, iron, gold, obsidian, titanite, dreadstone) | Resource world | `<ore>_vein.glb` (`blockbench_detailed_prompts.md` section 3.2) |
| `hickory_tree_placeholder` (recoloured oak) | Mountain, frost | `hickory_tree` |
| `frostbark_tree_placeholder` (pine, white canopy) | Frost | `frostbark_tree.glb` (now in `assets/models/trees/`, not yet swapped into `scatter.json`) |
| `titanwood_tree_placeholder`, `giant_titanwood` (scaled pine) | Plains, swamp | `titanwood_tree` |
| `runewood_tree_placeholder` (recoloured oak) | Swamp | `runewood_tree` |
| `gembark_tree_placeholder` (recoloured maple) | Plains | `gembark_tree` |
| `worldbark_tree_placeholder` (oak ×4) | Forest grove | `worldbark_tree` |
| Wildflowers, alpine flowers, plains flowers (rose with recoloured petals) | Forest, mountain, plains | Their own flower models |
| `dry_grass_tuft`, `frost_grass_tuft`, `tundra_grass_tuft`, `mountain_grass_tuft`, `plains_tall_grass`, `swamp_grass_tuft` (recoloured forest grass tufts) | All biomes | Fine as recolours (section 4.10), or dedicated models |
| `forest_fern`, `forest_reeds`, `heather_bush`, `red_flame_bush`, `copper_autumn_bush`, `frost_bush`, `frozen_dead_bush`, `berry_shrub`, `wild_wheat`, `dry_bush`, `swamp_reeds`, `swamp_fern`, `swamp_big_leaf`, `giant_mushroom` (recoloured tufts and bushes, all `_placeholder` in `scatter.json`) | Biomes | Their models from `game_worlds.md` section 4.10 |
| Landmarks: `stone_ruin`, `standing_stones`, `obsidian_vent` (cave), `giant_stone_peak_cairn`, `frozen_waterfall`, `ice_spire`, `stone_arch`, `pillar_ring`, `hollow_tree`, `dreadstone_pit`, `sunken_ruins`, `log_bridge` | Resource world | Landmark models |
| Not placed yet | | Lily pads, hanging moss, glow fungus, cave glow mushrooms, ice and gem crystal clusters, ground leaf litter models, mobs |
| Ambient sounds | Every biome | Loops for the `ambient_<biome>` players |

---

## 7. Choices the docs didn't cover

1. **Godot 4.7.2** (the installed stable). GDScript warning "inference on Variant" is set to a warning instead of an error.
2. **glTF UVs are not flipped.** glTF's UV origin is the top-left of the image, the same as Blockbench's pixel UVs, so flipping V (as the build prompt suggested) would turn the textures upside down.
3. **Converter output:** one mesh per model. Materials are split by texture and kind (solid, double-sided card, `_glow` emissive), with nearest sampling and alpha MASK where the texture has transparency. Group rotations are baked in; animations are skipped.
4. **The hub castle** uses J00BA's `hub_castle` Blockbench model (not a block-out), with box and cylinder colliders from its own block sizes. It is shown at **2.5×** model scale (about 40 m wide) so the centrepiece reads across the village; `CASTLE_SCALE` in `hub_props.gd` sets it.
5. **Terrain textures import as Image resources** (not textures), so building the texture array never reads back from the GPU. That readback hung the game now and then on this machine.
6. **Gravity** is 12 m/s² for a snappier jump. The imp walks slopes up to 46°.
7. **Biome switching** uses the band boxes (x ranges). The shader and the scatter use the exact warped border.
8. **World size:** the hub is 200 × 200 m centred on 0, 0. The resource world origin is its west-north corner (x 0, z −256).
9. **Scatter cells** of 64 m (foliage) and 128 m (trees) keep draw calls low for WebGL. The density spacing values are the starting point for the performance pass (section 8).
10. **Environment:** linear tonemapping and lower light energies than the doc colours suggest, because the Compatibility renderer looked washed out otherwise.
11. **Ore placement** is a seeded search per biome (4 nodes per ore) for spots matching section 4.8 (outcrops and riverbanks, cliffs, ice cliffs, mesas, muddy banks), plus 5 obsidian nodes round the volcanic cave and 5 dreadstone nodes round the dreadstone pit.

---

## 8. Performance notes

Measured with `--perf=4` (desktop, 1280 × 720, standing at each biome centre, camera zoom 10):

| World / biome | FPS | Draw calls | Foliage multimeshes | Tree multimeshes | Terrain chunks |
| --- | --- | --- | --- | --- | --- |
| hub | 60 | 134 | 31 | 8 | 16 |
| forest | 60 | 256 | 86 | 40 | 52 |
| mountain | 60 | 205 | 32 | 38 | 67 |
| frost | 60 | 164 | 20 | 32 | 64 |
| plains | 60 | 164 | 34 | 27 | 64 |
| swamp | 60 | 115 | 36 | 20 | 44 |

- Forest is the busiest (densest foliage); it stays under about 260 draw calls, which is comfortable for WebGL 2.
- Swamp has the shortest draw distance (120 m against 200 to 240 m elsewhere), matching its thick fog (density 0.018).
- Each placeholder prop (ores, landmarks, stalls) is merged into one mesh per material by `scripts/world/mesh_merge.gd`.
- Where to tune: `draw_distance` and fog per biome in `data/biomes.json`, spacing per scatter rule in `data/scatter.json`, cell sizes at the top of `scripts/world/scatter.gd`.

### 8.1 Web export check

- The Web preset (threads off) exports to `godot-game/export/web/` (about 40 MB with the wasm) and runs from a plain `python -m http.server`.
- It was checked in Chrome through Playwright, loading the hub and all five biomes, with no console errors. The screenshots are in `docs/images/world_build/` (`hub_overview.png`, `forest_overview.png`, and so on).
- Those headless runs use SwiftShader (CPU rendering), so their 4 to 10 FPS overlay reading isn't a real-GPU number. On a normal browser with a GPU, expect frame rates close to the desktop table above.
- Portals were tested both ways with `--portal_test` (hub → resource → hub).
- Nothing failed only in the web build.

---

## 9. World generation fixes

- **Walkable terrain:** after the height pass, `bake_world_data.gd` blurs the heights (3 passes of a 5 × 5 box blur, skipping the edge ring) and limits the slopes. The limit is about 35° everywhere and about 20° in path corridors, which now include the branch paths. Peaks above 70 m, the edge ring, the frost ice cliffs and the waterfall stay steep, except where a path runs through them. The bake prints a check line; currently it shows 0 cells over 44°, a 19.8° max path grade and 0 water leaks.
- **Water banks:** each water rect's bed is sunk 0.5 m under the level, and its edges are raised to 0.4 m above it. A slope cone raises the dry land next to those banks, so water never pokes out over low ground. The upper pool keeps a 10 m lip at the waterfall. Path corridors through water (the swamp) are kept 0.25 m above the water so the path stays dry.
- **Swamp path** uses `forest_dirt` instead of `swamp_boardwalk`.
- **Terrain textures:** every layer is now sampled triplanar (blend sharpness 8, flat ground takes a single sample), with anisotropic nearest filtering, so scree and slopes no longer stretch.
- **Water shader:** a Compatibility-safe lookalike of the stylised water J00BA asked for. That asset store shader needs Forward+ and has a proprietary licence, so it couldn't be used. The lookalike has 4 depth colour bands from a per-rect depth map (built in `game_world.gd` `_make_water`), shore foam, a fade to clear at the waterline, 0.04 m vertex waves and toon sparkles.
- **Sky and day/night:** `shaders/sky_day_night.gdshader` draws the gradient, pixel-stepped drifting clouds, the sun, and at night the moon and stars. The cycle is 30 minutes of day and 30 of night, with a 60 s fade. At night the one DirectionalLight3D becomes moonlight (#9fb4ff, energy 0.18), ambient energy drops to 45 % and the fog darkens. It is blended on top of the biome presets in `biome_environment.gd`. The debug flag `--night` starts at night.
- **Castle stairs** are one walkable ramp collider (about 29°) instead of six stacked step boxes.
- **Ores** only spawn on walkable ground (slope ≤ 0.3, and not at the foot of a cliff).
- **Foliage:** grass, bushes, ferns, reeds and mushrooms are about twice as dense, and flowers 1.25 times. Forest now draws 271 calls and plains 156, both at 60 fps.
- **Screenshots** of these fixes are in `docs/images/world_fixes/`.
- **Smoothing pass (soft hills, no sharp edges).** The mountain ridge noise is FBM, not ridged, at 1/160 with 3 octaves. Detail noise is 1/60. Hills, peaks, mesas, ice cliffs and swamp islands are all lower and wider. The border ring is `pow(1 - smoothstep(4, 80, e), 1.6) * (40 + low-frequency hill noise)`: rounded hills instead of spikes. Snow on the mountains starts at 55 m.
- **Post-process.** The whole grid, edge ring included, gets 5 passes of a 5×5 blur. The slope limiter then caps slopes at 24° (normal), 17° (paths) and 37° (`rugged`: the high mountain band and the edge ring). After that come 2 more blur passes and a second limiter pass. Only the 6 m round the waterfall is exempt.
- **Soft shores.** Each water rect has a wet mask with a noisy 6 ± 4 m margin, so there are no straight lines. Sides that meet the edge ring or another water rect have no margin. A chamfer distance transform shapes a 1:8 shelf under the water, down to 1.4 m deep. On land, a bank rises from the waterline. Within 12 m of the water the land rises at most 0.3 m per 2 m cell, and the first wet cells are raised to meet it. Both sides stay at least 0.1 m clear of the waterline.
- **Swamp path.** Through the water it now blends up to `level + 0.35` over 2.5 to 7 m, instead of a raised strip with square edges.
- **Water shader.** The depth map is 2 px per metre and sampled in smooth world coordinates. The colour is a smooth shallow-to-deep gradient. Foam is a soft half-strength band, and alpha fades out over the first 22 cm of depth, which hides the triangle edge at the waterline. There are fewer sparkles and smaller waves.
- **Water kept through the smoothing.** Cells that were under water before the blur get their carved height back afterwards. Each water bed is a smooth bowl: at most 0.3 m per 2 m cell, and 1.4 m deep. The river covers 12% of its rect (11% before smoothing). The swamp covers 10% (26% before), because tiny puddles now get proper shores and merge into the land. Dry land only has to stay above a water level inside that water's rect, or within 4 m of the water. Further out the bank blends back into the land.
- **Waterfall cliff line.** The river (3 m) meets the upper pool (10 m) along x = 214. A 16 × 54 m band there is `rugged` (37°): the step up to the upper plateau. Only the waterfall's rectangle (12 × 28 m) is fully exempt. Rect sides shared with other water are open (no shore margin) only at the waterfall.
- **BAKE CHECK** after smoothing: 0 leaks, 0 cells over 30° outside the waterfall or rugged ground, path grade 16.7° (target 18°), shore step 0.30 m (target 0.3).
