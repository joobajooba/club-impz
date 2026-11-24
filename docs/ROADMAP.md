# IMPLINGZ: design roadmap

> Claude: read `docs/CLAUDE.md` before working from this file.
>
> This file tracks the **design docs**. What has been built in the game, and what to build next, is in [BUILD-ROADMAP.md](BUILD-ROADMAP.md).

## How this works

The design is built in **passes** (sprints). Each pass has a goal and a short list of items. At the end of every pass there is:

1. **A report** in `reports/`: what was done and what needs your decision.
2. **A review by you**: you read the docs and the report, answer the open questions, and either approve them or ask for changes.
3. **The next pass**, which picks up your feedback.

Passes keep going until **you** mark every doc `Signed off`. Nothing is finished just because a pass ended.

**Statuses:** `Not started` → `Draft` → `In review` → `Signed off` (only you can set `Signed off`).

Decisions can also arrive between passes, as **user additions** (for example a table you hand over). They go straight into `DECISIONS.md` and the doc they belong to, and are logged in the pass log below.

---

## All documents, by importance

Every Markdown file in the repo, most important first. The order is **Proposed**. You can change it. When a `.md` file is added or removed, update this list in the same PR.

| # | Document | What it is | Status |
|---|---|---|---|
| 1 | [DECISIONS.md](DECISIONS.md) | Every decision you have made. The source of truth: anything else that disagrees with it is wrong. | Living log |
| 1a | [README.md](README.md) | Index of every design doc in this folder. | Living |
| 2 | [00-overview.md](00-overview.md) | The game's intent, core loop and the role of the NFT. Every other doc must agree with it. | In review |
| 3 | [ROADMAP.md](ROADMAP.md) (this file) | The design passes and the status of every design doc. | Living |
| 4 | [BUILD-ROADMAP.md](BUILD-ROADMAP.md) | The playable game: what is built, what is in review, and the next milestones. | Living |
| 5 | [02-resources.md](02-resources.md) | Resources and economy: ore tiers, pickaxes, energy, item pictures. The most filled-in design doc. | Draft |
| 5a | [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md) | Accounts, wallet linking, IMP coins, mint tokens, and the Supabase database shared with impz.club. | Draft |
| 5b | [GODOT.md](GODOT.md) | Building the game in Godot: what carries over from the Three.js test, project layout, platform, milestones G0–G8. | Draft |
| 6 | [ART-DIRECTION.md](ART-DIRECTION.md) | The art style: cartoon stylised 3D for the world, 2D pixel art for menus and inventory, the 32 reference listings, and a checklist for every 3D asset. | Draft |
| 6a | [MODELS-BLOCKBENCH.md](MODELS-BLOCKBENCH.md) | Blockbench voxel models for tools, weapons, creatures and items: quality rules, `.glb` export into Godot, checklist. | Draft |
| 6b | [BLOCKBENCH-STUDY.md](BLOCKBENCH-STUDY.md) | Research: the 26 mcmodels.net reference listings (D-052), how pros build, texture, animate and optimise Blockbench models, and how that maps onto our tools and creatures. | Draft |
| 7 | [01-activities.md](01-activities.md) | What players do in the world, and what each activity produces. | Draft |
| 8 | [05-skirmish.md](05-skirmish.md) | The Pokémon-style battle system, fought by tamed animals. | Draft |
| 9 | [03-games.md](03-games.md) | Minigames and their rewards. | Draft |
| 10 | [04-trade.md](04-trade.md) | How value moves between players. | Draft |
| 11 | [../CLAUDE.md](../CLAUDE.md) | Repo rules for Claude: staging branches, draft PRs, "commit to main", backups and rollback. | Rules |
| 12 | [CLAUDE.md](CLAUDE.md) | Design rules for Claude: don't deviate, quality first, statuses, how to run a pass, reports. | Rules |
| 13 | [../README.md](../README.md) | How to run the game, and its controls. | Reference |
| 14 | [reports/2026-10-13-mining-roadmap.md](reports/2026-10-13-mining-roadmap.md) | Report: the mining build roadmap completed (M3–M5) and D-010 to D-013. | Done |
| 15 | [reports/2026-10-11-pass-0.md](reports/2026-10-11-pass-0.md) | Report for Pass 0 (setup). | Done |
| 16 | [reports/_TEMPLATE.md](reports/_TEMPLATE.md) | The template every report follows. | Template |
| 17 | [reports/2026-10-20-godot-accounts-models.md](reports/2026-10-20-godot-accounts-models.md) | Report: move to Godot, accounts and database, Blockbench models (D-036 to D-050). | Done |
| 18 | [reports/2026-10-21-design-session.md](reports/2026-10-21-design-session.md) | Report: the 2026-10-21 session: mining, foraging, hunting, economy, overview, skirmish, games, trade, lumbering, fishing (D-054 to D-112). | Done |
| 19 | [reports/2026-10-22-proposals.md](reports/2026-10-22-proposals.md) | Report: proposals for the open decisions (prices, potions, farming, the dig, moves). | Done |
| 20 | [reports/2026-10-30-pass-5.md](reports/2026-10-30-pass-5.md) | Report: Pass 5 review after the move to club-impz; clashes with J00BA's docs. | Done |
| 21 | [implingz_collection.md](implingz_collection.md) | The Imp traits, for modelling them. | Draft |
| 22 | [game_direction.md](game_direction.md) | J00BA's top-level direction for Club Impz (v3). Treats itself as the source of truth for J00BA's docs. | J00BA's (not tracked in this roadmap's passes) |
| 23 | [game_worlds.md](game_worlds.md) | J00BA's hub world and resource world, biomes and art style. | J00BA's |
| 24 | [resource_gathering.md](resource_gathering.md) | J00BA's gathering rules, tools, tiers, XP. | J00BA's |
| 25 | [blockbench_detailed_prompts.md](blockbench_detailed_prompts.md) | J00BA's guide for turning a short request into a Blockbench build. | J00BA's |
| 26 | [xp_system.md](xp_system.md) | XP sources, skill levels, the player level curve, prestige, how XP is shown and kept safe. Written in J00BA's doc style, on top of `game_direction.md`. | Draft |
| 27 | [reports/2026-11-21-fishing-status.md](reports/2026-11-21-fishing-status.md) | Report: what is built and designed for fishing, and where the docs disagree. | Done |
| 28 | [reports/2026-11-21-fishing-expansion.md](reports/2026-11-21-fishing-expansion.md) | Report: nine ideas for expanding fishing, with a fishing XP table at J00BA's pace. All Proposed. | Done |
| 29 | [reports/2026-11-21-fishing-skill.md](reports/2026-11-21-fishing-skill.md) | Report: fishing written into `resource_gathering.md` section 7 as Proposed (expansion ideas 1 to 3), following the newer doc set topic by topic. | Done |
| 30 | [reports/2026-11-21-gathering-status.md](reports/2026-11-21-gathering-status.md) | Report: what is built and designed for mining, lumbering, foraging and hunting, and 12 places where the doc sets disagree. | Done |
| 31 | [reports/2026-11-21-gathering-expansion.md](reports/2026-11-21-gathering-expansion.md) | Report: every gathering skill evolved like fishing. Foraging and hunting written into `resource_gathering.md` as Proposed, plus sap, felling, wood hilts and ore events, with pace figures for each skill. | Done |
| 32 | [TOOL-CRAFTING-ROADMAP.md](TOOL-CRAFTING-ROADMAP.md) | Tools crafted from parts (working part, handle, fitting) for pickaxes, axes, sickles, rods and bows, with passes T0 to T9 and a build track. Crafting mechanics M1 to M11, take apart, gem inlays and what needs to be made (2026-11-22). Stage 2 of the mechanics, E1 to E5 (2026-11-22). Models stay as they are. All Proposed. | Draft |
| 33 | [reports/2026-11-21-tool-crafting-roadmap.md](reports/2026-11-21-tool-crafting-roadmap.md) | Report: the tool crafting roadmap, its consistency check and the four calls it needs. | Done |
| 34 | [TOOL-ANIMATIONS.md](TOOL-ANIMATIONS.md) | How the Imp uses each tool (what is built and its gaps), use animations taken further (bow, fishing loop, drop pops), crafting moments at the stations and in the menu, with passes A0 to A6. All Proposed. | Draft |
| 35 | [reports/2026-11-22-tool-mechanics-and-animations.md](reports/2026-11-22-tool-mechanics-and-animations.md) | Report: the crafting mechanics added to the tool crafting roadmap, the tool animations write-up, and the eight calls they need. | Done |
| 36 | [reports/2026-11-22-tool-mechanics-stage-2.md](reports/2026-11-22-tool-mechanics-stage-2.md) | Report: stage 2 of the tool crafting mechanics (E1 to E5), the ideas for later settled, and calls 9 to 12. | Done |
| 37 | [XP-INTERPRETATION.md](XP-INTERPRETATION.md) | Claude's own take on XP: keeps D-121 to D-123 and the curve, shows the last tool unlocks at 0.4% of the XP to 100, and proposes rested XP, yield nodes for levels 50 to 100, a first-craft tier reading and XP by item id. X1 to X3 Decided (D-141 to D-143) and folded into `xp_system.md` (D-144); X4 and X5 Proposed. | Draft |
| 38 | [reports/2026-11-22-xp-interpretation.md](reports/2026-11-22-xp-interpretation.md) | Report: the tool parts build (PR #113) and the XP interpretation, with four calls. | Done |
| 39 | [crafting.md](crafting.md) | Recipes, stations and tool progression (`game_direction.md` section 12). Version 1 holds the tool rules from pass T1: P1 to P8, parts and recipes per tree, fittings, stations, the workbench. Weapons and armour not covered yet. | Draft |
| 40 | [reports/2026-11-22-xp-calls-and-pass-t1.md](reports/2026-11-22-xp-calls-and-pass-t1.md) | Report: XP calls answered (D-141 to D-144) and pass T1 (D-145, D-146, `crafting.md`). | Done |

**Why this order:** decisions and the overview come first because every other doc must agree with them. The two roadmaps come next because they say what to work on. Then come the system docs, in the order they will be worked on. The art direction sits after Resources because every 3D asset already being built (veins, furnace, anvil, cave) must follow it. Resources is first because every other system makes or spends resources. The two `CLAUDE.md` files and the README tell people and Claude how to work in the repo, but they don't define the game. Reports are history.

**Local only, not on GitHub:** `docs/gathering/01-mining.md` and `reports/2026-10-11-pass-1.md`. They exist only in one collaborator's folder and aren't in this list until they are reconciled and merged (see [To reconcile](#to-reconcile-not-on-github)).

---

## Doc status

Each design system is a main row. Its sub categories (↳ rows) are the topics inside it, taken only from what is on `main`. A system with nothing written yet has no sub rows. New sub rows are added when a topic is decided or a section is written.

For a main row, **Status** is the doc's status. For a sub row, it is the topic's label: **Decided** (with the D-number), **Proposed** (Claude's suggestion, waiting for you), **Open question**, or **Not decided** (you've said it's still to come).

| # | Doc / topic | Status | Still open | Depends on | Last pass |
|---|---|---|---|---|---|
| **00** | **[Overview](00-overview.md)** | **In review** | The pitch (Proposed) and scope guardrails (Proposed) | n/a | User additions, 2026-10-21 |
| 00.1 | ↳ One-line pitch | Proposed | Your call on the new version | | |
| 00.2 | ↳ Design pillars | Decided (D-085) | n/a | | |
| 00.3 | ↳ Core loop | Decided (D-086) | n/a | | |
| 00.4 | ↳ Systems map | Decided (D-002) for the five systems | Each system's job is Proposed | | |
| 00.5 | ↳ Target player and platform | Decided (D-046, D-082 to D-084) | n/a | | |
| 00.6 | ↳ Scope guardrails | Proposed | Your call | | |
| **01** | **[Activities](01-activities.md)** | **Draft** | Farming; sections 4–8 | 00, 02 | User additions, 2026-10-21 |
| 01.0 | ↳ Activity list | Decided (D-036); lumbering (D-105 to D-108) and fishing (D-109 to D-112) designed | Farming is Proposed only | | |
| 01.1 | ↳ Mining | Decided in 02 (D-005 to D-013, D-054 to D-060), and built on the D-013 test values | Not written up in 01 yet | | |
| 01.2 | ↳ Mint tokens from gathering | Decided (D-040, D-045: Imp holders only) | The chance | | |
| **02** | **[Resources & economy](02-resources.md)** | **Draft** | Sections 1, 2 and 5–8 are empty | 00 | 0, then user additions (D-005 to D-013, D-054 to D-060) |
| 02.1 | ↳ Ore tiers and item pictures | Decided (D-005) | n/a: every vein but Copper is drawn in code in the build. J00BA's docs order the tiers differently (Pass 5 report) | | |
| 02.2 | ↳ Pickaxes: which mines which ore, and craft costs | Decided (D-006, D-011, D-059, D-060) | Whether the Stellarite pickaxe mines all ten ores is Proposed | | |
| 02.3 | ↳ Mining rewards and vein respawn | Decided (D-007, D-010) | n/a | | |
| 02.4 | ↳ Energy | Decided (D-008, D-009, D-057: 00:00 and 12:00 UTC) | n/a | | |
| 02.5 | ↳ Inventory | Decided (D-008) | Saving it between visits (build M6) | | |
| 02.6 | ↳ Gems | Decided (D-005, D-012) | n/a | | |
| 02.7 | ↳ Smelting: ore into ingots | Decided (D-054 to D-056): ore per ingot by tier, Coal as fuel, no energy | n/a: built in Godot | | |
| 02.8 | ↳ Hilts | Decided (D-058): wood hilts from lumbering, Void and Cosmic hilts from ingots and a gem | n/a: from 5 planks (D-107), built | | |
| 02.9 | ↳ Selling, and other crafting and blacksmithing | Selling decided (D-073, D-074); other crafting not decided | The base sell price; other crafting and blacksmithing | | |
| 02.10 | ↳ Prestige icons | Not decided | What they are for | | |
| 02.11 | ↳ Sources, sinks, currencies, tradeability | Open question | The six questions at the end of 02 | | |
| 02.12 | ↳ IMP coins and mint tokens | Decided (D-039, D-040, D-042, D-073 to D-078) | Every price; which cosmetics exist; trading between players (04) | | |
| 02.13 | ↳ Foraging: plants, drying, sickles, seeds | Decided (D-022 to D-027, D-061 to D-066) | Potions in detail, Impling food (waits on skirmish), farming | | |
| 02.14 | ↳ Hunting: animals, leather, bows, taming, tracking | Decided (D-028 to D-035, D-067 to D-072); bow names Proposed | What trophies and top-tier leather are for | | |
| **AD** | **[Accounts and data](ACCOUNTS-AND-DATA.md)** | **Draft** | Its nine open questions | 00, 02 | User addition, 2026-10-20 |
| AD.1 | ↳ Email accounts, linked wallet | Decided (D-041) | The link method is Proposed | | |
| AD.2 | ↳ One shared Supabase database | Decided (D-043) | Website table permissions fixed (2026-10-20) | | |
| AD.3 | ↳ Staked coins carried over | Decided (D-042); staking finished (D-050) | Move on wallet link is Proposed | | |
| AD.4 | ↳ Play as your Imp | Decided (D-038); Robinhood Chain now, ApeChain later (D-048); contract recorded (D-050) | ApeChain contract; models hosted in Supabase Storage (D-051) | | |
| AD.5 | ↳ Non-holders | Decided (D-049): a basic Imp model | Its texture is still to make | | |
| **GD** | **[Godot](GODOT.md)** | **Draft** | Phones, water shader licence, Godot version | 00 | User addition, 2026-10-21 |
| GD.1 | ↳ Platform: the browser | Decided (D-046) | n/a: on the Compatibility renderer, first web export works | | |
| **BB** | **[Blockbench models](MODELS-BLOCKBENCH.md)** | **Draft** | Imp height, stations | ART | User addition, 2026-10-22 |
| BB.1 | ↳ Stylised world, slight-voxel items and enemies | Decided (D-047) | n/a | | |
| BB.2 | ↳ Reference listings | Decided (D-052) | Study in BLOCKBENCH-STUDY is Proposed | | |
| BB.3 | ↳ Texel density: 2 pixels per unit | Decided (D-053) | n/a | | |
| BB.4 | ↳ Every tier of a tool has its own shape and detail | Decided (D-114, D-115) | All 56 tools made | | |
| BB.5 | ↳ Into Godot as `.glb`, not FBX | Decided (D-116) | Creature animations not tested yet | | |
| **03** | **[Games](03-games.md)** | **Draft** | How each minigame plays and its prizes (Proposed) | 00, 02 | User additions, 2026-10-21 |
| 03.1 | ↳ Four minigames, dig first | Decided (D-096) | n/a | | |
| 03.2 | ↳ Prizes, caps and fees | Decided (D-097, D-098) | Amounts | | |
| **04** | **[Trade system](04-trade.md)** | **Draft** | Listing rules, price floor, the progress check (Proposed) | 00, 02 | User additions, 2026-10-21 |
| 04.1 | ↳ Market and direct trades, 5% fee | Decided (D-081, D-099, D-100) | n/a | | |
| 04.2 | ↳ Who can trade, animals not tradeable | Decided (D-101, D-102) | What "some progress" is | | |
| **05** | **[Skirmish system](05-skirmish.md)** | **Draft** | Animal types, type chart, stats, moves (Proposed) | 00, 02 | User additions, 2026-10-21 |
| 05.1 | ↳ Tamed animals battle, teams of 3, turn-based | Decided (D-080, D-088) | n/a | | |
| 05.2 | ↳ Types, moves, levels | Decided (D-089, D-091) | The chart and moves are Proposed | | |
| 05.3 | ↳ PvE first, rewards, losing, stable | Decided (D-090, D-092 to D-095) | n/a | | |

**Why this order:** the overview decides what the NFT is and what the core loop is. Every system depends on that. Resources come next because every other system makes or spends them. If resources are designed last, the economy won't balance. Trade comes late because it depends on decisions about what is on-chain.

**Where things actually stand:** the mining part of Resources (02) has moved ahead of the overview through user additions. The overview's questions were answered on 2026-10-21 (D-080 to D-086), so 02 can move to `In review` once its empty sections (1, 2, 5–8) are written. Since 2026-10-30, J00BA's docs in this repo set different rules for some of the same things (Pass 5 report): that has to be settled first.

---

## Pass plan

The pass plan can change. Only the user changes it.

### Pass 0: Setup ✔
- [x] Folder structure, rules for Claude, doc templates
- [x] First draft of the overview, with open questions marked
- [x] Pass 0 report

### Pass 1: Foundations (overview)
**Goal:** settle the decisions every other doc depends on.
- [x] Answer the overview's open questions (NFT role, on-chain scope, earning, audience, platform)
- [x] Record the answers in `DECISIONS.md` (D-080 to D-086)
- [x] Lock the core loop and the systems map
- [x] Overview → `In review`

### Pass 2: Economy spine (resources, then activities)
**Goal:** define what exists in the economy and how players get it.
- [ ] Resources: list, sources, sinks, rarity tiers, which are tradeable
  - [x] Ten ore tiers, their ore, ingot and gem pictures (D-005)
  - [x] Which pickaxe mines which ore, and pickaxe craft costs (D-006)
  - [x] First playable reward: copper ore for 5 energy, 10-second vein respawn (D-007)
  - [x] Energy: 5 per mine for every ore, reset every 12 hours from midnight; 6×8 inventory (D-008, D-009)
  - [x] Tin gives tin ore (D-010)
  - [x] Gem chance per ore: 10% down to 1% by tier (D-012)
  - [x] A stronger pickaxe also mines every weaker ore (D-011)
  - [x] Energy reset: 00:00 and 12:00 UTC for every player (D-057)
  - [x] Smelter: ore per ingot by tier, Coal as fuel from Gold up, no energy cost (D-054 to D-056)
  - [x] Void and Cosmic hilts: crafted from ingots and a gem (D-058)
  - [x] Ash Wood and Oak Wood hilts: from 5 planks at the blacksmith (D-107)
  - [x] What the Stellarite pickaxe is for (double gem chance, D-059), and what Coal is for (furnace fuel, D-055)
  - [x] The Titanite pickaxe takes Titanite ingots (D-060)
  - [ ] Selling, and other crafting and blacksmithing
  - [ ] What the prestige icons are for
  - [ ] Sinks for every resource
- [ ] Activities: what players do and what each activity outputs
- [ ] Consistency check against the overview

### Pass 3: Play (skirmish and games)
**Goal:** define the two systems players spend most of their time in.
- [x] Skirmish: battle rules, stats, types, progression, PvE/PvP (drafted; chart and stats Proposed)
- [x] Games: minigame list, rewards, how they plug into the loop (drafted; details Proposed)
- [ ] Consistency check against resources

### Pass 4: Trade
**Goal:** define how value moves between players.
- [x] Trade: in-game vs marketplace, fees and sinks, anti-abuse (drafted; listing rules Proposed)
- [ ] Consistency check across all docs

### Pass 5+: Review passes
**Goal:** tighten, fix mismatches and get sign-off.
- [ ] Repeat until you mark every doc `Signed off`

### Build roadmap (started early, at your request on 2026-10-12)
The build roadmap was planned for after sign-off. You asked for it now, because the game is already being built alongside the design. It lives in [BUILD-ROADMAP.md](BUILD-ROADMAP.md). A build step can only use what is **Decided** here. Anything still open is marked as blocked there.

---

## To reconcile (not on GitHub)

One collaborator has local Pass 1 work that was never pushed. On 2026-10-13 it was saved on a **local-only** branch, `backup/local-pass-1-wip`, so it isn't lost. It was written against the old decision log, and it clashes with what is now on `main`:

- `docs/gathering/01-mining.md` (a mining design doc), `reports/2026-10-11-pass-1.md`, and edits to `00-overview.md`, `01-activities.md`, `DECISIONS.md` and this file.
- Its decisions are numbered D-005 to D-043, but `main` already uses D-005 to D-013.
- Some of them contradict `main`. For example, the local D-042 and D-043 say any pickaxe can mine any ore, but D-006 names one pickaxe per ore. The local D-023 uses cooldowns, but `main` uses energy.

`main` is the source of truth for now. Before any of that work is used, the two of you agree which rules win. Then the local decisions are renumbered after the last one on `main`, and any that change a decision on `main` are entered as **supersedes**.

---

## Current pass

**Pass 5: Review.** On 2026-10-21 every system was given its decided rules in one session (see the [report](reports/2026-10-21-design-session.md)). The overview is In review. 01–05 are Drafts with their remaining details Proposed. Next: you review the Proposed parts, and the base price is set from the staked balances.

On 2026-10-30 the work moved to the club-impz repo (D-117), next to J00BA's Club Impz docs. The [Pass 5 report](reports/2026-10-30-pass-5.md) brings stale lines up to date and lists where the two sets of docs disagree. **Blocking:** which set wins where they disagree.

---

## Pass log

| Pass | Dates | Goal | Outcome | Report |
|---|---|---|---|---|
| 0 | 2026-10-11 | Setup | Structure, rules and overview draft created | [report](reports/2026-10-11-pass-0.md) |
| User additions | 2026-10-12 | Mining resources | Ore tiers (D-005), pickaxes (D-006) and the first copper reward (D-007) recorded in 02. 02 moved to `Draft`. | No report |
| User additions | 2026-10-12 | Energy and inventory | Same energy cost for every ore, 12-hour reset from midnight, 6×8 inventory (D-008, D-009), via PR #13. | No report |
| Roadmap update | 2026-10-12 | Bring this file up to date | Doc status and Pass 2 progress updated to match `main`. Build roadmap started. Unpushed local work listed under "To reconcile". All 14 `.md` files listed by importance. Sub categories added under each design system in Doc status. | No report |
| User additions | 2026-10-13 | Complete the mining roadmap | Tin reward (D-010), stronger pickaxes mine weaker ores (D-011), gem chance (D-012), test smelting and hilt values (D-013). Build milestones M3–M5 built and in review (PR #16). | [report](reports/2026-10-13-mining-roadmap.md) |
| User additions | 2026-10-14 | Art direction | `ART-DIRECTION.md` created from your 32 reference listings, as `Draft`. Cartoon stylised 3D world (D-014). 2D pixel art for menus and inventory, 3D for anything in the world (D-015). The style rules are Proposed; six open questions at the end of the doc. | No report |
| User additions | 2026-10-15 | Art direction answers | Implingz are already done and left out (D-016). Veins can differ in colour (D-017). References are style only; assets are made by us (D-018). Veins should look like Stylized Ore, which you own a licence for (D-019). | No report |
| User additions | 2026-10-16 | Ore names | Mithril renamed Titanite, Adamantite renamed Dreadstone (D-020). | No report |
| User additions | 2026-10-16 | Repo layout | Design Markdown moved to `docs/` (D-021). Models, textures and sprites each have one folder. | No report |
| User additions | 2026-10-20 | Godot, accounts, Blockbench | Game type (D-036), Godot (D-037), Imp as character (D-038), crypto scope (D-039), mint tokens (D-040), email accounts and wallet (D-041), staked coins (D-042), shared Supabase (D-043), Blockbench voxel models (D-044). Three new docs: `ACCOUNTS-AND-DATA.md`, `GODOT.md`, `MODELS-BLOCKBENCH.md`. 01 moved to Draft. Later the same day: mint tokens for Imp holders only (D-045), browser game (D-046), stylised world with slight-voxel items and enemies (D-047), Robinhood Chain then ApeChain (D-048), and the current Supabase tables recorded. Then: basic Imp for non-holders (D-049), staking finished and the contract recorded (D-050). Imp models hosted in Supabase Storage (D-051). | [report](reports/2026-10-20-godot-accounts-models.md) |
| User additions | 2026-10-21 | Blockbench references | 26 mcmodels.net listings chosen as the Blockbench quality bar (D-052). `BLOCKBENCH-STUDY.md` created as `Draft`: what the references share, how they are built, textured, animated and optimised, and five open questions. Then: Blockbench texel density is 2 pixels per unit (D-053). | No report |
| User additions | 2026-10-21 | Finish mining | Ore per ingot by tier (D-054), Coal as furnace fuel (D-055), no energy for smelting or crafting (D-056), energy reset at 00:00 and 12:00 UTC (D-057), hilts (D-058), the Stellarite pickaxe doubles gem chances (D-059), the Titanite pickaxe takes Titanite ingots (D-060). Only wood hilts are still open for mining, and they wait on lumbering. | No report |
| User additions | 2026-10-21 | Foraging mechanics | One energy pool for all gathering, 5 per plant (D-061), plants per bundle by tier (D-062), metal sickles costing the same as pickaxes (D-063), 10-second regrowth (D-064), seeds go to farming (D-065), potions are short gathering boosts (D-066). Impling food waits on skirmish. | No report |
| User additions | 2026-10-21 | Hunting mechanics | 5 energy and 3 shots per animal, 10-second respawn (D-067), hides per leather (D-068), bows from the tier below's leather (D-069), arrows not used up (D-070), every animal tamed with its tier's bundle (D-071), a tamed animal raises trophy chances ×1.5 (D-072). Bow names Proposed. | No report |
| User additions | 2026-10-21 | Economy | Coins from selling to a merchant (D-073), sell prices by tier and kind (D-074), coins buy cosmetics, inventory rows, energy refills and wood hilts (D-075), three limits on refills (D-076), inventory rows double in price (D-077), mint token chance 0.1% and 1 token per mint (D-078). | No report |
| User additions | 2026-10-21 | Godot project in the repo | The Godot test project copied into `game/`, and the repo made private (D-079). The asset pack is the free CC0 Quaternius kit. | No report |
| User additions | 2026-10-21 | Everything left | Overview answered (D-080 to D-086), design only and build in Godot (D-087), skirmish (D-088 to D-095), games (D-096 to D-098), trade (D-099 to D-102), trophies and leather (D-103, D-104), lumbering (D-105 to D-108), fishing (D-109 to D-112). 03–05 drafted, overview In review. | [report](reports/2026-10-21-design-session.md) |
| User additions | 2026-10-22 | Blockbench tools | Every tier of a tool has its own shape and detail, e.g. a demon on the Dreadstone pickaxe (D-114), for every tool (D-115). All 56 tools made in Blockbench and put in the Imp's hand as `.glb`, not FBX (D-116). MODELS-BLOCKBENCH and GODOT updated to match. | No report |
| User addition | 2026-10-22 | Proposals for open decisions | Real prices as multiples of one base price (02), potions (02), farming details (01), the dig's board (03), 2 moves at level 1 (05). Impling food raised as an Open question. All **Proposed**: nothing decided. | [Report](reports/2026-10-22-proposals.md) |
| Review | 2026-10-30 | Pass 5, after the move to club-impz | The work moved to the club-impz repo (D-117). Stale lines about the Three.js test, test values, wood hilts and the renderer brought up to date in 00, 01, 02, ACCOUNTS-AND-DATA, ART-DIRECTION, GODOT, BUILD-ROADMAP and this file. Folder paths updated for the new layout. Two broken links in 01 fixed. J00BA's docs listed, and every clash with DECISIONS.md written up. Statuses unchanged. | [Report](reports/2026-10-30-pass-5.md) |
| User addition | 2026-11-21 | Fishing review and expansion | What fishing has (built only in the test scene, no XP) and eight mismatches between the doc sets. Nine expansion ideas: fish by water, a fishing XP table, shoal events, other catches, a reel, a fish log, a contest, meal buffs, bait. All **Proposed**: nothing decided, statuses unchanged. | [Status](reports/2026-11-21-fishing-status.md), [ideas](reports/2026-11-21-fishing-expansion.md) |
| User addition | 2026-11-21 | Fishing as a gathering skill | Expansion ideas 1 to 3 written into J00BA's `resource_gathering.md` section 7 (wood rods with unlock levels, the fish and pearl tables, fish by water, shoal events, pace of 82 days to level 100) and fish rows in `game_worlds.md` section 4.6. The newer doc set was followed topic by topic. All **Proposed**: no decisions, statuses unchanged. | [Report](reports/2026-11-21-fishing-skill.md) |
| User addition | 2026-11-21 | Gathering expanded like fishing | Mining, lumbering, foraging and hunting reviewed (built state, 12 mismatches). Written into J00BA's `resource_gathering.md`: ore events (4.3), sap, felling and a Pine Wood Hilt (5.1 to 5.3), foraging in full (section 6: sickles, plants and seeds, by biome, 75 days), hunting in full (section 8: bows, ten animals and trophies, six legendary hunt events, by biome, 78 days), a section 9 note and open question 4 (unlock levels). Plant and animal rows in `game_worlds.md` section 4.6. All **Proposed**: no decisions, statuses unchanged. | [Status](reports/2026-11-21-gathering-status.md), [ideas and write-up](reports/2026-11-21-gathering-expansion.md) |
| User addition | 2026-11-21 | Tool crafting roadmap | New `TOOL-CRAFTING-ROADMAP.md`: every tool assembled from a working part (paid with the decided recipe), a handle and a fitting (Nettle Cord, Hare Leather Strip, reels, bow staves, all from tier-1 resources). Part tables for the five tool trees, passes T0 to T9 (parts rules, one pass per tree, re-hafting, gem inlays, demon and lunar pickaxes, weapons), build and art tracks. All **Proposed**: no decisions, statuses unchanged. | [Report](reports/2026-11-21-tool-crafting-roadmap.md) |
| User addition | 2026-11-22 | Tool crafting mechanics and animations | `TOOL-CRAFTING-ROADMAP.md`: crafting mechanics M1 to M11 (part rows, instant crafts, make missing parts, unlocks that hold for traded parts, re-haft, part sell price, XP on assembly), take apart (3.4), gem inlays (3.5), and section 6 rewritten as what needs to be made (57 items, 9 icon drawings). Models stay as they are (P8 rewritten, at the user's direction). New `TOOL-ANIMATIONS.md`: what is built, rules A1 to A7, the bow and fishing loop, crafting moments, passes A0 to A6. All **Proposed**: no decisions, statuses unchanged. | [Report](reports/2026-11-22-tool-mechanics-and-animations.md) |
| User addition | 2026-11-22 | Tool crafting mechanics, stage 2 | `TOOL-CRAFTING-ROADMAP.md` section 3.6: mechanics that unfold one at a time (E1), one ×2.5 cap for every rare-drop boost (E2), pearls in the socket (E3), the reel setting the bite window (E4), and the tool rack as the choice against taking a tool apart (E5). The ideas for later in 3.1 to 3.3 are settled, six dropped with reasons. Calls 9 to 12 added. Animations left as they are, at the user's direction. All **Proposed**: no decisions, statuses unchanged. | [Report](reports/2026-11-22-tool-mechanics-stage-2.md) |
| User addition | 2026-11-22 | Tool calls answered | The user said yes to calls 1 to 12 in `TOOL-CRAFTING-ROADMAP.md` and A to D in `TOOL-ANIMATIONS.md`: **D-125 to D-140** (tools from three parts with tier-1 fittings, parts as items, workbench assembly and make missing parts, take apart and re-haft, ×1.25 gem and pearl inlays, part sell price, one ×2.5 boost cap, reel-set bite window, tool rack; hit-stop, station loops, hammer and saw props, swings seen by other players). Labels in both docs updated; the rest stays Proposed. Pass T1 is unblocked. J00BA has not agreed yet. Statuses unchanged. | [Decisions](DECISIONS.md) |
| User addition | 2026-11-22 | Tool parts built; XP interpretation | Tool parts built in Godot from D-125 to D-136 (PR #113, headless test passes; hub workbench later). New `XP-INTERPRETATION.md`: rested XP, yield nodes from level 50, first-craft tier reading, XP by item id. Four calls open. | [report](reports/2026-11-22-xp-interpretation.md) |
| Pass T1 (tool crafting) | 2026-11-22 | XP calls answered; tool parts rules decided | The user was fine with the four XP calls: **D-141** rested XP, **D-142** yield and drops from level 50, **D-143** first-craft tier, **D-144** `xp_system.md` stays the XP doc, with the answers folded in. Pass T1 done: **D-145** (P6) and **D-146** (P8), so P1 to P8 are all Decided, and the new `crafting.md` (Draft) holds them with the recipes, fittings, stations and workbench rules. J00BA has not agreed yet. | [Report](reports/2026-11-22-xp-calls-and-pass-t1.md) |
