# Report: Fishing expansion ideas (2026-11-21)

## In short
J00BA asked for fishing to be expanded. This report gives nine ideas, all **Proposed**, and none of them is in the docs. The biggest gap is not content: there is nowhere to fish in the live game (see [2026-11-21-fishing-status.md](2026-11-21-fishing-status.md)). So the recommendation is to put the existing fish into the resource world's water and give fishing XP first (ideas 1 and 2). After that, add shoal events (idea 3) or the fish log (idea 6).

## What changed
| Area | Change |
|---|---|
| Docs | None. |
| Decisions | None. |
| Folder | Added this report (same branch as the status report). |

## Evidence
- **GitHub, folder structure:** the same as the [status report](2026-11-21-fishing-status.md). No open PR overlaps these ideas, apart from PR #100 (HD rods).
- **Claude:** the XP table in idea 2 was checked with a script that uses the curve and pace model from `resource_gathering.md` sections 2 and 3. The script's mining figure matches the doc (1,808 hours, 75 days, to level 100), so the fishing figures use the same method.
- Water bodies are from `godot-game/scripts/tools/bake_world_data.gd:24-30`. Ore event odds are from `godot-game/autoload/ore_events.gd:15-18`.

## Consistency check
- Every mismatch in the status report applies here, most of all the rod ladder (D-110 against section 2.1) and the doc-set question.
- Ideas 1 and 3 put the tier 9 and 10 fish in events only, because the Void and Stellar biomes aren't in the resource world. That matches the build's voidstone and stellarite (ore events only). Neither fits `resource_gathering.md` section 3.2's model, which assumes nonstop top-tier gathering. For fishing the cost is small (idea 3).
- Fish names (D-109) don't follow biome order. Their names point to biomes, so a mid-game player goes forest, plains, swamp, frost and back to swamp (idea 1). The teleport menu (T) makes this cheap.

## Suggestions (not applied)

**1. Fish by water (Proposed).** Put fishing spots on the five bodies of water the resource world already has. Minnow is in every water, the way Coal is in every biome but Stellar (`game_worlds.md` section 4.4). Some fish sit deeper than their water's biome, the way obsidian sits in Mountain, so players come back with a better rod.

| Water (`bake_world_data.gd`) | Biome | Fish (tier) |
|---|---|---|
| `forest_river` | Forest | Minnow (1), Perch (2), Trout (3): all with the starter rod |
| `forest_upper_pool` (the swan pond) | Forest | Minnow (1), Trout (3), Catfish (4) |
| `plains_watering_hole` | Plains | Minnow (1), Goldfin Carp (5) |
| `swamp_water` | Swamp | Minnow (1), Shadow Eel (6), Bloodfin Snapper (8) |
| `frost_open_pool` | Frost | Minnow (1), Frostscale Pike (7) |
| Void shoal (event, idea 3) | Any water | Void Angler (9) |
| Stellar shoal (event, idea 3) | Any water | Starfin Koi (10) |

- Spots are fixed in place and shared (this answers `resource_gathering.md` open question 3). Proposed: 4 spots along each shore and 8 in the swamp.
- Whether a spot refreshes after 10 s (D-109) or never runs out (section 9) follows the doc-set answer. It is not changed here.
- Build cost: small. `FishingSpot` already works. It needs placing in the resource world, and each spot needs a fish list.

**2. A fishing table for `resource_gathering.md` section 7 (Proposed, needs J00BA).** This is J00BA's method: catch times follow the mining ladder, and XP per fish is set so that each tier earns the same XP per hour as the ore of that tier. A pearl gives double its fish's XP, like a gem (section 4.2), at the D-112 chances.

| Fish | Tier | Item id | Time to catch | Minimum rod (section 2.1) | XP per fish | Pearl, chance | XP per pearl | XP per hour |
|---|---|---|---|---|---|---|---|---|
| Minnow | T1 | `minnow` | 30s | Stone | 17 | River, 10% | 34 | 2,448 |
| Perch | T2 | `perch` | 45s | Stone | 33 | Sand, 9% | 66 | 3,115 |
| Trout | T3 | `trout` | 45s | Stone | 40 | Moss, 8% | 80 | 3,712 |
| Catfish | T4 | `catfish` | 60s | Bronze | 65 | Black, 7% | 130 | 4,446 |
| Goldfin Carp | T5 | `goldfin_carp` | 120s | Iron | 147 | Golden, 6% | 294 | 4,939 |
| Shadow Eel | T6 | `shadow_eel` | 240s | Gold | 324 | Shadow, 5% | 648 | 5,346 |
| Frostscale Pike | T7 | `frostscale_pike` | 300s | Obsidian | 444 | Frost, 4% | 888 | 5,754 |
| Bloodfin Snapper | T8 | `bloodfin_snapper` | 300s | Titanite | 510 | Blood, 3% | 1,020 | 6,487 |
| Void Angler | T9 | `void_angler` | 600s | Dreadstone | 1,143 | Void, 2% | 2,286 | 7,132 |
| Starfin Koi | T10 | `starfin_koi` | 1000s | Voidstone | 2,114 | Star, 1% | 4,228 | 7,763 |

- **Pace:** level 100 in 1,808 hours of nonstop fishing (75 days), the same as mining and lumbering. Level 50 comes in 17 hours and level 90 in 29 days.
- Player XP follows D-121 as it stands: 1 per second of catch time, and a pearl gives the same again.
- The "Minimum rod" column uses section 2.1. Under D-110 it would be each fish's own rod instead, and the pace would need checking again once rod unlock levels exist.
- **How it plays with D-109 (Proposed):** the time to catch is the wait before the bite. A bar fills and the fish circles closer. Then the D-109 timing window opens. A missed bite loses the fish and halves the bar.
- **Push-back:** one button press after a 10 to 17 minute wait is thin play, and a bot can time it from the bar. Idea 5 is one answer. **Open question:** is that enough for tiers 9 and 10?

**3. Shoal events (Proposed).** These use the ore events the build already has (`autoload/ore_events.gd`, `ORE_EVENTS` in `game-server/server.mjs`). A shoal appears at a spot on one of the waters for 15 minutes, with a banner for everyone, at the same odds as the ore events: Void Angler 1 in 45 per minute, Starfin Koi 1 in 120.
- New work: a list of shore spots. The 48 `EVENT_SPOTS` in `resource_landmarks.gd` are on land, for veins.
- **Pace check:** at these odds a void shoal is up about 29% of the time and a stellar one about 12%. If those are the only places to catch tiers 9 and 10, level 100 takes about 79 days nonstop instead of 75 (modelled). The top fish stay rare.
- **Open question:** caps. `03-games.md` gives the mine rush a Proposed cap of 10 ore a day, and D-097 caps minigame item prizes. The build's ore events have no cap: they pay per swing like normal gathering. Shoals should follow whichever rule the ore events end up with.

**4. Other catches (Proposed).**
- **Sunken chest:** a rare catch that could use the five coloured chest models from PR #101. Fill it only with items that already exist (ores, logs, pearls), never coins, so it doesn't add a new coin source, and cap it per day.
- **Junk** (an old boot, a driftwood branch): a light-hearted catch that sells for little. Each needs a 48×48 pixel icon (D-015).
- **Pearls need a use** (status report, mismatch 8). The choices are: sell only (the simplest, but it pays coins out), a crafting input (for example a rod upgrade, once `crafting.md` exists), or a cosmetic. **Open question.**

**5. A reel for the top tiers (Proposed).** For tiers 7 to 10, after the bite, the player holds F to keep a marker inside a moving zone for about 3 seconds. A slip loses the fish. It adds skill and stops simple bots.
- **Push-back:** it lowers XP per hour unless catch times are cut to match. It also needs a new piece of UI and has to work in the web build.

**6. Fish weight, a fish log and trophies (Proposed).** Each catch rolls a weight in its fish's range. The profile (P) shows a fish log: fish caught, the heaviest, and pearls found. This feeds `game_direction.md` section 7 challenges, for example "catch all ten fish", "find all ten pearls" or "a Starfin Koi over a set weight", which unlock trophies, titles and emblems.
- Weight is for show only and doesn't change the sell price, so it has no effect on the economy. The build cost is low: data and one profile panel.

**7. A hub pond and a weekly contest (Proposed).** This needs a pond in the hub (a new build in the walled town) and a server leaderboard. Under D-098 a competitive contest takes a small coin fee, part of which is destroyed, and prizes come from the game.
- **Push-back:** "heaviest fish" is mostly luck. With an entry fee, it looks like a lottery, which is a real risk in an NFT game. Better to score on skill (most fish in a 10-minute round) or run it as a free daily minigame under D-098, with cosmetic prizes.

**8. Meal buffs for battle animals (Proposed).** Cooked fish already feeds battle animals (D-111). Its XP effect is Proposed, and the build gives 15 XP per tier. Higher-tier meals could also give a small buff for one battle.
- **Push-back:** buffs from food that can be farmed or traded tilt battles toward whoever grinds or buys the most fish. That becomes pay-to-win once PvP exists. Recommend keeping food as XP only for now.

**9. Bait from foraging (Proposed, blocked).** Bait could cut the time to catch or raise the pearl chance. It is blocked: the foraging table (`resource_gathering.md` section 6) is a placeholder.
- **Push-back:** a bait speed bonus stacks with the tool and skill-tree bonuses (section 2.3), so the pace drifts. Leave it until foraging needs a use.

**Recommended order:** 1 and 2 first, because they are small and put fishing into the live game with XP. Then 3, which reuses the ore events end to end, or 6, which is cheap and has no economy risk. 4, 5 and 7 are bigger, and 8 and 9 should wait.

## What's next
Once you pick ideas, a design pass writes them into the docs. Then a build pass adds them as TEST values, starting with idea 1.

## What I need from you
1. Which ideas should go ahead? Answer by number.
2. Is the fish-by-water table in idea 1 right, including tiers 9 and 10 in shoal events only?
3. Should the idea 2 table be offered to J00BA for `resource_gathering.md` section 7?
