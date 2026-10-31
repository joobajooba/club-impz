# World generation fixes prompt

Copy everything inside the block below into a new Claude Code session on `joobajooba/club-impz`.

```text
Fix the Godot world build in godot-game/ (Godot 4.7, gl_compatibility renderer, web export, so no Forward+ features). Base your branch on the default branch, claude/project-thread-w0l9g3.

TOKEN RULES: Everything you need is listed below with exact files, functions and values. Read ONLY the files named for each batch, and only the parts you need (use grep/sed -n). Don't read docs/*.md beyond the lines named, don't explore the repo, and don't re-read a file after editing it. Do the work in the 5 batches below. Commit after each batch. Keep replies short.

GODOT: if `godot` isn't on PATH, download the Godot 4.7.2 stable Linux x86_64 build from github.com/godotengine/godot/releases and use it headless. Re-bake: `godot --headless --path godot-game --script res://scripts/tools/bake_world_data.gd`. Check: `godot --headless --path godot-game --quit` must show no script errors.

=== BATCH 1: quick edits ===
1. Keys (godot-game/project.godot, [input] section): toggle_debug F3 becomes key 3 (physical_keycode 51, unicode 51). debug_next_biome F4 becomes key 4 (physical_keycode 52, unicode 52). Add 3 actions: toggle_day_night = key 5 (53), toggle_fast_sprint = key 6 (54). Copy an existing InputEventKey line as the template. Update the comment and label text in scripts/debug_overlay.gd ("3 overlay  4 next biome  5 day/night  6 fast sprint").
2. Fast sprint (scripts/player/imp_player.gd): add `var fast_sprint := false`. Pressing toggle_fast_sprint flips it, in _unhandled_input. In _physics_process, sprint speed is sprint_speed * 5.0 when fast_sprint is on, and normal when it's off.
3. Swamp path (data/biomes.json): biomes.swamp.terrain.path is 27 (swamp_boardwalk), change it to 5 (forest_dirt). Leave layer_files alone.
4. Castle stairs (scripts/world/hub_castle.gd, the `for k in 6` loop in _ready): the 6 stacked step boxes are vertical walls that CharacterBody3D can't climb (the castle is shown at 2.5x, so each step is about 0.23 m). Replace the loop with ONE ramp: a ConvexPolygonShape3D wedge covering the same footprint, x from -15 to 15, z from -56 (y 0) to -40 (y 9), in Blockbench units * U, so the slope is about 29 degrees. The visual model stays as it is.
5. Ores (scripts/world/resource_landmarks.gd, _ore_spot_ok): ores currently pick cliff faces (mountain slope > 0.25, forest slope > 0.12, frost z < -130). Make ores spawn only on walkable ground: reject slope > 0.3. Also reject the spot if any of 4 samples 3 m away has slope > 0.45 (the foot of a cliff). Apply this before the `relaxed` early return. Change the per-biome match to: forest `slope > 0.06 or m.g > 0.3`, mountain `h > 26.0`, frost `z < -120.0`, plains `h > 14.0 or slope > 0.12`, swamp unchanged.
6. Foliage (data/scatter.json, the rules array): spacing words are in data/biomes.json density_spacing (carpet 1.5, dense 2.4, scattered 6, rare 22). Count scales with 1/spacing^2.
   - Double every NON-tree, NON-flower rule: give it `"spacing": <its current spacing> / 1.414`, rounded to 2 decimals. This covers all grass rules and every size alias in them (hub_grass, forest_grass, dry_grass_tuft, mountain_grass_tuft, frost_grass_tuft, tundra_grass_tuft, plains_tall_grass, plains_grass_tuft, wild_wheat_placeholder, swamp_grass_tuft) and the bushes, ferns, reeds and mushrooms.
   - Flowers x1.25 (spacing / 1.118): hub_rose, blue_wildflower, pink_wildflower, white_wildflower, rose_flower, alpine_flower_placeholder, plains_wildflower.
   - Leave the trees as they are.
Commit "batch 1".

=== BATCH 2: smoother terrain and water banks (scripts/tools/bake_world_data.gd only) ===
Heights come from height_at() per 2 m cell in _bake_resource(). The player's floor_max_angle is 46 degrees. Paths and hills are too steep, and water planes (rects in the layout "water" list, drawn by game_world.gd _make_water at a flat level) poke out over low ground. The worst case is forest_upper_pool, rect x 214..262, level 10, where the terrain falls to 3 at the waterfall.
1. In _bake_resource, compute all heights into a PackedFloat32Array first, then post-process, then write the PNG.
2. Path distance: include the branch points in path_dist as well as main_path.
3. Smooth: 3 passes of a 5x5 box blur over the grid, skipping the edge ring (cells where the edge distance e from height_at is < 46).
4. Slope limit: iterate (about 40 passes, or until nothing changes) lowering any cell that is more than `max_rise` above a 4-neighbour, down to neighbour + max_rise. max_rise = 2.0 * 0.70 (about 35 degrees) everywhere, except: the edge ring, cells with h > 70 (the high peak tops can stay as cliffs), the frost ice cliff band (x 512..768, z < -150), and 6 m around the waterfall (landmarks.waterfall). Inside path corridors (path_dist < 6 m, including branches) use max_rise = 2.0 * 0.36 (about 20 degrees).
5. Water banks: for each water rect (the same list as the layout "water"), lower every cell inside the rect whose height is below level+0.3 to at most level - 0.5, so the bed sits under the water. Then raise every cell on the rect's 2-cell border ring, and any cell inside the rect that touches an outside cell, to at least level + 0.4, so the water is always enclosed by terrain above it. For forest_upper_pool, leave the 10 m lip at the waterfall (x 214, z = river_z(214) ± 5) at level - 0.05. Run the slope limit again afterwards, but never lower a bank cell below level + 0.4.
6. Validation print at the end of the bake: the count of cells steeper than 44 degrees outside the exceptions (target 0), the max path grade in degrees (target <= 22), and the count of water cells that touch a cell below level outside their rect (target 0). If any target fails, adjust and re-bake. Max 3 tries, then report the numbers.
7. Re-bake. Commit the new data/*.png and data/*.json files with "batch 2".

=== BATCH 3: terrain textures and water shader ===
1. shaders/terrain.gdshader, end of fragment(): the "mid" layer (scree) and every non-steep layer are sampled top-down with wpos.xz / 4.0, so they stretch on slopes (mountain scree at slope 0.22 to 0.4). Replace both branches with one triplanar sample helper: weights = pow(abs(wnrm), vec3(8.0)) normalised; projections zy, xz, xy; same / 4.0 scale (keep 32 px per metre). Keep the steep layer choice logic as it is, and only change how textures are sampled. Use filter_nearest_mipmap_anisotropic on `layers` so slopes stay sharp at grazing angles. Flat ground (wnrm.y > 0.97) can take the single xz sample to save cost.
2. Water: J00BA asked for the emace-art "Stylized Water Shader" from the Godot asset store. It requires Forward+ and has a proprietary licence, so it can't be used in this Compatibility and web build. Write a lookalike in shaders/water.gdshader instead (keep the `flow` waterfall mode working):
   - Shallow-to-deep colour bands (4 bands) from water depth = level - terrain height. Pass the depth in from GDScript, with no depth texture: in game_world.gd _make_water, build a small FORMAT_RF ImageTexture per rect from terrain.data.height() at 1 m per pixel and pass it as `depth_map` plus `rect` (vec4).
   - Animated shore foam where depth < 0.35 (stepped noise, scrolling), soft fade to 0 alpha at depth 0.
   - Gentle vertex waves (amplitude 0.04): subdivide the PlaneMesh at 1 vertex per 2 m.
   - Toon specular sparkles: step() on the noise + view angle. Pixel snapping to the 32 px per metre grid as now.
   - Uniforms for shallow_color, deep_color (the deep colour is the biome's current water colour), foam_color.
Commit "batch 3".

=== BATCH 4: sky, clouds, day and night (scripts/environment/biome_environment.gd) ===
setup() uses a ProceduralSkyMaterial, and _apply(v) sets the sky colours and the sun from the biome presets in data/biomes.json env.
1. New shaders/sky_day_night.gdshader (shader_type sky): a gradient from uniforms sky_top, sky_horizon and ground; moving clouds (2 octaves of fbm on the sky dome projected dir.xz / dir.y, scrolling with TIME, pixel-stepped edges). A sun disc from LIGHT0_DIRECTION. Uniform `night` (0..1): at night, darken the gradient to deep blue, show a moon disc opposite the sun with a soft glow, and bright twinkling stars (hash on a direction grid, only above the horizon). Clouds turn dark grey-blue at night.
2. Swap sky_mat for a ShaderMaterial with that shader. _apply sets its uniforms instead of the ProceduralSkyMaterial properties.
3. Day and night cycle: day lasts 30 minutes, then night lasts 30 minutes (`const HALF_CYCLE := 1800.0`). Fade over the last 60 s of each half. Keep one DirectionalLight3D (one shadow pass for the web build): at night it becomes moonlight (#9fb4ff, energy 0.18, angled to the moon), ambient energy x0.45, and fog colour darkened. Blend this on top of the biome preset inside _apply, so biome fades still work.
4. Key 5 (toggle_day_night) flips day and night straight away (a 2 s fade) and restarts the 30 minute timer. Handle it in biome_environment.gd _unhandled_input.
Commit "batch 4".

=== BATCH 5: check and document ===
1. Run `godot --headless --path godot-game --quit` with no errors. Then take screenshots at 1280x720 with the existing flags (main.gd header): `--world=resource --biome=forest --shot=res://../docs/images/world_fixes/forest.png`, the same for mountain and swamp, plus `--world=hub --shot=res://../docs/images/world_fixes/hub.png`. Look at them once to check the water edges, the mountain textures and the swamp path. Run `--perf=4` in forest and plains. If FPS is below 55, lower foliage_view_distance in biomes.json in steps of 4. Don't drop the density.
2. docs/world_build_notes.md: in section 1.1 Controls, change rows 28 and 29 (F3 and F4 become 3 and 4) and add rows for 5 and 6. Add one short section "9. World generation fixes" listing what changed (5 to 10 bullets). Don't rewrite other sections.
3. Push and open a PR into claude/project-thread-w0l9g3 with a short summary, and commit the 4 screenshots in docs/images/world_fixes/.
```
