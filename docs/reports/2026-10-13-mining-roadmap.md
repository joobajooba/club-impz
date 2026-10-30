# Report: Completing the mining roadmap (2026-10-13)

## In short
Every mining rule that is decided is now built and playable. All ten ores are in the scene. A pickaxe mines its own ore and every ore below it. Ores sometimes drop their gem. A furnace and a blacksmith let you smelt ore into ingots and craft pickaxes. You answered the four questions that blocked this, and they are recorded as D-010 to D-013. Smelting and hilts run on **test values** until you decide them.

## What changed
| Area | Change |
|---|---|
| Docs | `02-resources.md` updated: gem chance column, the pickaxe rule, a "Smelting and hilts (test values)" section, and the inputs and outputs table. It stays **Draft**, because sections 1, 2 and 5–8 are still empty. `BUILD-ROADMAP.md`: M3, M4 and M5 moved to **In review**. `ROADMAP.md`, `design/CLAUDE.md` and `README.md` brought up to date. |
| Decisions | **D-010** tin gives tin ore. **D-011** a pickaxe also mines every lower-tier ore. **D-012** gem chance 10% (Tin) falling 1% per tier to 1% (Stellarite). **D-013** test values for the build: 2 ore make 1 ingot, the blacksmith supplies hilts. |
| Game | `main.js`, `index.html`: ten ore tiers driven by one data table, pickaxe gating, gems, pickup messages, name tags over veins, furnace and blacksmith menus, owned pickaxes (you start with Stone), and test tools in Settings. The floor grew from 10 m to 16 m to fit the new veins. |
| Art | Seven placeholder pickaxe sprites (`sprites/pickaxes/steel_` to `stellarite_pickaxe.png`), made by recolouring the iron sprite with each ingot's colours. Seven new skins in `models/pickaxe-skins.json`. Veins for Iron to Stellarite are the copper vein recoloured in code. |
| Folder | Added this report and the seven sprites. No files removed. |

## Evidence
- **GitHub:** `main` is at `7473aeb` (PR #15). PRs #8 to #15 were merged on 2026-10-12 (HUD, item art, copper vein, copper reward and energy, soil and inventory, GitHub Desktop rule, roadmap update). PR #10 was closed without merging. The latest backup tag is `backup/main-20261012-1939`. This work is draft **PR #16** on `staging/mining-roadmap`.
- **Claude:** this session read every design doc, the decision log, both roadmaps and the game code. It looked at every PNG in `sprites/items/` (contact sheet) before touching item work. It asked you the four blocking questions, then built and tested the game. The Claude in Chrome extension wasn't connected, so testing used headless Chrome driven over its DevTools protocol, at about 5 frames per second. These were checked in the running game:
  - Tin gives Tin ore and costs 5 energy.
  - The Stone pickaxe at Iron shows "Needs a Bronze pickaxe" and won't mine.
  - The furnace turns 21 tin ore into 10 ingots, leaving 1.
  - The blacksmith crafts Bronze for exactly 5 tin and 5 copper ingots and puts it in your hand.
  - Bronze mines Iron.
  - With the random roll forced, Coal gave its Ruby.
  - No errors in the console.
- **Folder structure:** `git diff --stat` covers `main.js`, `index.html`, `models/pickaxe-skins.json`, `README.md` and five files in `design/`, plus 8 new files (7 sprites, this report). The local, never-pushed Pass 1 work from 2026-10-11 was committed to a **local-only** branch, `backup/local-pass-1-wip`, before `main` was updated, so nothing was lost. It is not in this PR.

## Consistency check
- **The Titanite ingot has no use.** The D-006 craft table has the Titanite pickaxe taking 10 *Obsidian* ingots, as recorded (names as of D-020). No recipe uses Titanite ingots, so smelting Titanite ore leads nowhere. Built exactly as written.
- **Coal has no use.** It has no ingot and is in no recipe. Players can mine it, but it piles up.
- **The Stellarite pickaxe has no mining advantage.** The table names no ore for it. Under D-011 it mines the same ten ores as the Void pickaxe.
- **Gems have no sink** (nothing spends them yet). The same goes for every resource; 02 question 3 is still open.
- `02-resources.md` described the Stellarite ingot picture as "a blue chest with gold trim". The picture is a blue **bar** with yellow stars. Corrected in 02 and noted in its pass history.
- The overview (section 2) still says jump and emotes are "work in progress". They are built. This was already listed in the build roadmap's gaps.
- The local Pass 1 decisions (D-005 to D-043 on `backup/local-pass-1-wip`) still clash with `main`. For example, their "any pickaxe, just slower" rule differs from D-011. They are unchanged and listed under "To reconcile" in `ROADMAP.md`.

## Suggestions (not applied)
1. **Check the Titanite row.** If the Titanite pickaxe was meant to take 10 *Titanite* ingots, that one-word fix gives Titanite ingots a use. Today it matches the Obsidian row exactly.
2. **Give Coal a job.** The usual pattern is coal as furnace fuel: for example, smelting Steel, or every ingot above Iron, takes 1 coal. That would also give the Steel pickaxe its own material. It's your call, and it ties into the smelter recipe you're working on.
3. **Give the Stellarite pickaxe a purpose**, for example faster mining or a better gem chance. Or treat it as a prestige item and say so.
4. **Save the inventory in the browser as a test**, like energy, until accounts exist (M6). Today a reload wipes your ore and pickaxes, which makes real playtesting of the progression hard.
5. **Replace the placeholder art.** Drawn 3D veins for tiers 3–10, and drawn sprites for the Steel to Stellarite pickaxes.

## What's next
Review and test PR #16. Say **"commit to main"** when you're happy. Then the remaining mining work is design, not build: the smelter recipe, hilt sources, and what Coal, Titanite ingots and the Stellarite pickaxe are for.

## What I need from you
1. Review PR #16, and say "commit to main" if it's good.
2. Is the Titanite pickaxe recipe right (10 Obsidian ingots), or should it be 10 Titanite ingots?
3. When it's ready: the smelter recipe and how players get hilts, to replace the test values.
