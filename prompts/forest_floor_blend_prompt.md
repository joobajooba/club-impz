# Blend the forest floor textures smoothly

Repo: `joobajooba/club-impz`. Follow the GitHub workflow in the root `CLAUDE.md`: branch `staging/forest-floor-blend` from the default branch and open a draft PR. Keep the change small.

## Problem

`docs/images/forest_floor_blend/forest_floor_seam.png`: in the forest, the green `forest_grass` meets the `forest_leaf_litter` in a hard, almost straight line. It should fade from one to the other over a few metres.

## Why it happens

- `godot-game/shaders/terrain.gdshader`, `fragment()`: litter is an on/off pick, `m.a > 0.5 + (d2 - 0.5) * 0.2`. The dither only moves the edge a few centimetres, so it reads as a line. The dry grass patch rule (`patch_threshold`) works the same way.
- `godot-game/scripts/tools/bake_world_data.gd` (about line 318): litter is `clampf(n_litter * 1.6 + 0.1)` in a 1 m per pixel mask that the shader samples with linear filtering. Its 0.5 contour runs in straight segments between mask pixels, which is the straight line in the screenshot.

## Fix

1. **Shader.** For the litter and dry grass patch edges, turn the threshold into a weight over a band about 3 m wide (`smoothstep`), and push the mask value with small world-space noise (`vnoise` at about 1 to 2 m) before the smoothstep, so the edge stops following the mask grid. Inside the band, sample both layers and pick per texel with a height blend: compare each texel's luminance plus its weight, then add the existing clumped dither. Leaves and grass blades poke into each other first, and every pixel stays a whole texel of one layer. Only sample twice inside the band.
2. **Bake.** Soften the litter edge: `smoothstep(-0.15, 0.45, n_litter + n_detail at 2x frequency * 0.15)` instead of the clamp. Re-bake `data/resource_mask.png` (`godot --headless --path godot-game --script res://scripts/tools/bake_world_data.gd`).

Keep the rule in `docs/terrain_textures.md` section 4.2: blends happen in pixel steps on the 64 px per metre grid, never a soft colour fade. Don't touch paths, slopes, biome borders or the hub.

## Check

- `godot --headless --path godot-game --quit` prints no errors.
- Screenshots before and after of a forest spot like the one in the reference (`--world=resource --biome=forest`, flags in the header of `scripts/main.gd`), plus one close-up (`--zoom=4`) to show the pixels are still crisp. Put them in `docs/images/forest_floor_blend/` and in the PR.
