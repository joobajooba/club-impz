# Report: Tool crafting mechanics and tool animations (2026-11-22)

## In short
The tool crafting roadmap now says how crafting behaves for the player (M1 to M11), how tools are taken apart and re-hafted, how gem inlays work, and exactly what needs to be made: 57 items, 9 icon drawings and no model changes. A new `TOOL-ANIMATIONS.md` sets out what the game already animates, the gaps (no bow, fishing stops at the cast, no crafting moments) and how to take it further. Everything is Proposed; eight crafting calls and four animation calls are waiting.

## What changed
| Area | Change |
|---|---|
| Docs | `TOOL-CRAFTING-ROADMAP.md` (Draft): header note; note under 1.3 that models stay as they are; P8 rewritten (parts are icons only); new 2.6 crafting mechanics M1 to M11; new 3.4 take apart and re-haft; new 3.5 gem inlays; passes T0, T2, T5, T6, T7 updated; B3 and B5 extended, B6 added; section 6 replaced by "What needs to be made"; two risks updated; calls 5 to 8. New `TOOL-ANIMATIONS.md` (Draft). `ROADMAP.md`: row 32 updated, rows 34 and 35, one pass-log row. `docs/README.md`: one row. |
| Decisions | None. |
| Folder | Added `docs/TOOL-ANIMATIONS.md` and this report. Changed `docs/TOOL-CRAFTING-ROADMAP.md`, `docs/ROADMAP.md`, `docs/README.md`. |

## Evidence
- **GitHub:** branch `staging/design-tool-crafting-mechanics`, stacked on `staging/design-tool-crafting` (PR #108). Commits 867951e (mechanics) and the animations commit after it. Separately, PR #109 (`staging/godot-imports`, against the default branch) commits 1,729 Godot `.import` files for assets already on the default branch. Open PRs: #100, #103 to #109. No new backup tags (latest `backup/main-20261116-1312`); nothing was merged.
- **Claude:** on 2026-11-21 the user asked to develop the roadmap's mechanics, leave the existing Blockbench models alone and focus on what needs making. On 2026-11-22 they asked to finish that, write up animations too, set aside the open calls and commit the import files. Earlier work is in `reports/2026-11-21-tool-crafting-roadmap.md`.
- **Folder structure:** `git diff --stat` for the mechanics commit: 3 files, 130 insertions, 15 deletions. The animations commit adds 2 files and edits `ROADMAP.md` and `README.md`. The 1,729 untracked `.import` files are now in PR #109 and are still untracked on this branch.

## Consistency check
- **Item pictures checked.** All 223 PNGs in `sprites/source/items/` were viewed (contact sheets) and matched to the `02-resources.md` mining table before writing about gems and icons. Titanite and Dreadstone use the `mithril` and `adamantite` files, as the table says. D-005 still names those tiers Mithril and Adamantite; this is already known, and the roadmap follows D-060 and the table.
- **No pickaxe icons in `items/`.** Axes, sickles, rods and bows have icons there; pickaxes live in `sprites/source/pickaxes/`, with only Stone, Bronze and Iron drawn (`02-resources.md`). Section 6.2 takes pickaxe head colours from there.
- **Bow icons have a string, bow models don't.** The string drawn in code (`TOOL-ANIMATIONS.md` section 3) brings the models in line with the icons without editing them.
- **Rare drops in 3.5 lean on Proposed work.** Sap (`resource_gathering.md` 5.1) and seeds (section 6) are Proposed in PR #107. Gems (D-012), pearls (`02-resources.md`) and trophies (D-103) are not.
- **First-craft XP (M11)** comes from `xp_system.md`, itself a proposal.
- **Fishing.** D-109's cast-and-bite loop runs only in the test scene, on a different rig from the live Imp's. The animation passes build on the live Imp (pass A6).
- Fixed a broken row in the roadmap's 2.1 table (the Rod row was missing a cell).

## Suggestions (not applied)
- If the merchant base price (D-074) is set high, use ×1.10 for inlays instead of ×1.25.
- Retire the test scene's gatherer rig (`characters/gatherer.gd`) once the live Imp can fish, so there's one set of animations to tune.
- Animation passes A1 (bow) and A2 (fishing) first: the bow is the one tool with no animation, and the bite cue is gameplay, not polish.

## What's next
Pass T1 of the roadmap (calls 1 to 4), then T6 and T7 once calls 5 and 6 are answered. For animations, pass A1 (the bow) once hunting is in the live world. Every animation pass touches J00BA's `imp_visual.gd`, so J00BA needs to agree too.

## What I need from you
1. Calls 1 to 4 (roadmap section 7): fittings as an extra cost, parts as items, assembly at the workbench, tier-1 fittings only.
2. Calls 5 to 8: take apart and re-haft, gem inlays (×1.25, ×1.10 or no), *Make missing parts* at the workbench, part sell price.
3. Animation calls A to D (`TOOL-ANIMATIONS.md` section 7): hit-stop, station loops, hammer and saw props, other players seeing your swings.
