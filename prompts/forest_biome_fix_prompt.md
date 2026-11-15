# Forest biome fix prompt

Copy everything inside the block below into a new Claude Code session on `joobajooba/club-impz`.

Why: J00BA's screenshots (in `docs/images/forest_biome_fix/`) show four problems in the forest.

1. `path_up_cliff.png`: the main dirt path runs straight up the face of the cliff. The baked data shows why. That cliff is where the forest meets the mountain band (x 230 to 300). The main path climbs it on a flattened ramp (7.4 m at x 200 to 27 m at x 300, a grade of 0.3), and `_stamp_path` paints dirt on every metre of it. From the forest, the ramp reads as a dirt stripe up the cliff. J00BA wants paths to stop at the bottom of cliffs and mountains.
2. `pond.png`: the upper pool above the waterfall (the one with the swans) holds only about 204 m² of water, x 214 to 230 and z 54 to 68. That's because it's only the river channel (`h_forest`, 9 m wide), and the wet mask keeps 6 ± 4 m of land inside every rect border. J00BA wants it much larger, spreading over the meadow circled in the screenshot (north and east of the water).
3. `cliff_tops.png`: the tops of those same cliffs are rolling hills, which looks low quality. The mountain band's top is `h_mountain` ridge noise (27 to 100 m). Five blur passes and the 24° slope limit (the face is under 40 m, so it isn't `rugged`) round the rim into a 30 m roll. J00BA wants flatter, smoother tops.
4. `map_edge_gap.png`: at a forest border, the cliff wall stops and a grassy slope runs on past the world's edge beside a grey mountain, so players can walk out of the map. The straight line where the forest leaf litter stops is the world border (the shader draws mask = 0 outside it). The baked skirt in the repo looks sealed: a flood fill over `resource_skirt.png` at a 46° limit gets no further than 16 m out. So the gap is either in how the game builds the ground out there or in a build J00BA has that differs. Batch 1 finds the spot before anything is changed.

```text
Improve the forest biome in godot-game/ (Godot 4.7, gl_compatibility renderer, web export). Base your branch on the default branch, claude/project-thread-w0l9g3. Follow the repo CLAUDE.md GitHub workflow: branch staging/forest_biome_fix, draft PR. Pull first. If the line references below have moved, follow the intent and the target numbers, not the exact lines. J00BA's four screenshots are in docs/images/forest_biome_fix/. Look at each one once before batch 1.

WHAT J00BA ASKED FOR (do these and nothing else):
A. Dirt paths stop at the bottom of mountains and cliffs. They don't run up the face.
B. The upper forest pool (the swan pond above the waterfall) is much larger, with more water.
C. The cliff tops are flatter and smoother, with no rolling hills along the top.
D. The gap in the forest border where players can walk out of the map is sealed.

TOKEN RULES: Everything you need is listed below with exact files, functions and values. Read ONLY the files named for each batch, and only the parts you need (use grep/sed -n). Don't read docs/*.md beyond the lines named, don't explore the repo, and don't re-read a file after editing it. Do the work in the 6 batches below. Commit after each batch. Keep replies short.

GODOT: if `godot` isn't on PATH, download the Godot 4.7.2 stable Linux x86_64 build from github.com/godotengine/godot/releases and use it headless. Re-bake: `godot --headless --path godot-game --script res://scripts/tools/bake_world_data.gd`. Check: `godot --headless --path godot-game --quit` must show no script errors. Screenshots: `-- --world=resource --at=x,z --yaw=.. --pitch=.. --zoom=.. --shot=res://../docs/images/forest_biome_fix/<name>.png` (flags are listed in the header of scripts/main.gd; cam_yaw = atan2(-fwd.x, -fwd.z) in scripts/player/imp_player.gd).

THE SYSTEMS (all in scripts/tools/bake_world_data.gd unless named):
- Layout: main_path follows path_z(x) from x 36 to 1240. Branches run from the main path to each landmark (_build_resource_layout). path_dist is the distance to the nearest path on the 2 m grid.
- Heights: height_at() blends the biome functions (h_forest, h_mountain, ...) by the warped depth s = warped_s(x, z). Bands are 256 wide with a 22.5 blend each side, so forest to mountain is s 233.5..278.5. In x 200..560, the main path is flattened to the pass height ph = 8 + smoothstep(240, 300, x) * 14 (about 27 m on top), using smax/smin, and fades back over smoothstep(7, 48, d_path).
- _post_process: kind per cell (0 normal 24°, 1 path 17°, 2 waterfall exempt, 3 rugged 37° = mountain band cells over 40 m, plus _in_fall_cliff). Then 5 passes of _blur5, _slope_limit, 2 passes of _blur5, _slope_limit, _recarve, _shape_water (which ends with _soften and _validate, the BAKE CHECK prints).
- Mask (1 m per pixel, built after the heights, so hs is available): R path (_stamp_path, radius 2.6 main and 1.7 branches), G wet, B special, A litter. The terrain shader (shaders/terrain.gdshader around line 143) draws the path layer wherever m.r > 0.5 and turns steep off there.
- Water: WATER const. forest_upper_pool is rect [211, 40, 262, 120], level 10.0. forest_river is [0, 40, 211, 120], level 3.0. _shape_water step b keeps a noisy 6 ± 4 m margin of land inside every rect side that isn't shared with other water. Step e is the waterfall notch (lip_z = river_z(214) = 63) and the bank of at least 10.5 m over x 209..216, z 36..124.
- Skirt: _skirt_rise / _bake_skirt (4 m samples, resource_skirt.png). In game, scripts/terrain/world_data.gd skirt_height() (Catmull-Rom, blended to the border height over 8 m) feeds one ring of 64 m detailed chunks with colliders outside the border (scripts/terrain/terrain_world.gd, margin = 1), and the far mesh (8 m lattice, no collider) beyond. The invisible safety walls stand WALL_OUT = 34 m outside the border (_build_walls). The player can climb 46° (imp_player.gd floor_max_angle).

=== BATCH 1: see it first ===
1. Take before shots (1280x720) and look at each once:
   - before_path.png: --at=150,13, facing +x (east along the main path), pitch -0.1. It should match path_up_cliff.png: a dirt stripe running up the cliff face ahead.
   - before_pond.png: --at=232,36, facing +z (south over the pool), pitch -0.45. It should match pond.png: a small pool by the waterfall crest.
   - before_tops.png: --at=170,-40, facing +x, pitch 0. It should match cliff_tops.png: a rolling, hilly skyline along the cliff top.
2. Find the map edge gap. Write a small headless tool script, scripts/tools/edge_check.gd, that loads WorldData("resource") and flood-fills from every border cell outward over data.height() on a 1 m grid. It may step only where the rise is at most tan(46°) per metre. It prints every reachable cell more than 6 m outside the border, grouped into 32 m spots (border side, x, z, how far out, height). It must use data.height(), the same function the chunk meshes and colliders use, not the baked PNG. Also check the four corners, the chunk ring's outer edge at 64 m (where the colliders end and the far mesh, which has no collider, takes over) and the seams between margin chunks.
   - Then match J00BA's map_edge_gap.png. The player stands on the border with forest litter on the left and grass outside on the right. A brown cliff ahead and to the left ends in a straight vertical edge. On the right is a grey mountain. So it's a forest border, x 0..256 on the north side (z -256) or south side (z 256), or the west side (x 0). Take a shot at each spot the tool reports, plus one at each forest corner looking along the border. Name them gap_<n>.png and find the one that matches.
   - If the tool finds nothing and no shot matches, stand the player at the border in the forest's four directions with --bot style walking (or a short scripted walk outward at each forest border spot every 32 m) and log the furthest point reached outside. Report it and go on. Batch 5 seals the border either way.
3. Measure and print the starting numbers for the report: upper pool wet area (m²), plateau roughness (batch 2 check), the number of path mask pixels on the climb (batch 4 check), and the reachable cells outside the border.
Commit "batch 1" (the tool and the before shots).

=== BATCH 2: flat cliff tops (C) ===
Goal: seen from the forest, the mountain band is a cliff that rises from the forest floor to a level tableland. The rim is clean, and the real peaks (highest_peak and the ridge at 470, -60) stand further back. No rolling hills along the top.
1. In height_at(), after the biome blend and before the pass clamp, flatten the near part of the mountain band into a plateau:
   - plateau_h = 27.0 + n_hill.get_noise_2d(x * 0.35, z * 0.35) * 1.5. The 27 m matches the main path's pass height, so the path meets the top level. The broad, gentle noise keeps it from looking like a ruler.
   - The weight w rises from 0 at warped s 248 to 1 at s 262 (smoothstep), stays 1 to s 330, and fades out over s 330..380. Beyond that, h_mountain's peaks rise as they do now. h = lerp(h, plateau_h, w): the top is level ground cut from the hills, and the 14 m ramp-in of w is the face, which ends in the rim instead of rolling over.
   - The face, from the forest floor (about 12 m at s 234) up to the plateau: below s 248 keep the existing forest-to-mountain blend. The rim must be rounded over about 3 m, not 30 (batch 2 step 3 keeps it that way after the blur).
   - Keep the landmarks flat where they stand: standing_stones (330, 118) and the obsidian_cave branch must still sit on level ground. Check their height after the bake: the standing stones at 27 ± 1.5 m.
2. In _post_process, mark the face as rugged (kind 3) wherever the warped s is 228..268 and the cell isn't a path corridor (kind 1) or the waterfall (kind 2). The face then keeps 37° and isn't flattened to a 24° ramp. Keep everything else as it is.
3. The blur rounds the rim again. After the last _slope_limit and before _recarve, re-apply the plateau from step 1 (h = lerp(h, plateau_h, w) where s > 266, rim rounded with smin(h, plateau_h, 2.0)), so the top stays level and the rim stays crisp. Run _slope_limit once more afterwards so no cell breaks its limit.
4. Don't touch the skirt (_skirt_rise, _bake_skirt), h_mountain's peaks beyond s 380, or the frost, plains or swamp.
5. Add a BAKE CHECK plateau line: the standard deviation of height over plateau cells (w = 1, s 270..325, not path) with a target under 1.0 m, the share of plateau cells steeper than 10° with a target under 3%, and a rim check. For 20 lines across the rim, evenly spaced in z from -230 to 230, measure the distance from the last cell steeper than 30° to the first cell flatter than 8°, with a target of 8 m or less.
6. Re-bake and commit the data with "batch 2".

=== BATCH 3: a bigger swan pond (B) ===
Goal: the upper pool is at least 4 times larger (about 800 m² or more, from 204 m²). It spreads north and east over the meadow J00BA circled, with a natural, uneven shore. The waterfall crest stays where it is.
1. h_forest: dig a pond basin for the upper pool. Use an ellipse centred at (232, 52) with radius 18 m in x and 20 m in z, so roughly x 214..250 and z 32..72. Wobble its edge by ±3 m with n_detail.get_noise_2d(x * 1.5, z * 1.5), so it isn't an oval. The bed is 10.0 - 1.6 = 8.4 in the middle, shelving up to the level over the outer 6 m. The shore rises from 10.0 to 10.8 over 4 m beyond the edge, then meets the meadow. Merge it with the existing channel carve using minf, so the channel and the notch don't change.
2. WATER: change forest_upper_pool's rect to [211, 26, 262, 120]. With the 6 ± 4 m margin in step b, the water can then reach about z 32. Don't move the shared x 211 side.
3. Keep the bank in _shape_water step e (x 209..216, at least 10.5 outside the notch) and check that the new basin doesn't cut into it. The pool's west shore must stay at x 216 or more, except at the notch.
4. The main path runs at z 15..18 here. Keep the shore (the outer edge of the 4 m rise) at least 10 m from the path's edge, and pull the basin's north edge in if it doesn't fit. After batch 2, check that the basin's east side doesn't run into the cliff face. If it does, stop the basin 6 m short of the face's foot.
5. scripts/world/resource_landmarks.gd line 56: forest_upper_pool swans 2 becomes 4.
6. data/scatter.json: check that the forest reeds and fern rules (forest_reeds_placeholder, forest_fern_placeholder) and waterfall_bank_plants grow round the new shore with the same rules as other shores. Don't add rules.
7. Add the upper pool's wet area (m²) to the BAKE CHECK print (target 800 or more). Edge leaks, water leaks and the max shore step must still pass (0, 0, 0.3 m or less). Fix and re-bake until they pass (max 3 tries, then report the numbers).
8. Re-bake and commit with "batch 3".

=== BATCH 4: paths stop at the foot of cliffs and mountains (A) ===
Goal: no dirt runs up a cliff or mountain face. A path ends at the bottom of the climb, and the climb shows the ground around it. Where the route carries on over the top (the main path across the mountain band to the frost), the dirt picks up again once the ground is level on top. The terrain doesn't change in this batch, so the ramp the player walks up stays. Only the dirt texture stops.
1. In _bake_resource, before the _stamp_path calls, work out which stretches of each path polyline are a climb. Use the baked hs (_h_at). For each point, take the grade over the 8 m around it along the path: |h(next 4 m) - h(previous 4 m)| / 8. A climb is any run where that grade is over 0.15 (about 8.5°) and the height changes by more than 3 m over the whole run. Shorter bumps and dips keep their path.
2. Pass a per-point weight to _stamp_path. It's 0 on a climb, rises back to 1 over 4 m at each end, and is ragged with n_detail so the path doesn't end in a straight line. In _stamp_path, multiply v by the weight at the nearest polyline point.
3. Water crossings: if a climb is a river bank (the run is within 6 m of a water rect where the path dips into the bed), leave it alone, because the path has to reach the water's edge. Today that's the worldbark_grove branch where it crosses the river.
4. Add a BAKE CHECK path line: path mask pixels (R > 0.5) on cells whose slope along the path is over 0.15, with a target of 0. Also list which paths were cut, with the x/z of the start and end of each cut. Expected: the main path at about x 236..300, and the frozen_waterfall branch (grade 0.32). Report anything else it cuts.
5. Re-bake and commit with "batch 4".

=== BATCH 5: seal the border (D) ===
1. Fix the cause found in batch 1:
   - If it's the terrain (a gully or a low saddle in the skirt): in _skirt_rise, make the wall rise at least 20 m within 14 m of the border everywhere. Clamp the gully term so a ravine can't open a walkable floor (the gully may cut into the face, but its floor must stay steeper than 50°). Also make sure the corners use the same rise (d to the clamped point already does this. Check that the Catmull-Rom in world_data.gd skirt_height() doesn't undershoot near a corner).
   - If it's in game (a missing or misplaced margin chunk, a seam between the ring and the far mesh, or colliders missing outside the border): fix that in terrain_world.gd so every margin chunk has its mesh and collider while the player is within 64 m of it.
   - If the spot only exists in J00BA's build and not in this branch, say so in the report with the edge_check numbers.
2. Safety net (always do this): move the invisible walls in from WALL_OUT 34 to just outside the shelf at the cliff foot, at the minimum shelf width minus 0.5 m (the shelf is 2 to 4.5 m, so about 1.5 m). The world then can't be left even if a gully opens later. Keep them 2000 m tall. Check that the portal clearing (36, 0) and the west foothills are still free to walk in and that no landmark or scatter sits on a wall.
3. Run edge_check.gd again: the target is 0 reachable cells more than 3 m outside the border. Re-take the matching gap shot as after_gap.png. The cliff must run on unbroken, and walking into the old gap must stop at the border.
4. Commit with "batch 5".

=== BATCH 6: check and document ===
1. `godot --headless --path godot-game --quit` with no errors. Retake the batch 1 shots with the same flags as after_path.png, after_pond.png and after_tops.png. Look at each once. Pass if:
   - The dirt path ends at the bottom of the cliff, and there's no stripe up the face.
   - The pond is clearly bigger, fills the meadow north and east of the old pool, has an uneven shore and no straight water edges, and the waterfall still pours from the crest.
   - The cliff top reads as a level edge with peaks only further back, and no rolling bumps along the rim.
   - The map edge is sealed.
   Fix anything that fails once, then report.
2. Walk it with the player (not camera mode): up the main path ramp to the plateau and across to the standing stones, all the way round the new pond shore, and along each forest border. No falling through, no getting stuck, no standing on water, no leaving the map.
3. Run `--perf=4` with --at=232,52. FPS must not drop more than 3 from the before number.
4. docs/world_build_notes.md: update the "Walkable terrain" line (around line 210), the "Water banks" line (around line 211) and the "Post-process" line (around line 224) to describe the plateau, the bigger upper pool, paths stopping at climbs and the walls at the cliff foot. Don't rewrite other sections.
5. Push staging/forest_biome_fix and open a draft PR into claude/project-thread-w0l9g3. Include a short summary, the BAKE CHECK numbers before and after, the before and after screenshots, and where the map edge gap was and what caused it.
```
