# Club Impz

Browser game built in Godot, with crypto features, part of the Implingz NFT project. This repository also holds the general website and the Supabase database setup.

## Layout

| Folder | What goes here |
| --- | --- |
| `docs/` | Markdown documents: design docs, specs, plans, notes. Start at [`docs/README.md`](docs/README.md). |
| `godot-game/` | The Godot project (open this folder in Godot) |
| `godot-game/assets/models/` | 3D game models |
| `godot-game/assets/sprites/` | 2D sprites and sprite sheets |
| `godot-game/assets/textures/` | Textures and materials |
| `godot-game/assets/*/source/` | Source files the game doesn't load: Blender and Blockbench sources, their build scripts, the original inventory icons. Each has a `.gdignore`, so Godot skips it. |
| `website/` | The general website |
| `supabase/` | Supabase database: migrations, edge functions, config |

Game assets live inside `godot-game/` so Godot can import them (Godot only sees files inside its project folder).

The IMPLINGZ game from the old COLLAB_IMPZ repo was moved in on 2026-10-30 as one snapshot. Its folders inside `godot-game/` (`autoload/`, `characters/`, `gathering/`, `models/`, `sprites/`, `Textures/`, `glTF/`, `ui/`, `world/` …) keep their names, so every `res://` path still works. The full history of that work stays in the private COLLAB_IMPZ repo.

## Run locally

Open `godot-game/project.godot` in Godot 4.7 and press F5. The game starts in `demo_landscape.tscn`.

Controls: WASD to walk (relative to the camera), Shift to sprint, Space to jump, hold the right mouse button to look around, scroll to zoom. F gathers or uses what you're next to, T tames an animal, Q switches between your tools of the kind in hand, I opens the inventory, Esc closes a menu. Profile (top right) connects a wallet.

Where things are (all near the start): the **mining** area about 24 m south; the **camp** (merchant, stable, battle board, treasure dig) south-east; the **foraging** meadow and **lumber** grove to the west and north-west; the **hunting** grounds further south; **fishing** spots along the pond just west of the start, with a campfire.

Gathering: every action costs 5 of one shared 100 energy, which refills at 00:00 and 12:00 UTC. Each skill has its own tools and a tool reaches its tier and every tier below; the Imp takes out the right tool for the job.
- Mining: three swings break a vein; ore, sometimes a gem. Furnace: ore (and Coal from Gold up) into ingots.
- Foraging: pick a plant; sometimes its seed. Drying rack: plants into bundles.
- Lumbering: three chops fell a tree; logs, sometimes sap. Sawbench: logs into planks, and rods.
- Hunting: three arrows, the animal goes poof; its hide, sometimes a trophy. Tanning rack: hides into leather, and bows. T with a dried bundle of the animal's tier tries to tame it.
- Fishing: F to cast, F again when the fish bites. Campfire: fish into cooked fish.
- Blacksmith (by the furnace): hilts (wood hilts from planks), pickaxes, sickles and axes.
Everything regrows 10 seconds after it's gathered.

Camp (TEST rules and prices, not decided yet): the merchant buys items and sells energy refills, inventory rows and stable slots; the stable holds tamed animals (one follows you and raises trophy chances, three make your battle team, cooked fish gives them XP); the battle board runs turn-based battles against wild animals; the treasure dig gives 3 picks of a 5×5 grid once per energy reset.

Test tools: under the inventory grid are buttons to refill energy, add 20 of every raw item, unlock every tool, add 1000 coins and tame three starter animals. Items, tools, coins, animals and energy are saved on this device (TEST) until the server is connected.

## Pickaxe model

`godot-game/assets/models/source/pickaxe.glb` is built in Blender by `build_pickaxe.py` next to it (see the comment at its top for the command). Its skins live in `pickaxe-skins.json`, one per sprite in `godot-game/assets/sprites/source/pickaxes/`. The game reads its copy in `godot-game/models/mining/`. Which tier each tool reaches, and every recipe, are in `godot-game/autoload/game_data.gd`.
