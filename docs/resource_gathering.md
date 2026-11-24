# Resource Gathering

> Status: draft v2 · Owner: J00BA · Last updated: 2026-11-21 (sections 4.3, 5.1 to 5.3, 6, 7, 8 and the section 9 note Proposed by Claude, waiting for J00BA)
>
> How players gather every resource in the resource world: tools, tiers, gather times, drops and skill XP. This doc must agree with `game_direction.md`. Where the two differ, `game_direction.md` wins until it is updated.

---

## 1. Overview

There are five gathering skills. Each one has its own tool, its own resources and its own skill level from **1 to 100**.

| Skill | Tool | Resource | Processed into | Status |
| --- | --- | --- | --- | --- |
| Mining | Pickaxe | Ores (+ gems) | Ingots | Done (section 4) |
| Lumbering | Axe | Logs (+ sap, Proposed) | Planks | Done (section 5), sap Proposed (section 5.1) |
| Foraging | Sickle (Proposed) | Plants (+ seeds) | Plant bundles | Proposed (section 6) |
| Fishing | Rod | Fish (+ pearls) | Cooked fish | Proposed (section 7) |
| Hunting | Bow (Proposed) | Animals → hides (+ trophies) | Leather | Proposed (section 8) |

All gatherable resources live in the **resource world**. None spawn in the hub world.

---

## 2. How gathering works

These rules apply to every gathering skill.

1. **Find a resource node** in the resource world (an ore rock, a tree, a plant, a fishing spot, a mob).
2. **Check the tool.** The player needs the **minimum tool** for that node's resource tier, or better. If they don't have it, the node can't be gathered and the game says which tool is needed.
3. **Gather.** Gathering is **not instant**. The player starts the action and a progress bar fills over the resource's **gather time** (shorter with a better tool, see section 2.3). Moving away or starting another action cancels it.
4. **Receive the item.** When the bar completes, the item is added to the player's **inventory**.
5. **Earn XP.** The player earns XP in the matching skill (section 3) and player level XP (amount to be decided).
6. **Bonus drops.** Some resources can drop an extra item (for example gems while mining). Imp holders also have an extremely rare chance to find a **mint token** on any gather (see `holder_bonuses.md`).

### 2.1 Tool progression

The same ladder is used for **every** gathering tool (pickaxe, axe, and later the foraging, fishing and hunting tools). Proposed exceptions: fishing rods are made from planks (section 7.1) and bows from leather (section 8.1). Sickles use this ladder (section 6.1).

```
stone ─▶ bronze ─▶ iron ─▶ gold ─▶ obsidian ─▶ titanite ─▶ dreadstone ─▶ voidstone ─▶ stellarite
```

- **Stone tools are the starter tools.** Every new player gets a `stone_pickaxe` and a `stone_axe`.
- **The tool is the only gate** on what a player can gather. There are no skill level requirements on resources.
- Better tools are **crafted** from resources the player gathers. Recipes go in `crafting.md`.
- The **recipe** for each tool tier is unlocked by **skill level** in that tool's skill (section 2.2).
- **Bronze** is an alloy made from **tin and copper** ingots. It has no ore of its own.
- **Stellarite** is the final tool tier. Stellarite tools aren't needed to gather anything; they are the fastest tools in the game (section 2.3).

| Tool tier | Pickaxe id | Axe id | Recipe unlocks at skill level | Gathers resource tiers |
| --- | --- | --- | --- | --- |
| Stone | `stone_pickaxe` | `stone_axe` | Starter tool | T1 to T3 |
| Bronze | `bronze_pickaxe` | `bronze_axe` | 5 | Up to T4 |
| Iron | `iron_pickaxe` | `iron_axe` | 15 | Up to T5 |
| Gold | `gold_pickaxe` | `gold_axe` | 25 | Up to T6 |
| Obsidian | `obsidian_pickaxe` | `obsidian_axe` | 35 | Up to T7 |
| Titanite | `titanite_pickaxe` | `titanite_axe` | 45 | Up to T8 |
| Dreadstone | `dreadstone_pickaxe` | `dreadstone_axe` | 55 | Up to T9 |
| Voidstone | `voidstone_pickaxe` | `voidstone_axe` | 70 | Up to T10 |
| Stellarite | `stellarite_pickaxe` | `stellarite_axe` | 90 | All, fastest |

### 2.2 Tool recipe unlocks

As a skill levels up, its **skill tree** unlocks the crafting recipe for the next tool tier (the levels are in the table in section 2.1). For example, reaching **mining level 5** unlocks the `bronze_pickaxe` recipe, and **lumbering level 5** unlocks the `bronze_axe` recipe.

- The player still needs the materials to craft the tool.
- Once crafted, the tool can gather every resource up to its tier. The resources themselves have no level requirement.
- The foraging, fishing and hunting tools will follow the same unlock levels.
- The exact skill tree layout goes in `skill_trees.md`.

### 2.3 Tool speed bonus

A better tool gathers lower tier resources **a bit faster**.

- Each tool tier **above the minimum** for a resource cuts its gather time by **5%**.
- Example: coal needs a stone pickaxe (30s). With an iron pickaxe (2 tiers above) it takes 27s. With a stellarite pickaxe (8 tiers above) it takes 18s.
- Stellarite tools are 1 tier above the minimum for T10, so they gather stellarite and worldbark 5% faster.
- Skill tree speed buffs stack on top of this (see `skill_trees.md`).

---

## 3. Skill XP curve

Every gathering skill uses the **same XP curve**, levels **1 to 100**. It is the RuneScape curve, extended to level 100:

```
xp needed to reach level L = floor( sum from n = 1 to L-1 of floor( n + 300 × 2^(n / 7) ) / 4 )
```

Each level needs about **10% more XP** than the one before, so early levels fly by and the last levels are a real grind. Level 92 is roughly the halfway point in total XP.

| Level | Total XP | Level | Total XP |
| --- | --- | --- | --- |
| 2 | 83 | 60 | 273,742 |
| 5 | 388 | 70 | 737,627 |
| 10 | 1,154 | 80 | 1,986,068 |
| 20 | 4,470 | 85 | 3,258,594 |
| 30 | 13,363 | 90 | 5,346,332 |
| 40 | 37,224 | 92 | 6,517,253 |
| 50 | 101,333 | 99 | 13,034,431 |
| | | **100** | **14,391,160** |

The full table for all 100 levels should be generated from the formula in code, not typed by hand.

### 3.1 Target pace

> Goal: a player gathering **nonstop, 24 hours a day**, reaches **level 100 in about 2.5 months** (target window 2 to 3 months). One month of nonstop play is **not** enough.

### 3.2 Working

The model assumes the player crafts each new tool as soon as its recipe unlocks (section 2.2), always gathers the highest tier that tool allows, and gets the tool speed bonus (section 2.3). It ignores time lost to walking and selling, so real play will be slower.

XP per hour for a resource = `(xp per gather + gem chance × gem xp) × 3600 / gather time`.

Mining, nonstop:

| Reached level | Hours | Days |
| --- | --- | --- |
| 10 | 0.3 | under 1 |
| 30 | 2.7 | under 1 |
| 50 | 17 | 0.7 |
| 70 | 108 | 4.5 |
| 90 | 701 | 29 |
| 99 | 1,642 | 68 |
| **100** | **1,808** | **75 (about 2.5 months)** |

- Fast start: level 10 in under 20 minutes, level 50 within the first day.
- After one month of nonstop play the player is around level 90, with more than half the XP for 100 still to go.
- A more normal 4 hours a day is roughly 15 months to level 100.
- Lumbering is tuned to the same pace (section 5).

Changing pace later is easy: scale every XP value in sections 4 and 5 by the same amount (for example × 0.8 makes 100 take about 94 days).

---

## 4. Mining

- **Tool:** pickaxe. Starts with `stone_pickaxe`.
- **Nodes:** ore rocks in the resource world.
- **Output:** one ore per successful mine. Ores are smelted into ingots at a station (see `crafting.md`).
- **Bonus drop:** each ore has a chance to drop its gem (section 4.2).

### 4.1 Ores

| Ore | Tier | Ore id | Ingot id | Time to mine | Minimum pickaxe | XP per ore | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coal | T1 | `coal` | `coal` (no ingot) | 30s | Stone | 20 | 2,496 |
| Tin | T2 | `tin_ore` | `tin_ingot` | 45s | Stone | 32 | 3,072 |
| Copper | T3 | `copper_ore` | `copper_ingot` | 45s | Stone | 40 | 3,733 |
| Iron | T4 | `iron_ore` | `iron_ingot` | 60s | Bronze | 65 | 4,420 |
| Gold | T5 | `gold_ore` | `gold_ingot` | 120s | Iron | 150 | 4,950 |
| Obsidian | T6 | `obsidian_ore` | `obsidian_ingot` | 240s | Gold | 330 | 5,346 |
| Titanite | T7 | `titanite_ore` | `titanite_ingot` | 300s | Obsidian | 450 | 5,760 |
| Dreadstone | T8 | `dreadstone_ore` | `dreadstone_ingot` | 300s | Titanite | 520 | 6,490 |
| Voidstone | T9 | `voidstone_ore` | `voidstone_ingot` | 600s | Dreadstone | 1,150 | 7,130 |
| Stellarite | T10 | `stellarite_ore` | `stellarite_ingot` | 1000s | Voidstone | 2,100 | 7,762 |

Time to mine is with the minimum pickaxe; better pickaxes are faster (section 2.3). XP per hour is with the minimum pickaxe and includes the average XP from gems.

### 4.2 Gems

Gems drop as a bonus while mining their ore. The ore is still received. A gem gives **double the XP of its ore**. Gem rarity does not follow resource tier on purpose (for example diamond is rarer than topaz).

| Gem | Tier | Gem id | Found when mining | Chance | XP per gem |
| --- | --- | --- | --- | --- | --- |
| Diamond | T1 | `diamond` | Coal | 1/50 | 40 |
| Topaz | T2 | `topaz` | Tin | 1/10 | 64 |
| Sapphire | T3 | `sapphire` | Copper | 1/12 | 80 |
| Amethyst | T4 | `amethyst` | Iron | 1/15 | 130 |
| Ruby | T5 | `ruby` | Gold | 1/20 | 300 |
| Emerald | T6 | `emerald` | Obsidian | 1/25 | 660 |
| Jade | T7 | `jade` | Titanite | 1/30 | 900 |
| Painite | T8 | `painite` | Dreadstone | 1/50 | 1,040 |
| Arcanium | T9 | `arcanium` | Voidstone | 1/60 | 2,300 |
| Eclipsium | T10 | `eclipsium` | Stellarite | 1/75 | 4,200 |

### 4.3 Ore events

> **Proposed** by Claude on 2026-11-21: this writes down what J00BA's build already does (`godot-game/autoload/ore_events.gd`, `scripts/player/ore_miner.gd`), so the doc matches the game.

- The resource world in the build has five biomes (forest to swamp). Void and Stellar aren't in it yet, so **voidstone and stellarite come only from ore events**.
- Each minute there is a **1 in 45** chance of a voidstone vein and a **1 in 120** chance of a stellarite vein. A vein stays for **15 minutes** at one of 48 event spots, and every player sees a banner for 5 seconds. Online, the server rolls the events so everyone gets the same vein.
- Anyone with a good enough pickaxe can mine an event vein at the same time. Each swing has a chance to give the ore, about one ore per time to mine, so no player holds the vein.
- A voidstone vein is up about 29% of the time and a stellarite vein about 12%. With that, mining takes about **1,901 hours (79 days)** to level 100, against 75 in section 3.2. That is still inside the target.
- Fishing shoals (section 7.4) and legendary hunts (section 8.3) are Proposed as events of the same kind.

---

## 5. Lumbering

- **Tool:** axe. Starts with `stone_axe`.
- **Nodes:** trees in the resource world.
- **Output:** one log per successful chop. Logs are processed into planks at a station (see `crafting.md`).
- **Bonus drop:** none for now. Proposed: each tree drops its sap (section 5.1).

Lumbering has no gems, so each log gives a little more XP than the matching ore. That keeps both skills at the same pace (about 75 days nonstop to level 100). Time to chop and XP per hour are with the minimum axe.

| Tree | Tier | Log id | Planks id | Time to chop | Minimum axe | XP per log | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pine | T1 | `pine_log` | `pine_planks` | 30s | Stone | 22 | 2,640 |
| Birch | T2 | `birch_log` | `birch_planks` | 45s | Stone | 38 | 3,040 |
| Oak | T3 | `oak_log` | `oak_planks` | 45s | Stone | 48 | 3,840 |
| Maple | T4 | `maple_log` | `maple_planks` | 60s | Bronze | 75 | 4,500 |
| Hickory | T5 | `hickory_log` | `hickory_planks` | 120s | Iron | 165 | 4,950 |
| Frostbark | T6 | `frostbark_log` | `frostbark_planks` | 240s | Gold | 355 | 5,325 |
| Titanwood | T7 | `titanwood_log` | `titanwood_planks` | 300s | Obsidian | 480 | 5,760 |
| Runewood | T8 | `runewood_log` | `runewood_planks` | 300s | Titanite | 540 | 6,480 |
| Gembark | T9 | `gembark_log` | `gembark_planks` | 600s | Dreadstone | 1,190 | 7,140 |
| Worldbark | T10 | `worldbark_log` | `worldbark_planks` | 1000s | Voidstone | 2,160 | 7,776 |

### 5.1 Sap (Proposed)

> **Proposed** by Claude on 2026-11-21, waiting for J00BA. Every other skill has a rare drop (gems, seeds, pearls, trophies). This gives trees one too, using the IMPLINGZ rule that each tree drops a sap or amber at the gem chances (D-108).

Sap works like gems (section 4.2). The log is still received, and sap gives double its log's XP. Each tree uses the gem chance of the same ore tier. To keep lumbering at the same pace, the log XP drops to the ore XP of the same tier. Lumbering then earns exactly what mining earns (75.3 days to level 100, against 75.2 now).

| Tree | Tier | Sap | Sap id | Chance | XP per log (now → Proposed) | XP per sap |
| --- | --- | --- | --- | --- | --- | --- |
| Pine | T1 | Pine Resin | `pine_sap` | 1/50 | 22 → 20 | 40 |
| Birch | T2 | Birch Sap | `birch_sap` | 1/10 | 38 → 32 | 64 |
| Oak | T3 | Oak Resin | `oak_sap` | 1/12 | 48 → 40 | 80 |
| Maple | T4 | Maple Sap | `maple_sap` | 1/15 | 75 → 65 | 130 |
| Hickory | T5 | Hickory Amber | `hickory_sap` | 1/20 | 165 → 150 | 300 |
| Frostbark | T6 | Frostbark Amber | `frostbark_sap` | 1/25 | 355 → 330 | 660 |
| Titanwood | T7 | Titanwood Amber | `titanwood_sap` | 1/30 | 480 → 450 | 900 |
| Runewood | T8 | Runewood Amber | `runewood_sap` | 1/50 | 540 → 520 | 1,040 |
| Gembark | T9 | Gembark Amber | `gembark_sap` | 1/60 | 1,190 → 1,150 | 2,300 |
| Worldbark | T10 | Worldbark Amber | `worldbark_sap` | 1/75 | 2,160 → 2,100 | 4,200 |

- Ids follow the build's `<tree>_sap` pattern (`game_data.gd:305`).
- Icons: `sap_pine`, `sap_birch` and `sap_oak` already exist. The IMPLINGZ amber icons can stand in by tier colour until the others are drawn.
- **Open question:** what sap is for, beyond selling to the merchant (D-124). The same is open for pearls.

### 5.2 Felling and regrowth

> **Proposed:** this writes down the build (`scripts/world/lumbering.gd:11`, J00BA, 2026-11-08).

- When the bar fills, the tree falls and leaves a stump. It grows back after **5 minutes**.
- A felled tree is felled **only for the player who chopped it**. Other players still see it standing, so trees stay shared (section 9).
- This differs from section 9 (nodes never run out) and from D-105 (a tree grows back after 10 seconds). The section 9 note follows the build.

### 5.3 Wood hilts (Proposed)

The tool recipes need wood hilts. D-107 makes the Ash Wood Hilt from 5 Ash planks and the Oak Wood Hilt from 5 Oak planks, and the build does the same (`game_data.gd:163`). This doc's trees have no Ash, so in this world the first crafted tools could never be made.

- **Proposed:** a **Pine Wood Hilt** (`pine_hilt`) from 5 Pine planks replaces the Ash Wood Hilt. Pine is tier 1 and is chopped with the starter axe, which is why D-107 put Ash at tier 1.
- The Oak Wood Hilt stays as it is. Oak is tier 3 in both tree lists.
- The full recipes belong in `crafting.md`, which isn't written yet.

---

## 6. Foraging

> **Proposed** by Claude on 2026-11-21, waiting for J00BA. J00BA's placeholder asked for a plant table. The IMPLINGZ docs already have one (D-022 to D-027 and D-061 to D-066 in `DECISIONS.md`, built in the test scene), so this section fits it into this doc's rules. Where the two doc sets differ, it follows the newer one. The reasons are in `reports/2026-11-21-gathering-expansion.md`.

- **Tool:** sickle. Starts with `stone_sickle`.
- **Nodes:** plants in the resource world (section 6.3).
- **Output:** one plant per pick. A drying rack turns 2 to 5 plants (by tier) into one plant bundle, with no fuel and no energy (D-062). Bundles are used for taming in a later update, and for potions and Impling food (D-023).
- **Bonus drop:** each plant can come with its seed (section 6.2). Seeds are for farming, which isn't designed yet (D-065).
- **Picking:** the Imp crouches and picks while the progress bar fills.
- **Energy:** a pick spends 5 energy while there is energy left (D-061). With no energy left, foraging still gives plants and XP (D-123).

### 6.1 Sickles

Sickles use the section 2.1 ladder, the same as pickaxes and axes: `stone_sickle` to `stellarite_sickle`, with the same recipe unlock levels and the same tiers they can pick. Section 2.1 is newer than D-063, and it already names foraging tools as part of the ladder.

- **Conflict:** D-063 gives one sickle per plant tier, including a Steel sickle, and the Stone sickle picks only Nettle. The build follows D-063 (`game_data.gd:352`). D-063 stays as it is until both collaborators agree.
- D-063's recipes (each sickle costs the same as that pickaxe) still fit. They belong in `crafting.md`.

### 6.2 Plants and seeds

Pick times follow the mining ladder (section 4.1). XP per plant is set so each tier earns the same XP per hour as the ore of that tier. Plant names are from D-026. Time to pick and XP per hour are with the minimum sickle, and XP per hour includes the average XP from seeds.

| Plant | Tier | Plant id | Bundle id | Time to pick | Minimum sickle | XP per plant | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nettle | T1 | `nettle` | `nettle_bundle` | 30s | Stone | 17 | 2,448 |
| Marigold | T2 | `marigold` | `marigold_bundle` | 45s | Stone | 33 | 3,115 |
| Bluebell | T3 | `bluebell` | `bluebell_bundle` | 45s | Stone | 40 | 3,712 |
| Thornroot | T4 | `thornroot` | `thornroot_bundle` | 60s | Bronze | 65 | 4,446 |
| Sunpetal | T5 | `sunpetal` | `sunpetal_bundle` | 120s | Iron | 147 | 4,939 |
| Nightshade | T6 | `nightshade` | `nightshade_bundle` | 240s | Gold | 324 | 5,346 |
| Frostbloom | T7 | `frostbloom` | `frostbloom_bundle` | 300s | Obsidian | 444 | 5,754 |
| Bloodcap | T8 | `bloodcap` | `bloodcap_bundle` | 300s | Titanite | 510 | 6,487 |
| Voidlily | T9 | `voidlily` | `voidlily_bundle` | 600s | Dreadstone | 1,143 | 7,132 |
| Starmoss | T10 | `starmoss` | `starmoss_bundle` | 1000s | Voidstone | 2,114 | 7,763 |

Seeds work like gems (section 4.2). The plant is still received, and a seed gives double its plant's XP. The chance falls from 10% to 1% by tier (D-025). These are the same chances as pearls, so the XP values match the fish in section 7.2.

| Seed | Tier | Seed id | Found when picking | Chance | XP per seed |
| --- | --- | --- | --- | --- | --- |
| Nettle seed | T1 | `nettle_seed` | Nettle | 10% | 34 |
| Marigold seed | T2 | `marigold_seed` | Marigold | 9% | 66 |
| Bluebell seed | T3 | `bluebell_seed` | Bluebell | 8% | 80 |
| Thornroot seed | T4 | `thornroot_seed` | Thornroot | 7% | 130 |
| Sunpetal seed | T5 | `sunpetal_seed` | Sunpetal | 6% | 294 |
| Nightshade seed | T6 | `nightshade_seed` | Nightshade | 5% | 648 |
| Frostbloom seed | T7 | `frostbloom_seed` | Frostbloom | 4% | 888 |
| Bloodcap spores | T8 | `bloodcap_seed` | Bloodcap | 3% | 1,020 |
| Voidlily seed | T9 | `voidlily_seed` | Voidlily | 2% | 2,286 |
| Starmoss spores | T10 | `starmoss_seed` | Starmoss | 1% | 4,228 |

- Ids are the build's (`game_data.gd:279`). All icons exist (`plant_`, `bundle_` and `seed_` files, `02-resources.md`).
- Player XP follows D-121: 1 per second of pick time, and a seed gives the same again.

### 6.3 Where to forage

Nettle grows in every biome, the way coal is in almost every biome. Some plants need a better sickle than their biome's other resources, so players come back later.

| Biome | Plants (resource tier) |
| --- | --- |
| Forest | Nettle (T1), marigold (T2), bluebell (T3), bloodcap (T8) |
| Mountain | Nettle (T1), thornroot (T4), starmoss (T10) by the highest peak |
| Frost | Nettle (T1), frostbloom (T7) |
| Plains | Nettle (T1), marigold (T2), sunpetal (T5) |
| Swamp | Nettle (T1), nightshade (T6), bloodcap (T8), voidlily (T9) |

- Every tier grows in one of the five biomes the build has, so foraging needs no events. Bloodcap in the forest and starmoss by the highest peak are the goals to come back for, like worldbark in the forest.
- If the Void and Stellar biomes are built, voidlily and starmoss can move there.

### 6.4 Picking and regrowth

- A picked plant is gone **only for the player who picked it**, and grows back after **5 minutes**. This is the build's rule for trees (section 5.2). It replaces D-064's 10 seconds, which made sense with D-007's short gathers but not with gather times of 30 to 1,000 seconds.
- Plants are fixed in place like trees, so nothing needs sending over the network.

### 6.5 Pace

Sickles follow the section 2.1 ladder and every tier grows in the world, so foraging has the same pace as mining: about **1,808 hours (75 days)** to level 100.

- **Open question:** taming. D-071 tames an Eclipse Dragon with Starmoss bundles at a 5% chance: on average 20 bundles, which is 100 Starmoss. At 1,000 seconds a pick that is about 28 hours of nonstop picking. That fits a late-game goal, but it is a big change from the 10-second picks the IMPLINGZ tables were costed on (`02-resources.md`).

---

## 7. Fishing

> **Proposed** by Claude on 2026-11-21, waiting for J00BA. This section fits the IMPLINGZ fishing rules (D-109 to D-112 in `DECISIONS.md`, built in the test scene) into this doc's gathering system. Where the two doc sets differ, it follows the newer one. The reasons are in `reports/2026-11-21-fishing-skill.md`.

- **Tool:** fishing rod. Starts with `driftwood_rod`.
- **Nodes:** fishing spots on the water in the resource world (section 7.3).
- **Output:** one fish per catch. A campfire cooks raw fish and burns logs as fuel. Cooked fish is food for battle animals (D-111).
- **Bonus drop:** each fish can come with its pearl (section 7.2).
- **Catching:** press F to cast. The progress bar fills over the time to catch while a fish circles closer. Then it bites and a short timing window opens. Press F inside the window to land the fish (D-109). A missed bite loses the fish and drops the bar to half.
- **Energy:** a catch spends 5 energy while there is energy left (D-109). With no energy left, fishing still gives fish and XP (D-123).

### 7.1 Rods

Rods don't use the section 2.1 ladder. Each fish tier has its own rod, made from planks (D-110). J00BA's PR #100 (2026-11-15) builds these ten rods, so this is the newer rule. A rod catches its own tier and every tier below. The speed bonus in section 2.3 applies for each rod tier above the fish's tier.

| Rod | Tier | Rod id | Recipe (D-110) | Recipe unlocks at fishing level | Catches |
| --- | --- | --- | --- | --- | --- |
| Driftwood | 1 | `driftwood_rod` | Starter rod, free | Starter | T1 |
| Ash | 2 | `ash_rod` | 10 Ash planks | 2 | Up to T2 |
| Birch | 3 | `birch_rod` | 10 Birch planks | 3 | Up to T3 |
| Oak | 4 | `oak_rod` | 10 Oak planks | 5 | Up to T4 |
| Pine | 5 | `pine_rod` | 10 Pine planks | 15 | Up to T5 |
| Goldleaf | 6 | `goldleaf_rod` | 10 Goldleaf planks | 25 | Up to T6 |
| Ebony | 7 | `ebony_rod` | 10 Ebony planks | 35 | Up to T7 |
| Silverbark | 8 | `silverbark_rod` | 10 Silverbark planks | 45 | Up to T8 |
| Bloodwood | 9 | `bloodwood_rod` | 10 Bloodwood planks | 55 | Up to T9 |
| Voidwood | 10 | `voidwood_rod` | 10 Voidwood planks | 70 | All |

- Levels 5 to 70 match section 2.1 for the same resource tier. The starter rod catches only Minnow, so the Ash and Birch rods unlock at levels 2 and 3, within the first few minutes.
- No rod sits above Voidwood, so fishing has no level 90 speed tool like Stellarite.
- **Open question:** the recipe woods are the IMPLINGZ trees (`02-resources.md`), not the section 5 trees (Pine to Worldbark). Whichever tree list wins sets each rod's recipe, and maybe its name.

### 7.2 Fish and pearls

Catch times follow the mining ladder (section 4.1). XP per fish is set so each tier earns the same XP per hour as the ore of that tier. Fish names are from D-109. Time to catch and XP per hour are with the minimum rod, and XP per hour includes the average XP from pearls.

| Fish | Tier | Fish id | Cooked id | Time to catch | Minimum rod | XP per fish | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minnow | T1 | `minnow` | `cooked_minnow` | 30s | Driftwood | 17 | 2,448 |
| Perch | T2 | `perch` | `cooked_perch` | 45s | Ash | 33 | 3,115 |
| Trout | T3 | `trout` | `cooked_trout` | 45s | Birch | 40 | 3,712 |
| Catfish | T4 | `catfish` | `cooked_catfish` | 60s | Oak | 65 | 4,446 |
| Goldfin Carp | T5 | `goldfin_carp` | `cooked_goldfin_carp` | 120s | Pine | 147 | 4,939 |
| Shadow Eel | T6 | `shadow_eel` | `cooked_shadow_eel` | 240s | Goldleaf | 324 | 5,346 |
| Frostscale Pike | T7 | `frostscale_pike` | `cooked_frostscale_pike` | 300s | Ebony | 444 | 5,754 |
| Bloodfin Snapper | T8 | `bloodfin_snapper` | `cooked_bloodfin_snapper` | 300s | Silverbark | 510 | 6,487 |
| Void Angler | T9 | `void_angler` | `cooked_void_angler` | 600s | Bloodwood | 1,143 | 7,132 |
| Starfin Koi | T10 | `starfin_koi` | `cooked_starfin_koi` | 1000s | Voidwood | 2,114 | 7,763 |

Pearls work like gems (section 4.2). The fish is still received, and a pearl gives double its fish's XP. The chance falls from 10% to 1% by tier (D-112).

| Pearl | Tier | Pearl id | Found when catching | Chance | XP per pearl |
| --- | --- | --- | --- | --- | --- |
| River Pearl | T1 | `river_pearl` | Minnow | 10% | 34 |
| Sand Pearl | T2 | `sand_pearl` | Perch | 9% | 66 |
| Moss Pearl | T3 | `moss_pearl` | Trout | 8% | 80 |
| Black Pearl | T4 | `black_pearl` | Catfish | 7% | 130 |
| Golden Pearl | T5 | `golden_pearl` | Goldfin Carp | 6% | 294 |
| Shadow Pearl | T6 | `shadow_pearl` | Shadow Eel | 5% | 648 |
| Frost Pearl | T7 | `frost_pearl` | Frostscale Pike | 4% | 888 |
| Blood Pearl | T8 | `blood_pearl` | Bloodfin Snapper | 3% | 1,020 |
| Void Pearl | T9 | `void_pearl` | Void Angler | 2% | 2,286 |
| Star Pearl | T10 | `star_pearl` | Starfin Koi | 1% | 4,228 |

- Player XP follows D-121: 1 per second of catch time, and a pearl gives the same again.
- **Open question:** what pearls are for, beyond selling to the merchant (D-124).

### 7.3 Where to fish

Minnow lives in every water, the way coal is in almost every biome. Some fish need a better rod than their biome's other resources, so players come back later.

| Biome | Water | Fish (resource tier) |
| --- | --- | --- |
| Forest | River | Minnow (T1), perch (T2), trout (T3) |
| Forest | Swan pond | Minnow (T1), trout (T3), catfish (T4) |
| Frost | Open pools in the frozen lakes | Minnow (T1), frostscale pike (T7) |
| Plains | Watering holes | Minnow (T1), goldfin carp (T5) |
| Swamp | Swamp water | Minnow (T1), shadow eel (T6), bloodfin snapper (T8) |
| Any | A shoal event (section 7.4) | Void angler (T9) or starfin koi (T10) |

- Void and Stellar have no water (`game_worlds.md` sections 4.8.6 and 4.8.7), so tiers 9 and 10 come only from shoals. Mountain water has no fish yet.
- Spots are fixed in place and shared, like every other node (section 9): 4 along each shore and 8 in the swamp. This answers open question 3 for fishing.
- **Conflict:** D-109 says a spot refreshes 10 seconds after a catch, but section 9 says nodes never run out. Section 9 is newer, so this section follows it. D-109 stays as it is until both collaborators agree.

### 7.4 Shoal events

- A shoal appears at one fishing spot for 15 minutes, with a banner for everyone. It reuses the ore events the build already runs for voidstone and stellarite (`godot-game/autoload/ore_events.gd`).
- Each minute there is a 1 in 45 chance of a Void Angler shoal and a 1 in 120 chance of a Starfin Koi shoal, the same odds as the ore events. A void shoal is up about 29% of the time and a stellar shoal about 12%.
- Shoals need their own list of shore spots. The build's 48 event spots are on land.
- **Open question:** daily caps. Shoals follow whatever rule the ore events get.

### 7.5 Pace

This uses the section 3.2 method. Between shoals the player catches the best fish in normal water (Bloodfin Snapper).

| Reached level | Hours | Days |
| --- | --- | --- |
| 10 | 0.3 | under 1 |
| 30 | 2.7 | under 1 |
| 50 | 17 | 0.7 |
| 70 | 110 | 4.6 |
| 90 | 737 | 31 |
| 99 | 1,783 | 74 |
| **100** | **1,967** | **82 (about 2.7 months)** |

- Fishing is a week slower than mining (75 days) because the top fish only come from shoals and there is no level 90 rod. It is still inside the 2 to 3 month target (section 3.1).
- To match mining exactly, multiply every fishing XP value by about 1.09.
- **Open question:** at tiers 9 and 10, one F press after a 10 to 17 minute wait is thin play, and a bot could time it from the bar. A reel step after the bite is one answer (idea 5 in `reports/2026-11-21-fishing-expansion.md`).

---

## 8. Hunting

> **Proposed** by Claude on 2026-11-21, waiting for J00BA. J00BA's placeholder asked for a mob table. The IMPLINGZ docs already have one: 16 animals with hides, leathers, trophies and bows (D-028 to D-035 and D-067 to D-072 in `DECISIONS.md`, built in the test scene). This section fits it into this doc's rules. Tiers 1 to 10 are hunted like every other resource. Tiers 11 to 16 don't fit the 10-tier ladder, so they become rare legendary hunts (section 8.3) and none of the 16 is dropped. Mob behaviour still belongs in `world_mobs.md`. The reasons are in `reports/2026-11-21-gathering-expansion.md`.

- **Tool:** bow (D-030; `game_direction.md` section 5 lists bows as a crafted tool). Starts with `hare_bow`.
- **Nodes:** animals in the resource world (section 8.4). Each has a home and wanders round it, like the build's mobs (`scripts/world/mob.gd`). An animal stands still while it is being hunted. Animals don't run away or fight back (D-067).
- **Output:** one hide per hunt. A tanning rack turns 2 to 5 hides (by tier) into one leather, with no fuel and no energy (D-068). Leather makes bows (D-069) and cosmetic outfits (D-104).
- **Bonus drop:** each animal can drop its trophy (section 8.2). Trophies go in the trophy cabinet (D-103).
- **Hunting:** the Imp shoots three arrows while the progress bar fills. The third lands as the bar completes, and the animal goes poof (D-028, D-067).
- **Respawn:** a hunted animal is gone **only for the player who hunted it**, and comes back after **5 minutes**, like trees and plants (sections 5.2 and 6.4). This replaces D-067's 10 seconds.
- **Energy:** a hunt spends 5 energy while there is energy left (D-067). With no energy left, hunting still gives hides and XP (D-123).
- Taming (D-071) and tracking (D-072) don't change. Taming comes in a later update (`game_direction.md` section 5).

### 8.1 Bows

Bows don't use the section 2.1 ladder. Each animal tier has its own bow, made from 10 leather of the tier below (D-069), the same way rods are made from planks (section 7.1). A bow hunts its own tier and every tier below (D-034). The speed bonus in section 2.3 applies for each bow tier above the animal's tier, counting up to the Starwyrm Bow: the legendary bows hunt the normal animals at the Starwyrm Bow's speed.

| Bow | Tier | Bow id | Recipe (D-069) | Recipe unlocks at hunting level | Hunts |
| --- | --- | --- | --- | --- | --- |
| Hare Bow | 1 | `hare_bow` | Starter bow, free | Starter | T1 |
| Fox Bow | 2 | `fox_bow` | 10 Hare leather | 2 | Up to T2 |
| Boar Bow | 3 | `boar_bow` | 10 Fox leather | 3 | Up to T3 |
| Wolf Bow | 4 | `wolf_bow` | 10 Boar leather | 5 | Up to T4 |
| Goldhorn Stag Bow | 5 | `goldhorn_stag_bow` | 10 Wolf leather | 15 | Up to T5 |
| Shadowcat Bow | 6 | `shadowcat_bow` | 10 Goldhorn Stag leather | 25 | Up to T6 |
| Frostmane Yeti Bow | 7 | `frostmane_yeti_bow` | 10 Shadowcat leather | 35 | Up to T7 |
| Cinder Salamander Bow | 8 | `cinder_salamander_bow` | 10 Frostmane Yeti leather | 45 | Up to T8 |
| Voidstalker Bow | 9 | `voidstalker_bow` | 10 Cinder Salamander leather | 55 | Up to T9 |
| Starwyrm Bow | 10 | `starwyrm_bow` | 10 Voidstalker leather | 70 | Up to T10 |
| Stormhorn Ram Bow | 11 | `stormhorn_ram_bow` | 10 Starwyrm leather | 75 | Up to legendary T11 |
| Tidecrest Serpent Bow | 12 | `tidecrest_serpent_bow` | 10 Stormhorn Ram leather | 78 | Up to legendary T12 |
| Mossmane Behemoth Bow | 13 | `mossmane_behemoth_bow` | 10 Tidecrest Serpent leather | 81 | Up to legendary T13 |
| Crystalback Basilisk Bow | 14 | `crystalback_basilisk_bow` | 10 Mossmane Behemoth leather | 84 | Up to legendary T14 |
| Sunfeather Griffin Bow | 15 | `sunfeather_griffin_bow` | 10 Crystalback Basilisk leather | 87 | Up to legendary T15 |
| Eclipse Dragon Bow | 16 | `eclipse_dragon_bow` | 10 Sunfeather Griffin leather | 90 | All |

- Levels 5 to 70 match section 2.1 for the same resource tier, as the rods do. The legendary bows unlock every 3 levels from 75, so the whole set is open at level 90, like the Stellarite tools.
- Bow names are Proposed in `02-resources.md`. Ids are the build's (`game_data.gd:357`).

### 8.2 Animals and trophies

Hunt times follow the mining ladder (section 4.1). XP per hide is set so each tier earns the same XP per hour as the ore of that tier. Animal names are from D-032. Time to hunt and XP per hour are with the minimum bow, and XP per hour includes the average XP from trophies.

| Animal | Tier | Hide id | Leather id | Time to hunt | Minimum bow | XP per hide | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hare | T1 | `hare_hide` | `hare_leather` | 30s | Hare | 17 | 2,448 |
| Fox | T2 | `fox_hide` | `fox_leather` | 45s | Fox | 32 | 3,041 |
| Boar | T3 | `boar_hide` | `boar_leather` | 45s | Boar | 40 | 3,763 |
| Wolf | T4 | `wolf_hide` | `wolf_leather` | 60s | Wolf | 63 | 4,400 |
| Goldhorn Stag | T5 | `goldhorn_stag_hide` | `goldhorn_stag_leather` | 120s | Goldhorn Stag | 143 | 4,942 |
| Shadowcat | T6 | `shadowcat_hide` | `shadowcat_leather` | 240s | Shadowcat | 313 | 5,352 |
| Frostmane Yeti | T7 | `frostmane_yeti_hide` | `frostmane_yeti_leather` | 300s | Frostmane Yeti | 426 | 5,766 |
| Cinder Salamander | T8 | `cinder_salamander_hide` | `cinder_salamander_leather` | 300s | Cinder Salamander | 485 | 6,495 |
| Voidstalker | T9 | `voidstalker_hide` | `voidstalker_leather` | 600s | Voidstalker | 1,076 | 7,127 |
| Starwyrm | T10 | `starwyrm_hide` | `starwyrm_leather` | 1000s | Starwyrm | 1,974 | 7,760 |

Trophies work like gems (section 4.2). The hide is still received, and a trophy gives double its hide's XP. The chance falls from 10% by 0.6% a tier (D-033).

| Trophy | Tier | Trophy id | Found when hunting | Chance | XP per trophy |
| --- | --- | --- | --- | --- | --- |
| Lucky Foot | T1 | `lucky_foot` | Hare | 10.0% | 34 |
| Brush Tail | T2 | `brush_tail` | Fox | 9.4% | 64 |
| Boar Tusk | T3 | `boar_tusk` | Boar | 8.8% | 80 |
| Wolf Fang | T4 | `wolf_fang` | Wolf | 8.2% | 126 |
| Golden Antler | T5 | `golden_antler` | Goldhorn Stag | 7.6% | 286 |
| Shadow Claw | T6 | `shadow_claw` | Shadowcat | 7.0% | 626 |
| Frozen Heart | T7 | `frozen_heart` | Frostmane Yeti | 6.4% | 852 |
| Ember Scale | T8 | `ember_scale` | Cinder Salamander | 5.8% | 970 |
| Void Eye | T9 | `void_eye` | Voidstalker | 5.2% | 2,152 |
| Star Horn | T10 | `star_horn` | Starwyrm | 4.6% | 3,948 |

- A tamed animal tracking for the player still multiplies trophy chances by 1.5 (D-072).
- Player XP follows D-121: 1 per second of hunt time, and a trophy gives the same again.

### 8.3 Legendary hunts

The six highest animals appear only as events, the same kind as ore events (section 4.3).

- Each minute there is a **1 in 60** chance of a legendary hunt. The beast is picked by weight, so the higher ones are rarer: 6, 5, 4, 3, 2, 1 for tiers 11 to 16. An Eclipse Dragon is 1 hunt in 21, about once a day.
- The beast stays for **15 minutes** at an event spot in its home biome, and everyone sees a banner. Anyone with a good enough bow can shoot it at the same time. Each shot has a chance to give its hide, about one hide per 300 seconds (3 in a 15-minute hunt), so no player holds it.
- A legendary hunt is up about 22% of the time. Its XP per hour is 9% higher per tier than the Starwyrm's, so it helps but isn't needed for the pace. Hides come faster than normal animals, so each hide gives less XP.

| Beast | Tier | Home biome | XP per hide | Trophy | Chance | XP per trophy |
| --- | --- | --- | --- | --- | --- | --- |
| Stormhorn Ram | T11 | Mountain | 653 | Thunder Curl | 4.0% | 1,306 |
| Tidecrest Serpent | T12 | Frost | 719 | Abyss Pearl | 3.4% | 1,438 |
| Mossmane Behemoth | T13 | Swamp | 793 | Verdant Mane | 2.8% | 1,586 |
| Crystalback Basilisk | T14 | Mountain | 874 | Prism Shard | 2.2% | 1,748 |
| Sunfeather Griffin | T15 | Plains | 964 | Sun Feather | 1.6% | 1,928 |
| Eclipse Dragon | T16 | Swamp | 1,063 | Eclipse Crown | 1.0% | 2,126 |

- J00BA's lairs make good event spots: the obsidian cave and the highest peak (mountain), the ice spire (frost) and the swamp entrance, where the dark dragon waits (`resource_landmarks.gd:42-46`).
- **Open question: the legendary grind.** Each legendary bow takes 50 hides of the beast below (D-068, D-069), about 17 hunts of it. With the odds above, a Stormhorn Ram comes about every 3.5 hours and a Sunfeather Griffin every 10.5, so the whole set of legendary bows takes about 21 days of being online. An Eclipse Dragon leather (D-104's top outfit) takes about 2 dragon hunts, roughly 2 days. That suits a top-end goal, but it is slow. Raising the odds to 1 in 30 a minute halves every figure.

### 8.4 Where to hunt

Hares live in every biome, the way coal is in almost every biome. Some animals need a better bow than their biome's other resources, so players come back later.

| Biome | Animals (resource tier) |
| --- | --- |
| Forest | Hare (T1), fox (T2), boar (T3) |
| Mountain | Hare (T1), wolf (T4), cinder salamander (T8) by the obsidian cave |
| Frost | Hare (T1), wolf (T4), frostmane yeti (T7), starwyrm (T10) by the ice spire |
| Plains | Hare (T1), fox (T2), goldhorn stag (T5) |
| Swamp | Hare (T1), shadowcat (T6), voidstalker (T9) |

- Wolves already roam the forest, mountain and frost in the build (`resource_landmarks.gd:30`). Under this proposal they are the Wolf (T4) and can be hunted where they live in mountain and frost. The forest wolf packs would need moving, or the starter forest has a tier 4 animal.
- **Open question:** J00BA's other mobs (cows, highland cows, pigs, ogres, the stone golem and the dragons) aren't in the animal list. Proposed: they stay as scenery that can't be hunted. J00BA may prefer to use some of them as models instead (the pig for the Boar, the dark dragon for the Eclipse Dragon). The other animals still need models (D-115).
- **Open question:** the build gives every player a sword (`game_data.gd:159`: "no gathering skill yet"). Under this proposal it isn't a hunting tool.

### 8.5 Pace

This uses the section 3.2 method, with the bows' unlock levels above.

| Reached level | Hours | Days |
| --- | --- | --- |
| 10 | 0.3 | under 1 |
| 30 | 2.7 | under 1 |
| 50 | 17 | 0.7 |
| 70 | 107 | 4.5 |
| 90 | 701 | 29 |
| 99 | 1,692 | 70 |
| **100** | **1,867** | **78 (about 2.6 months)** |

- Hunting is 3 days slower than mining because its last speed step is the Starwyrm Bow (level 70), with nothing like the Stellarite tools at 90. Legendary hunts make up some of that for players who join them.
- To match mining exactly, multiply every hunting XP value by about 1.03.
- If the legendary bows also hunted the normal animals faster, level 100 would take 64 days. That is why they don't.

---

## 9. Resource placement

- Resource nodes are **placed in the world from the start**. They are part of the map and never move or spawn somewhere new.
- Nodes **never run out**. An ore rock, tree or plant stays after it is gathered and can be gathered again straight away.
- Higher tier nodes mostly sit deeper in the resource world. Which resources are in each biome is in `game_worlds.md` section 4.
- Nodes are shared: any number of players can gather from the same node at once.
- **Proposed note (2026-11-21):** the build fells trees (section 5.2). So ore rocks and fishing spots never run out, while trees, plants and animals are gone **for the player who gathered them** for 5 minutes, then come back (sections 5.2, 6.4 and 8). Other players can still gather them, so every node stays shared.

---

## 10. Open questions

1. How much player level XP does each gather give?
2. Inventory size and what happens when it is full.
3. Fishing spots and mobs: are they fixed in place like ores and trees, and do mobs respawn after being hunted? (Proposed for fishing spots: fixed and shared, section 7.3. Proposed for animals: each has a fixed home, and a hunted animal comes back after 5 minutes for that player, section 8.)
4. Tool recipe unlock levels. The build (`game_data.gd:142`, J00BA, 2026-11-14) unlocks tool tier N at skill level 5 × (N − 1) for every tool, and its metal ladder has a Steel tier between Iron and Gold. Section 2.1 has different levels and no Steel. The pace hardly changes: about 73.5 days to mining level 100 with the build's levels, against 75. Which should this doc follow? Sections 6.1, 7.1 and 8.1 use section 2.1 for now.
