# Resource Gathering

> Status: draft v2 · Owner: J00BA · Last updated: 2026-11-21 (section 7 Proposed by Claude, waiting for J00BA)
>
> How players gather every resource in the resource world: tools, tiers, gather times, drops and skill XP. This doc must agree with `game_direction.md`. Where the two differ, `game_direction.md` wins until it is updated.

---

## 1. Overview

There are five gathering skills. Each one has its own tool, its own resources and its own skill level from **1 to 100**.

| Skill | Tool | Resource | Processed into | Status |
| --- | --- | --- | --- | --- |
| Mining | Pickaxe | Ores (+ gems) | Ingots | Done (section 4) |
| Lumbering | Axe | Logs | Planks | Done (section 5) |
| Foraging | To be decided | Plants | Plant bundles | Placeholder (section 6) |
| Fishing | Rod | Fish (+ pearls) | Cooked fish | Proposed (section 7) |
| Hunting | To be decided (bow / weapon) | Mobs → hides, mob drops | To be decided | Placeholder (section 8) |

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

The same ladder is used for **every** gathering tool (pickaxe, axe, and later the foraging, fishing and hunting tools). Proposed exception: fishing rods are made from planks (section 7.1).

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

---

## 5. Lumbering

- **Tool:** axe. Starts with `stone_axe`.
- **Nodes:** trees in the resource world.
- **Output:** one log per successful chop. Logs are processed into planks at a station (see `crafting.md`).
- **Bonus drop:** none for now.

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

---

## 6. Foraging

> Placeholder. J00BA will supply the plant table (names, tiers, gather times, minimum tools).

- Follows the same rules as section 2 and the same tool ladder as section 2.1.
- Plants are used to make **plant bundles** (for taming in a later update).
- XP per plant will be set with the same method as section 3.2 once the table is in.

| Plant | Tier | Item id | Time to pick | Minimum tool | XP per plant |
| --- | --- | --- | --- | --- | --- |
| *to be added* | | | | | |

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

> Placeholder. J00BA will supply the mob table (names, tiers, time to hunt, minimum weapon). Mob behaviour lives in `world_mobs.md`.

- Follows the same rules as section 2 and the same tool ladder as section 2.1.
- Hunting a mob gives hides and other mob drops.
- XP per mob will be set with the same method as section 3.2 once the table is in.

| Mob | Tier | Drops | Time to hunt | Minimum weapon | XP per mob |
| --- | --- | --- | --- | --- | --- |
| *to be added* | | | | | |

---

## 9. Resource placement

- Resource nodes are **placed in the world from the start**. They are part of the map and never move or spawn somewhere new.
- Nodes **never run out**. An ore rock, tree or plant stays after it is gathered and can be gathered again straight away.
- Higher tier nodes mostly sit deeper in the resource world. Which resources are in each biome is in `game_worlds.md` section 4.
- Nodes are shared: any number of players can gather from the same node at once.

---

## 10. Open questions

1. How much player level XP does each gather give?
2. Inventory size and what happens when it is full.
3. Fishing spots and mobs: are they fixed in place like ores and trees, and do mobs respawn after being hunted? (Proposed for fishing spots: fixed and shared, section 7.3.)
