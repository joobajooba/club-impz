# Tool crafting roadmap

> **Proposed** by Claude on 2026-11-21, at the user's request: tools should be crafted from several parts that make sense, and the five tool trees should be expanded. Nothing here is decided. Where a proposal touches a decision in `DECISIONS.md`, it says which one. The full recipes will live in `crafting.md` once that doc exists (it is planned in `game_direction.md` section 12).

> **2026-11-22:** at the user's request, the crafting mechanics are added (section 2.6, take apart in 3.4, gem inlays in 3.5, what needs to be made in section 6, calls 5 to 8). The user also set two limits: the existing Blockbench models stay as they are, and the work focuses on mechanics. The tool animations are in `TOOL-ANIMATIONS.md`.

> **2026-11-22, later:** at the user's request, stage 2 of the mechanics is added (section 3.6: E1 to E5, and the ideas for later settled; calls 9 to 12). The animations are left as they are.

> **2026-11-22, decided:** the user said yes to calls 1 to 12 (section 7). They are **D-125 to D-136** in `DECISIONS.md`, and the labels below say which part each one covers. Everything else here stays Proposed. J00BA has not agreed yet.
>
> **2026-11-22, pass T1:** P6 and P8 are Decided too (D-145, D-146), and P1 to P8, the fittings, the stations and the decided mechanics are written into the new `crafting.md`, which now leads for those rules. This roadmap keeps the trees (section 3) and the passes still to come.

**Labels:** **Decided** (in `DECISIONS.md`, with its D-number), **Proposed** (Claude's suggestion, waiting for you), **Open question** (not settled).

**The five trees** are the five gathering tool ladders: pickaxes, axes, sickles, fishing rods and bows. Weapons come last (pass T9).

---

## 1. Where things stand

### 1.1 Decided recipes

| Tree | Crafted tiers | What a tool costs today | Decided by |
|---|---|---|---|
| Pickaxes | Bronze to Stellarite (9) | Ingots + 1 hilt. Stone is the free starter. | D-006, D-060 |
| Sickles | Bronze to Stellarite (9) | The same as the pickaxe of that metal. | D-063 |
| Axes | Bronze to Stellarite (9) | Half the pickaxe's ingots + its hilt. Rounding up is Proposed (`02-resources.md`, lumbering table). | D-106 |
| Rods | Ash to Voidwood (9) | 10 planks of tree tier N−1. Driftwood is the free starter. | D-110 |
| Bows | Fox to Eclipse Dragon (15) | 10 leather of animal tier N−1. Hare Bow is the free starter. | D-069 |
| Hilts | Ash, Oak, Void, Cosmic | 5 Ash or Oak planks; 2 Void ingots + Arcanium; 2 Stellarite ingots + Eclipsium. At the blacksmith. | D-058, D-107 |

Crafting costs no energy (D-056). Gathering the materials does.

### 1.2 What is built

- Every tool is one recipe: its materials plus a hilt, crafted in one step (`godot-game/autoload/game_data.gd:351-364`). No parts exist yet.
- Where each kind is crafted (`game_data.gd:153`): pickaxes, sickles and axes at the blacksmith; bows at the tanning rack and rods at the sawbench (both Proposed in the code comment).
- Recipes unlock every 5 skill levels, tier N at level 5 × (N−1) (`game_data.gd:142-148`, J00BA, 2026-11-14).
- Swords cost the same as a pickaxe (`game_data.gd:354`, Proposed).
- The crafting menu (`ui/station_menu.gd`) and the processing stations are only in the test scene (`demo_landscape.tscn`). The hub has an anvil and a workbench, both placeholders (`scenes/hub/anvil_placeholder.tscn`, `workbench_placeholder.tscn`).

### 1.3 Models

The 58 tool models (plus 5 lineup files) are in `godot-game/assets/models/tools/` (sources in `assets/models/source/blockbench/tools/`). Every tier has its own shape (D-114, D-115).

| Tree | Groups in the `.bbmodel` | Gap for a parts system |
|---|---|---|
| Pickaxes, axes, sickles | `handle`, `head`, `details` | No `binding` group. |
| Rods | `handle`, `head`, `details`, `line` | The reel (body, spool, crank) has no group of its own. |
| Bows | `handle`, `head` (older outliner layout) | **No string.** |
| `demon_pickaxe`, `lunar_pickaxe` | One group each, not split | Not in any doc (added from J00BA's sprites, commit 9976470). |

**The models stay as they are** (your direction, 2026-11-21). No `binding`, `reel` or `string` group is added; the gaps above are kept only as a record. Parts are shown as icons (rule P8), and the bow string is drawn in code (`TOOL-ANIMATIONS.md`).

### 1.4 Gaps and conflicts this roadmap has to work around

1. **Two tool ladders.** D-063 and the build have a Steel tier and one sickle per plant tier. J00BA's ladder (`resource_gathering.md` section 2.1) has no Steel, and its starter tools reach tiers 1 to 3. The tables below follow `DECISIONS.md` and the build.
2. **Two tree lists.** The rod recipes use the IMPLINGZ trees (Ash first). J00BA's section 5 trees start with Pine, which is why PR #107 proposes a Pine Wood Hilt (section 5.3). Every wood recipe here says "tier-1 planks" for that reason.
3. **Two unlock schemes.** The build unlocks every 5 levels; section 2.1 uses 5, 15, 25 … 90. Parts follow whichever wins (rule P6).
4. **Where bows and rods are crafted** is not decided (D-069 and D-110 give only the cost).
5. **No hub stations work yet**, so nothing can be crafted in the live world.

---

## 2. The parts model (Decided: D-125 to D-128, D-145, D-146; written into `crafting.md` in pass T1)

### 2.1 Three parts per tool

Every crafted tool is put together from three parts: the **working part** that does the job, the **handle** you hold, and a **fitting** that joins or drives them.

| Tree | Working part (the decided material) | Handle | Fitting |
|---|---|---|---|
| Pickaxe | **Head**: the D-006 / D-060 ingots | The decided hilt | **Binding**: cord or leather strip |
| Axe | **Head**: the D-106 ingots | The decided hilt | **Binding** |
| Sickle | **Blade**: the D-063 ingots | The decided hilt | **Binding** |
| Rod | **Blank** (the pole): the D-110 planks | The grip, part of the blank | **Reel** (ingots) and **line** (cord) |
| Bow | **Wrap** (hide backing and grip): the D-069 leather | Part of the wrap | **Stave** (planks) and **string** (cord) |

Why these parts: they are what a real tool of that kind is made of, each one comes from a different skill, and each maps to a group the models already have (section 1.3). The leather wrap is what makes a Wolf Bow a Wolf Bow, so the animal still names and themes the bow (D-115).

### 2.2 Rules

- **P1. Three parts per tool,** as in 2.1.
- **P2. The decided material pays for the working part, unchanged.** The ingots, planks, leather and hilts in D-006, D-058, D-060, D-063, D-069, D-106, D-107 and D-110 stay exactly as they are. **The fitting is the only new cost.** That still changes the total those decisions give: Decided (D-125).
- **P3. Fittings come only from tier-1 resources,** gathered with the starter tools: Nettle, Hare, tier-1 trees, Tin and Copper. So no skill's tools are locked behind another skill's progress. A miner needs a few minutes of foraging and hunting, not a Steel sickle.
- **P4. Parts are real inventory items.** They stack, and they can be traded like any item (D-081). Fittings are shared across trees; heads, blades, blanks and wraps belong to one tool.
- **P5. Each part is made at the station of its material; every tool is assembled at the workbench** (section 2.4). No energy for any step (D-056).
- **P6. A part's recipe unlocks with its tool,** at the same skill level. Fittings are always unlocked. Decided (D-145).
- **P7. Starter tools have no parts** (Stone tools, Driftwood Rod, Hare Bow), the same as today.
- **P8. Parts are icons, not models.** The assembled tool keeps the model it has today (section 1.3). Parts appear only as 48×48 inventory icons (D-015), and their colours come from the icons of their materials. Decided (D-146).

### 2.3 Fittings

| Fitting | Id | Made from | Station | Gathering it takes |
|---|---|---|---|---|
| Nettle Cord | `nettle_cord` | 1 Nettle bundle | Drying rack | 2 Nettle picks (D-062) |
| Hare Leather Strip | `hare_leather_strip` | 1 Hare leather | Tanning rack | 2 Hare hunts (D-068) |
| Tin Reel | `tin_reel` | 1 Tin ingot | Anvil | 2 Tin mines (D-054) |
| Copper Reel | `copper_reel` | 1 Copper ingot | Anvil | 2 Copper mines |
| Bronze Reel | `bronze_reel` | 1 Tin ingot + 1 Copper ingot | Anvil | 4 mines |
| Bow Stave | `bow_stave` | 2 tier-1 planks (Ash; Pine if J00BA's tree list wins) | Sawbench | 4 chops (D-107) |

### 2.4 Stations

| Station | Makes | Status |
|---|---|---|
| Anvil (blacksmith) | Heads, blades, reels; hilts | Hilts at the blacksmith are Decided (D-058, D-107). The rest is Decided (D-127). |
| Sawbench | Rod blanks, bow staves | Decided (D-127). The build already crafts rods here. |
| Tanning rack | Bow wraps, leather strips | Decided (D-127). The build already crafts bows here. |
| Drying rack | Nettle Cord | Decided (D-127). |
| Workbench (hub) | Assembles every tool from its three parts | Decided (D-127). Gives the hub's placeholder workbench its job. |

### 2.5 What the fittings add

All of it is gathered with starter tools. Counts are gathering actions.

| Tree (full crafted set) | Fittings | Extra actions | Main recipe, for scale | Increase |
|---|---|---|---|---|
| Pickaxes (9) | 4 cords, 5 strips | 18 | About 415 mines plus hilts | ~4% |
| Axes (9) | 4 cords, 5 strips | 18 | About half the pickaxe ingots | ~8% |
| Sickles (9) | 4 cords, 5 strips | 18 | The same as pickaxes | ~4% |
| Rods (9) | 9 cords, 3 Tin, 3 Copper, 3 Bronze reels | 42 | About 330 chops (`02-resources.md`, fishing) | ~13% |
| Bows (15) | 15 staves, 15 cords | 90 | About 560 hides for 150 leather (D-068) | ~16% |

The pickaxe figure counts ore and Coal for the ingots (D-054, D-055). The fittings are a small extra on every tree; their job is to make each tool a thing you assemble and to link the skills (D-085, "skills feed each other"), not to slow anyone down.

### 2.6 Crafting mechanics (Proposed; M4 and M7 to M10 Decided: D-129 to D-132)

How crafting behaves for the player, step by step. The build facts each rule starts from are in brackets.

| # | Mechanic | Rule |
|---|---|---|
| M1 | **Part rows** | At the workbench each tool row shows its three parts, each with *have / need* and the station that makes it. A part you are missing shows the materials it takes. (The build's tool row already shows icon, reach, lock, cost and Craft/Owned: `ui/station_menu.gd:74-96`.) |
| M2 | **Instant, no energy** | Every craft and assembly is done the moment you press the button, as in the build, with no energy (D-056). The animation plays alongside and never holds the item back (`TOOL-ANIMATIONS.md`, rule A1). |
| M3 | **One of each tool, any number of parts** | You own at most one copy of each tool, as now (`Inventory.owns`; tools live in `GameData.tools`, not the bag). Parts are bag items: you can make spares, stack them and trade them (P4, D-081). Assembling a tool you already own is blocked. |
| M4 | **Make what's missing** | The workbench's *Make missing parts* button builds any missing part from **processed** materials in your bag (ingots, planks, leather, bundles). It never smelts, saws, tans or dries: raw materials still go through their station (D-107, D-086). If something is short, it shows the full shopping list instead. This is how B3's one-click promise works. |
| M5 | **Batches** | Fittings craft ×1, ×5 or ×all, since they are shared and stack. Heads, blades, blanks and wraps craft one at a time, since each belongs to one tool. |
| M6 | **Unlocks hold for traded parts** | A part's recipe unlocks with its tool (P6). Assembly needs the tool's unlock level too, so a part bought from another player cannot skip a level (the build unlocks tier N at level 5 × (N−1), `game_data.gd:142-148`). Without this, coins could buy progress. |
| M7 | **Re-haft when upgrading** | When you assemble tier N and own tier N−1 of the same kind, the workbench offers *Re-haft*: it takes N−1 apart (3.4) and moves its hilt, reel or stave straight into the new tool. One click, nothing to carry. |
| M8 | **Take apart** | Any crafted tool you don't have in hand can be taken apart for its returned part (3.4). Starter tools have no parts and stay with you, so no one is ever left without a tool. |
| M9 | **Gem inlay** | One gem socket per crafted tool, filled at the workbench (3.5). The gem is used up. |
| M10 | **Part sell price** | Parts sell to the merchant under D-074 read literally: *the raw items they took, plus 25%*, counted once. Not +25% per step, which would pay about +95% for a part three steps from the ore. Crafted tools still can't be sold (they have no price, `game_data.gd:490`). |
| M11 | **XP on the tool, not the parts** | Making parts and fittings gives no XP. The first assembly of each tool gives its first-craft XP (D-121: 500 × tier). D-121's processing XP counts raw items used, and parts are made from processed ones, so they give none. So spare parts can't be used to farm XP. |

No durability: tools don't wear out today, and nothing here adds wear.

---

## 3. The five trees (Proposed; the fitting each tier takes is Decided, D-125)

Ids follow the build's pattern (`<tier>_<kind>`), with the part name added.

### 3.1 Pickaxes, axes and sickles

One table, because the three metal tools share their metals, hilts and bindings.

| Tier | Metal | Pickaxe head and sickle blade (D-006, D-060, D-063) | Axe head (D-106) | Hilt (D-058, D-107) | Binding |
|---|---|---|---|---|---|
| 1 | Stone | Starter, no parts | Starter | n/a | n/a |
| 2 | Bronze | 5 Tin + 5 Copper ingots | 3 Tin + 3 Copper | Ash Wood | 1 Nettle Cord |
| 3 | Iron | 5 Iron | 3 Iron | Ash Wood | 1 Nettle Cord |
| 4 | Steel | 10 Iron | 5 Iron | Ash Wood | 1 Nettle Cord |
| 5 | Gold | 10 Gold | 5 Gold | Ash Wood | 1 Nettle Cord |
| 6 | Obsidian | 10 Obsidian | 5 Obsidian | Oak Wood | 1 Hare Leather Strip |
| 7 | Titanite | 10 Titanite | 5 Titanite | Oak Wood | 1 Hare Leather Strip |
| 8 | Dreadstone | 10 Dreadstone | 5 Dreadstone | Oak Wood | 1 Hare Leather Strip |
| 9 | Void | 10 Void | 5 Void | Void | 1 Hare Leather Strip |
| 10 | Stellarite | 10 Stellarite | 5 Stellarite | Cosmic | 1 Hare Leather Strip |

- Part ids: `gold_pickaxe_head`, `gold_axe_head`, `gold_sickle_blade`.
- Cord for the light Ash-hilt tools, a leather grip for the heavy heads from Obsidian up. The model shows the binding in the tier's own colours.
- **Ideas for later:** the gem socket became 3.5. The axe-head and sickle-edge ideas are dropped in 3.6, with the reasons.

### 3.2 Rods

| Tier | Rod | Blank (D-110) | Reel | Line |
|---|---|---|---|---|
| 1 | Driftwood | Starter, no parts | n/a | n/a |
| 2 | Ash | 10 Ash planks | Tin Reel | 1 Nettle Cord |
| 3 | Birch | 10 Birch planks | Tin Reel | 1 Nettle Cord |
| 4 | Oak | 10 Oak planks | Tin Reel | 1 Nettle Cord |
| 5 | Pine | 10 Pine planks | Copper Reel | 1 Nettle Cord |
| 6 | Goldleaf | 10 Goldleaf planks | Copper Reel | 1 Nettle Cord |
| 7 | Ebony | 10 Ebony planks | Copper Reel | 1 Nettle Cord |
| 8 | Silverbark | 10 Silverbark planks | Bronze Reel | 1 Nettle Cord |
| 9 | Bloodwood | 10 Bloodwood planks | Bronze Reel | 1 Nettle Cord |
| 10 | Voidwood | 10 Voidwood planks | Bronze Reel | 1 Nettle Cord |

- Part ids: `ash_rod_blank` … `voidwood_rod_blank`. The float stays part of the model, not a crafted part.
- The blank woods follow whichever tree list wins (section 1.4, item 2).
- **Ideas for later:** the reel and the bite window are worked out in 3.6 (E4). The lure slot stays blocked (3.6, dropped ideas).

### 3.3 Bows

| Tier | Bow | Wrap (D-069) | Stave | String |
|---|---|---|---|---|
| 1 | Hare Bow | Starter, no parts | n/a | n/a |
| 2 to 10 | Fox to Starwyrm | 10 leather of tier N−1 | 1 Bow Stave | 1 Nettle Cord |
| 11 to 16 | Stormhorn Ram to Eclipse Dragon (legendary) | 10 leather of tier N−1 | 1 Bow Stave | 1 Nettle Cord |

- Part ids: `fox_bow_wrap` … `eclipse_dragon_bow_wrap`.
- The stave is tier-1 wood for every bow (rule P3). The model themes it on the bow's animal anyway (D-115), so an Eclipse Dragon Bow still looks like one.
- **Ideas for later:** a trophy in the legendary bows and an arrow-head slot are both dropped in 3.6, with the reasons.

### 3.4 Take apart and re-haft (pass T6, Decided: D-129)

Taking a tool apart gives back the part that carries on to the next tier. Everything else is used up.

| Tree | You get back | Used up | Saved over the full tree | Net with the fittings (2.5) |
|---|---|---|---|---|
| Pickaxes, axes, sickles (each) | The hilt | Head or blade, binding | 60 chops: one Ash and one Oak hilt serve all seven wood-hilt tiers, 25 chops instead of 85 (D-107: Ash planks take 2 logs, Oak 3) | 42 actions **cheaper** than today |
| Rods | The reel | Blank, line | 16 mines: one reel of each metal instead of three | 26 actions dearer |
| Bows | The stave | Wrap, string | 56 chops: one stave instead of fifteen | 34 actions dearer |

- A returned hilt only helps while the next tier takes the same one: Ash for tiers 2 to 5, Oak for 6 to 8. Void and Cosmic hilts each serve one tier (D-058), so they come back but have no next tool. They can be sold under M10 or kept for trade.
- With take apart, the metal trees end up cheaper than the decided recipes and rods and bows a little dearer. That changes the hilt totals in D-006, D-060, D-063 and D-106: Decided (D-129).
- **Push-back:** fewer hilts needed means less demand for Ash and Oak planks and, while lumbering isn't live, fewer wood hilts bought from the merchant (D-075), which is one of the few coin sinks. It's small (five fewer hilts per tree), but it's a sink lost.

### 3.5 Gem inlays (pass T7, Decided: D-130)

Gems have two uses today: selling (D-074) and the Void and Cosmic hilts (D-058). An inlay gives them a third that stays in play.

- **One socket per crafted tool.** Starter tools have none.
- **Which gem fits.** A gem of tier N−1 or higher, by the mining table in `02-resources.md` (Topaz 1, Sapphire 2, Amethyst 3, Ruby 4, Emerald 5, Jade 6, Diamond 7, Painite 8, Arcanium 9, Eclipsium 10). A Bronze pickaxe (tier 2) takes Topaz or better; a Stellarite pickaxe takes Arcanium or Eclipsium. Bows from tier 11 take Eclipsium.
- **What it does.** The tool's rare-drop chance ×1.25. One perk for every tree, so there's nothing to balance per tool:

| Tool | Its rare drop | Base chance |
|---|---|---|
| Pickaxe | Gem | 10% at Tin to 1% at Stellarite (D-012); ×2 with the Stellarite pickaxe (D-059), so ×2.5 with an inlay too |
| Axe | Sap | `resource_gathering.md` 5.1 (Proposed, PR #107) |
| Sickle | Seed | `resource_gathering.md` section 6 (Proposed) |
| Rod | Pearl | `02-resources.md`, fishing |
| Bow | Trophy | D-103 |

- **What it's worth.** Rare drops sell for 10× their tier's raw item (D-074), so the inlay adds about **+12% coin income** from that tool's gathering at a 10% drop chance, **+2%** at 1%, and **+17%** on a Tin vein with the Stellarite pickaxe. A Topaz pays for itself in about 40 Tin mines.
- **The gem is lost** when the tool is taken apart (3.4) or re-hafted (M7), so inlays are a steady gem sink. You can't swap a gem out.
- **Fair to everyone.** Gems only come from play, so Imp holders get no edge beyond what they mine (D-085).
- **Push-back:** it's a real income boost, so almost everyone will inlay. That's fine as a sink, but if the merchant base price (D-074, not set) runs high, ×1.10 is the safer size. The user chose ×1.25 (D-130).

### 3.6 Stage 2: how the mechanics grow (E1 Proposed; E2 to E5 Decided: D-133 to D-136)

Sections 2.6, 3.4 and 3.5 are stage 1: what crafting does. Stage 2 is what happens around it: how a player meets each mechanic, how the boosts add up, and what to do with a tool you've outgrown. It adds no new items and no new stations.

#### E1. One mechanic at a time

A new player shouldn't meet parts, re-hafting and sockets all at once. Each one appears the first time it can matter. The flags live in the save (B4).

| When | What appears | Until then |
|---|---|---|
| Your first crafted tool in any tree (tier 2) | One **Craft** button: it runs *Make missing parts* (M4), then assembles. If a raw material is short, the shopping list says where it comes from, for example "1 Nettle Bundle: drying rack, from 2 Nettle (stone sickle)". | The tool row looks as it does in the build today. |
| The first time a part or fitting is in your bag | The part rows (M1) open by default from then on. | Part rows are folded under "Parts". |
| Your second crafted tool of one kind (tier 3) | *Re-haft* (M7) and *Take apart* (M8), with one line on what moves over. | Hidden, since there is nothing to move yet. |
| You hold a gem or pearl that fits a tool you own (E3) | The socket on that tool's row (M9). | No empty socket is shown. |

- The first Nettle Cord is the first time one skill feeds another (D-085): a miner's Bronze pickaxe needs one bundle from foraging. The shopping list makes that a pointer, not a wall.
- E1 needs no call of its own. It is how B3's menu shows calls 2, 5, 6 and 7.

#### E2. One rule for stacking boosts

Four things raise a rare-drop chance, and only one pair has a stacking rule so far:

| Boost | Rare drop | Size | Status |
|---|---|---|---|
| Stellarite pickaxe | Gems | ×2 | Decided (D-059) |
| A tamed animal tracking | Trophies | ×1.5 | Decided (D-072) |
| Potion | One per skill | ×1.15 to ×1.6 | Proposed (`02-resources.md`, potions) |
| Inlay | The tool's rare drop | ×1.25 | Decided (D-130) |

- **Rule:** the boosts multiply, and the total is capped at **×2.5** for every rare drop. This takes the potion cap (×2.5, gems only) and applies it to all five rare drops. Mint token chances never change (D-045, D-076).
- **What it means:**
  - **Gems with the Stellarite pickaxe and an inlay:** 2 × 1.25 = 2.5, at the cap. A Prospector's Draught adds nothing on top, so the menu should say "at cap" rather than let a player waste a potion.
  - **Trophies with tracking and an inlay:** 1.5 × 1.25 = 1.875. A Tracker's Brew from a tier-5 bundle up (×1.35) reaches the cap.
  - **Pearls, seeds and sap:** an inlay and the strongest potion make 1.25 × 1.6 = 2.0, under the cap.
- **Why a cap:** rare drops sell for 10× their tier's raw item (D-074). At the cap, a Tin vein with its 10% gem chance pays 2.5× its ore's value in gems, 3.5× in total. With no cap, the Stellarite pickaxe, an inlay and the strongest potion make ×4, and the vein pays 5×.
- **Push-back:** with the cap, the gem potion is useless to anyone holding an inlaid Stellarite pickaxe. That is the price of D-059 being so strong. The other way out, leaving the inlay off the Stellarite pickaxe's gem roll, is harder to explain to players.

#### E3. Pearls fit the socket too

Pearls have no use besides selling (`resource_gathering.md` 5.1, open question). They have the gem chances (D-112) and ten tiers, so they fit 3.5 without a new rule.

- A socket takes a **gem or a pearl** of tier N−1 or higher. Pearl tiers: River 1, Sand 2, Moss 3, Black 4, Golden 5, Shadow 6, Frost 7, Blood 8, Void 9, Star 10 (`02-resources.md`, fishing).
- The effect is the same ×1.25, and the pearl is lost on take apart or re-haft, the same as a gem.
- Fishing then feeds every tool the way mining does (D-085). A player who fishes can inlay without mining, so gems stop being the only route.
- The pip on the icon is the `pearl_*` icon scaled down (6.2). All ten are in `sprites/source/items/`.
- **Not sap or trophies.** Pine Resin and Birch Sap aren't stones, so only the Amber tiers would fit, which makes a split rule. Trophies fill cabinet sets (D-103), and seeds wait for farming (D-065). What sap is for stays open.

#### E4. The reel sets the bite window

Fishing is the only skill with a timing moment (D-109). So far the reel only adds cost. **Decided (D-135):** the window narrows as the fish get harder, and the reel wins it back.

- **Window** for a fish of tier T: W × (1 − 0.04 × (T − 1)). A Minnow gets the full W, a Starfin Koi 0.64 W. W is set when fishing is built in Godot; it isn't built yet.
- **Reel:** no reel (the Driftwood rod) ×1.0, Tin ×1.1, Copper ×1.25, Bronze ×1.4.
- **A rod takes its listed reel (3.2) or a better one.** Swapping costs nothing at the workbench, and the old reel goes back to the bag.

| Fish tier, with the rod of that tier | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Listed reel | none | Tin | Tin | Tin | Copper | Copper | Copper | Bronze | Bronze | Bronze |
| Window (× W) | 1.00 | 1.06 | 1.01 | 0.97 | 1.05 | 1.00 | 0.95 | 1.01 | 0.95 | 0.90 |

- So the newest fish you can catch is always about as hard to time as your first Minnow, and the fish below it get easier as you climb: a Minnow on a Bronze reel gets 1.4 W. Only the top fish tightens a little. That is steady progress you can feel (D-085).
- **Push-back:** this is a web game, and the server judges every drop (`GODOT.md`). A narrow window on a slow connection loses fish the player timed right. W has to be wide enough to survive web latency, measured once fishing is built. A bot times any window perfectly, so this does nothing against bots.

#### E5. Keep it on the rack, or take it apart

Take apart (3.4) saves 42 actions per metal tree, so everyone will do it, and an outgrown tool is only salvage. The rack makes it a choice.

- The tool rack beside the hub workbench shows every tool you still own, inlays included. The model exists (`assets/models/props/workshop/tool_rack`). Your profile shows the rack the way it shows trophies (D-103).
- **A full rack** means owning every tier of one kind at the same time: Stone to Stellarite pickaxes, say, or every bow from Hare to Eclipse Dragon. Each of the five gives a cosmetic and a title, the same reward as a trophy set (D-103). Which cosmetic and title is open, as it is for trophies.
- A full rack costs exactly the decided recipes, since no hilt was taken back. The take-apart saving becomes something you can spend on a goal, and players who don't care lose nothing.
- It also brings back the hilt demand and the merchant hilt sales that take apart cut (3.4, push-back).

#### Considered and dropped

The ideas for later in 3.1 to 3.3, and why stage 2 leaves them out:

| Idea | Why not |
|---|---|
| A sickle blade edge that raises the seed chance | The inlay and the Green Thumb Tonic already raise it, and E2's cap would eat a third boost. |
| Axe heads that matter for felling | Felling is one bar per tree, then a stump for 5 minutes (`resource_gathering.md` 5.2). The only levers are gather time (2.3) and drops (the inlay), and both are taken. |
| Legendary bows that take a trophy | The legendary bows already take about 21 days online (`resource_gathering.md` 8.3). A trophy at a 1 to 4% chance adds days, and it takes the trophy out of its cabinet set (D-103). |
| An arrow-head slot | Arrows aren't used up (D-070). A slot would be a second bow fitting with a speed or drop perk, and both are taken. |
| A bait or lure slot | Still blocked, as in the fishing report (idea 9): speed bait drifts the pace, and pearl bait copies the Angler's Tonic. |
| Wear and repair | Tools don't wear (2.6). Repairs would turn a finished tool into a chore. |

---

## 4. Passes

Each pass is design only, ends with a report (`docs/CLAUDE.md` section 6), and needs your yes before the next. Build work follows in section 5 once a pass is decided.

| Pass | Goal | Items | Needs | Done when |
|---|---|---|---|---|
| **T0** ✔ | This roadmap | Status, parts model, five trees, passes; then crafting mechanics, take apart, inlays and what needs to be made (2026-11-22); then stage 2 (3.6) | Your requests (2026-11-21, 2026-11-22) | This doc is in review |
| **T1** | Parts rules decided | Calls 1 to 4 in section 7; record D-numbers; write P1 to P8 into `crafting.md` (new doc, needs your yes) | You; J00BA for `crafting.md` | Each rule is Decided or dropped. **Done 2026-11-22:** P1 to P8 Decided (D-125 to D-128, D-145, D-146) and written into `crafting.md`; J00BA hasn't agreed yet |
| **T2** | Pickaxes, the pilot tree | Head ids and recipes, bindings, icon plan (no model changes, P8); the menu that unfolds (E1) | T1 | The 3.1 pickaxe column is Decided |
| **T3** | Axes and sickles | The same pattern; settle the Steel tier and the Stone sickle's reach between D-063 and section 2.1 | T2; both collaborators | 3.1 is Decided for all three tools |
| **T4** | Rods | Blanks, reels, line; settle the tree list; the reel and the bite window (E4) | T1; both collaborators | 3.2 is Decided |
| **T5** | Bows | Wraps, staves, strings; legendary bows; the string drawn in code (`TOOL-ANIMATIONS.md`) | T1, T4 (the stave wood) | 3.3 is Decided |
| **T6** | Re-hafting and salvage | Move a hilt or reel from an outgrown tool to the next one; break a tool down for some of its parts. Drafted in 3.4 and M7, M8; the tool rack in E5. | T2 to T5 | Decided or dropped. It lowers the decided totals, so it needs its own D-number. |
| **T7** | Gem inlays | An optional gem socket per tool for a small perk. Besides selling (D-074), gems have one use today: the Void and Cosmic hilts. Drafted in 3.5 and M9; pearls (E3) and the stacking cap (E2) in 3.6. | T6 | Perks and limits Decided. Gems come from play, so holders get no extra power (D-085). |
| **T8** | Demon and lunar pickaxes | Find out from J00BA what they are (skins, event rewards, another tier). No design until then. | J00BA | Their purpose is Decided |
| **T9** | Weapons | 77 models (11 tiers × sword, staff, spear, shield, mace, dagger, battle axe). Parts sketch: blade or head, hilt, guard or grip. | Combat designed (mobs don't fight yet; `world_mobs.md` isn't written) | Out of scope until then |

---

## 5. Build track

Milestones to move into `BUILD-ROADMAP.md` once T1 and T2 are decided. Only decided rules get built.

- **B1. Data.** Parts and fittings tables in `game_data.gd`, and `_add_tool` (`:351-364`) split into part recipes plus an assembly recipe.
- **B2. Stations in the live world.** The hub anvil and workbench do real work. The sawbench, tanning rack and drying rack exist only in the test scene.
- **B3. Crafting menu with part slots.** Part rows (M1), batches (M5) and the *Make missing parts* button (M4), so assembling stays one click for players who don't care about parts. The rows unfold one mechanic at a time (E1).
- **B4. Saving.** Parts in the saved inventory. The device save is a test and Supabase isn't connected yet (build milestone M6).
- **B5. Headless test.** For every tool, its parts add up to the decided cost plus its fitting; a traded part can't be assembled below its unlock level (M6).
- **B6. Take apart, re-haft and inlays** (after T6 and T7). A gem slot on each owned tool in the save, the ×1.25 rare-drop roll on the server (it judges every drop, `GODOT.md`), and the returned part on take apart. Then the ×2.5 cap on every rare-drop roll (E2), pearls in the socket (E3) and the rack with its five full-rack rewards (E5). The reel factor (E4) goes in with fishing, which isn't built in Godot yet.

**Built (PR #113, 2026-11-22):** B1; B3 with E1; B4 in the device save; B5 (`tests/test_tool_parts.tscn`); B6 except the tool rack and its rewards (E5) and the reel factor (E4). B2 only in part: a workbench in the test landscape (`demo_landscape.tscn`), while the hub's anvil and workbench are still placeholders. Rods take exactly their listed reel; "or a better one" and the free swap (D-135) wait for E4. The rare-drop rolls are still made in the game, not on the server.

## 6. What needs to be made

The models are not on this list (P8).

### 6.1 Items

57 new bag items, all Proposed.

| Kind | Count | Ids |
|---|---|---|
| Pickaxe heads | 9 | `bronze_pickaxe_head` … `stellarite_pickaxe_head` |
| Axe heads | 9 | `bronze_axe_head` … `stellarite_axe_head` |
| Sickle blades | 9 | `bronze_sickle_blade` … `stellarite_sickle_blade` |
| Rod blanks | 9 | `ash_rod_blank` … `voidwood_rod_blank` |
| Bow wraps | 15 | `fox_bow_wrap` … `eclipse_dragon_bow_wrap` |
| Fittings | 6 | `nettle_cord`, `hare_leather_strip`, `tin_reel`, `copper_reel`, `bronze_reel`, `bow_stave` |

### 6.2 Icons

57 icons at 48×48 (D-015). **Proposed:** 9 drawings, each recoloured per tier from an icon that already exists, the way the placeholder pickaxes were made (`02-resources.md`, pickaxe pictures).

| Drawing | Icons | Colours from |
|---|---|---|
| Pickaxe head | 9 | The pickaxe sprites in `sprites/source/pickaxes/` (Stone, Bronze and Iron are drawn; the rest are placeholders) |
| Axe head | 9 | `items/tool_<metal>_axe.png` |
| Sickle blade | 9 | `items/tool_<metal>_sickle.png` |
| Rod blank | 9 | `items/plank_<wood>.png` |
| Bow wrap | 15 | `items/leather_<animal>.png` (rolled leather with a strap) |
| Nettle Cord | 1 | `items/bundle_nettle.png` (green leaves tied with twine) |
| Hare Leather Strip | 1 | `items/leather_hare.png` (a tan roll) |
| Reel | 3 | `items/ingot_tin.png`, `items/ingot_copper.png`; Bronze from `items/tool_bronze_axe.png`, as there's no Bronze ingot |
| Bow Stave | 1 | `items/plank_ash.png` |

- Titanite and Dreadstone metal colours are in the `mithril` and `adamantite` files (`02-resources.md`, mining table).
- Some source icons carry a mark: the Void swirl, the Stellarite stars, and the marks on the Starwyrm, Voidstalker, Stormhorn Ram and Eclipse Dragon leathers. A flat recolour loses it, so 11 icons need a hand touch-up (the Void and Stellarite heads and blades, the Voidwood blank and those four wraps).
- **Inlaid tools** show the gem as a small pip in the corner of the tool's icon: the `gemstone_*` icon scaled down in the UI. No new drawings.

### 6.3 Stations in the world

- **Workbench and anvil:** in the hub as placeholders (`scenes/hub/workbench_placeholder.tscn`, `anvil_placeholder.tscn`). They need to work (B2).
- **Sawbench, tanning rack, drying rack:** the models exist (`assets/models/props/stations/`), but they're placed only in the test scene (`demo_landscape.tscn`). They need a place in the live world (B2).
- **Tool rack (E5):** the model exists (`assets/models/props/workshop/tool_rack`). It needs a place beside the hub workbench, holding the tools you own.

### 6.4 Code, animations and docs

- **Code:** B1 to B6 (section 5).
- **Animations:** crafting, assembly, take apart and inlay moments, plus the bow string. See `TOOL-ANIMATIONS.md`.
- **Docs:** once T1 is decided, the recipes move to `crafting.md` (planned in `game_direction.md` section 12), and each call gets its D-number.

## 7. Risks and calls

**Risks**

- **More steps.** A tool goes from one craft to up to four. B3's "craft missing parts" button keeps it to one click.
- **Inventory space costs coins** (D-077), and parts take slots. Parts stack, and a head is usually made just before it is assembled.
- **Linking skills harder.** Higher-tier fittings (say, Obsidian bindings from Wolf leather) would make a miner hunt to tier 4 first. That hurts steady progress (D-085) for players who like one skill. P3 avoids it.
- **Art scope** for two people. The recolour plan cuts the icons from 57 to 9 drawings plus 11 touch-ups, and there are no model edits (P8).
- **Traded parts and coins.** Parts can be bought, so coins could buy progress. M6 stops it: assembly still needs the level.
- **Two doc sets.** The tables follow `DECISIONS.md` and the build. If J00BA's ladder or tree list wins, the names and the Steel row change, not the parts model.

**Calls answered** (the user said yes to all twelve on 2026-11-22; J00BA has not agreed yet)

1. **Fittings add a small cost** on top of the decided recipes (section 2.5): yes, **D-125**.
2. **Parts as real items** (P4): yes, **D-126**.
3. **Assemble at the hub workbench** (P5): yes, **D-127**.
4. **Tier-1 fittings only** (P3): yes, **D-128**.
5. **Take apart and re-haft** (3.4, M7, M8): yes, **D-129**.
6. **Gem inlays** (3.5, M9) at ×1.25: yes, **D-130**.
7. **Make missing parts at the workbench** (M4), from processed materials only: yes, **D-131**.
8. **Parts sell for their raw items plus 25%, once** (M10): yes, **D-132**.
9. **One ×2.5 cap for every boost** (E2): yes, **D-133**.
10. **Pearls in the socket** (E3): yes, **D-134**.
11. **The reel sets the bite window** (E4): yes, **D-135**.
12. **The tool rack** (E5): yes, **D-136**.

Calls 1 to 4 unblock pass T1; calls 5 and 6 unblock T6, T7 and the build's B3.
