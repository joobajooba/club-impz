# Resource Gathering

> Status: draft v1 · Owner: J00BA · Last updated: 2026-10-29
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
| Fishing | To be decided (rod) | Fish | To be decided | Placeholder (section 7) |
| Hunting | To be decided (bow / weapon) | Mobs → hides, mob drops | To be decided | Placeholder (section 8) |

All gatherable resources live in the **resource world**. None spawn in the hub world.

---

## 2. How gathering works

These rules apply to every gathering skill.

1. **Find a resource node** in the resource world (an ore rock, a tree, a plant, a fishing spot, a mob).
2. **Check the tool.** The player needs the **minimum tool** for that node's resource tier, or better. If they don't have it, the node can't be gathered and the game says which tool is needed.
3. **Gather.** Gathering is **not instant**. The player starts the action and a progress bar fills over the resource's **gather time**. Moving away or starting another action cancels it.
4. **Receive the item.** When the bar completes, the item is added to the player's **inventory**.
5. **Earn XP.** The player earns XP in the matching skill (section 3) and player level XP (amount to be decided).
6. **Bonus drops.** Some resources can drop an extra item (for example gems while mining). Imp holders also have an extremely rare chance to find a **mint token** on any gather (see `holder_bonuses.md`).

### 2.1 Tool progression

The same ladder is used for **every** gathering tool (pickaxe, axe, and later the foraging, fishing and hunting tools).

```
stone ─▶ bronze ─▶ iron ─▶ gold ─▶ obsidian ─▶ titanite ─▶ dreadstone ─▶ void ─▶ stellarite
```

- **Stone tools are the starter tools.** Every new player gets a `stone_pickaxe` and a `stone_axe`.
- Better tools are **crafted** from resources the player gathers. Recipes go in `crafting.md`.
- **Bronze** is an alloy made from **tin and copper** ingots. It has no ore of its own.
- **Stellarite** is the final tool tier. Stellarite tools aren't needed to gather anything; they are the end-game tool and will get their bonus from `crafting.md` / `skill_trees.md`.

| Tool tier | Pickaxe id | Axe id | Unlocks resource tiers |
| --- | --- | --- | --- |
| Stone | `stone_pickaxe` | `stone_axe` | T1 to T3 |
| Bronze | `bronze_pickaxe` | `bronze_axe` | T4 |
| Iron | `iron_pickaxe` | `iron_axe` | T5 |
| Gold | `gold_pickaxe` | `gold_axe` | T6 |
| Obsidian | `obsidian_pickaxe` | `obsidian_axe` | T7 |
| Titanite | `titanite_pickaxe` | `titanite_axe` | T8 |
| Dreadstone | `dreadstone_pickaxe` | `dreadstone_axe` | T9 |
| Void | `void_pickaxe` | `void_axe` | T10 |
| Stellarite | `stellarite_pickaxe` | `stellarite_axe` | End-game tool |

### 2.2 Suggested skill levels

The XP model in section 3 assumes players move up to a new resource tier around these skill levels. **Open question:** should these be hard requirements (like RuneScape) or only a guide, with the tool being the only gate?

| Resource tier | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Skill level | 1 | 5 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 85 |

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

The model assumes the player always gathers the highest tier unlocked at their level (section 2.2), with no time lost to walking, selling or respawns. Real play will be slower.

XP per hour for a resource = `(xp per gather + gem chance × gem xp) × 3600 / gather time`.

Mining, nonstop:

| Reached level | Hours | Days |
| --- | --- | --- |
| 10 | 0.4 | under 1 |
| 30 | 3.3 | under 1 |
| 50 | 20 | 0.8 |
| 70 | 122 | 5 |
| 85 | 475 | 20 |
| 90 | 744 | 31 |
| 99 | 1,735 | 72 |
| **100** | **1,909** | **80 (about 2.6 months)** |

- Fast start: level 10 in under 30 minutes, level 50 within the first day.
- After one month of nonstop play the player is around level 90, with more than half the XP for 100 still to go.
- A more normal 4 hours a day is roughly 16 months to level 100.
- Lumbering is tuned to the same pace (section 5).

Changing pace later is easy: scale every XP value in sections 4 and 5 by the same amount (for example × 0.8 makes 100 take about 100 days).

---

## 4. Mining

- **Tool:** pickaxe. Starts with `stone_pickaxe`.
- **Nodes:** ore rocks in the resource world.
- **Output:** one ore per successful mine. Ores are smelted into ingots at a station (see `crafting.md`).
- **Bonus drop:** each ore has a chance to drop its gem (section 4.2).

### 4.1 Ores

| Ore | Tier | Ore id | Ingot id | Time to mine | Minimum pickaxe | Suggested level | XP per ore | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coal | T1 | `coal` | `coal` (no ingot) | 30s | Stone | 1 | 20 | 2,496 |
| Tin | T2 | `tin_ore` | `tin_ingot` | 45s | Stone | 5 | 32 | 3,072 |
| Copper | T3 | `copper_ore` | `copper_ingot` | 45s | Stone | 10 | 40 | 3,733 |
| Iron | T4 | `iron_ore` | `iron_ingot` | 60s | Bronze | 20 | 65 | 4,420 |
| Gold | T5 | `gold_ore` | `gold_ingot` | 120s | Iron | 30 | 150 | 4,950 |
| Obsidian | T6 | `obsidian_ore` | `obsidian_ingot` | 240s | Gold | 40 | 330 | 5,346 |
| Titanite | T7 | `titanite_ore` | `titanite_ingot` | 300s | Obsidian | 50 | 450 | 5,760 |
| Dreadstone | T8 | `dreadstone_ore` | `dreadstone_ingot` | 300s | Titanite | 60 | 520 | 6,490 |
| Voidstone | T9 | `voidstone_ore` | `voidstone_ingot` | 600s | Dreadstone | 70 | 1,150 | 7,130 |
| Stellarite | T10 | `stellarite_ore` | `stellarite_ingot` | 1000s | Void | 85 | 2,100 | 7,762 |

XP per hour includes the average XP from gems.

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

Lumbering has no gems, so each log gives a little more XP than the matching ore. That keeps both skills at the same pace (about 80 days nonstop to level 100).

| Tree | Tier | Log id | Planks id | Time to chop | Minimum axe | Suggested level | XP per log | XP per hour |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pine | T1 | `pine_log` | `pine_planks` | 30s | Stone | 1 | 22 | 2,640 |
| Birch | T2 | `birch_log` | `birch_planks` | 45s | Stone | 5 | 38 | 3,040 |
| Oak | T3 | `oak_log` | `oak_planks` | 45s | Stone | 10 | 48 | 3,840 |
| Maple | T4 | `maple_log` | `maple_planks` | 60s | Bronze | 20 | 75 | 4,500 |
| Hickory | T5 | `hickory_log` | `hickory_planks` | 120s | Iron | 30 | 165 | 4,950 |
| Frostbark | T6 | `frostbark_log` | `frostbark_planks` | 240s | Gold | 40 | 355 | 5,325 |
| Titanwood | T7 | `titanwood_log` | `titanwood_planks` | 300s | Obsidian | 50 | 480 | 5,760 |
| Runewood | T8 | `runewood_log` | `runewood_planks` | 300s | Titanite | 60 | 540 | 6,480 |
| Gembark | T9 | `gembark_log` | `gembark_planks` | 600s | Dreadstone | 70 | 1,190 | 7,140 |
| Worldbark | T10 | `worldbark_log` | `worldbark_planks` | 1000s | Void | 85 | 2,160 | 7,776 |

---

## 6. Foraging

> Placeholder. J00BA will supply the plant table (names, tiers, gather times, minimum tools).

- Follows the same rules as section 2 and the same tool ladder as section 2.1.
- Plants are used to make **plant bundles** (for taming in a later update).
- XP per plant will be set with the same method as section 3.2 once the table is in.

| Plant | Tier | Item id | Time to pick | Minimum tool | Suggested level | XP per plant |
| --- | --- | --- | --- | --- | --- | --- |
| *to be added* | | | | | | |

---

## 7. Fishing

> Placeholder. J00BA will supply the fish table (names, tiers, gather times, minimum tools).

- Follows the same rules as section 2 and the same tool ladder as section 2.1.
- XP per fish will be set with the same method as section 3.2 once the table is in.

| Fish | Tier | Item id | Time to catch | Minimum rod | Suggested level | XP per fish |
| --- | --- | --- | --- | --- | --- | --- |
| *to be added* | | | | | | |

---

## 8. Hunting

> Placeholder. J00BA will supply the mob table (names, tiers, time to hunt, minimum weapon). Mob behaviour lives in `world_mobs.md`.

- Follows the same rules as section 2 and the same tool ladder as section 2.1.
- Hunting a mob gives hides and other mob drops.
- XP per mob will be set with the same method as section 3.2 once the table is in.

| Mob | Tier | Drops | Time to hunt | Minimum weapon | Suggested level | XP per mob |
| --- | --- | --- | --- | --- | --- | --- |
| *to be added* | | | | | | |

---

## 9. Resource generation

> To be decided with J00BA: how resource nodes spawn, run out and respawn in the resource world.

Questions this section will answer:

- Where nodes are placed (fixed spots, or random spots in each zone).
- Whether higher tiers sit deeper in the world, in their own zones.
- Whether a node runs out after one gather (or a few) and how long it takes to respawn.
- Whether nodes are shared by all players or separate for each player.

---

## 10. Open questions

1. Should the suggested skill levels in section 2.2 be hard requirements, or is the tool the only gate?
2. Section 9: how should resources generate and respawn?
3. Do better tools gather faster than the minimum tool, or does speed only come from skill tree buffs?
4. How much player level XP does each gather give?
5. Inventory size and what happens when it is full.
