# Game Worlds

> Status: draft v1 · Owner: J00BA · Last updated: 2026-10-29
>
> The two worlds in Club Impz, the hub world and the resource world: what each one is for, what players can do there, how they look and the art style for both. This doc must agree with `game_direction.md` and `resource_gathering.md`. Where they differ, `game_direction.md` wins until it is updated.

---

## 1. Overview

Club Impz has **two worlds**. Each one has a single job.

| World | Job | Feel | Gathering | Combat |
| --- | --- | --- | --- | --- |
| Hub world | Social | Club Penguin: hang out, chat, show off | None | None (to be confirmed) |
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
| Castle | The centrepiece of the hub. Use to be decided (for example challenge hall or trophy hall) |
| Portal to the resource world | How players travel to the resource world (section 5) |

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
- **Higher tier resources sit deeper in the world** (see `game_direction.md` section 4.2). Players start near the portal in the easy biomes and travel further out as their tools improve.
- Resource nodes are fixed in place and never run out (see `resource_gathering.md` section 9).
- Every biome is **full of foliage**.

### 4.3 Biomes

The biomes J00BA has named so far are forest, plains, mountain, frost, poison swamp, void and cosmic space. More will be added.

The table below is a **proposal**: it places each biome by depth and matches it to the resources whose names and tiers fit it best. J00BA to confirm or change.

| Depth | Biome | Resource tiers | Ores | Trees | Look |
| --- | --- | --- | --- | --- | --- |
| 1 (start) | Plains | T1 to T2 | Coal, tin | Pine, birch | Open grassland, flowers, gentle hills, near the portal |
| 2 | Forest | T3 to T4 | Copper, iron | Oak, maple | Dense trees, ferns, mushrooms, streams |
| 3 | Mountain | T5 to T6 | Gold, obsidian | Hickory | Tall peaks, cliffs, caves, rocky paths |
| 4 | Frost | T6 to T7 | Titanite | Frostbark, titanwood | Snow, ice, frozen lakes, blue light |
| 5 | Poison swamp | T8 | Dreadstone | Runewood | Murky green water, toxic fog, twisted roots |
| 6 | Void | T9 | Voidstone | Gembark | Dark, floating rocks, purple glow, glowing crystals |
| 7 (deepest) | Cosmic space | T10 | Stellarite | Worldbark | Starry sky, floating islands, low gravity feel |

- Plants, fish and mobs for each biome will be added once their tables are in `resource_gathering.md` and `world_mobs.md`.
- The existing mob models (`cow`, `pig`, `highland_cow`, `wolf`, `ogre`, `dragon`, `pale_dragon`) still need to be placed in biomes.

---

## 5. Travel between worlds

> To be decided. Proposal below.

- Players travel between the two worlds through a **portal**: one in the hub, one at the start of the resource world.
- Using the portal loads the other world. Inventory, tools and progress carry over.

---

## 6. Open questions

1. **Travel:** how do players move between the hub and the resource world? Is a portal right, and can players return to the hub from anywhere (for example a teleport) or only from the portal?
2. **Biomes:** is the biome and tier mapping in section 4.3 right? Which other biomes should be added?
3. **Combat in the hub:** is the hub fully safe (no combat at all)?
4. **Dying:** what happens when a player dies to a mob in the resource world (for example respawn at the portal, lose nothing)?
5. **Castle:** what is the castle used for?
6. **Events:** what kind of hub events are planned, and are they scheduled or random?
7. **Quests:** are quests the same as challenges (`challenges.md`), or a separate system with their own doc?
8. **Player count:** how many players share one copy of each world at the same time?
