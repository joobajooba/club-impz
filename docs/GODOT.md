# IMPLINGZ: building the game in Godot

| Status | Last pass | Depends on |
|---|---|---|
| Draft | User addition, 2026-10-20 | 00, 02, ACCOUNTS-AND-DATA, MODELS-BLOCKBENCH |

> Claude: read `docs/CLAUDE.md` before working from this file. Read this whole file before writing or changing any Godot scene, script or import setting.
>
> Labels: **Decided** (in `DECISIONS.md`) · **Proposed** (Claude's suggestion) · **Open question**

**Purpose of this doc:** the game moves from the Three.js browser test to the Godot engine. This doc says what carries over, how the Godot project is laid out, and how it connects to the database and the 3D models.

**Words used here.**
- **Godot:** a free, open-source game engine. Its scripting language is **GDScript**.
- **Scene / node:** in Godot, everything is a tree of nodes, saved as a scene (`.tscn`). A player, a vein or a menu is each a scene.
- **Autoload:** a script Godot loads once at start-up that every scene can reach (for example `Api` or `Inventory`).
- **Export:** building the finished game for a platform (Windows, Mac, the web).

---

## 1. What is decided

| Topic | Decision |
|---|---|
| Engine | Godot, 3D (**D-037**). |
| The Three.js build | A test. Its **decided rules** carry over (ores, pickaxes, gems, energy, inventory, foraging, hunting: D-005 to D-035). Its **code** does not (**D-037**). |
| Starting point | The Godot test from the "Hightail-like game in Godot" chat (**D-037**). |
| Game type | A grinding gathering game that keeps growing: mining, lumbering, hunting, fishing, farming, foraging (**D-036**). |
| Character | NFT holders can play as their Imp (**D-038**). |
| Models | Tools, weapons, creatures and items come from Blockbench as FBX (**D-044**). See [MODELS-BLOCKBENCH.md](MODELS-BLOCKBENCH.md). |
| Data | Accounts, coins, mint tokens and saves live in the shared Supabase database (**D-043**). See [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md). |
| Platform | Played **in the browser** (**D-046**). |
| World style | Stylised cartoon, like the test project's assets. Items and enemies are Blockbench models with a slight voxel feel (**D-047**). |

## 2. The Godot test project today

On 2026-10-20 Claude looked at the local test project (`Documents/map-world-test`, project name `Map_WorldTest`). On 2026-10-21 it was copied into the COLLAB_IMPZ repo as **`game/`** (D-079), and on 2026-10-30 moved to club-impz as **`godot-game/`** (D-117), without its `.godot/` cache and `build/` export folders. **Work in `godot-game/` from now on**: the old `map-world-test` folder is no longer the copy that counts. What it has:

| Part | Files | What it does |
|---|---|---|
| Engine version | `project.godot` | Godot **4.7**, **Compatibility** renderer (switched 2026-10-22 for the browser, section 3). |
| Player | `characters/player.gd`, `player.tscn`, `impling.glb` | A walking Imp character |
| World | `world/world_generator.gd`, `terrain/ground.obj` | Builds the ground |
| Foliage | `meadow/meadow_scatter.gd`, `foliage_wind.gdshader` | Scatters grass and plants that sway in the wind |
| Inventory | `ui/inventory_ui.tscn` | Inventory screen, opened with I |
| Controls | `project.godot` input map | Sprint, jump (Space), inventory (I) |
| Free asset pack | `FBX/`, `FBX (Unity)/`, `glTF/`, `OBJ/`, most of `Textures/`, `Preview_*.jpg`, `License_Standard.txt` | Quaternius's **Stylized Nature MegaKit, free version** (68 of 116 models). Licence **CC0 1.0** (public domain): free to use, change, ship and share. It was not bought. |
| Water shader | `Shaders/EA_CoolWater.gdshader`, `Materials/EA_Water_Tropical.tres`, `Textures/EA_Foam_Voronoi.tres`, `Textures/EA_Water_Normal.tres` | Added after the kit. **Open question:** where it came from, and its licence. |

The kit ships each model in four formats. Godot needs only one, so the others could be removed later to keep the repo small. **Open question**, not done.

## 3. Platform: the browser (Decided, D-046; details Proposed)

The game runs in the browser, as a Godot **web export**, ideally on impz.club. What that means for the build:

- **Renderer: Compatibility.** Browsers only support Godot's Compatibility renderer. The test project uses Forward+. **Switched on 2026-10-22.** The sun was lowered from 1.2 to 0.5 and the exposure set to 0.8, because Compatibility has no HDR range and the old lighting clipped to white. The water shader now remaps depth for Compatibility. The meadow wind shader and `tint.gdshader` work unchanged. Some Forward+ effects (volumetric fog, SDFGI, some screen effects) don't exist in Compatibility.
- **First web export (2026-10-22): it works.** The no-threads `Web` preset in `godot-game/export_presets.cfg` exports to `godot-game/build/web/` (git-ignored). Headless Chrome runs it on WebGL 2 with the Compatibility renderer and reaches the meadow with the HUD. Size: `index.pck` 104 MB (55 MB gzipped), `index.wasm` 39.5 MB (9.7 MB gzipped), 138 MB in all. The web templates must be in `%APPDATA%/Godot/export_templates/4.7.2.stable/` (`web_nothreads_release.zip`, `web_nothreads_debug.zip`).
- **Shrinking the download (Proposed).** Most of the pack is the asset kit's 2048 px bark and leaf textures (about 5.4 MB each once imported), which exist twice, in `Textures/` and `glTF/`. Options: import them at 1024 px (Import dock → Size Limit), point the glTF models at one shared copy, and export only the resources the game uses instead of `all_resources`. That last one needs care, because some models are loaded by path from code. Serve the files with gzip or Brotli.
- **GDScript only.** Godot 4's web export doesn't support C#. All game code is GDScript.
- **Export without threads.** Godot 4.3 and later can export for the web without thread support. That version runs on any web host without special server headers. The threaded version needs the host to send two security headers (COOP and COEP), which can break wallet pop-ups and other scripts on impz.club. **Proposed:** export without threads.
- **Download size.** The browser downloads the engine (several MB) and every asset on each first visit. Keep textures small, compress models, and load areas only when needed. Measure the build size at every milestone.
- **Wallets work in the page.** MetaMask and Rabby are browser extensions, so the game can call them directly through Godot's `JavaScriptBridge` (ACCOUNTS-AND-DATA, section 4).
- **Shared login with the website.** On impz.club the game can share the website's Supabase login (ACCOUNTS-AND-DATA, section 10).
- **Saving.** Browsers can clear local storage at any time. Everything that matters is saved on the server (ACCOUNTS-AND-DATA, section 9).
- **Phones (Open question).** Godot web exports run on phone browsers, but slowly, and touch controls would be needed. Desktop browsers first is **Proposed**.

## 4. What carries over from the Three.js test (Proposed order)

The Three.js build reached milestones M0 to M5 (see [BUILD-ROADMAP.md](BUILD-ROADMAP.md)). In Godot each is rebuilt from the **design docs**, not by translating `main.js`. Proposed Godot milestones:

| # | Milestone | Rebuilds | Notes |
|---|---|---|---|
| G0 | Project in the repo | n/a | Move the Godot project into this repo (section 5). Pin the Godot version. |
| G1 | Walk and camera | M0 | Third-person camera, walk, sprint, jump, emotes. The test already has walk and jump. |
| G2 | Data tables | n/a | Ores, plants and animals as data, not code (section 6). |
| G3 | Mining loop | M1, M3, M4 | Ten ore veins, pickaxe gating (D-006, D-011), three swings, gems (D-012), 10-second regrow (D-007). |
| G4 | Energy and inventory | M2 | 100 energy, 5 per mine, 12-hour reset (D-008, D-009). 6×8 inventory with the held tool top-left (D-008). Uses the existing 48×48 icons in `godot-game/assets/sprites/source/`. |
| G5 | Furnace and blacksmith | M5 | Build the decided rules (D-054 to D-060), not the D-013 test values. Wood hilts stay a test until lumbering. |
| G6 | Accounts and saving | M6 | Sign up, log in, server-side saving, link wallet. ACCOUNTS-AND-DATA sections 3, 7–9. |
| G7 | Play as your Imp | M7 | Load the player's Imp at runtime (D-038). Everyone else plays as the basic Imp (D-049). |
| G8 | Mint tokens | n/a | Server-rolled while mining (D-040). Shown on impz.club. |
| Later | Foraging, hunting, lumbering, fishing, farming | n/a | Foraging and hunting are designed (D-022 to D-035). The other three are not. |

**Built so far (2026-10-22, Done: PR #36 merged to `main`):** G2 to G5, from the decided rules, not translated from `main.js`:

- **G2:** `godot-game/autoload/game_data.gd` holds the ore, gem, pickaxe and hilt tables (D-005 to D-012, D-054 to D-060), with the Titanite and Dreadstone names (D-020).
- **G3:** a mining area about 24 m south of the spawn (now `godot-game/gathering/area.gd`). It has 15 veins for the ten ores, three swings to break a vein, pickaxe gating with "Needs a … pickaxe", gems (doubled while holding the Stellarite pickaxe, D-059), and a 10-second regrow. The pickaxe is held in the Imp's right hand and Q switches it. **TEST:** the layout and the vein art (the copper vein recoloured per ore, as in the Three.js test).
- **G4:** energy is 100, each mine costs 5, and it resets at 00:00 and 12:00 **UTC** (D-057). It is saved on the device until G6. The inventory is a 6×8 grid (D-008). It reset on restart until G6, which saves it on the device (TEST). **TEST tools** sit under the inventory grid.
- **G5:** the furnace uses the D-054 ore counts and burns Coal from Gold up (D-055). The blacksmith crafts Void and Cosmic hilts (D-058) and every pickaxe (D-006, D-060). **TEST:** wood hilts were free until lumbering was built; now they take 5 planks (D-107).
- The world generator has a new `clearings` setting that keeps the mining area free of grass and props without changing the rest of the world.

**Built since (2026-10-22, Done: PR #38 merged to `main`):** the other four gathering skills and, at the user's request, playable TEST versions of systems that are not fully decided.

- **Decided rules:** foraging (D-022 to D-026, D-061 to D-064), hunting with taming and tracking (D-028 to D-035, D-067 to D-072), lumbering (D-105 to D-108) and fishing (D-109 to D-112), with their stations and tools. Wood hilts are now made from planks (D-107), so the free-hilt test is gone. All gathering shares one energy pool (D-061). The stable has 6 slots and one follower (D-071, D-095).
- **Proposed in the docs, built as stated:** where bows and rods are made (tanning rack, sawbench), axe costs rounded up, bow and rod names, campfire logs, picking as one action, the tool picked automatically for each job, and tools shown above the inventory grid instead of in it.
- **TEST, at the user's request (2026-10-22):** the merchant's prices (D-074's rules on a made-up base price of 2), refill, row and slot prices; battles from 05-skirmish's Proposed types, chart, stats and levels, with made-up moves; the treasure dig from 03-games' Proposed rules. Each is labelled TEST in the game and the code.
- **Art (TEST):** plants and trees are kit models recoloured from their icons, animals are simple box creatures, and sickles, axes, bows and rods have code-drawn icons and models, until drawn and Blockbench art exists.
- Still not built: farming and potions (not designed), trading and multiplayer minigames (need a server), mint tokens (G8), cosmetics (none designed), saving (G6).

**Proposed:** G6 should come **before** the game is shared with any players, so nobody builds up progress that only lives on their own computer.

## 5. Where the Godot project lives (Decided, D-079; details Proposed)

- It is in this repo under **`godot-game/`** (the folder holding `project.godot`), so both collaborators review it through `staging/` PRs like everything else. Open `godot-game/project.godot` in Godot.
- `godot-game/.gitignore` keeps the `.godot/` cache and Windows `desktop.ini` files out. Export builds are never committed either.
- The Three.js files (`index.html`, `main.js`, `package.json`) were removed on 2026-10-22 (**Decided, D-113**), once G2 to G5 were built. They are in the git history before that date.
- **Large files:** if models and textures grow past a few hundred MB, switch them to Git LFS. Not needed yet.

Proposed layout inside `godot-game/` (the test project's folders stay as they are until the work is reorganised):

```
game/
  project.godot
  autoload/        Api.gd, Session.gd, GameData.gd, Inventory.gd
  scenes/          world, player, veins, menus
  models/          imported Blockbench FBX exports (see MODELS-BLOCKBENCH)
  sprites/         the 48×48 icons, shared with ../sprites or copied in
  data/            item tables cached from the database
```

## 6. How the code is organised (Proposed)

- **Autoloads:**
  - `Api`: every call to Supabase (ACCOUNTS-AND-DATA, section 9).
  - `Session`: who is logged in, their username, wallet and Imp.
  - `GameData`: the ore, plant and animal tables, loaded from the database at start-up.
  - `Inventory`: the player's items, tools and energy, as the server last reported them.
- **Data, not code.** A new ore, plant or animal is a new row in the item table, not a new script. The Three.js build already worked this way (one ore table drove all ten veins), and the pickaxe skins file (`godot-game/assets/models/source/pickaxe-skins.json`) shows the same idea for models.
- **One scene per kind of thing.** One `OreVein` scene with a `tier` setting, not ten vein scenes. One `Pickaxe` scene that swaps its texture per tier (MODELS-BLOCKBENCH, section 6).
- **The server is the judge.** The game plays the swing animation and asks the server what was found. It never decides drops itself (ACCOUNTS-AND-DATA, section 8).

## 7. Importing Blockbench models (Proposed; details in MODELS-BLOCKBENCH)

- Godot 4.3 and later import **FBX** directly. The test project is on 4.7.
- Blockbench models sit in a stylised cartoon world (D-047), so they must be lit by the same lights and look at home there (MODELS-BLOCKBENCH, section 10).
- Voxel textures are tiny pixel images. Godot smooths textures by default, which makes them blurry. For every Blockbench texture:
  - material **Texture Filter: Nearest**,
  - texture import **Compress Mode: Lossless** (the default compression smears small pixel textures),
  - **mipmaps off**, or Nearest-with-mipmaps if distant models shimmer.
- Set this once in a shared material or an import preset, not by hand on every model.

## 8. Open questions

1. **Phones:** desktop browsers only at first, or phones too (section 3)?
2. **Water shader:** where did the `EA_` water files come from, and what is their licence (section 2)?
3. ~~**The Three.js prototype:** keep it as a reference after G5, or delete it?~~ Answered 2026-10-22: removed (D-113).
4. **Godot version:** stay on 4.7 for both collaborators?
5. **Unused model formats:** remove the kit's FBX, FBX (Unity) or OBJ copies that Godot doesn't use (section 2)?

Answered on 2026-10-21: the project went into the repo, which was private (D-079). Since 2026-10-30 it is in the public club-impz repo under `godot-game/` (D-117). The asset pack is free and CC0, so it can be shipped and shared.

## Pass history
| Pass | Change |
|---|---|
| User addition, 2026-10-20 | Doc created. Godot engine (D-037), game type (D-036), Imp as character (D-038), Blockbench models (D-044). Test project reviewed. Milestones, layout and import settings are Proposed. Status Draft. |
| User addition, 2026-10-20 (later) | Browser game (D-046): section 3 rewritten (Compatibility renderer, GDScript only, no-threads export, size). World style (D-047) noted. Platform question replaced by the phone question. |
| User addition, 2026-10-21 | Godot project copied into `game/`, repo made private (D-079). Asset pack corrected: it is the free CC0 Quaternius kit, not a bought pack. G0 done, apart from pinning the Godot version. Open questions 2 and 3 answered; water shader and unused formats added. |
| User addition, 2026-10-22 | G2 to G5 built in `game/` (mining, energy, inventory, furnace, blacksmith) from the decided rules. In review. |
| User addition, 2026-10-22 (later) | Three.js web test removed (D-113). Section 5 and open question 3 updated. |
| User addition, 2026-10-22 (later) | Foraging, hunting, lumbering and fishing built in `game/`, plus TEST merchant, battles and treasure dig at the user's request. In review. |
| User addition, 2026-10-22 (later) | PRs #36 and #38 merged to `main`: G2 to G5 and the gathering skills are Done. |
| User addition, 2026-10-22 (later) | Renderer switched to Compatibility. Lighting retuned, water depth remapped. |
| User addition, 2026-10-22 (later) | First web export: works in the browser; size measured; ways to shrink it Proposed. |
| User addition, 2026-10-22 (later) | G6 built offline-ready: `Api` and `Save` autoloads, account section, `supabase/` SQL (not applied). See BUILD-ROADMAP M6. |
