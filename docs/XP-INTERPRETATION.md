# XP: Claude's interpretation

> Status: draft · Written 2026-11-22, at the user's request ("write up in your own interpretation an XP system")
>
> **Calls answered 2026-11-22** (the user: "I'm fine with the XP calls"): X1, X2 and X3 are Decided (D-141 to D-143), and `xp_system.md` stays the XP doc with the answers folded in (D-144). X4 and X5 are still Proposed. J00BA hasn't agreed yet.
>
> `xp_system.md` is the existing XP draft. This doc is Claude's own take: it keeps every decided rule and the parts of that draft it agrees with, and proposes changes where the numbers show a problem. Nothing here changes a decision. Every line is labelled **Decided** (with its D-number or source doc), **Proposed** or **Open question**.

---

## 1. What XP is for

Four rules shape everything below (Proposed, except where marked):

1. **XP measures play, and is never spent.** Levels only go up. Coins never buy XP (Decided, D-121).
2. **XP should always point at the next thing.** A level that unlocks nothing is a number, not a goal.
3. **The pace is for people, not bots.** Only a bot plays nonstop, so a system tuned to nonstop play rewards bots most (`xp_system.md` section 7 says the same).
4. **XP never pays for the economy's work.** Processing and parts feed other players and the merchant. XP stays with gathering, so no one farms XP by moving items around (M11).

---

## 2. What stays as decided

| Rule | Source |
|---|---|
| Five skills, levels 1 to 100, on one curve: RuneScape's, extended to 100 (14,391,160 XP) | Decided, `resource_gathering.md` section 3 |
| Target: level 100 in about 2.5 months of nonstop gathering | Decided, `resource_gathering.md` section 3.1 |
| Skill XP per gather from the resource tables; a gem gives double its ore | Decided, `resource_gathering.md` sections 4 to 8 |
| Tool recipe N unlocks at skill level 5 × (N − 1): the Stellarite pickaxe at 45, the Eclipse Dragon Bow at 75 | Decided by J00BA, 2026-11-14 (`game_data.gd`, `RECIPE_EVERY`) |
| A skill-tree node every 5 levels up to 100; nodes are buffs for that skill (faster gathering, better drops), unlocked in a chain | Decided by J00BA (`game_direction.md` section 6.2; `SKILL_TREE_MAX`) |
| Player XP: 1 per second a gather took, the same again for a gem, 10% for processing, 500 × tier for a first craft, challenges and battles | Decided, D-121 |
| Imp holders get +5% skill XP, flat | Decided, D-122 |
| Energy limits only mint token rolls, not gathering or XP | Decided, D-123 |
| Player level 1 to 50 with prestige; the curve 100 × L + 5 × L² (88 hours to 50) | Prestige Decided (`game_direction.md` 6.1); the curve Proposed in `xp_system.md` 5.1, and Claude agrees with it |
| XP is granted by the server, stored as XP (never as a level), keeps counting past 100 | Proposed in `xp_system.md` 4 and 7; Claude agrees |

---

## 3. The problem, in numbers

Mining with the best tool at every level (rates from `resource_gathering.md` 4.1; the Stellarite pickaxe mines 5% faster, `mining.gd`):

| Level | Total XP | Share of the XP to 100 | Reached after (nonstop) | At 2 hours a day |
|---|---|---|---|---|
| 45 (last tool) | 61,512 | **0.4%** | about 9 hours | 5 days |
| 50 | 101,333 | 0.7% | 14 hours | 1 week |
| 60 | 273,742 | 1.9% | 1.5 days | 2.5 weeks |
| 70 | 737,627 | 5.1% | 4 days | 7 weeks |
| 80 | 1,986,068 | 13.8% | 10 days | 4 months |
| 90 | 5,346,332 | 37% | 28 days | 11 months |
| 99 | 13,034,431 | 91% | 67 days | 2.2 years |
| 100 | 14,391,160 | 100% | 74 days | **2.4 years** |

What this shows:

- **Every tool is crafted within the first 0.4% of the XP.** J00BA's every-5-levels unlock (2026-11-14) is a good early game: something new every hour or so. But after level 45, 99.6% of the XP is earned doing one thing, the top resource, at about 8,150 XP an hour. A Stellarite vein takes 1,000 seconds per ore.
- **The back half has nothing to point at yet.** Levels 50 to 100 hold 11 tree nodes, and `skill_trees.md` isn't written. Between them the gaps grow from hours to months: 80 to 85 alone is 2.5 months at 2 hours a day.
- **The pace only fits a bot.** 2.5 months is the nonstop figure. A player on 2 hours a day takes 2.4 years; a bot that never stops gets there 12 times faster.
- **Boosts barely touch it.** A gem gives double its ore's XP, so a higher gem chance adds XP. At a 1% gem chance (Stellarite), the full ×2.5 cap (D-133) adds 3% XP an hour; at 10% (Tin in D-012) it adds 25%, and Tin still earns under half the top rate. The tool parts and inlays (D-125 to D-136) don't change the pace.

---

## 4. Proposals

### X1. Rested XP: the bonus only people get (Decided, D-141)

- **While you're away, you bank rested time:** 10 minutes for every hour since your last gather, up to **2 hours** (full after 12 hours away, about one energy reset).
- **While rested time lasts, every gather gives double skill XP**, gems included. The gather's seconds are taken from the bank. One bank for all five skills.
- **Skill XP only.** Player XP stays at 1 per second, so the player level still means "time played" (D-121).
- **Order:** base XP × 2 (rested) × 1.05 (holder, D-122), rounded down once.
- **What it does:** a player on 2 hours a day gets all of them at double: 45 to 100 drops from 2.4 years to 1.2. On 4 hours a day, from 15 months to 10. **A bot running nonstop never banks anything**, so the 74-day nonstop pace, and the decided target, don't move.
- **Fits the decisions:** it isn't a new XP source (D-121), coins can't buy it, it isn't tied to energy (D-123), and everyone gets it the same.
- **On the server:** the bank is worked out from the time of the last accepted gather, so the game never sends it.

### X2. The back half unlocks yield, not speed (Decided, D-142; the node numbers are placeholders)

J00BA's nodes are "faster gathering or better drops" (`game_direction.md` 6.2). Faster gathering also means faster XP, which pulls the decided pace in again and has to be re-modelled each time a node changes. **Yield doesn't:** a chance at a second raw item makes the back half pay more without touching XP an hour.

A template for each skill's nodes from 50 (the recipe nodes 5 to 45 come first, Decided):

| Level | Node | Effect |
|---|---|---|
| 50 | Bounty I | 5% chance of a second raw item |
| 55 | Keen Eye I | Rare drops ×1.1, inside the ×2.5 cap (D-133) |
| 60 | Bounty II | 10% |
| 65 | Steady Hands | A cancelled gather keeps half its progress |
| 70 | Bounty III | 15% |
| 75 | Keen Eye II | Rare drops ×1.2 in all |
| 80 | Bounty IV | 20% |
| 85 | Cosmetic | The skill's tool trail when you gather |
| 90 | Bounty V | 25% |
| 95 | Keen Eye III | Rare drops ×1.3 in all |
| 100 | Mastery | A title and an emblem for the skill (like trophy sets, D-103) |

- The second item gives no XP and never rolls a mint token. Mint token chances never change (D-045).
- Every number here is a placeholder for `skill_trees.md`. The proposal is the shape: yield and drops in the back half, speed only in the tool ladder.

### X3. First-craft XP, read for the parts build (Decided reading of D-121, D-143)

- **"Tool tier" means its place among the crafted tools:** Bronze 1 to Stellarite 9 (D-121's example counts to Stellarite 8, from an older ladder; the build has nine crafted metal tools), Ash Rod 1 to Voidwood Rod 9, Fox Bow 1 to Eclipse Dragon Bow 15. Starter tools give nothing.
- **Once per tool, per account,** however it was made: Craft, or Re-haft (M7). Taking a tool apart and making it again pays nothing. Parts and fittings pay nothing (M11).
- **All of it:** 22,500 player XP for each metal tree, 22,500 for rods and 60,000 for bows: **150,000** in all, 46% of a run to player level 50. It is spread over each skill's levels 5 to 45 (to 75 for bows), so it reads as steady milestones, not one jump.

### X4. One XP table per world, looked up by item (Proposed)

The build has two ore ladders: the live world uses J00BA's (`mining.gd`, Coal first), and the test landscape uses the IMPLINGZ one (`game_data.gd`, Tin first). They give the same ore different tiers.

- **XP is looked up by item id, never by tier.** Each live-world table carries its XP (as `lumbering.gd` already does); `mining.gd` gets the same `xp` field from `resource_gathering.md` 4.1.
- All ten ore ids, and the Pine, Birch and Oak logs, are in both ladders, so their XP works in both worlds. Logs only one ladder has (Ash, Maple…) give none until the tables agree. Foraging, hunting and fishing XP wait for one resource table per skill (`xp_system.md` section 10); until then those three give no skill XP.

### X5. What the player sees (Proposed, on top of `xp_system.md` section 6)

- **Rested time** is a soft second colour on the skill bar, with "Rested: 1 h 40 m" on hover. XP drops say "×2" while it lasts.
- **The next node is always on screen:** the skill's level-up toast and the Stats tab name it and its level ("Next: Bounty II at Mining 60").
- **Time to the next level, at your current rate,** on hover of the skill bar. In the back half this is the line that keeps a long goal readable.

---

## 5. How it gets built (Proposed)

`xp_system.md` section 8 has the shape: one `Progress` autoload, XP stored, levels worked out, signals for the UI. Where it hooks into today's code:

| Source | Where |
|---|---|
| Gathering, live world | `Mining.give` (`scripts/world/mining.gd`, called from `ore_miner.gd`) and `tree_chopper.gd` (`Inventory.gain` of the log) |
| Gathering, test landscape | `Inventory.gather` |
| Processing (player XP only) | `Inventory.process` |
| First craft | `Inventory.craft` (both Craft and Re-haft) |
| Recipe locks | `GameData.skill_level` reads TEST levels from `data/profile_test.json` today; it moves to `Progress` |
| Saving | `Save.state()`, as TEST, until the server keeps it |

- The rested bank needs one more saved value: the time of the last gather.
- A headless test in `tests/`, next to `test_tool_parts.tscn`, checks the curve (level 2 = 83, level 100 = 14,391,160) and the rested arithmetic.

---

## 6. Push-back

- **The tail stays very long.** Even with X1, Mining 99 takes over a year at 2 hours a day, and most players will stop somewhere in the 70s or 80s. That's normal for a RuneScape-style curve, but it means levels 50 and 70 need to feel like real milestones on the profile, not stops on the way to 100.
- **Yield adds items.** 25% more raw items from players above 90 means more coins from the merchant. Few players get there, and the merchant's base price is still TEST (D-074), so this is the number to watch.
- **Keen Eye is weak for gems.** An inlaid Stellarite pickaxe already sits at the ×2.5 cap (D-133), so Mining's Keen Eye nodes do nothing for those players. Mining may want a different node there.
- **Rested time favours short sessions.** A player who plays 8 hours a day gets the same 2 hours at double as one who plays 2. That's the point, but long-session players may feel it.

---

## 7. Calls answered

1. **Rested XP (X1):** yes, at 10 minutes per hour away and a 2-hour bank. D-141.
2. **Back-half nodes (X2):** yield and drops from 50 instead of speed. D-142.
3. **First-craft tier (X3):** the crafted tool's place in its tree. D-143.
4. **Which XP doc leads:** `xp_system.md`, with the answers folded in. D-144 (Claude took this option: the docs rules don't allow replacing a doc unless asked).
