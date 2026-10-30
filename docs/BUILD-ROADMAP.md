# IMPLINGZ: build roadmap

> Claude: read `docs/CLAUDE.md` before working from this file. Code changes still follow the root `CLAUDE.md`: a `staging/` branch and a draft PR for every change.

This file tracks the **playable game** in this repo: what is built, what is in review, and what comes next. The design docs are tracked in [ROADMAP.md](ROADMAP.md).

> **Engine change (D-037, 2026-10-20).** The game is now built in **Godot**. M0 to M5 below were built in the Three.js test and stay as the record of what was proved. The Three.js test itself was removed on 2026-10-22 (D-113); it is in the git history before that date. The Godot rebuild is planned as milestones G0 to G8 in [GODOT.md](GODOT.md#4-what-carries-over-from-the-threejs-test-proposed-order) (**Proposed**). M6 and M7 become G6 and G7, and their design is now in [ACCOUNTS-AND-DATA.md](ACCOUNTS-AND-DATA.md).

## Rules

- **Build only what is decided.** A step can use a rule only if it is in `DECISIONS.md`. If a step needs something that isn't decided, it is **Blocked**, and the blocking question goes to the design roadmap. Test values are fine, but label them as test values in the code and the PR, as the energy refill was.
- **The design wins over the prototype.** If the game and a design doc disagree, the doc is right, and the gap is listed under [Gaps](#gaps-between-the-game-and-the-design).
- **One milestone at a time.** Finish or park the current one before starting the next.
- Update this file in the same PR as the change it describes.

**Statuses:** `Done` (merged to `main`) · `In review` (open PR) · `Next` · `Blocked` (waiting on a decision) · `Later`.

The milestone order below is **Proposed**. You can reorder it.

---

## Milestones

| # | Milestone | Status | Waiting on |
|---|---|---|---|
| M0 | Walk scene | Done | n/a |
| M1 | First mining loop | Done | n/a |
| M2 | Inventory and energy | Done | n/a |
| M3 | All ten ores in the scene | Done | Drawn sprites for pickaxes 4–10 (veins 3–10 built in Godot, 2026-10-22) |
| M4 | Gems | Done | n/a |
| M5 | Smelting and pickaxe crafting | Done, on test values | Nothing: the real rules are decided (D-054 to D-060). Wood hilts stay a test until lumbering. |
| G2–G5 | Godot: mining, energy, inventory, furnace and blacksmith | Done | PR #36, merged 2026-10-22. Built on the decided rules (D-054 to D-060), not the D-013 test values. See GODOT.md section 4. |
| Gathering | Godot: foraging, hunting (taming, stable, tracking), lumbering, fishing | Done | PR #38, merged 2026-10-22. Decided rules (D-022 to D-035, D-061 to D-072, D-105 to D-112). |
| TEST systems | Godot: merchant, battles, treasure dig | Done, on TEST values | PR #38, merged 2026-10-22. Built from Proposed rules with TEST numbers at the user's request (2026-10-22). Not decisions. |
| Wild nodes | Godot: ore veins and plants spread across the open world | In review, TEST layout | Asked for on 2026-10-30. Where wild nodes grow, how many, and which tiers grow where are not decided. |
| M6 | Saving and accounts (Godot G6) | In review, offline | Built offline-ready (2026-10-22): the game client, a TEST save on the device, and the `game` schema SQL (not applied). Waits on the Supabase project being connected and the server functions (gather, sell, craft). |
| M7 | Imps and the NFT (Godot G7) | Later | Upload the Imp `.glb` files somewhere the game can load them; the basic Imp's texture (ACCOUNTS-AND-DATA, questions 5–6) |
| Later | Skirmish, games, trade, shared chat | Later | Design docs 03–05 |

---

### M0: Walk scene: Done
- [x] Platform, character, walk cycle, third-person camera (drag to look, scroll to zoom)
- [x] Ore rocks with collision (PR #4)
- [x] Jump, and an emote panel with six emotes (PR #5)

### M1: First mining loop: Done
- [x] Pickaxe model from Blender, with Stone, Bronze and Iron sprite skins (PR #7)
- [x] Mine a rock with F: three swings, then the rock breaks (PR #7)
- [x] Game HUD: coins and energy display, profile, global chat panel, settings, menus moved to the centre (PR #8)
- [x] 48×48 item art for all ores, ingots, gems and prestige icons (PR #9, D-005)
- [x] Copper ore vein placed in the scene (PR #11)
- [x] Copper vein gives 1 copper ore and costs 5 energy. Veins grow back after 10 seconds (PR #12, D-007)

### M2: Inventory and energy: Done
- [x] Inventory menu: a 6×8 grid. Pickaxes first (click one to hold it), then mined items with counts. The top-left slots show only the held tool. (PR #13, D-008)
- [x] Every mine costs 5 energy. Energy resets to 100 at 00:00 and 12:00, with no slow refill. Saved in the browser. (PR #13, D-008, D-009)
- [x] Soil floor texture, square profile picture, chat width lined up with the HUD (PR #13)
- **Decided since (D-057):** the reset is at 00:00 and 12:00 UTC for every player. The build still uses each player's own clock (see Gaps).

### M3: All ten ores in the scene: Done
Decided: the ten tiers and the ore each gives (D-005, D-010), and which pickaxe mines which ore (D-006, D-011).
- [x] Tin gives 1 tin ore, the same as copper (D-010).
- [x] A vein for each of tiers 3–10 (Iron to Stellarite), with a name tag that shows as you walk up. **Test art:** each is the copper vein, with its rock and crystals recoloured from the ore's picture. Drawn models for each tier can replace them later.
- [x] The floor is now 16 m across (was 10 m) to fit them. Low tiers sit near the start, high tiers around the edge. Copper has a second vein. **Test layout.**
- [x] A pickaxe mines its named ore and every ore below (D-011). The prompt says which pickaxe you need, for example "Needs a Bronze pickaxe".
- [x] Skins for all ten pickaxes. Steel to Stellarite are **placeholders**: their sprites are the iron sprite recoloured with each ingot's colours.
- [x] Every pickup shows a short "+1 Iron ore" line.

### M4: Gems: Done
- [x] Mining an ore sometimes also gives its gem: 10% for Tin, down to 1% for Stellarite (D-012). Gem pickups are highlighted.

### M5: Smelting and pickaxe crafting: Done, on test values
Decided: what each crafted pickaxe costs in ingots (D-006). Test values until you decide the rest (D-013).
- [x] Furnace in the scene: F opens it. **Test recipe:** 2 ore make 1 ingot. Coal can't be smelted.
- [x] Blacksmith's anvil in the scene: F opens it. Crafts each pickaxe for the D-006 ingots exactly. Shows what you have and what you need. **Test:** the blacksmith supplies the hilt.
- [x] Players start with only the Stone pickaxe. Crafting adds a pickaxe and puts it in your hand. Q cycles the pickaxes you own.
- [x] **Test tools** in Settings, so reviewers can try every tier quickly: refill energy, +20 of every ore, unlock all pickaxes. Remove before launch.
- [ ] Replace the test values with the decided rules: ore per ingot by tier (D-054), Coal as fuel (D-055), Void and Cosmic hilts from ingots and a gem (D-058), double gem chance with the Stellarite pickaxe (D-059), Titanite ingots for the Titanite pickaxe (D-060). Wood hilts stay free as a test until lumbering exists.

### Mining: what's left after M5
Everything decided for mining up to D-013 is built. What's left:
- Building the rules decided on 2026-10-21 (D-054 to D-060) in place of the test values.
- Drawn 3D veins for tiers 3–10, and drawn sprites for the Steel to Stellarite pickaxes.
- How lumbering gives Ash Wood and Oak Wood hilts (D-058). Lumbering isn't designed yet.
- Resetting energy at 00:00 and 12:00 UTC (D-057), checked by the server rather than the player's clock.
- Saving the inventory between visits (M6).

### M6: Saving and accounts: In review, offline
- [x] Keep the inventory between visits: items, tools, coins, rows and the stable are saved on this device by the `Save` autoload (**TEST**: the player can edit the file; the server keeps the real copy once connected).
- [x] `Api` autoload: Supabase sign-up, log-in, session refresh and server function calls over HTTPS. Offline while `game/config/supabase.cfg` is empty. Tested against a local mock of Supabase.
- [x] Account section in the Profile menu (email and password, D-041).
- [x] `supabase/migrations/…_game_schema.sql`: the section 8 tables with read-own-rows RLS, a player row made at sign-up, `load_state()` and `username_free()`. **Not applied.**
- [ ] Connect the Supabase project (expose the `game` schema, put the URL and anon key in the config).
- [ ] Server functions for every write: gather (drops and mint tokens rolled on the server), sell, craft, refill, the energy reset. Then the game stops trusting its own save.
- [ ] Coins on the HUD: today the counter is fixed at 0, and nothing earns or spends coins.
- **Decided since (D-041 to D-043):** player data lives in the shared Supabase database, with email accounts and a linked wallet. Saving is done by server functions (ACCOUNTS-AND-DATA, sections 7–8).
- **No longer blocked on design.** The current tables are recorded in ACCOUNTS-AND-DATA, section 3. The claim is saved by Supabase and staking is finished (D-050). It waits for the Godot rebuild.

### M7: Imps and the NFT: Blocked
- [ ] Use the player's Imp as their character, and anything else the NFT does in the game.
- **Decided since (D-038):** holders play as their Imp. The model is loaded at runtime (ACCOUNTS-AND-DATA, section 4).
- **Decided since (D-048):** Robinhood Chain now, ApeChain later. The ownership check reads both during the move.
- **Decided since (D-049, D-050):** non-holders play as a basic Imp. The Robinhood Chain contract is known.
- **Since:** Imp models are referenced in the metadata (MML) and kept locally as `.glb`. The basic Imp needs only its texture.
- **Waiting on:** uploading the `.glb` files to Supabase Storage (D-051) and the basic Imp's texture. Not a design blocker any more.

### Later
- Skirmish, games and trade: drafted in 03–05 on 2026-10-21. Their smallest first versions are the starting points: wild battles (05), the daily treasure dig (D-096) and the market board (04). Everything new is built in Godot (D-087).
- Shared chat: the chat panel works only on your own screen. There is no server, so other players don't see messages.
- Other gathering skills. Foraging is decided enough to build picking, drying and sickles (D-022 to D-027, D-061 to D-064). Potions and Impling food are not. Hunting is decided enough to build hunts, tanning, bows, taming and tracking (D-028 to D-035, D-067 to D-072). Lumbering and fishing too (D-105 to D-112).

---

## Gaps between the game and the design

These are known differences. They don't need a fix until their milestone comes up.

| Game today | Design | Milestone |
|---|---|---|
| Furnace: 2 ore make 1 ingot, with no Coal. The blacksmith supplies every hilt. The Titanite pickaxe takes Obsidian ingots. Gem chances are never doubled. | 2 to 5 ore per ingot, and Coal from Gold up (D-054, D-055). Void and Cosmic hilts from ingots and a gem (D-058). Titanite ingots (D-060). The Stellarite pickaxe doubles gem chances (D-059). Wood hilts stay a test until lumbering. | M5 |
| Energy resets at 00:00 and 12:00 on each player's own clock | 00:00 and 12:00 UTC for every player (D-057) | M2 |
| Items, tools, coins and the stable are saved on the device (TEST), not on the server | The server keeps them and decides every change (ACCOUNTS-AND-DATA, section 9) | M6 |
| Overview section 2 says jump and emotes are "work in progress" | They are built (PR #5) | Design Pass 1 |

---

## Log

| Date | Change |
|---|---|
| 2026-10-12 | Build roadmap created from `main` at `da2a51a` and open PR #13. |
| 2026-10-12 | PR #13 merged: M2 marked Done. Energy gap rows removed. |
| 2026-10-13 | PR #16: M3, M4 and M5 built from D-010 to D-013 and moved to In review. Mining's remaining open items listed. |
| 2026-10-13 | PR #16 merged: M3, M4 and M5 marked Done (M5 still on the D-013 test values). |
| 2026-10-20 | Engine moves to Godot (D-037). Godot milestones G0–G8 proposed in GODOT.md. M6 and M7 now wait on specific questions in ACCOUNTS-AND-DATA instead of the overview. Later: browser game (D-046), so the Godot project must switch to the Compatibility renderer; chain recorded (D-048). |
| 2026-10-21 | Mining rules decided (D-054 to D-060): M5's test values can now be replaced, except wood hilts. Gaps updated. |
| 2026-10-21 | Design session: skirmish, games, trade, lumbering and fishing decided. New rules are built in Godot, not the Three.js test (D-087). |
| 2026-10-22 | Godot G2–G5 built in `game/`: the mining loop, energy (UTC reset, D-057), inventory, and the furnace and blacksmith on the decided rules. In review. |
| 2026-10-22 | Three.js web test removed (D-113). The game is only the Godot project in `game/`. |
| 2026-10-22 | Foraging, hunting, lumbering and fishing built in Godot on the decided rules; wood hilts now from planks (D-107). The user asked for playable TEST versions of the merchant, battles and treasure dig too; their rules are Proposed and their numbers TEST. In review. |
| 2026-10-22 | PRs #36 (G2–G5), #37 (remove Three.js) and #38 (gathering and TEST systems) merged to `main` (backup tag `backup/main-20261022-1152`). G2–G5, Gathering and TEST systems marked Done. |
| 2026-10-22 | Renderer switched to Compatibility (D-046). Sun 1.2 → 0.5 and exposure 0.8 so the scene doesn't clip to white. Water shader remaps depth for Compatibility. |
| 2026-10-22 | First web export (no threads): it runs in Chrome on WebGL 2. 138 MB (about 65 MB gzipped), mostly 2048 px textures. Shrinking it is Proposed in GODOT.md section 3. |
| 2026-10-22 | Poses retuned from side and back captures. The pickaxe and axe now rise beside the head on the right (overhead, the big head hid them). The bow stays upright when raised and is held out to the left. |
| 2026-10-22 | Art: veins for tiers 3–10 built in code in the Stylized Ore look, each tier with its own shape (`gathering/vein_art.gd`). 48×48 icons for all sickles, axes, bows and rods and the four hilts (`sprites/build_tool_icons.py`). Plants, trees, animals and the 3D tool models are still TEST art. |
| 2026-10-22 | G6 built offline-ready: `Api` (Supabase Auth and server function calls), a TEST device save, the Profile menu's account section, and the `game` schema SQL (not applied). Typing in a text box no longer moves the Imp. |
| 2026-10-30 | Wild nodes (**TEST layout**): about 150 ore veins in outcrops of 2–4 and 350 plants in patches of 3–6 across the open world, outside the gathering sites. The same world on every load (seeded from the world seed). Tiers rise with distance from the middle: tiers 1–2 near the start, every tier by the map edge, and each tier up rarer. Ores stay out of the flat plains; ferns, leafy plants and mushrooms grow only in the woods. Each vein is one of four shapes of its ore, and every node has its own size and turn. Gathering, energy and respawn are the decided rules. |
