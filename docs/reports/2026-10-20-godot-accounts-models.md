# Report: Godot, accounts and Blockbench models (2026-10-20)

## In short
The game moves from the Three.js browser test to the **Godot** engine and is played **in the browser**. Players get **email accounts** with a **linked wallet**. Their staked **IMP coins** carry over when they link the same wallet. **Imp holders** can find **mint tokens** while gathering and spend them on impz.club. The game and impz.club share the **existing Supabase database**, whose current tables are now recorded. The world stays **stylised cartoon**, with Blockbench items and enemies that have a **slight voxel feel**. Implings are on **Robinhood Chain** and will move to **ApeChain**. Players without an Imp play as a **basic Imp**. Staking is finished. Sixteen decisions are recorded (D-036 to D-051). Everything past the decisions is Proposed.

## What changed
| Area | Change |
|---|---|
| Docs | **New, Draft:** `ACCOUNTS-AND-DATA.md`, `GODOT.md`, `MODELS-BLOCKBENCH.md`. **Updated:** `00-overview.md` (section 2; questions 1, 3 and 5 partly answered), `01-activities.md` (activity list, mint tokens, NFT touchpoints; moved to **Draft**), `02-resources.md` (currencies section, two input and output rows, NFT touchpoints), `ART-DIRECTION.md` (note at the top; world style answered), `BUILD-ROADMAP.md` (engine change, M6 and M7 blockers), `ROADMAP.md`, and `README.md` and `CLAUDE.md` in `docs/` (new docs listed; the "no pixel-art textures on 3D models" rule now excepts Blockbench items and enemies). |
| Decisions | **D-036** game type and activities. **D-037** Godot. **D-038** play as your Imp. **D-039** crypto kept small, coins in-game only. **D-040** mint tokens. **D-041** email accounts and a linked wallet. **D-042** staked coins carry over. **D-043** one shared Supabase database (Claude's choice at your request). **D-044** Blockbench models as FBX. **D-045** mint tokens for Imp holders only. **D-046** played in the browser. **D-047** stylised cartoon world, slight-voxel items and enemies. **D-048** Robinhood Chain now, ApeChain later. **D-049** basic Imp for non-holders. **D-050** staking finished, `wallet_connections` to be removed, Robinhood Chain contract recorded. **D-051** Imp `.glb` files hosted in Supabase Storage. |
| Folder | Added the three docs above and this report. No files removed. No code changed. |

## Evidence
- **GitHub:** `main` is at `366d530` (PR #26). Open draft PRs: #20 (stylised cave rock and ore veins) and #23 (Claude working rules). Neither uses D-036 or later. This work is draft PR #27 on `staging/design-godot-accounts-models`.
- **Claude:** this session read every `.md` in the repo and the open PRs' file lists. It looked at the local Godot test project (`Documents/map-world-test`): Godot 4.7, Forward+ renderer, a player using `impling.glb`, a world generator, a wind-swayed meadow, and an inventory screen. Claude could not open the "Hightail-like game in Godot" chat, which is in a separate conversation. You shared screenshots of `imp_coin_balances` and `imp_coin_claims` and an export of `profiles`. Only their columns are recorded, because this repo is public. `wallet_connections` was not seen and will be removed. The RLS policies were not seen. You confirmed the merchant claim is saved by Supabase. Imp models are referenced in the metadata as MML and kept locally as `.glb`. The basic Imp needs only its texture.
- **Folder structure:** 11 docs changed and 4 files added, all in `docs/`.

## Consistency check
- **Currencies vs the overview guardrail.** The overview's Proposed guardrail is "no more than one currency". There are now IMP coins and mint tokens. Mint tokens buy nothing in the game, so they act more like a reward ticket than a second currency, but the guardrail should be reworded or the overview should say so.
- **The Godot test project uses Forward+.** A browser game (D-046) needs the Compatibility renderer. The meadow shader and lighting need re-checking after the switch.
- **The Supabase data has four things to check** (ACCOUNTS-AND-DATA, section 3): one profile is marked claimed with no claim row; usernames aren't unique; a test row; some coin values are empty instead of 0.
- **D-019 and D-047 agree.** Ore veins stay in the Stylized Ore look, and the world stays stylised. Only items and enemies are Blockbench.
- **ROADMAP is behind on foraging and hunting.** D-022 to D-035 (PRs #24 to #26) have no pass log rows and no sub rows under 02 in Doc status. Left as it is, because that was out of scope for this session.
- **The root `README.md` and `CLAUDE.md`** still describe the Three.js test as the game. Left as is until the Godot project is moved into the repo (GODOT.md, open question 2).
- **The Godot test project isn't in the repo**, so the second collaborator can't see or review it.

## Suggestions (not applied)
1. **Done: the website's table permissions were fixed on 2026-10-20** (impz-club PR #1, then the database permissions).
2. **Move old coins on wallet link, not with claim codes** (ACCOUNTS-AND-DATA, section 7). Every balance is already tied to a wallet, and the signature proves ownership.
3. **After launch, keep one coin balance**: the game's. The merchant tab shows and spends the same balance.
4. **Switch the Godot test project to the Compatibility renderer before building more world.**
5. **Keep the chain and contract as settings** so the ApeChain move doesn't need a new game build, and keep token IDs the same across the move.
6. **Test the first Hare and pickaxe in the meadow** before modelling the rest, to check the slight-voxel look sits well in the stylised world.
7. **Move the Godot project into this repo** (`game/`) so both of you review it through PRs, once the bought asset pack's licence is checked.
8. **A deeper Blockbench research pass**, if you want one: study a set of top Hypixel-style models and turn what they share into worked examples in MODELS-BLOCKBENCH.

## What's next
Answer the questions below. Then G0 (the Godot project in the repo, on the Compatibility renderer) can start, and the wallet-link and coin-move server function can be written against the real tables.

## What I need from you
1. **When to move Supabase to a paid plan**, for daily backups.
2. **Review PR #27** and say "commit to main" when it's right.
