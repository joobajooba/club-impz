# Report: Fishing, what is built and designed (2026-11-21)

## In short
Fishing is fully decided in the IMPLINGZ docs (D-109 to D-112) and has been built as a TEST since 2026-10-22, but only in the old test scene. Players can't fish in the live game: the biome resource world has five bodies of water and no fishing spots. J00BA's fishing section (`resource_gathering.md` section 7) is still a placeholder, so fishing has no XP. Ideas for growing fishing are in the companion report, [2026-11-21-fishing-expansion.md](2026-11-21-fishing-expansion.md).

## What changed
| Area | Change |
|---|---|
| Docs | None. This is a status report. `ROADMAP.md` lists it. |
| Decisions | None. |
| Folder | Added this report and the companion report. Changed `docs/ROADMAP.md` (two rows in the file list, one in the pass log). |

## Evidence
- **GitHub:**
  - Fishing was built in COLLAB_IMPZ PR #38 (`staging/godot-all-gathering`, merged 2026-10-22: "foraging, hunting, lumbering, fishing + TEST merchant, battles, dig"). It came into club-impz with the move commit `d6c30e6`. Later commits only touched the fishing code for held tools (`cabd2f4`, D-116) and the teleport menu (`c6b34e2`).
  - Open draft **PR #100** (`staging/hd-rods`, 2026-11-15): all 10 rods remade in HD, 32 files, not merged.
  - PR #89 (merged 2026-11-15) added the forest swan pond: water, but no fishing spots.
  - The titles of all 104 PRs were checked. No other PR, open or merged, is about fishing, rods or pearls.
  - Default branch head `fc894bf`. Newest backup tag `backup/main-20261116-1312`.
- **Claude:** two Claude sessions on 2026-11-21 read the code and the docs. What the build has:

  | Part | Where | State |
  |---|---|---|
  | Cast, wait, bite, reel (press F, then F again in the window, D-109) | `godot-game/characters/gatherer.gd:261-288` | Built. Cast 0.7 s, bite after 1.5 to 4 s and a 1.0 s window, both labelled TEST (`gatherer.gd:21-23`) |
  | Fishing spot: splash on a bite, a circling fish, 2 m reach | `godot-game/gathering/fishing_spot.gd` | Built |
  | Line and float | `gatherer.gd:323`, `scripts/tools/held_tool.gd` | Built |
  | Where the spots are | `gathering/area.gd:93`, spots and a campfire | **Only in `demo_landscape.tscn`**. The game starts in `scenes/main.tscn` |
  | Fish, pearls and rods | `autoload/game_data.gd:108` (fish), `:327` (`_build_fishing`), `:359` (rods, D-110) | All 10 tiers, matching `02-resources.md` |
  | Cooking (D-111) | Campfire in `ui/station_menu.gd` | Built |
  | Feeding battle animals | `autoload/stable.gd:118`, `ui/stable_menu.gd` | Built: 15 animal XP per fish tier, a Proposed value (`05-skirmish.md` line 81) |
  | Selling | Fish tab in `ui/merchant_menu.gd` | Built (TEST merchant) |
  | Fishing skill and XP | `ui/profile/profile_menu.gd:31` lists the skill | **No skill XP is built** (there is no `progress.gd` yet) |
  | Icons (fish, cooked fish, pearls) | `godot-game/assets/sprites/source/items/` and copies in `godot-game/sprites/items/` | All present |

  The resource world's water is listed in `godot-game/scripts/tools/bake_world_data.gd:24-30`: the forest river, the forest swan pond, the frost open pool, the plains watering hole and the swamp water. Mountain has no water. Void and Stellar are not in the resource world (it has five 256 m biome bands), and voidstone and stellarite come only from ore events (`autoload/ore_events.gd`).
- **Folder structure:** the working tree was clean on `fc894bf`. This branch adds 2 files in `docs/reports/` and changes `docs/ROADMAP.md`.

## Consistency check
1. **Fish table.** `02-resources.md` has the ten fish (D-109). J00BA's `resource_gathering.md` section 7 is a placeholder waiting for J00BA's own fish table. Which doc set wins is still open (`README.md`).
2. **Rods.** D-110 gives one wooden rod per fish tier, each catching its own tier and lower. `resource_gathering.md` section 2.1 says fishing tools use the same ladder as every tool (stone to stellarite, stone covers tiers 1 to 3), with recipes unlocked by skill level. The two can't both hold.
3. **Rod woods.** D-110's rods take planks of the IMPLINGZ trees (Ash to Starwood, `02-resources.md`). The build's world and `game_worlds.md` use J00BA's trees (Pine to Worldbark). D-110's rule is by tier ("tier N−1 planks"), so it still works; the rod names and recipes don't.
4. **Spot refresh.** D-109 says a spot refreshes 10 s after a catch. `resource_gathering.md` section 9 says nodes never run out and are shared.
5. **Energy.** D-109 charges 5 energy per catch. D-123 says energy only limits mint token rolls. J00BA hasn't agreed to D-123 yet.
6. **Catch time.** The build's bite comes after 1.5 to 4 s (TEST). `resource_gathering.md` section 3 sets gather times of 30 s to 1,000 s for the other skills.
7. **Where to fish.** `resource_gathering.md` open question 3 (are fishing spots fixed?) and `game_worlds.md` section 4.6 (fish per biome "added later") are both unanswered.
8. **Pearls.** D-112 makes pearls drop, but no doc gives them a use.

## Suggestions (not applied)
- See [2026-11-21-fishing-expansion.md](2026-11-21-fishing-expansion.md): nine ideas, an order to do them in, and a fishing XP table worked out to J00BA's pace.
- Close or merge PR #100 before any new rod work, so two rod sets don't drift apart.

## What's next
Answer the questions below, then a build pass puts fishing spots into the resource world (expansion report, idea 1).

## What I need from you
1. Which fish and rods should the build follow: D-109 to D-112, or J00BA's section 7 and the section 2.1 tool ladder? This needs J00BA too.
2. Should PR #100 (HD rods) be merged, or held until question 1 is answered?
