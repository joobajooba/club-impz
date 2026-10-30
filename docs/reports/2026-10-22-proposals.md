# Report: proposals for the open decisions (2026-10-22)

## In short
The user asked for every decision still waiting on them to be written as a proposal, so they can approve or change each one in a single review. Prices, potions, farming, the treasure dig and starting moves are now **Proposed** in the docs. Nothing new is decided, and no D-numbers were added.

## What changed
| Area | Change |
|---|---|
| Docs | **02-resources** (Draft): prices as multiples of one base price; potions; Impling food raised as an Open question. **01-activities** (Draft): farming details. **03-games** (Draft): the dig's board. **05-skirmish** (Draft): 2 moves at level 1. Statuses unchanged. |
| Decisions | None. Everything added is Proposed or an Open question. |
| Folder | This report added. ROADMAP.md: report row and pass log row. |

## Evidence
- **GitHub:** PRs #36–#38 merged to `main` today (backup tag `backup/main-20261022-1152`). Open in the same session, as a stack of code PRs: #39 roadmap statuses, #40 texture paths, #41 Compatibility renderer, #42 first web export, #43 poses, #44 vein art and tool icons. This PR stands on its own and is based on `main`.
- **Claude:** this session worked through the work queue from the top. These proposals are queue items 7–10.
- **Folder structure:** `docs/01-activities.md`, `02-resources.md`, `03-games.md`, `05-skirmish.md`, `ROADMAP.md` changed; `reports/2026-10-22-proposals.md` added.

## Consistency check
- **Impling food vs D-080 and D-111.** D-023 says bundles make "Impling food", but the Imp doesn't battle (D-080), and cooked fish already feeds battle animals (D-111). Left as an Open question in 02, not fixed quietly.
- **Prices vs the TEST build.** The build's TEST numbers (base 2, refill 600, rows from 100, cap 4) don't match the proposal (base 1, refill 500 b, rows from 50 b, cap 4). They should be brought in line only once the proposal is approved.
- **Dig vs the TEST build.** The build has 9 coin squares and 2 item squares, paying 5–20 coins flat. The proposal has 9 coin, 3 item and 1 rare square, with coins scaled by tier and b.
- **Moves.** The build gives 1 move at level 1. The proposal gives 2.

## Suggestions (not applied)
- Once the base price is approved, the build's prices should read `b` from one place (`GameData.BASE_PRICE`) and derive the refill, rows and slots from it, so they can't drift apart.
- Farming and potions both add a camp station (farm patch, cauldron). The camp clearing may need to be a little bigger.

## What's next
The user reviews this PR. Approved items become D-numbers, then get built in place of the TEST numbers.

## What I need from you
1. **Prices:** approve, or change, the multiples of b in 02 (refill 500 b, rows and slots 50 b doubling with a cap of 4, hilts 25 b and 110 b). The base price itself waits on the staked balances.
2. **Potions:** approve the five potions, their strength by bundle tier, 10 minutes, the cauldron, and the limits (no mint tokens, no energy, gem chance capped at ×2.5).
3. **Impling food:** option A (treats for tamed animals) or B (cosmetic)?
4. **Farming, the dig, starting moves:** approve or change the additions in 01, 03 and 05.
