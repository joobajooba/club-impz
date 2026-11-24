# Report: Gathering, what is built and designed (2026-11-21)

## In short
The user asked for the other gathering skills to get the same review as fishing. Mining and lumbering are built in the live resource world from J00BA's `resource_gathering.md`. Foraging and hunting are built only in the old test scene, from the IMPLINGZ tables in `02-resources.md`. The live world has no plants to pick, and its mobs can't be hunted. No skill earns XP yet. The two doc sets disagree on every skill's tiers, tools or regrowth (12 mismatches below). The ideas, and what was written into the docs, are in [2026-11-21-gathering-expansion.md](2026-11-21-gathering-expansion.md).

## What changed
| Area | Change |
|---|---|
| Docs | None in this report. The companion report covers the doc changes. |
| Decisions | None. |
| Folder | Added this report. `ROADMAP.md` lists it. |

## Evidence
- **GitHub:**
  - J00BA built the live world's gathering on 2026-11-08: mining (`1027793`), lumbering with 5-minute stumps (`54885fc`), ore events (`1e983ca`) and wandering mobs (`a653767`). The tool unlock rule (every 5 levels) came in J00BA's playtest snapshot `86f88dc` (2026-11-15, the code comment says 2026-11-14).
  - Foraging, hunting and the test-scene versions of every skill came from COLLAB_IMPZ PR #38 (merged 2026-10-22), brought over in the move commit `d6c30e6`.
  - Open PRs: #100 (HD rods), #103 (poster), #104 (hub chests), #105 and #106 (fishing, stacked). This work is stacked on #106 because it edits the same doc.
  - Default branch head `fc894bf`. Newest backup tag `backup/main-20261116-1312`.
- **Claude:** this session read the code and both doc sets. What the build has:

  | Skill | Live game (`scenes/main.tscn`) | Test scene only (`demo_landscape.tscn`) |
  |---|---|---|
  | Mining | Built from `resource_gathering.md` section 4: 10 ores and gems, times, minimum pickaxes, the speed bonus, shared veins that never run out (`scripts/world/mining.gd`, `scripts/player/ore_miner.gd`). Voidstone and stellarite come only from ore events (`autoload/ore_events.gd`). | The IMPLINGZ order (Tin first, D-005), 10 s respawn |
  | Lumbering | Built from section 5: 10 trees, minimum axes, speed bonus (`scripts/world/lumbering.gd`). A felled tree is a stump for 5 minutes, for that player only. No rare drop. Frostbark is still a recoloured pine. | IMPLINGZ trees (Ash to Starwood) with saps (D-105 to D-108) |
  | Foraging | **Not built.** There are no plants to pick. | 10 plants, seeds, drying rack, one sickle per tier (`game_data.gd:55`, `:276`, `:352`) |
  | Hunting | **Not built.** Nine mob kinds wander their biomes (`scripts/world/mob.gd`, `resource_landmarks.gd:30-46`): "No combat or hunting yet". The toolbar has a sword with no skill. | 16 animals as box creatures, three shots (D-067), bows, tanning, taming, stable, battles (`characters/gatherer.gd:8`, `game_data.gd:71`) |
  | All skills | **No skill XP** (there is no `progress.gd`). The live world spends **no energy**: only the test scene calls `Inventory.gather` (`inventory.gd:230`). | Energy 5 per gather |

- **Folder structure:** the branch started clean on `927bd64` (PR #106), apart from about 1,700 untracked `.import` files from the first Godot import, which are left out. This work changes `docs/resource_gathering.md`, `docs/game_worlds.md` and `docs/ROADMAP.md`, and adds two reports.

## Consistency check
1. **Mining tiers.** `resource_gathering.md` section 4 has Coal at T1 and gem chances of 1/50 to 1/75. D-005 and D-012 have Tin at T1, Coal at T4 and chances of 10% falling to 1%. Four gems pair with different ores (Diamond, Ruby, Emerald, Jade). The live world follows section 4.
2. **Tool ladder.** Section 2.1 has no Steel tier, and Stone reaches T1 to T3. The build's metal list has Steel (`game_data.gd:131`), as D-006 does. Mining still works because it looks tools up by name.
3. **Recipe unlock levels.** Section 2.1 unlocks Bronze at 5, Iron at 15, up to Stellarite at 90. The build unlocks tier N at level 5 × (N − 1) for every tool (`game_data.gd:142`). The pace model gives 73.5 days to mining level 100 with the build's levels and 75.3 with the doc's, so the effect is small.
4. **Trees.** Section 5 has Pine to Worldbark. D-105 has Ash to Starwood. The live world uses section 5. The test scene, the rod recipes (D-110) and the wood hilts (D-107) use the IMPLINGZ trees.
5. **Wood hilts.** D-107 and the build make the Ash Wood Hilt from Ash planks. Section 5 has no Ash, so with section 5's trees the Bronze tools could never be crafted.
6. **Regrowth.** Section 9 says nodes never run out. The live world fells trees for 5 minutes. D-064, D-067 and D-105 say 10 seconds for plants, animals and trees.
7. **Lumbering rare drop.** Section 5 has none. D-108 gives every tree a sap. Ids differ too: section 5 says `pine_planks`, the build says `pine_plank`.
8. **Foraging.** Section 6 was a placeholder waiting for J00BA. D-022 to D-027 and D-061 to D-066 already decide the plants, seeds, sickles and drying rack.
9. **Sickles.** D-063 gives one sickle per plant tier (Stone picks only Nettle). Section 2.1 says every gathering tool uses its ladder.
10. **Hunting.** Section 8 was a placeholder ("bow / weapon", "mobs"). D-028 to D-035 decide 16 animals with bows, which doesn't fit the 10-tier ladder. J00BA's world mobs (cows, pigs, ogres, dragons, a golem) aren't the IMPLINGZ animals. Only the wolf is in both.
11. **Energy.** D-061, D-067 and D-105 charge 5 energy per gather. D-123 makes energy limit only mint token rolls. The live world charges nothing. J00BA hasn't agreed to D-123.
12. **Gather times.** The live world uses 30 to 1,000 seconds. The IMPLINGZ costings (taming, bows, hilts in `02-resources.md`) assume short gathers and 20 gathers per energy reset.

Also found: `game_worlds.md` section 4.6 line 197 says the mob models "still need to be placed in biomes". The build has placed them (`resource_landmarks.gd`).

## Suggestions (not applied)
- See [2026-11-21-gathering-expansion.md](2026-11-21-gathering-expansion.md): the ideas, which were written into the docs as Proposed, and which were left as suggestions.
- Build `progress.gd` (skill XP) before more gathering content. Without it no skill has levels, so no tool unlock works in the live game.

## What's next
J00BA reviews the Proposed sections. Then a build pass can put plants and huntable animals into the live world.

## What I need from you
1. Do the Proposed foraging and hunting sections (6 and 8) go to J00BA as they are, or do you want changes first?
2. Recipe unlock levels: section 2.1's levels, or the build's every 5 levels? This needs J00BA too.
