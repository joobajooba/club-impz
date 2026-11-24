# Report: XP, Claude's interpretation, and the tool parts build (2026-11-22)

## In short
The tool-crafting decisions D-125 to D-136 are now built in Godot (PR #113), with a headless test that passes. On top of that, a new doc, `XP-INTERPRETATION.md`, gives Claude's own take on XP. It keeps every decided XP rule. It shows that the last tool unlocks at 0.4% of the XP to level 100, and proposes rested XP, yield-based back-half nodes and a reading of first-craft XP. Nothing in it is decided yet.

## What changed
| Area | Change |
|---|---|
| Docs | New `XP-INTERPRETATION.md` (Draft). `TOOL-CRAFTING-ROADMAP.md` section 5 says what is built; `BUILD-ROADMAP.md` gets a "Tool parts" milestone and a log row (both on PR #113). `ROADMAP.md` rows 37 and 38 and a pass-log row; a `README.md` row. `xp_system.md` is not changed. |
| Decisions | None. Four calls are open (`XP-INTERPRETATION.md` section 7). |
| Folder | Added `docs/XP-INTERPRETATION.md`, this report, `godot-game/tests/test_tool_parts.gd` and `.tscn`. Changed (PR #113): `game_data.gd`, `inventory.gd`, `save.gd`, `station_menu.gd`, `merchant_menu.gd`, `inventory_ui.gd`, `station.gd`, `area.gd`, `tool_art.gd`, `mining.gd`, `export_presets.cfg`. |

## Evidence
- **GitHub:** PR #113 `staging/tool-parts-build` (65d79e8 code, 2540d2e docs), draft, base `staging/design-tool-calls` (#112). This doc is on `staging/design-xp-interpretation`, stacked on #113. Open PRs before this session: #100, #103 to #112. No merges and no backup tags this session.
- **Claude:** built stages 1 to 3 of the tool-parts plan (the user said yes, build the Proposed bits as written, hub later). Ran `tests/test_tool_parts.tscn` headless: all checks pass with no script errors. `scenes/main.tscn` and `demo_landscape.tscn` load headless with no errors. Not clicked through by hand in the running game. Then wrote the XP doc. Curve numbers come from the RuneScape formula (checked against `resource_gathering.md` section 3); hours use the rates in section 4.1 and the 5% pickaxe speed bonus in `mining.gd`.
- **Folder structure:** `git diff --stat` on this branch: the new XP doc, this report, and rows in `ROADMAP.md` and `README.md`.

## Consistency check
- `xp_system.md` (draft) lists the recipe levels as "bronze at 5, iron at 15 … stellarite at 90". J00BA's 2026-11-14 change made it every 5 levels (Stellarite at 45). `xp_system.md` still has the old list.
- D-121's first-craft example counts "bronze 1 … stellarite 8". The build has nine crafted metal tools and 15 crafted bows. `XP-INTERPRETATION.md` X3 proposes a reading; it isn't decided.
- Two ore ladders in the build: the live world (`mining.gd`, Coal tier 1) and the test landscape (`game_data.gd`, Tin tier 1). Ore ids match, so XP by item id works for ores; most log ids don't.
- `resource_gathering.md` section 3.2 models the pace with the old recipe levels. With the new ones the nonstop total barely moves (about 74 days), but level 50 now comes in about 14 hours, not 17.

## Suggestions (not applied)
- Update `xp_system.md` section 1 to J00BA's every-5-levels recipe rule once the user says which XP doc leads.
- When `skill_trees.md` is written, leave Mining's "Keen Eye" nodes out or replace them: an inlaid Stellarite pickaxe is already at the ×2.5 cap (D-133).
- Consider counting first-craft XP toward the lifetime total only, not the first prestige run, if 150,000 XP (46% of a run) feels too front-loaded.

## What's next
Answers to the four XP calls; then `Progress` (the XP autoload) can be built behind TEST labels, hooked where `XP-INTERPRETATION.md` section 5 lists. Tool parts: a hand play-through of the workbench, the hub workbench and anvil (B2), and J00BA's agreement on D-125 to D-140.

## What I need from you
1. Rested XP (X1): yes, at 10 minutes per hour away and a 2-hour bank?
2. Back-half nodes (X2): yield and drops from level 50, not speed, so the decided pace holds?
3. First-craft tier (X3): a tool's place in its tree (Bronze 1 to Stellarite 9, bows to 15)?
4. Which XP doc leads: `xp_system.md` with these answers folded in, or this one?
