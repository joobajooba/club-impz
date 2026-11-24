# Report: Gathering expanded like fishing (2026-11-21)

## In short
The user asked for every gathering skill to be evolved the way fishing was, and said they would decide later what happens with foraging and hunting. So foraging and hunting now have full **Proposed** sections in J00BA's `resource_gathering.md`, built from the IMPLINGZ tables. Mining and lumbering got smaller additions: the ore events written down, a sap drop for trees, felling and wood hilts. Every skill now follows one pattern: 10 tiers on the mining time ladder, a rare drop worth double XP, tier 1 in every biome, and about 75 to 79 days to level 100. Nothing is decided. All of it waits for J00BA and the user. What the build has is in [2026-11-21-gathering-status.md](2026-11-21-gathering-status.md).

## What changed
| Area | Change |
|---|---|
| Docs | `resource_gathering.md`: header, section 1 table, section 2.1 note, new 4.3 (ore events), 5.1 to 5.3 (sap, felling, wood hilts), section 6 (foraging) and section 8 (hunting) written in full, a section 9 note, open question 3 updated and question 4 added. `game_worlds.md` section 4.6: plant and animal rows. All marked **Proposed**. |
| Decisions | None. No D-number was changed. Where a section differs from a decision, it says so. |
| Folder | Added this report and the status report. `ROADMAP.md`: two file-list rows and one pass-log row. |

## Evidence
- **GitHub, folder structure:** the same as the [status report](2026-11-21-gathering-status.md). Branch `staging/design-gathering`, stacked on PR #106 because both edit `resource_gathering.md`.
- **Claude:** every XP value and pace figure came from one script using the curve and pace model in `resource_gathering.md` sections 2 and 3. Its mining figure matches the doc (1,808 hours, 75.3 days), so the other figures use the same method:

  | Skill | Hours to level 100 | Days |
  |---|---|---|
  | Mining, as the doc models it | 1,808 | 75 |
  | Mining, the build's world (voidstone and stellarite from ore events only) | 1,901 | 79 |
  | Mining, the build's unlock levels | 1,763 | 73.5 |
  | Lumbering, now (no rare drop) | 1,805 | 75 |
  | Lumbering with sap (section 5.1) | 1,808 | 75 |
  | Foraging (section 6) | 1,808 | 75 |
  | Hunting (section 8) | 1,867 | 78 |
  | Fishing (section 7, earlier today) | 1,967 | 82 |

## Consistency check
Each topic follows the newer doc set, as for fishing, with two exceptions, both flagged below.

| Topic | IMPLINGZ set | J00BA's doc or build | Followed |
|---|---|---|---|
| Ores and trees | D-005, D-105 (October) | Sections 4 and 5, the live world (Nov 8) | J00BA's, unchanged |
| Regrowth | 10 s (D-064, D-067, D-105) | Section 9: never run out. Build: trees gone 5 min per player (Nov 8) | The build for trees, plants and animals. Ores and fish never run out |
| Tree rare drop | Sap per tree (D-108) | Section 5: "none for now" | **Exception:** sap is added. "For now" left room, and it gives lumbering the same shape as the other four skills, with no change of pace |
| Plants and seeds | D-022 to D-027 | Section 6 placeholder, empty | IMPLINGZ (the only table) |
| Sickles | One per tier (D-063) | Section 2.1 ladder, which names foraging tools (Oct 29) | Section 2.1 |
| Animals | 16 tiers (D-028 to D-035) | Section 8 placeholder; world mobs as scenery | IMPLINGZ: tiers 1 to 10 as normal, 11 to 16 as legendary events, so none is dropped |
| Bows | From leather (D-069) | Section 2.1 ladder | **Exception:** D-069. Bows are the only tool use for leather, the build has them, and rods were handled the same way |
| Wood hilts | Ash and Oak planks (D-107) | No Ash in section 5 | Proposed Pine Wood Hilt, Oak unchanged |
| Energy | 5 per gather | D-123: limits only mint token rolls | Both: spend 5 while there is energy left |

Still open: unlock levels (doc against build, open question 4), and the 12 mismatches in the status report, which these sections settle only as proposals.

## Suggestions
**Written into the docs (Proposed):**
1. **Ore events written down** (section 4.3). The build has them, and the doc didn't.
2. **Sap for every tree** (section 5.1). Each tree gets a sap at its ore tier's gem chance. Log XP drops to the ore's XP, so lumbering earns exactly what mining does.
3. **Felling and regrowth** (5.2, 6.4, 8, section 9 note). Trees, plants and animals are gone for 5 minutes for the player who gathered them, as the build already does for trees. Every node stays shared.
4. **Pine Wood Hilt** (5.3). Without it, J00BA's trees can't make the first crafted tools.
5. **Foraging** (section 6). Sickles on the section 2.1 ladder, the ten plants and seeds with XP, plants by biome, and the same pace as mining.
6. **Hunting** (section 8). Bows from leather, ten animals and trophies with XP, animals by biome, and six legendary hunts as world events at J00BA's lairs.

**Not applied:**
- **Stellarite tools double every rare-drop chance.** This extends D-059 from pickaxes to every skill and gives the level 90 tool a purpose beyond 5% speed. It touches D-059 and section 2.1, so the user and J00BA decide.
- **A collection log.** Extend the trophy cabinet (D-103) to every rare drop (gems, sap, seeds, pearls, trophies), with a title for each completed page. That gives pearls and sap a use without adding coins to the economy.
- **Fewer banners.** Ore events, shoals and legendary hunts together would show a banner about every 13 minutes. Show it only to players whose tool can use the event, and put the rest in the chat's World Events tab.
- **J00BA's farm mobs.** Cows, highland cows and pigs could belong to farming later (seeds are already for farming, D-065), rather than to hunting.
- **Build order.** `progress.gd` (skill XP) first. Then plants in the live world: the test scene's plant nodes and art exist. Then huntable animals, which need a hunt action and models. Legendary hunts and shoals can reuse `autoload/ore_events.gd`.

**Pushing back:**
- **Long gathers for plants and animals.** Picking one Starmoss takes 1,000 seconds, the same as Stellarite. It reads oddly, and it slows the IMPLINGZ costings a lot: taming an Eclipse Dragon needs about 28 hours of Starmoss, and the first nine crafted bows need about 17 hours of hunting. Shorter times with less XP per item would keep the same pace, but they would multiply the top items coming into the economy. Equal supply across skills seemed the safer default.
- **The legendary grind** (section 8.3). The whole set of legendary bows takes about 21 days online, because D-068 and D-069 make each one cost 50 hides of a beast that shows up every few hours. That's fine for a top goal if intended. If not, the event odds are the lever.
- **A sword in every toolbar** with no skill. This proposal doesn't use it for hunting, because `game_direction.md` and D-030 both say bows. J00BA should say what it is for.

## What's next
J00BA reviews the Proposed sections in PR order (#105, #106, then this one). After that, a build pass can start with skill XP.

## What I need from you
1. Shall I tag J00BA on this PR as it is, or do you want changes to foraging or hunting first?
2. Legendary hunts: keep tiers 11 to 16 as events, or place them as fixed animals at the lairs? Fixed animals would give more XP late on and make level 100 come sooner.
3. Recipe unlock levels: section 2.1, or the build's every 5 levels? This needs J00BA too.
