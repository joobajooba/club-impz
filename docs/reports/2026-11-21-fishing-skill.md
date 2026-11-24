# Report: Fishing as a gathering skill (2026-11-21)

## In short
The user asked Claude to take fishing forward in whatever way is best, and to follow the most recent doc set. Fishing now has a full **Proposed** section in J00BA's `resource_gathering.md` (section 7: rods, fish, pearls, where to fish, shoal events, pace), and its fish are listed by biome in `game_worlds.md` section 4.6. These are ideas 1, 2 and 3 from the [expansion report](2026-11-21-fishing-expansion.md). Nothing is decided until J00BA agrees.

## What changed
| Area | Change |
|---|---|
| Docs | `resource_gathering.md`: section 7 goes from a placeholder to Proposed sections 7.1 to 7.5. The fishing row in section 1, one line in section 2.1 (rods are the exception to the ladder) and a note on open question 3. `game_worlds.md` section 4.6: ten fish rows, marked Proposed. Statuses unchanged. |
| Decisions | None. |
| Folder | Added this report. `ROADMAP.md`: file list row 29 and a pass-log row. |

**Which set is newer, topic by topic.** "Most recent" was read per topic, because neither set is newer on everything:

| Topic | IMPLINGZ set | J00BA's set | Followed |
|---|---|---|---|
| Fish, pearls, cast and bite, campfire | D-109, D-111, D-112 (2026-10-21) | Section 7 was an empty placeholder (2026-10-29) | IMPLINGZ, the only content there is |
| Rods | Made from planks, one per tier (D-110, 2026-10-21). J00BA remade these ten rods in PR #100 (2026-11-15) | The metal ladder in section 2.1 (2026-10-29) | IMPLINGZ wood rods. J00BA's own PR #100 is the newest fishing work |
| Gather times, skill XP, pace | None | Sections 2 and 3 (2026-10-29) | J00BA |
| Where resources are | Test scene only | The resource world (`game_worlds.md` section 4) | J00BA |
| Spot refresh | 10 seconds after a catch (D-109, 2026-10-21) | Nodes never run out (section 9, 2026-10-29) | J00BA's section 9. D-109 is not changed (see below) |
| Energy and player XP | D-109 (5 per catch), D-121, D-123 (2026-11-08) | `xp_system.md` points to D-121 and D-123 | D-121 and D-123 |

## Evidence
- **GitHub:** branch `staging/design-fishing-skill`, stacked on `staging/design-fishing` (draft PR #105). PR #100 (J00BA, draft, open) adds `driftwood_rod` to `voidwood_rod`. Dates come from `git log` on each doc and the dates in `DECISIONS.md`.
- **Claude:** item ids are copied from the build (`godot-game/autoload/game_data.gd:109-118`, `:330-335`, `:359-364`). The pace model from the expansion report was rerun with the wood rods and shoals. Its mining figure still matches `resource_gathering.md` section 3.2 (1,808 hours to level 100), so the fishing figures (1,967 hours, 82 days) use the same method.
- **Folder structure:** two docs changed, one report added, `ROADMAP.md` updated. Nothing in `godot-game/` changed.

## Consistency check
- **This changes J00BA's doc using IMPLINGZ content.** `README.md` says neither set changes the other until the doc-set question is answered. The user asked for it here, everything is labelled Proposed, and J00BA reviews it in the PR.
- **Spot refresh:** section 7.3 follows section 9 (spots never run out), which conflicts with D-109's 10-second refresh. D-109 is left as it is. One of them has to change.
- **Rod recipes:** the rod woods are IMPLINGZ trees (Ash, Goldleaf, Ebony and so on), but the resource world grows J00BA's trees (Pine to Worldbark). Pine is tier 1 in one list and the tier 5 rod's wood in the other. Until the tree lists are reconciled, no rod above Driftwood can be crafted from the resource world's trees.
- **Pace:** fishing takes 82 days to level 100, against 75 for mining and lumbering. That's still inside the 2 to 3 month target.
- `02-resources.md` still describes fishing without skill XP, and the build still uses TEST bite times (1.5 to 4 s). Both are left as they are.
- The waters in section 7.3 match the five in `godot-game/scripts/tools/bake_world_data.gd:24-30`.

## Suggestions (not applied)
- If every skill should take exactly the same time, multiply every fishing XP value by about 1.09. The table keeps tier-for-tier parity with the ores instead.
- Once J00BA agrees, run a build pass: place fishing spots in the resource world with the section 7.3 fish lists, as TEST values. Only decided rules get built, so this waits.
- The fish log (expansion idea 6) is the cheapest next addition and carries no economy risk.

## What's next
J00BA reviews PR #105 and this stacked PR. Once both collaborators agree, the rules go into `DECISIONS.md` and a build pass adds fishing to the resource world.

## What I need from you
1. Spot refresh: should spots never run out (section 9, the newer rule, which replaces part of D-109), or keep the 10-second refresh?
2. Will you ask J00BA to review section 7, or should it wait for the doc-set answer?
