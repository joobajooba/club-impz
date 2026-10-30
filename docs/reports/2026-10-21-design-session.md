# Report: design session (2026-10-21)

## In short
In one session the user decided the rules for every system that was still open: the last of mining, foraging, hunting, the economy, the overview, skirmish, games, trade, lumbering and fishing. That is D-054 to D-112. The overview is now **In review**, and 03, 04 and 05 went from empty to **Draft**. Details the user didn't decide (the type chart, minigame prize tables, market listing rules, farming, prices) are written as **Proposed**. No game code changed: new rules are built in Godot (D-087).

## What changed
| Area | Change |
|---|---|
| Docs | 00 → In review. 01, 02 updated (still Draft). 03, 04, 05 written (Not started → Draft). ROADMAP, BUILD-ROADMAP, ACCOUNTS-AND-DATA, GODOT, docs/CLAUDE.md kept in step. |
| Decisions | D-054 to D-060 (mining), D-061 to D-066 (foraging), D-067 to D-072 (hunting), D-073 to D-078 (economy), D-080 to D-112 (overview, skirmish, games, trade, trophies, leather, lumbering, fishing). |
| Folder | 60 new icons in `sprites/items/` (`log_`, `plank_`, `sap_`, `fish_`, `cooked_`, `pearl_`), drawn by the new `sprites/build_lumber_fishing_icons.lua`. This report. |

## Evidence
- **GitHub:** the other collaborator merged #33 (the Godot project into `game/`, D-079) during this session and opened #34 (Blockbench Stone pickaxe). This session's decisions were renumbered to D-080 to D-112 to follow D-079. PRs #29 (mining), #30 (foraging), #31 (hunting) and #32 (economy) merged to `main` on 2026-10-21, after the backup tag `backup/main-20261021-1245`. 27 fully merged `staging/` branches were deleted at the user's request. Left: `staging/claude-workflow` (#23, open), `staging/stylized-rocks-veins` (#20, open) and `staging/copper-ore-vein` (not merged, PR #10 closed). D-080 onward are on `staging/design-all-systems`, in a draft PR.
- **Claude:** every decision was asked as a multiple-choice question in this session and recorded the same day. Where the user picked an option against Claude's advice (energy refills), the limits they chose are recorded with it (D-076).
- **Folder structure:** `git diff --stat main` on the branch: the design docs above, 60 PNGs, 1 Lua script, this report. Nothing outside `docs/` and `sprites/`.

## Consistency check
- **"Impling food" (D-023) no longer has an obvious meaning.** The Imp doesn't battle (D-080), and battle-animal food is cooked fish (D-111). What bundle-based Impling food is for is still open.
- **Two currencies.** Coins and mint tokens. The overview guardrail says "one currency unless the economy doc proves otherwise". Mint tokens are spent only on impz.club, so they behave more like a reward record than a currency, but the guardrail should be reworded or the exception accepted.
- **Unused top-tier items.** Starwood planks have no rod (D-110 stops at tier 10, made from Voidwood). They can only be sold (D-074), the same as before for Eclipse Dragon leather, which now makes outfits (D-104).
- **Water type** appears only at tier 12 (Tidecrest Serpent), so early teams can't use it. Noted as an open question in 05.
- **ROADMAP** still has no pass log rows for the 2026-10-17 foraging and hunting additions (D-022 to D-035).
- **`miningexample.png`** (untracked, in the repo root) shows Coal as tier 1 with an ingot, which disagrees with D-005. The user said to leave it.
- Fixed: the mint token link in 01 pointed at a section that had moved.

## Suggestions (not applied)
1. Let **Impling food** (D-023) be a cosmetic care item for the Imp, such as a happy animation or an emote unlock, so bundles have a use that is fair to free players.
2. Make **Fox or Boar the Water type** instead, so new players meet all the core types early.
3. Give **Starwood planks** a use: a top-tier cosmetic (a furniture or trophy-cabinet frame).
4. Add lumbering and fishing to `sprites/build_item_tables.lua`, so they get table pictures like mining, foraging and hunting.
5. Add the new systems (lumbering, fishing, skirmish, minigames, market) to the Godot milestones in GODOT.md.

## What's next
Review pass: the user reads the Proposed parts of 03, 04, 05 and the farming section in 01, approves or changes them, and sets prices once the staked balance sizes are known. The Godot project has since been added to the repo in `game/` (D-079, PR #33, by the other collaborator during this session), so the rebuild can start from there.

## What I need from you
1. **Staked balance sizes:** the largest and the typical `portable_imp_coin`, so the base sell price and every other price can be proposed.
2. **Review the Proposed parts:** the type chart and animal types (05), minigame details (03), market rules and the progress check (04), farming (01), and the new pitch (00).
3. **Questions only you can answer:** biomes and time of day (ART-DIRECTION), the Godot version and keeping or deleting the Three.js test (GODOT), Imp height and FBX or glTF (MODELS-BLOCKBENCH), the ApeChain contract and the wallet change waiting period (ACCOUNTS-AND-DATA).
