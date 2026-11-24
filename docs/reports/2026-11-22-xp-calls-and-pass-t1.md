# Report: XP calls answered and pass T1 (2026-11-22)

## In short
The user was fine with the four XP calls, so rested XP, yield nodes from level 50 and the first-craft tier reading are decided, and `xp_system.md` stays the XP doc with them folded in. Pass T1 of the tool crafting roadmap is done: the last two parts rules (P6, P8) are decided and every tool rule now lives in a new `crafting.md`. J00BA hasn't agreed to any of it yet.

## What changed
| Area | Change |
|---|---|
| Docs | `xp_system.md`: four rows in section 1, the first-craft row in 3.2 read by D-143, new 3.5 Rested XP, a D-142 line in section 4, a rested line in section 8 (Draft). `XP-INTERPRETATION.md`: header note, X1 to X3 labelled Decided, "Calls answered" (Draft). `TOOL-CRAFTING-ROADMAP.md`: header note, section 2 label, P6 and P8 Decided, T1 row marked done. New `crafting.md` (Draft). `ROADMAP.md`: rows 37, 39, 40 and a pass-log row. `README.md`: one row |
| Decisions | D-141 rested XP; D-142 yield and drops from level 50; D-143 first-craft tier; D-144 `xp_system.md` leads; D-145 part recipes unlock with their tool (P6); D-146 parts are icons, not models (P8) |
| Folder | Added `docs/crafting.md` and this report. Changed `DECISIONS.md`, `xp_system.md`, `XP-INTERPRETATION.md`, `TOOL-CRAFTING-ROADMAP.md`, `ROADMAP.md`, `README.md` |

## Evidence
- **GitHub:** branch `staging/design-xp-calls-t1`, stacked on `staging/design-xp-interpretation` (PR #114). Open drafts before this one: #100, #103 to #114. None merged since the last report; no new backup tags.
- **Claude:** this session recorded the user's answers ("I'm fine with the XP calls, design pass T1 yes"). Call 4 had no recommended option, so Claude took "keep `xp_system.md` and fold the answers in", because `docs/CLAUDE.md` section 2 rules out replacing a doc unless asked. P6 and P8 are recorded as Decided because T1's exit is "each rule is Decided or dropped", and the user had already said to build them as written (PR #113).
- **Folder structure:** `git diff --stat`: 6 files changed, 44 insertions, 15 deletions, plus the two new files.

## Consistency check
- `xp_system.md` section 1 and section 4 still say tool recipes unlock at 5, 15 … 90. The build and `XP-INTERPRETATION.md` follow J00BA's every-5-levels rule (tier N at 5 × (N − 1), Stellarite at 45). Not changed here.
- D-121 says "bronze 1 … stellarite 8"; the build has nine crafted metal tools, which D-143 now reads as Bronze 1 to Stellarite 9.
- `game_direction.md` section 12 plans `crafting.md` for weapons and armour too. Version 1 covers tools only (Open question 1 in that doc).
- The rod blank and bow stave woods still depend on which tree list wins (`02-resources.md` vs `game_worlds.md`).

## Suggestions (not applied)
- Update `xp_system.md` sections 1 and 4 to the every-5-levels unlocks, once J00BA confirms that's the rule.
- Make M6 (unlocks hold for traded parts) a decision. It is built, and without it coins can buy progress.

## What's next
Pass T2 (pickaxes as the pilot tree: head ids, icon plan, the unfolding menu), and the build work the user asked for in the same message: the hub anvil and workbench, fishing in the live world, and smoother Imp animations.

## What I need from you
1. Is M6 a decision?
2. Should J00BA be tagged on this PR to agree D-141 to D-146?
