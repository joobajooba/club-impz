# Crafting

> Status: draft v1 · Owner: open (J00BA to agree) · Last updated: 2026-11-22
>
> Recipes, stations and tool progression, as planned in `game_direction.md` section 12. This first version holds the **tool** rules: written in pass T1 of `TOOL-CRAFTING-ROADMAP.md`, which keeps the reasoning, the numbers behind them and the passes still to come. This doc must agree with `game_direction.md`. Where the two differ, `game_direction.md` wins until it is updated.
>
> Every rule here is labelled. **Decided** means it is in `DECISIONS.md` (with its D-number). **Proposed** is Claude's suggestion, waiting for the collaborators. **Open question** is not settled. The tool decisions (D-125 to D-146) were made by the user on 2026-11-22; J00BA hasn't agreed yet.

---

## 1. What this doc covers

| Covered | Not yet |
|---|---|
| Tools: pickaxes, axes, sickles, rods, bows. Their parts, fittings, stations, assembly, take apart, inlays | Weapons and armour (Open question; the build's swords cost the same as a pickaxe, Proposed in code) |
| Hilts (D-058, D-107) | Other blacksmithing and other crafting (not decided) |

Crafting costs no energy (D-056). Gathering the materials does.

---

## 2. The rules (P1 to P8)

| # | Rule | Label |
|---|---|---|
| P1 | **Three parts per tool:** the working part that does the job, the handle you hold, and a fitting that joins or drives them (section 3) | Decided, D-125 |
| P2 | **The decided material pays for the working part, unchanged.** The ingots, planks, leather and hilts in D-006, D-058, D-060, D-063, D-069, D-106, D-107 and D-110 stay as they are. The fitting is the only new cost | Decided, D-125 |
| P3 | **Fittings come only from tier-1 resources** gathered with the starter tools (Nettle, Hare, tier-1 trees, Tin, Copper), so no skill's tools wait on another skill's progress | Decided, D-128 |
| P4 | **Parts are real inventory items.** They stack and can be traded like any item (D-081). Fittings are shared across trees; heads, blades, blanks and wraps belong to one tool | Decided, D-126 |
| P5 | **Each part is made at the station of its material; every tool is assembled at the workbench** (section 4). No energy for any step | Decided, D-127 |
| P6 | **A part's recipe unlocks with its tool,** at the same skill level. Fittings are always unlocked | Decided, D-145 |
| P7 | **Starter tools have no parts:** Stone tools, Driftwood Rod, Hare Bow | Decided, D-125 |
| P8 | **Parts are icons, not models.** The assembled tool keeps its model; parts are 48×48 inventory icons (D-015), coloured from their materials' icons | Decided, D-146 |

Tool recipe N unlocks at skill level 5 × (N − 1) (Decided by J00BA, 2026-11-14; `RECIPE_EVERY` in `game_data.gd`).

---

## 3. Parts and recipes

### 3.1 The parts of each tool (Decided, D-125)

| Tree | Working part (the decided material) | Handle | Fitting |
|---|---|---|---|
| Pickaxe | Head: the D-006 / D-060 ingots | The decided hilt | Binding |
| Axe | Head: the D-106 ingots | The decided hilt | Binding |
| Sickle | Blade: the D-063 ingots | The decided hilt | Binding |
| Rod | Blank: the D-110 planks (the grip is part of it) | Part of the blank | Reel and line |
| Bow | Wrap: the D-069 leather (the grip is part of it) | Part of the wrap | Stave and string |

### 3.2 Fittings (Decided, D-125 and D-128)

| Fitting | Id (Proposed) | Made from | Station |
|---|---|---|---|
| Nettle Cord | `nettle_cord` | 1 Nettle bundle | Drying rack |
| Hare Leather Strip | `hare_leather_strip` | 1 Hare leather | Tanning rack |
| Tin Reel | `tin_reel` | 1 Tin ingot | Anvil |
| Copper Reel | `copper_reel` | 1 Copper ingot | Anvil |
| Bronze Reel | `bronze_reel` | 1 Tin ingot + 1 Copper ingot | Anvil |
| Bow Stave | `bow_stave` | 2 tier-1 planks (Ash; Pine if J00BA's tree list wins) | Sawbench |

### 3.3 Metal tools

Materials: D-006, D-060, D-063 (pickaxe head, sickle blade), D-106 (axe head, rounding up Proposed), D-058 and D-107 (hilts). Bindings: D-125. Part ids such as `gold_pickaxe_head`, `gold_axe_head`, `gold_sickle_blade`: Proposed (pass T2).

| Tier | Metal | Pickaxe head, sickle blade | Axe head | Hilt | Binding |
|---|---|---|---|---|---|
| 1 | Stone | Starter, no parts | Starter | n/a | n/a |
| 2 | Bronze | 5 Tin + 5 Copper ingots | 3 Tin + 3 Copper | Ash Wood | Nettle Cord |
| 3 | Iron | 5 Iron | 3 Iron | Ash Wood | Nettle Cord |
| 4 | Steel | 10 Iron | 5 Iron | Ash Wood | Nettle Cord |
| 5 | Gold | 10 Gold | 5 Gold | Ash Wood | Nettle Cord |
| 6 | Obsidian | 10 Obsidian | 5 Obsidian | Oak Wood | Hare Leather Strip |
| 7 | Titanite | 10 Titanite | 5 Titanite | Oak Wood | Hare Leather Strip |
| 8 | Dreadstone | 10 Dreadstone | 5 Dreadstone | Oak Wood | Hare Leather Strip |
| 9 | Void | 10 Void | 5 Void | Void | Hare Leather Strip |
| 10 | Stellarite | 10 Stellarite | 5 Stellarite | Cosmic | Hare Leather Strip |

Hilts (D-058, D-107), at the anvil: Ash Wood from 5 Ash planks, Oak Wood from 5 Oak planks, Void from 2 Void ingots + 1 Arcanium, Cosmic from 2 Stellarite ingots + 1 Eclipsium.

### 3.4 Rods

Blank: 10 planks of tree tier N − 1 (D-110). Reel and line: D-125. Part ids `ash_rod_blank` … `voidwood_rod_blank`: Proposed (pass T4). The woods follow whichever tree list wins (Open question, `TOOL-CRAFTING-ROADMAP.md` 1.4).

| Tier | Rod | Blank | Reel | Line |
|---|---|---|---|---|
| 1 | Driftwood | Starter, no parts | n/a | n/a |
| 2 to 4 | Ash, Birch, Oak | 10 planks of the tier below | Tin Reel | Nettle Cord |
| 5 to 7 | Pine, Goldleaf, Ebony | 10 planks of the tier below | Copper Reel | Nettle Cord |
| 8 to 10 | Silverbark, Bloodwood, Voidwood | 10 planks of the tier below | Bronze Reel | Nettle Cord |

A rod takes its listed reel or a better one, swapped free at the workbench (D-135).

### 3.5 Bows

Wrap: 10 leather of animal tier N − 1 (D-069). Stave and string: D-125. Part ids `fox_bow_wrap` … `eclipse_dragon_bow_wrap`: Proposed (pass T5).

| Tier | Bow | Wrap | Stave | String |
|---|---|---|---|---|
| 1 | Hare Bow | Starter, no parts | n/a | n/a |
| 2 to 16 | Fox to Eclipse Dragon (11 to 16 legendary) | 10 leather of the tier below | Bow Stave | Nettle Cord |

---

## 4. Stations (Decided, D-127)

| Station | Makes |
|---|---|
| Anvil (blacksmith) | Heads, blades, reels; hilts (D-058, D-107) |
| Sawbench | Rod blanks, bow staves |
| Tanning rack | Bow wraps, leather strips |
| Drying rack | Nettle Cord |
| Workbench (hub) | Assembles every tool from its three parts |

---

## 5. At the workbench

| Mechanic | Rule | Label |
|---|---|---|
| Make missing parts | Builds any missing part from **processed** materials in the bag (ingots, planks, leather, bundles). It never smelts, saws, tans or dries. If something is short, it shows the full shopping list | Decided, D-131 |
| Take apart | A crafted tool not in hand gives back its hilt (metal tools), reel (rods) or stave (bows); the rest is used up, inlays included. Starter tools can't be taken apart | Decided, D-129 |
| Re-haft | Assembling tier N while owning tier N − 1 of the same kind moves that part across in one click | Decided, D-129 |
| Inlay | One socket per crafted tool: a gem (Topaz 1 to Eclipsium 10) or pearl (River 1 to Star 10) of tier N − 1 or higher. Rare-drop chance ×1.25. Used up; can't be swapped; lost on take apart or re-haft | Decided, D-130, D-134 |
| One boost cap | Rare-drop boosts multiply, capped at ×2.5 for gems, sap, seeds, pearls and trophies. Mint token chances never change (D-045, D-076) | Decided, D-133 |
| Selling parts | Parts sell for the raw items they took plus 25%, counted once. Crafted tools can't be sold | Decided, D-132 |
| Tool rack | Beside the workbench; shows every tool you own, inlays included. A full rack of one kind gives a cosmetic and a title (which ones: Open question) | Decided, D-136 |
| Part rows | Each tool row shows its three parts with have / need and the station that makes each | Proposed (M1) |
| Instant | Every craft is done the moment you press the button; the animation never holds the item back | Proposed (M2) |
| One of each tool | At most one copy of each tool; any number of parts | Proposed (M3) |
| Batches | Fittings craft ×1, ×5 or ×all; other parts one at a time | Proposed (M5) |
| Unlocks hold for traded parts | Assembly needs the tool's unlock level too, so a bought part can't skip a level | Proposed (M6) |
| XP | Parts and fittings give no XP; the first assembly of each tool gives first-craft XP (D-121, read by D-143) | Decided, D-143 |
| One mechanic at a time | The first craft is one button; part rows, re-haft, take apart and the socket appear when they first matter | Proposed (E1) |

---

## 6. What is built

- Parts, fittings, part recipes at their stations, the workbench (Craft, make missing parts, shopping list), take apart, re-haft, inlays, the ×2.5 cap and part sell prices are in Godot, in the test landscape (`demo_landscape.tscn`), with a headless test (`tests/test_tool_parts.tscn`). PR #113, draft. The Proposed rules above are built as written, at the user's request.
- The hub's anvil, workbench, furnace, sawbench, tanning rack and drying rack open the same menus with E (`scripts/world/hub_town.gd` STATIONS, test `tests/test_hub_stations.tscn`), in the PR stacked on this one. The tool rack (D-136) isn't built yet.

---

## 7. Open questions

1. **Weapons and armour:** recipes, stations and whether they use parts.
2. **Tree list:** the rod blanks and the bow stave follow whichever tree list wins (IMPLINGZ Ash to Starwood, or J00BA's Pine to Worldbark).
3. **Demon and Lunar pickaxes:** models exist (from J00BA's sprites) but no doc gives them a recipe or a use.
4. **Full rack rewards:** which cosmetic and title (D-136).
