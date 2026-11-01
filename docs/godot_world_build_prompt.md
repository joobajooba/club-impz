# Godot World Build Prompt

> Status: draft v1 · Owner: J00BA · Last updated: 2026-10-30
>
> A ready-to-paste prompt that asks Claude to build the first playable version of the Club Impz worlds in Godot: a walkable imp, the hub world and the resource world with five biomes (forest, mountain, frost, plains, swamp), painted with the terrain textures and filled with the existing models. Void and stellar, multiplayer, Supabase and wallets come later.

---

## How to use it

Start a Claude Code session on this repository and paste **either** of these:

- The short version: `Read docs/godot_world_build_prompt.md and do the build in its "The prompt" section.`
- The full prompt in the box below (copy everything inside it).

Claude works in milestones and commits after each one, so you can stop it, look at the result in Godot and ask for changes between milestones.

---

## The prompt

````text
You are building the first playable version of the Club Impz worlds in Godot. The repo is joobajooba/club-impz. Open the Godot project in godot-game/.

READ FIRST (these markdown docs are the source of truth; follow them exactly and don't contradict them):
- docs/game_direction.md (the game; wins over every other doc)
- docs/game_worlds.md (the two worlds, art style, biomes in section 4.8, Godot notes in 4.9, plants in 4.10)
- docs/terrain_textures.md (the 28 terrain textures, layer order and blend rules)
- docs/blockbench_detailed_prompts.md sections 1.3 (scale), 1.5 (textures), 1.8 (folders) and 3.4.5 (wind)
- docs/resource_gathering.md (only to place ore and tree nodes in the right biomes; no gathering yet)
If you need to choose something the docs don't cover, make a sensible choice, write it down in the build notes (see DELIVERABLES) and keep going.

GOAL
A small, good looking, walkable slice of the game that runs in the browser:
1. A placeholder imp the player walks around with a third person camera.
2. The hub world: a village with a castle, a cobbled square and dirt paths.
3. The resource world: one smooth heightmap terrain with five biomes in depth order forest -> mountain -> frost -> plains -> swamp, each with its own ground textures, trees, foliage, ore node placeholders, sky, fog, light, water and ambient particles.
4. Portals that move the player between the hub and the resource world.

OUT OF SCOPE FOR NOW (don't build these, but don't block them either): void and stellar biomes, multiplayer, chat, Supabase, wallets and NFTs, gathering, skills, inventory, mobs and AI, crafting, shops, UI beyond a small debug overlay.

HARD RULES
- Godot 4, latest stable release (4.5 or newer), GDScript only.
- Renderer: Compatibility (gl_compatibility). The game ships as a Godot web export, so everything must work in the Compatibility renderer and in a web build: no volumetric fog, no SDFGI, no compute shaders, no GPU particle features the Compatibility renderer lacks (use CPUParticles3D if in doubt).
- Web export without thread support (so it runs on any static host without special headers).
- Every file and folder name is lowercase with _ instead of spaces. Node names in scenes are snake_case too.
- Keep it light for the browser (game_worlds.md section 2.2): MultiMeshInstance3D for foliage, visibility ranges for trees, rocks and foliage, small shared textures, a draw distance that fits each biome's fog.
- Pixel textures stay crisp: every model and terrain texture uses Nearest filtering with mipmaps. Never use linear filtering on game art.
- Don't edit the .bbmodel files or the PNG textures. If a model or texture is missing, use a placeholder and list it in the build notes.
- Commit after each milestone with a clear message.

PROJECT LAYOUT (create what's missing)
godot-game/
  project.godot
  assets/            (exists: models/, textures/, sprites/)
  scenes/            main.tscn, hub/hub_world.tscn, resource/resource_world.tscn, player/imp_player.tscn, shared/portal.tscn
  scripts/           player/, world/, terrain/, environment/, tools/
  shaders/           terrain.gdshader, foliage_wind.gdshader, water.gdshader
  data/              biomes.tres (or .json), world layout images
tools/               Python helpers that run outside Godot (generate_terrain_textures.py already lives here)

Main scene: main.tscn, which loads the hub world first (every player spawns in the hub, game_worlds.md section 1).

MILESTONE 1: PROJECT, IMP AND CAMERA
- Create project.godot with the Compatibility renderer, the default texture filter set to Nearest with mipmaps, physics at 60 ticks, and a Web export preset (threads off) in export_presets.cfg.
- Input map: move_forward (W, up), move_back (S, down), move_left (A, left), move_right (D, right), jump (space), sprint (shift), camera_orbit (right mouse button), camera_zoom_in and camera_zoom_out (mouse wheel).
- scenes/player/imp_player.tscn: CharacterBody3D with a capsule collider and a placeholder imp built from a few BoxMesh parts so it reads as the base imp from blockbench_detailed_prompts.md section 1.2: a big cube head with giant dark eyes and white highlight pixels, pointy ears sticking out sideways, a small leafy tuft, a short green body (imp green skin ramp from section 5) and stubby limbs. Total height 18 Blockbench units = 1.125 m (16 units = 1 m). Keep the visual in a child node named visual so a real imp model can replace it later.
- Movement relative to the camera, smooth turning to face the move direction, gravity, a small jump, walk about 4 m/s and sprint about 6.5 m/s, slopes up to about 45 degrees, simple bob or squash animation while walking.
- Third person camera: SpringArm3D behind and above the imp, orbit with right mouse drag, zoom with the wheel (about 3 to 14 m), no clipping through terrain, smooth follow.
- A tiny debug overlay (F3 toggles): FPS, player position, current biome.
- Test on a flat test ground, then commit.

MILESTONE 2: IMPORT THE BLOCKBENCH MODELS
Godot can't read .bbmodel files. Write tools/bbmodel_to_gltf.py (Python 3, numpy and pillow allowed) that converts every .bbmodel under godot-game/assets/models/ into a .glb next to it with the same name:
- Format is Blockbench 5.0 "free" with per-face UVs. Each element is a cube with from, to, origin (pivot) and rotation (degrees, X then Y then Z as Blockbench applies them), plus groups in the outliner with their own origin and rotation. Apply group transforms down the hierarchy.
- Faces: north, east, south, west, up, down. Skip faces whose texture is null. UVs are in pixels of the texture resolution (resolution.width and height); flip V for glTF. Respect UV rotation if a face has one.
- Zero-thickness cubes are alpha cards (foliage): emit both sides (or a double sided material).
- Units: 16 Blockbench units = 1 metre, so scale by 1/16. Keep the model standing on y = 0.
- Texture: use the embedded texture (or the matching PNG in godot-game/assets/textures/<group>/). Material: unshaded off, alpha scissor (hard alpha) for foliage and leaves, Nearest filtering, cull disabled only for cards.
- Cubes whose names end in _glow get a separate emissive material (game_worlds.md section 4.9).
- Skip elements with export false (the scale_dummy) and skip animations for now.
Run it on all models (trees, foliage, mobs), check a few in Godot next to the imp for scale, and commit the converter and the .glb files.

MILESTONE 3: TERRAIN SYSTEM
Build a custom chunked heightmap terrain that works in the Compatibility renderer (Terrain3D is not needed; game_worlds.md section 4.9 allows a custom heightmap mesh):
- Heights come from a deterministic generator (FastNoiseLite with fixed seeds) shaped per biome, so the world is the same every load. Bake the result to data images (height, biome weights, path mask) with an editor tool script so J00BA can later repaint them, and load those at runtime.
- Chunks of 64 x 64 m with 2 m vertex spacing (smooth terrain, not blocks), a HeightMapShape3D collider per chunk, and only chunks near the player visible (fog hides the rest).
- Smooth normals. No stepped or voxel ground: the pixel look comes from the textures (game_worlds.md section 4.7).
- Terrain material (shaders/terrain.gdshader):
  - All 28 textures in one Texture2DArray in the exact layer order from docs/terrain_textures.md section 2, built with Texture2DArray.create_from_images() after generating mipmaps. Sampler: filter_nearest_mipmap, repeat_enable.
  - UV from world position: world.xz / 4.0 (one 128 px tile = 4 m, 32 px per metre). Triplanar for the rock layers on steep slopes.
  - Choose layers per biome with the rule table in terrain_textures.md section 4.2: base, noise patches, steep slopes (from the normal), high ground (from height), low and wet ground, and paths (from the path mask).
  - Biomes blend over a 30 to 60 m border. Blend in pixel steps snapped to the 32 px per metre grid (dithered or height based), not a soft fade, so transitions keep the pixel look.
  - Keep it cheap: only evaluate the two strongest biomes at any point.
- Water: a flat plane per lake or river with shaders/water.gdshader (biome water colour from game_worlds.md section 4.8, gentle pixel ripples, no screen space refraction).

MILESTONE 4: HUB WORLD
scenes/hub/hub_world.tscn, about 200 x 200 m, on its own small terrain using the hub layers (hub_grass, hub_dirt_path, hub_cobblestone):
- Landmarks from game_worlds.md section 3.3: spawn point, village square (cobblestone, the main hangout), market stalls, crafting area, the castle as the centrepiece (scenery only), and the portal to the resource world.
- There's no castle, building or stall model yet: block them out with simple, clean placeholder meshes in the right size and colour (stone grey castle with towers, wooden stalls with cloth roofs, a smelter and workbenches), each in its own scene so the real Blockbench models can replace them later.
- Dirt paths link spawn, square, market, crafting area, castle and portal. A low wall or hills around the edge keep players in.
- Lush but tidy foliage: forest grass tufts, bushes and the rose flower along paths and around buildings, a few oak and birch trees.
- No resource nodes and no combat in the hub (game_worlds.md section 3.1).
- Bright, friendly sky and light (start from the forest values in section 4.8.1).

MILESTONE 5: RESOURCE WORLD AND BIOMES
scenes/resource/resource_world.tscn:
- Layout: about 1280 x 512 m. Five bands in depth order from the start: forest -> mountain -> frost -> plains -> swamp, each about 256 m deep, with noise-warped borders and 30 to 60 m blend zones. The portal clearing back to the hub is at the start of the forest. Ring the edge with tall mountains or water so players can't walk off the map.
- Leave room past the swamp for void and stellar later (they are floating islands, so they will be separate meshes).
- Shape each biome's terrain from its Terrain row in game_worlds.md section 4.8: forest gentle hills with a winding river and a waterfall; mountain tall peaks (visible from the forest), cliffs, passes, scree and snowy tops; frost wide snowfields with wind ripples, a frozen lake and ice cliffs; plains flat to rolling grassland with mesas, a stone arch and dry riverbeds; swamp flat mud flats with shallow pools and small raised islands.
- A main path runs through every biome from the portal to the far end (forest_path -> mountain_path -> frost_packed_snow -> plains_path -> swamp_boardwalk), with branches to each landmark.
- Landmarks from each biome's Landmarks row (placeholders are fine: the worldbark grove can be very large scaled oak placeholders, the highest peak, standing stones, the frozen waterfall, the giant stone arch, the giant hollow swamp tree). Each one must be visible from far away.

Placement (deterministic, seeded scatter driven by data in data/biomes, not hand placed one by one):
- Trees from game_worlds.md section 4.5 using the converted models: pine_tree, birch_tree and oak_tree in the forest; maple_tree, maple_tree_2 and maple_tree_3 in the mountain valleys. Trees without a model yet (hickory, frostbark, titanwood, runewood, gembark, worldbark) get a recoloured or rescaled placeholder from the existing trees, named with the real id (for example hickory_tree_placeholder) and listed in the build notes. Snow loaded trees in frost can use a white tinted canopy.
- Trees: one MultiMesh or instanced scene per tree type per chunk, with visibility ranges, a simple trunk collider, and the wind shader on the leaves.
- Ore nodes from section 4.4 (coal, tin, copper, iron, gold, obsidian, titanite, dreadstone): there are no ore models yet, so make one placeholder scene per ore (a lumpy grey rock of a few boxes with chunky crystals in the ore colour from blockbench_detailed_prompts.md section 3.2) named <ore>_vein_placeholder. Place them where section 4.8 says (rock outcrops and riverbanks in forest, cliffs and caves in mountain, ice cliffs in frost, mesas in plains, muddy banks in swamp). Put obsidian near a volcanic vent or cave mouth in the mountain and dreadstone in the most toxic swamp area.
- Foliage from section 4.10 with the density words (carpet, dense, scattered, rare) turned into real spacing numbers. Use the existing foliage models (forest_grass_tuft_small, _medium, _large, forest_grass_carpet, green_leafy_bush_small, _large, red_mushroom_group, brown_mushroom_group, rose_flower). For other biomes, recolour the grass tufts to the biome's grass ramp (section 4.10: one plant shape serves several biomes) and use simple placeholders for anything else. Foliage is MultiMeshInstance3D per chunk, with a short visibility range (about 40 to 60 m) and fading out.
- No foliage on paths, water or steep rock.
- Wind: shaders/foliage_wind.gdshader on all trees and foliage, stronger in plains and mountain (game_worlds.md section 4.9).

Environment per biome (scripts/environment/):
- One environment preset per biome from the Sky and light and Fog rows in section 4.8 (sky top and horizon colours, sun colour and angle, fog colour and density). Swamp has the densest fog, plains a golden haze, mountain a pink and peach haze.
- An Area3D per biome; when the player crosses a border, fade the WorldEnvironment and sun to the new biome over a few seconds. Depth and height fog only (no volumetric fog in web builds).
- One ambient CPUParticles3D emitter per biome that follows the player: pollen and seeds (forest), mist and falling leaves (mountain), snow (frost), dust and grass seeds (plains), fireflies and spores (swamp).
- Ambient sound hooks per biome (empty AudioStreamPlayer nodes with the right names are fine; no sound files yet).

MILESTONE 6: PORTALS AND POLISH
- scenes/shared/portal.tscn: a glowing ring placeholder with an Area3D. Hub portal -> resource world forest portal clearing; resource world portal -> hub spawn. Fade to black, change scene, place the player at the target spawn point.
- Debug overlay shows the current biome. Add a debug key (F4) to cycle teleports to each biome's centre for quick checking.
- Performance pass for the web build: check draw calls and FPS in each biome, shorten draw distances in swamp (thick fog), reduce foliage density if needed.

MILESTONE 7: WEB EXPORT CHECK
- Export the Web build to godot-game/export/web/ (git ignored), serve it locally (for example python3 -m http.server) and check it loads and runs in Chromium.
- Take a screenshot in the hub and in each of the five biomes (Playwright with the pre-installed Chromium is fine) and save them to docs/images/world_build/ with lowercase names like forest_overview.png.
- If something only fails in the web build, fix it or note it.

DELIVERABLES
- The Godot project working in the editor and as a web build.
- tools/bbmodel_to_gltf.py and the converted .glb files.
- docs/world_build_notes.md: how the terrain, biome data, scatter and environment systems work, how to tune them (where the numbers live), the controls, every placeholder that is waiting for a real model or texture, and every choice you made that the docs didn't cover.
- Screenshots in docs/images/world_build/.
- One commit per milestone.

QUALITY BAR
The style is Hytale mixed with RuneScape: Dragonwilds (game_worlds.md section 2): soft lighting, bold shapes, lots of foliage, crisp pixel textures. Each biome must be recognisable from one screenshot by its ground colour, sky, fog and trees alone. Forest feels friendly; each biome after it feels a bit stranger and harsher.
````

---

## Choices made in this prompt

These aren't in the other docs yet. Change them here if you want something different.

| Choice | Why |
| --- | --- |
| Compatibility renderer, web export without threads | The game runs in the browser; this is the most compatible setup and works on any static host |
| Custom chunked heightmap terrain instead of a terrain addon | Works in the Compatibility renderer and in web builds without native extensions |
| Resource world about 1280 × 512 m, biomes in 256 m bands | Big enough to explore, small enough for a browser build. Easy to grow later |
| Hub about 200 × 200 m | A compact village where players meet easily |
| Python converter from `.bbmodel` to `.glb` | Godot can't read Blockbench files; a script converts all models the same way and can be run again when models change |
| First scope: imp, camera, hub, biomes, portals | Multiplayer, Supabase, wallets, gathering and mobs come after the world exists |
