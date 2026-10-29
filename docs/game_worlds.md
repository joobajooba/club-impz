# Game Worlds

> Status: draft v4 · Owner: J00BA · Last updated: 2026-10-29
>
> The two worlds in Club Impz, the hub world and the resource world: what each one is for, what players can do there, how they look and the art style for both. This doc must agree with `game_direction.md` and `resource_gathering.md`. Where they differ, `game_direction.md` wins until it is updated.

---

## 1. Overview

Club Impz has **two worlds**. Each one has a single job.

| World | Job | Feel | Gathering | Combat |
| --- | --- | --- | --- | --- |
| Hub world | Social | Club Penguin: hang out, chat, show off | None | None, the hub is combat free |
| Resource world | Grind | RuneScape: explore, gather, level up | All gathering | Mobs |

- Every player **spawns in the hub world** when they start the game.
- The hub world is for **everything social**. The resource world is for **levelling up the game's skills**.
- Players can **chat in both worlds** (see `game_direction.md` section 4.1).

---

## 2. Art style

The style for both worlds is a mix of **Hytale** and **RuneScape: Dragonwilds**.

- **Overall look:** a stylized, colourful game like Dragonwilds. Soft lighting, bold shapes, lots of foliage.
- **Models:** Hytale style **voxel models** for everything placed in the world: trees, plants, rocks, ore nodes, animals, mobs, NPCs, tools, weapons and buildings. Models are made in **Blockbench**.
- **Textures:** Hytale style low resolution, hand painted pixel textures on those models.
- **Not block based.** The world is **not** made of square blocks like Minecraft. Players can't place or break terrain.
- **Terrain:** the ground, hills and mountains are **normal smooth terrain** (a sculpted heightmap, not cubes), painted with **stylized voxel / pixel textures** so it matches the models.
- **Foliage:** both worlds are full of foliage (grass, flowers, bushes, vines, mushrooms) so they look lush and alive. The resource world has the most.
- **2D assets** (inventory items, prestige icons, titles, emblems, UI) are made in **Aseprite** and are not part of the 3D world (see `game_direction.md` section 4).

### 2.1 Asset folders

All world assets live in the Godot project and follow the naming rules (lowercase, `_` instead of spaces).

| Asset | Folder | Example |
| --- | --- | --- |
| 3D models | `godot-game/assets/models/` | `models/mobs/wolf.bbmodel` |
| Textures and materials | `godot-game/assets/textures/` | `textures/terrain/frost_snow.png` |
| 2D sprites | `godot-game/assets/sprites/` | `sprites/items/stone_pickaxe.png` |

### 2.2 Technical notes

The game runs in the **browser** (Godot web export), so the worlds need to stay light.

- Use **level of detail** and draw distance limits for trees, rocks and foliage.
- Draw foliage and grass in **batches** (Godot `MultiMeshInstance3D`) instead of one node per plant.
- Keep textures **small and shared** between models where possible. The pixel style helps here.

---

## 3. Hub world

### 3.1 Purpose

The hub world is the **social area**. It is where players meet, talk and show off what they have earned in the resource world.

- **Every player spawns here** when they start the game.
- **No resource gathering.** No resource nodes spawn in the hub (see `resource_gathering.md` section 1).
- **No combat.** The hub is completely combat free. There are no mobs and players can't fight each other.
- Players come back here between grinding sessions to craft, sell, take on challenges and socialise.

### 3.2 What players can do

| Activity | Details | Spec doc |
| --- | --- | --- |
| Chat | Talk to other players | To be decided |
| Show off | Skins, cosmetics, items, trophies, titles, emblems, profile cards | `game_direction.md` section 9 |
| Talk to NPCs | Shops, challenge givers, quest givers, crafting station keepers | To be decided |
| Craft and process | Smelt ores into ingots, make planks, craft tools, weapons and armour at stations | `crafting.md` |
| Sell | Sell items to NPCs for coins. No player-to-player trading | `game_direction.md` section 5 |
| Start quests and challenges | Pick up challenges and quests from NPCs | `challenges.md` |
| Interact with things | Sit on benches, open doors, use notice boards, and other small interactions | To be decided |
| Events | Occasional events for players in the hub | To be decided |

### 3.3 Layout and landmarks

A **beautiful village** built around a **castle**. Proposed landmarks:

| Landmark | What happens there |
| --- | --- |
| Spawn point | Where every player appears when they log in |
| Village square | The main hangout and the place for events |
| Market stalls | NPC shops where players buy and sell |
| Crafting area | Smelter, workbenches and other crafting stations |
| Castle | The centrepiece of the hub. Scenery only for now, to make the hub look great |
| Portals | How players travel to the resource world (section 5) |

---

## 4. Resource world

### 4.1 Purpose

The resource world is **purely for levelling up** the game's skills.

- **Explore** a large open wilderness.
- **Gather** every resource: ores, trees, plants and fish (see `resource_gathering.md`).
- **Kill mobs** for hides and drops (hunting).
- **Tame mobs** with plant bundles. Taming comes in a later update (see `game_direction.md` section 5).
- **Level up** the five skills and the player level.

### 4.2 Layout

- The resource world is **open wilderness**, split into **biomes**.
- **Higher tier resources mostly sit deeper in the world** (see `game_direction.md` section 4.2). Players start in the forest and travel further out as their tools improve.
- Each biome has a **mix of tiers**, not one tier. Coal, for example, is found almost everywhere.
- Some early biomes also hold a **high tier node** that players can see long before they can gather it, as a goal to come back to (for example obsidian in the mountain and worldbark in the forest).
- Resource nodes are fixed in place and never run out (see `resource_gathering.md` section 9).
- Every biome is **full of foliage**.

### 4.3 Biomes

The biomes go in this order, from the start of the resource world to the deepest part. More biomes may be added later.

```
forest ─▶ mountain ─▶ frost ─▶ plains ─▶ swamp ─▶ void ─▶ stellar
```

| Depth | Biome | Look |
| --- | --- | --- |
| 1 (start) | Forest | Dense trees, ferns, mushrooms, streams |
| 2 | Mountain | Tall peaks, cliffs, caves, rocky paths |
| 3 | Frost | Snow, ice, frozen lakes, blue light |
| 4 | Plains | Wide open grassland, rolling hills |
| 5 | Swamp | Poison swamp: murky green water, toxic fog, twisted roots |
| 6 | Void | Dark, floating rocks, purple glow, glowing crystals. No trees |
| 7 (deepest) | Stellar | Cosmic space: starry sky, floating islands, low gravity feel. No trees |

### 4.4 Ores by biome

| Biome | Ores (resource tier) | Notes |
| --- | --- | --- |
| Forest | Coal (T1), tin (T2), copper (T3) | All mineable with the starter `stone_pickaxe` |
| Mountain | Coal (T1), tin (T2), copper (T3), iron (T4), obsidian (T6) | Obsidian needs a `gold_pickaxe`, so players come back later |
| Frost | Coal (T1), iron (T4), gold (T5) | |
| Plains | Coal (T1), titanite (T7) | |
| Swamp | Coal (T1), iron (T4), gold (T5), dreadstone (T8) | |
| Void | Coal (T1), obsidian (T6), voidstone (T9) | |
| Stellar | Gold (T5), stellarite (T10) | The only biome with no coal |

### 4.5 Trees by biome

| Biome | Trees (resource tier) | Notes |
| --- | --- | --- |
| Forest | Pine (T1), birch (T2), oak (T3), worldbark (T10) | Worldbark needs a `voidstone_axe`, so it can't be chopped until end game |
| Mountain | Maple (T4), hickory (T5) | |
| Frost | Hickory (T5), frostbark (T6) | |
| Plains | Titanwood (T7), gembark (T9) | |
| Swamp | Titanwood (T7), runewood (T8) | |
| Void | None | |
| Stellar | None | |

### 4.6 Where to find each resource

| Resource | Tier | Biomes |
| --- | --- | --- |
| Coal | T1 | Forest, mountain, frost, plains, swamp, void |
| Tin | T2 | Forest, mountain |
| Copper | T3 | Forest, mountain |
| Iron | T4 | Mountain, frost, swamp |
| Gold | T5 | Frost, swamp, stellar |
| Obsidian | T6 | Mountain, void |
| Titanite | T7 | Plains |
| Dreadstone | T8 | Swamp |
| Voidstone | T9 | Void |
| Stellarite | T10 | Stellar |
| Pine | T1 | Forest |
| Birch | T2 | Forest |
| Oak | T3 | Forest |
| Maple | T4 | Mountain |
| Hickory | T5 | Mountain, frost |
| Frostbark | T6 | Frost |
| Titanwood | T7 | Plains, swamp |
| Runewood | T8 | Swamp |
| Gembark | T9 | Plains |
| Worldbark | T10 | Forest |

- Plants, fish and mobs for each biome will be added once their tables are in `resource_gathering.md` and `world_mobs.md`.
- The existing mob models (`cow`, `pig`, `highland_cow`, `wolf`, `ogre`, `dragon`, `pale_dragon`) still need to be placed in biomes. Section 4.8 has suggestions.

### 4.7 Biome look and feel: shared rules

This section and sections 4.8 and 4.9 describe how each biome should look and feel, ready for building the world in Godot. The 3D assets in each biome are built with `blockbench_detailed_prompts.md`. Ores and trees must match sections 4.4 and 4.5.

**Inspiration.** Each game brings something different:

| Game | What to take from it |
| --- | --- |
| Hytale | The main look: Hytale style voxel trees, plants and props, feathery alpha cut leaves, painted pixel textures, rich colour per zone |
| RuneScape: Dragonwilds | Soft painterly lighting, warm god rays, lush foliage everywhere, stylized but grounded world |
| Valheim | Each biome feels more dangerous than the last, and you can see it from far away. Strong fog and light per biome. Landmarks you see long before you can reach them |
| RuneScape | Classic fantasy places with a clear identity (Morytania swamp, Trollheim mountains, Fremennik snow, the Abyss) |
| Minecraft | Each biome has its own grass, leaf and water colour, so you know where you are from the ground colour alone. The End for floating, empty void islands |

**Reference images.** J00BA supplied nine reference screenshots. What to take from each:

| Reference | Biome | What to copy |
| --- | --- | --- |
| Hytale pine forest with a river | Forest | Tall blue green pines with dark red trunks, one golden autumn tree for contrast, a clear blue river with stepping stones and a fallen log bridge, dry golden grass, small flower patches, a snowy mountain in the distance |
| Hytale autumn forest from above | Forest, mountain | A canopy of mixed colours: green, lime, gold, orange and deep red trees side by side. Grass, dirt and leaf litter patches on the ground |
| Hytale misty sunset valley | Mountain | Peach and pink sky, mountains fading into haze, dark pines, pale snowy paths, standing stones. Light carries the mood |
| Hytale dark trunk autumn grove | Mountain | Huge dark trunks framing the view, orange and red canopies, a golden ground with dry grass and shrubs, small glowing mushrooms |
| Hytale Emerald Wilds gully | Forest | Rolling hills cut by a river, blue leafed trees next to red and orange ones, teal ground under the trees, pale rock outcrops in the grass |
| Hytale swamp with a giant tree house | Swamp | Thick green fog, drooping vines, wet flat ground with pools, a giant hollow tree with platforms, lanterns and rope bridges, fireflies |
| Hytale snow field with a polar bear | Frost | Bright blue sky, deep snow with wind ripples, snow loaded pines next to clean green ones, a few orange grass tufts poking through, a big white bear |
| Purple fog forest | Void | Purple haze, dark towering shapes, thorny black dead bushes, no colour except purple. Void has **no trees** (section 4.5), so the tall shapes become rock and crystal spires |
| Voxel galaxy with planets | Stellar | Deep purple space, a bright glowing galaxy ring, planets with rings and a lava planet, floating asteroids, star sparkles everywhere |

**Rules for every biome:**

- **Readable from far away.** Each biome has its own sky, fog colour, ground colour and tree shapes, so a player can tell where they are from one screenshot.
- **Gets stranger with depth.** Forest is friendly and familiar. Each biome after it is less like the real world, ending in open space.
- **Full of foliage.** Ground cover everywhere except paths, water and bare rock. Void and stellar use crystals and glowing plants instead of grass.
- **Landmarks.** Every biome has at least one big landmark visible from far away, so players can find their way and want to go there.
- **Soft borders.** Biomes blend over a border zone (about 30 to 60 metres): the ground textures mix, trees thin out, and the fog and light fade from one biome to the next.
- **Stylized terrain, not blocks.** Smooth sculpted terrain (section 2). The stepped look in the reference images comes from the textures and the models, not from the ground.

### 4.8 Biomes

Every biome uses the same template. Hex colours are starting points; tune them in Godot. Mob ideas are suggestions until `world_mobs.md` is written.

#### 4.8.1 Forest (depth 1, start)

> Friendly, sunny and green. The place every new player learns the game.

| Part | Description |
| --- | --- |
| Feel | Calm, safe and beautiful. Morning light, birdsong, a gentle river. Like Hytale's Emerald Grove and the first area of Dragonwilds |
| Sky and light | Clear light blue sky (`#8fc8f0` at the top, `#d8eef8` at the horizon), warm white sun (`#fff2d8`), soft god rays through the canopy |
| Fog | Very light blue haze, only in the distance (`#cfe4ee`) |
| Terrain | Gentle rolling hills, small valleys and a winding river through the middle. A few low rock outcrops and grassy ledges |
| Ground textures | `forest_grass` (rich green), `forest_grass_dry` (golden patches, like the river reference), `forest_dirt`, `forest_leaf_litter`, `forest_path` |
| Gatherable trees | Pine, birch and oak everywhere. Birch can use a golden autumn leaf variant for colour pops, like the aspen in the river reference |
| Worldbark | A few giant worldbark trees stand in one ancient grove deep in the forest, towering over everything. Players see them from the start, but can't chop them until end game. They glow faintly at night |
| Ore | Coal, tin and copper veins on rock outcrops, riverbanks and small hillside cuts |
| Rocks | Grey green stone, mossy tops |
| Foliage | Tall grass, ferns, wildflowers (blue, pink, white), berry bushes, red and brown mushrooms, fallen logs, stumps |
| Water | Clear, bright blue river and ponds with stepping stones, reeds at the edges, a fallen log bridge |
| Landmarks | The worldbark grove, the river and its waterfall, an old stone ruin on a hill, the portal clearing |
| Particles | Floating pollen and dandelion seeds, falling leaves, butterflies, fireflies at dusk |
| Sound | Birds, wind through leaves, running water |
| Mob ideas | `cow`, `pig`, `wolf` (forest edges) |

#### 4.8.2 Mountain (depth 2)

> Tall, misty and dramatic. Autumn colours in the valleys, snow on the peaks.

| Part | Description |
| --- | --- |
| Feel | Big and wild. Steep climbs, long views and cold air. Like Trollheim in RuneScape and Valheim's mountains, with the misty sunset light from the reference |
| Sky and light | Warm peach and pink sky low down, pale blue up high (`#f2b8a0` to `#a8c4e0`). Low golden sun, long shadows |
| Fog | Pink and peach haze that hides the far peaks (`#e8b8a8`). Thicker in the valleys |
| Terrain | Steep peaks, cliffs, ridges, narrow passes, switchback paths, scree slopes, waterfalls and caves. Snow on the high peaks |
| Ground textures | `mountain_grass` (olive), `mountain_rock` (blue grey), `mountain_scree`, `mountain_snow` (peaks only), `mountain_path` |
| Gatherable trees | Maple in the valleys (red, orange and gold canopies, fallen leaves on the ground). Hickory on the higher slopes |
| Ore | Coal, tin, copper and iron on cliff faces and in caves. **Obsidian** is deep in caves or around an old volcanic vent, where players find it early and come back with a `gold_pickaxe` |
| Rocks | Blue grey stone, layered and jagged, lichen spots, snow on top near the peaks |
| Foliage | Mountain grass, heather (purple), alpine flowers, small shrubs, dry grass on ledges, glowing mushrooms in caves |
| Water | Fast streams, waterfalls, small cold lakes |
| Landmarks | The highest peak (visible from the forest), standing stones on a ridge, a long rope bridge over a gorge, the obsidian cave |
| Particles | Mist drifting over passes, falling maple leaves, snow blowing off the peaks |
| Sound | Strong wind, distant eagles, echoing water |
| Mob ideas | `highland_cow`, `wolf`, `ogre` (in caves) |

#### 4.8.3 Frost (depth 3)

> Bright, cold and clean. Deep snow and frozen lakes under a bright blue sky.

| Part | Description |
| --- | --- |
| Feel | Beautiful but harsh. Bright days and quiet, aurora lit nights. Like Hytale's Borea and RuneScape's Fremennik lands |
| Sky and light | Deep clear blue sky (`#3a78d8` at the top, `#bcd8f4` at the horizon), bright white sun, blue shadows on the snow. Green and purple aurora at night |
| Fog | Pale icy blue (`#d8e8f4`). Blizzard patches with thick white fog |
| Terrain | Wide snowfields with wind ripples, frozen lakes, ice cliffs, ice spikes, snowy hills. A few dark rock outcrops |
| Ground textures | `frost_snow` (with wind ripples), `frost_ice`, `frost_packed_snow` (paths), `frost_rock`, `frost_tundra` (green grey grass at the edges) |
| Gatherable trees | Snow loaded hickory and frostbark. Mix snow covered trees with a few clean dark green ones, like the reference |
| Ore | Coal, iron and gold. Gold veins glint in ice cliffs |
| Rocks | Pale stone with snow caps and icicles |
| Foliage | Frosted grass tufts, orange tundra grass poking through the snow, frozen shrubs, ice crystal clusters, snow berries |
| Water | Frozen lakes with cracks you can walk on, a few open dark blue pools |
| Landmarks | A huge frozen waterfall, a giant ice spire, a frozen lake with something trapped under the ice |
| Particles | Falling snow, sparkling ice dust, breath mist, aurora at night |
| Sound | Howling wind, creaking ice, crunching snow |
| Mob ideas | `pale_dragon`, `wolf` (snow variant), a polar bear (new model, like the reference) |

#### 4.8.4 Plains (depth 4)

> Vast, golden and windy. A huge open steppe under giant trees. Bigger and more dangerous than it looks.

| Part | Description |
| --- | --- |
| Feel | Wide open and epic. Endless golden grass blowing in the wind, with huge titanwood trees and gem crystal groves. Like Valheim's plains: it looks calm, but it is a late game zone |
| Sky and light | Warm, hazy sky (`#e8d8a8` at the horizon, `#90b8d8` at the top), strong low sun, long shadows from the giant trees |
| Fog | Warm golden dust haze (`#e8dcb0`) |
| Terrain | Flat to rolling grassland, big mesas, rock arches and tall stone pillars, dry riverbeds |
| Ground textures | `plains_grass` (gold and straw), `plains_grass_green` (patches near water), `plains_dirt` (red brown), `plains_rock` (sandy), `plains_path` |
| Gatherable trees | Titanwood stands alone or in small groups across the grass, huge and steel grey. Gembark grows in sheltered groves, with gem crystals glinting on the trunks |
| Ore | Coal everywhere. Titanite crystal columns on mesas and rock arches |
| Rocks | Sandy and warm, layered like mesas |
| Foliage | Very tall golden grass that sways (the most grass of any biome), wheat like stalks, dry bushes, wildflowers, gem crystals in the gembark groves |
| Water | A few shallow streams and watering holes with green grass around them |
| Landmarks | A giant stone arch, a ring of ancient pillars, the biggest titanwood tree, a gembark grove that glitters at sunset |
| Particles | Grass seeds and dust blowing in the wind, gem sparkles near gembark |
| Sound | Constant wind through the grass, distant thunder, grazing herds |
| Mob ideas | Herd animals (`cow` variants), large predators. To be decided in `world_mobs.md` |

#### 4.8.5 Swamp (depth 5)

> Poisonous, foggy and overgrown. Glowing runes in the trees and red light in the rocks.

| Part | Description |
| --- | --- |
| Feel | Eerie and heavy. Thick green fog, drooping trees, toxic water. Like Morytania's Mort Myre swamp in RuneScape, Valheim's swamp and the Hytale swamp reference |
| Sky and light | Hidden by fog. Dim green grey (`#7aa898`), sunlight broken into shafts through the canopy |
| Fog | Thick poison green (`#5e9a80`), the densest fog in the game. Lower and thicker over water |
| Terrain | Flat and wet: mud flats, shallow pools, small raised islands joined by roots and boardwalks |
| Ground textures | `swamp_mud`, `swamp_moss`, `swamp_grass` (dark olive), `swamp_slime` (toxic green near dreadstone), `swamp_boardwalk` |
| Gatherable trees | Runewood, drooping with long hanging vines and glowing runes carved in the trunks. Titanwood rises out of the fog like dark columns |
| Ore | Coal, iron and gold on muddy banks. Dreadstone in the wettest, most toxic parts, with red glowing cracks and dripping slime |
| Rocks | Dark wet stone with slime and moss |
| Foliage | Reeds, cattails, lily pads, hanging moss, vines, giant mushrooms, glowing fungus, roots over the water |
| Water | Murky green toxic water with bubbles. Whether it hurts players is to be decided (section 6) |
| Landmarks | A giant hollow tree with platforms, lanterns and rope bridges (like the reference), sunken ruins, a dreadstone pit glowing red |
| Particles | Fireflies, rising bubbles, spores, drips from the vines |
| Sound | Frogs, insects, bubbling water, creaking wood |
| Mob ideas | `ogre`, swamp creatures. To be decided in `world_mobs.md` |

#### 4.8.6 Void (depth 6)

> Dark, purple and broken. Floating islands over an endless drop. No trees.

| Part | Description |
| --- | --- |
| Feel | Wrong and quiet. The world is coming apart. Like the purple fog reference, Minecraft's End and RuneScape's Abyss |
| Sky and light | Dark purple sky (`#2a1440` to `#5a2a7a`), no sun. Light comes from the glowing voidstone and a faint purple glow from below |
| Fog | Thick purple haze (`#6a3a8a`), the far distance fades to dark |
| Terrain | Floating islands of black purple rock over a bottomless drop, joined by narrow land bridges and floating stepping stones. Cracks in the ground glow purple |
| Ground textures | `void_rock` (black purple), `void_dust`, `void_cracked` (glowing cracks), `void_crystal_ground` |
| Trees | **None** (section 4.5). Tall rock and crystal spires take the place of trees in the skyline |
| Ore | Coal, obsidian and voidstone. Voidstone crystals glow and have small rocks floating above them |
| Rocks | Black purple stone with glowing purple veins, pieces floating just above the ground |
| Foliage | Thorny black dead bushes (like the reference), purple crystal clusters, glowing void flowers, ash grass |
| Water | None. Instead, the drop between islands, with purple light far below |
| Landmarks | A broken floating island that slowly turns, a huge voidstone crystal spire, a rift in the sky |
| Particles | Floating rock debris, purple embers rising, sparks around voidstone |
| Sound | Deep low hum, distant cracking, near silence |
| Mob ideas | `dragon` (void variant, like the void dragon reference). To be decided in `world_mobs.md` |

#### 4.8.7 Stellar (depth 7, deepest)

> Open space. Star dusted islands among planets and a glowing galaxy. The end of the world.

| Part | Description |
| --- | --- |
| Feel | Awe and wonder. The reward for reaching the end. Like the galaxy reference: calm, huge and beautiful |
| Sky and light | Deep space (`#140c2a` to `#3a2a6a`) full of stars, a glowing galaxy ring, ringed planets and a lava planet in the sky. Soft gold and white light from the galaxy |
| Fog | Very light violet haze (`#4a3a7a`), only in the far distance, so the view stays wide |
| Terrain | Floating islands of dark blue star dusted rock, smaller than the void islands, with space all around. Asteroid stepping stones between them |
| Ground textures | `stellar_rock` (dark blue with sparkles), `stellar_dust` (gold star dust), `stellar_crystal_ground` |
| Trees | **None** (section 4.5). Crystal formations and floating asteroids fill the skyline |
| Ore | Gold and stellarite. Stellarite glows white gold, with tiny fragments orbiting it |
| Rocks | Dark blue rock with star sparkle pixels, asteroid chunks floating around |
| Foliage | Star moss (soft glowing ground cover), glowing crystal flowers, gold star dust patches |
| Water | None |
| Landmarks | The galaxy ring in the sky, a planet close enough to see its surface, a huge stellarite crystal at the very end of the world |
| Particles | Twinkling stars, drifting star dust, shooting stars, orbiting fragments |
| Sound | Soft ambient music, gentle chimes, deep space hum |
| Mob ideas | To be decided in `world_mobs.md` |

### 4.9 Building the biomes in Godot

Recommendations for building the biomes in Godot. The game runs in the browser (section 2.2), so these favour things that work in a web build. Test each one in the web build before relying on it.

| Part | How |
| --- | --- |
| Terrain | One heightmap terrain for the whole resource world (a terrain addon such as Terrain3D, or a custom heightmap mesh). Void and stellar islands are separate meshes, because they float |
| Ground textures | Paint the terrain with the biome texture sets above (tiling PNGs, built with `blockbench_detailed_prompts.md` section 3.12). Use about 4 to 5 textures per biome and blend them at the borders |
| Foliage | Scatter grass, flowers and small plants with `MultiMeshInstance3D`, in chunks that hide past a set distance. Trees and rocks are instanced scenes with level of detail |
| Sky and fog | One `WorldEnvironment` per biome (sky colours, fog colour and density, sun colour and angle). Fade between them when a player crosses a border (an `Area3D` per biome). Use the regular depth and height fog; volumetric fog isn't available in browser builds |
| Glow | Cubes named `_glow` in Blockbench get an emissive material (voidstone, stellarite, runes, crystals) |
| Particles | Each biome has one ambient particle emitter that follows the player (pollen, snow, spores, embers, star dust) |
| Wind | The wind shader from `blockbench_detailed_prompts.md` on all trees and foliage. Stronger in the plains and mountain, none in stellar |
| Sound | One ambient sound loop per biome, faded at the borders like the environment |
| Performance | Keep draw distance shorter in the swamp and void, where thick fog hides the distance anyway |

---

## 5. Travel between worlds

- Players travel between the hub and the resource world using **portals**.
- Using a portal loads the other world. Inventory, tools and progress carry over.
- Exact portal placement is to be decided (section 6).

---

## 6. Open questions

1. **Portals:** where are the portals? For example one portal from the hub to the forest, or one portal per biome that unlocks as the player reaches it. Can players return to the hub from anywhere (for example a teleport) or only from a portal?
2. **Dying:** what happens when a player dies to a mob in the resource world (for example respawn at the portal, lose nothing)?
3. **Events:** what kind of hub events are planned, and are they scheduled or random?
4. **Quests:** are quests the same as challenges (`challenges.md`), or a separate system with their own doc?
5. **Player count:** how many players share one copy of each world at the same time?
6. **Scenery trees:** should biomes also have trees that can't be chopped, just for looks (for example the autumn trees in the reference images)? Section 4.8 assumes no, and uses colour variants of the gatherable trees instead.
7. **Swamp water:** does the toxic swamp water hurt players?
8. **Void and stellar falls:** what happens when a player falls off a floating island?
9. **Day and night:** is there a day and night cycle? Section 4.8 describes some night effects (aurora, glowing worldbark) in case there is.
