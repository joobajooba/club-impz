# Report: tool crafting roadmap (2026-11-21)

## In short
A new roadmap, `TOOL-CRAFTING-ROADMAP.md`, proposes that every tool is assembled from three parts: a working part, a handle and a fitting. The decided recipes stay as they are and pay for the working part; the fitting is a small new cost from tier-1 resources. Nothing is decided. Four calls from you block the first pass (T1).

## What changed
| Area | Change |
|---|---|
| Docs | New `TOOL-CRAFTING-ROADMAP.md` (Draft): status of the five tool trees, the parts model (rules P1 to P8), part tables for every tree, passes T0 to T9, build and art tracks, risks and four calls. `ROADMAP.md` and `README.md` list it. |
| Decisions | None. |
| Folder | Added `docs/TOOL-CRAFTING-ROADMAP.md` and this report. Changed `docs/ROADMAP.md` and `docs/README.md`. |

## Evidence
- **GitHub:** branch `staging/design-tool-crafting`, stacked on `staging/design-gathering` (PR #107). Open PRs before this one: #100, #103, #104, #105, #106, #107. No merges or backup tags since the last report.
- **Claude:** this session read the decided recipes (D-006, D-056, D-058, D-060, D-063, D-069, D-106, D-107, D-110, D-114, D-115), the tool code (`game_data.gd:124-168`, `:340-371`), J00BA's tool sections (`resource_gathering.md` 2.1, 5.3, 6.1, 7.1, 8.1) and the part groups in the tool models. Blockbench 5.2.2 was installed earlier in the session for the art track.
- **Folder structure:** two files added and two changed, all in `docs/`. The untracked `.import` files from the first Godot import are still untracked and not part of this change.

## Consistency check
1. **Bows have no string** in any of the 16 bow models, and they use an older outliner layout (`handle`, `head`).
2. **`demon_pickaxe` and `lunar_pickaxe`** are in `assets/models/tools/` (from J00BA's sprites, commit 9976470) but no doc says what they are.
3. **The rods' reel** has no group of its own in the models.
4. **Two ladders, two tree lists, two unlock schemes** between `DECISIONS.md` and `resource_gathering.md` (already listed in the gathering status report). The roadmap follows `DECISIONS.md` and the build, and says where the other set would change names.
5. **Where bows and rods are crafted** is in the build only as a Proposed code comment (`game_data.gd:151`).

## Suggestions (not applied)
- Fittings from tier-1 resources only (P3), so no skill's tools wait on another skill's progress.
- One icon per part kind, recoloured per tier: 9 drawings instead of 57.
- A "craft missing parts" button, so a tool is still one click.

## What's next
Pass T1: decide the parts rules, then write them into `crafting.md` if you want that doc created. Pass T2 makes pickaxes the pilot tree.

## What I need from you
1. Fittings add a small cost on top of the decided recipes (section 2.5 of the roadmap). Yes or no?
2. Parts as real items, or only slots in the crafting menu?
3. Assemble at the hub workbench, or at each tool's own station?
4. Tier-1 fittings only, or tiered fittings that link the skills harder?
